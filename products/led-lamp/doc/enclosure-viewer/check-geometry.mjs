// Check the actual print meshes, without requiring a CAD installation in doc CI.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../public/assets/enclosure/", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("manifest.json", root), "utf8"));
const parts = new Map(manifest.parts.map((part) => [part.name, part]));
const near = (a, b, message) => assert(Math.abs(a - b) < 1e-4, `${message}: ${a} != ${b}`);
const key = (point) => point.map((n) => n.toFixed(5)).join(",");

async function mesh(part) {
  const bytes = await readFile(new URL(part.file, root));
  const count = bytes.readUInt32LE(80);
  assert.equal(bytes.length, 84 + 50 * count, `${part.name}: invalid binary STL length`);
  const triangles = [];
  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  const edges = new Map();
  let volume = 0;
  for (let i = 0; i < count; i++) {
    const vertices = Array.from({ length: 3 }, (_, j) => Array.from({ length: 3 }, (_, k) => bytes.readFloatLE(84 + i * 50 + 12 + j * 12 + k * 4)));
    triangles.push(vertices);
    for (const vertex of vertices) vertex.forEach((value, axis) => {
      assert(Number.isFinite(value));
      minimum[axis] = Math.min(minimum[axis], value);
      maximum[axis] = Math.max(maximum[axis], value);
    });
    const [a, b, c] = vertices;
    volume += (a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6;
    for (let j = 0; j < 3; j++) {
      const from = key(vertices[j]), to = key(vertices[(j + 1) % 3]);
      assert.notEqual(from, to, `${part.name}: degenerate triangle edge`);
      const id = [from, to].sort().join("|");
      const edge = edges.get(id) || { count: 0, direction: 0 };
      edge.count++;
      edge.direction += from < to ? 1 : -1;
      edges.set(id, edge);
    }
  }
  assert(volume > 0, `${part.name}: inverted/empty mesh`);
  for (const edge of edges.values()) assert(edge.count === 2 && edge.direction === 0, `${part.name}: non-manifold or inconsistent winding`);
  near(minimum[2], 0, `${part.name}: print must start at Z=0`);
  return { triangles, minimum, maximum, volume };
}

function squareHole(shape, center, z, width, label) {
  const segments = [];
  for (const triangle of shape.triangles) {
    const points = new Map();
    for (let i = 0; i < 3; i++) {
      const a = triangle[i], b = triangle[(i + 1) % 3];
      if (Math.abs(b[2] - a[2]) < 1e-8) continue;
      const t = (z - a[2]) / (b[2] - a[2]);
      if (t < 0 || t > 1) continue;
      const point = a.map((v, j) => v + t * (b[j] - v));
      points.set(key(point), point);
    }
    if (points.size !== 2) continue;
    const line = [...points.values()];
    if (line.every((v) => [0, 1].every((j) => Math.abs(v[j] - center[j]) <= width / 2 + 1e-4))) segments.push(line);
  }
  assert(segments.length > 0, `${label}: square hole missing`);
  for (let axis = 0; axis < 2; axis++) {
    const values = segments.flatMap((line) => line.map((v) => v[axis]));
    near(Math.min(...values), center[axis] - width / 2, `${label}: hole lower bound`);
    near(Math.max(...values), center[axis] + width / 2, `${label}: hole upper bound`);
  }
  near(segments.reduce((sum, [a, b]) => sum + Math.hypot(a[0] - b[0], a[1] - b[1]), 0), width * 4, `${label}: square perimeter`);
}

const printable = manifest.parts.filter((p) => ["print", "coupon"].includes(p.group));
assert.equal(printable.filter((p) => p.group === "print").length, 21);
assert.equal(printable.filter((p) => p.group === "coupon").length, 8);
assert(!manifest.parts.some((p) => p.group === "hardware"), "Metal shell hardware must not return");
const meshes = new Map(await Promise.all(printable.map(async (p) => [p.name, await mesh(p)])));
const bands = manifest.parts.filter((p) => "profile_angle_degrees" in p);
assert.equal(bands.length, 6);
let outline;
for (const band of bands) {
  near(band.profile_angle_degrees, 0, "Twisting band forbidden");
  near(band.body_height_mm, 13, "Band body height");
  const shape = meshes.get(band.name);
  // Ignore only the bottom band's intentional USB-notch sector.
  const vertices = [...new Set(shape.triangles.flat().filter((p) => Math.hypot(p[0], p[1]) >= 54 && !(p[1] > 50 && Math.abs(p[0]) < 9.1)).map((p) => key(p.slice(0, 2))))].sort();
  assert(vertices.length > 0);
  if (outline) assert.deepEqual(vertices, outline, "Star profiles must align in the actual meshes");
  outline = vertices;
}
near(meshes.get("00-base").maximum[2], manifest.config.floor_thickness + manifest.config.pin_height, "Thin base with locating pins");
const opening = manifest.config.post_width + manifest.config.post_clearance;
for (let index = 1; index <= 3; index++) {
  const suffix = String(index).padStart(2, "0");
  const post = parts.get(`post-${suffix}-flat`), foot = parts.get(`foot-${suffix}`);
  const shape = meshes.get(post.name);
  const length = manifest.datums.top - manifest.config.post_bottom_recess;
  [length, 4, 4].forEach((v, axis) => near(shape.maximum[axis] - shape.minimum[axis], v, `${post.name}: flat dimensions`));
  near(shape.volume, length * 16, `${post.name}: solid cuboid`);
  near(post.rotation_y_degrees, -90, "Post assembly rotation");
  near(post.position[0] - 2, foot.position[0], "Post/foot X alignment");
  near(post.position[1], foot.position[1], "Post/foot Y alignment");
  near(post.position[2], 1, "Recessed post bottom");
  squareHole(meshes.get(foot.name), [0, 0], 3, opening, foot.name);
  for (const band of [...bands, parts.get("00-base")]) squareHole(meshes.get(band.name), foot.position.slice(0, 2), band.name === "00-base" ? 1.7 : 6.5, opening, band.name);
}
console.log("Enclosure geometry PASS: 29 manifold print STLs, six aligned bands, flat square posts and matching square channels");
