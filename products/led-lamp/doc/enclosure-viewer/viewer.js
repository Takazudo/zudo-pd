import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const el = (id) => document.getElementById(id);
const status = el("status");
const viewport = el("viewport");

async function main() {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0x17191b);
  renderer.localClippingEnabled = true;
  viewport.append(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, .1, 3000);
  camera.up.set(0, 0, 1);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.listenToKeyEvents(viewport);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x777080, 2.2));
  for (const [x, y, z, intensity] of [[90, -90, 180, 3], [-120, 80, 100, 2]]) {
    const light = new THREE.DirectionalLight(0xfff6e2, intensity);
    light.position.set(x, y, z);
    scene.add(light);
  }
  const response = await fetch("manifest.json");
  if (!response.ok) throw new Error(`Manifest: HTTP ${response.status}`);
  const manifest = await response.json();
  const panelCount = manifest.config.panel_count;
  el("layers").max = panelCount;
  el("layers").value = panelCount;
  const loader = new STLLoader();
  const parts = [];
  const clip = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0);
  let frame;
  const render = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const { width, height } = viewport.getBoundingClientRect();
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
    });
  };
  controls.addEventListener("change", render);
  const resize = new ResizeObserver(render);
  resize.observe(viewport);
  const entries = manifest.parts.filter((p) => p.group !== "coupon");
  let loaded = 0;
  await Promise.all(entries.map(async (entry) => {
    const response = await fetch(entry.file);
    if (!response.ok) throw new Error(`${entry.name}: HTTP ${response.status}`);
    const geometry = loader.parse(await response.arrayBuffer());
    const material = new THREE.MeshStandardMaterial({ color: entry.color, roughness: .45, metalness: entry.group === "hardware" ? .7 : .08 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.fromArray(entry.position);
    scene.add(mesh);
    parts.push({ ...entry, mesh });
    status.textContent = `Loading CAD meshes… ${++loaded} / ${entries.length}`;
  }));
  parts.sort((a, b) => a.name.localeCompare(b.name));
  for (const part of parts.filter((p) => p.group === "print")) {
    const option = document.createElement("option");
    option.value = part.name;
    option.textContent = part.name;
    el("part").append(option);
  }
  const viewDirection = new THREE.Vector3(1.2, -1.65, 1.15).normalize();
  function fit(direction = viewDirection) {
    const bounds = new THREE.Box3();
    for (const part of parts) if (part.mesh.visible) bounds.expandByObject(part.mesh);
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    const { width, height } = viewport.getBoundingClientRect();
    const verticalFov = THREE.MathUtils.degToRad(camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * width / height);
    const radius = size.length() / 2;
    const distance = radius / Math.sin(Math.min(verticalFov, horizontalFov) / 2) * 1.03;
    camera.position.copy(center).addScaledVector(direction, distance);
    controls.target.copy(center);
    controls.update();
    render();
  }
  function update(refit = false) {
    const gap = Number(el("separation").value);
    const layers = Number(el("layers").value);
    const selected = el("part").value;
    el("separation-value").value = `${gap} mm`;
    el("layers-value").value = `${layers} / ${panelCount}`;
    for (const part of parts) {
      const panel = /^\d\d-/.test(part.name) && part.name !== "00-base";
      part.mesh.visible = selected ? part.name === selected :
        (!panel || part.level <= layers) &&
        (part.group !== "electronics" || el("electronics").checked) &&
        (!part.name.startsWith("post-") || el("hardware").checked);
      part.mesh.position.fromArray(selected ? [0, 0, 0] : part.position);
      part.mesh.rotation.y = selected ? 0 : THREE.MathUtils.degToRad(part.rotation_y_degrees || 0);
      if (!selected && part.group === "print") part.mesh.position.z += Math.max(0, part.level) * gap;
      if (!selected && part.group === "electronics") part.mesh.position.z += part.level * gap;
      if (!selected && part.group === "hardware" && part.level > 0) part.mesh.position.z += part.level * gap;
      const transparent = el("transparent").checked && part.group === "print";
      part.mesh.material.transparent = transparent;
      part.mesh.material.opacity = transparent ? .25 : 1;
      part.mesh.material.depthWrite = !transparent;
      part.mesh.material.clippingPlanes = el("section").checked && part.group !== "electronics" ? [clip] : [];
    }
    const part = parts.find((p) => p.name === selected);
    el("part-note").textContent = part ? `${part.note || part.name}. Size: ${part.bounds_mm[1].map((v, i) => (v - part.bounds_mm[0][i]).toFixed(1)).join(" × ")} mm.` : "Every panel is a separate, flat-printable part.";
    el("part-download").hidden = !part;
    if (part) el("part-download").href = part.file;
    status.textContent = part ? part.name : `${manifest.revision} · ${parts.filter((p) => p.mesh.visible).length} visible parts · ${manifest.datums.top.toFixed(1)} mm enclosure height`;
    viewport.dataset.visibleParts = parts.filter((p) => p.mesh.visible).length;
    viewport.dataset.separation = gap;
    if (refit) fit();
    render();
  }
  for (const id of ["separation", "layers"]) el(id).addEventListener("input", () => update(id === "separation"));
  for (const id of ["electronics", "hardware", "transparent", "section"]) el(id).addEventListener("change", () => update());
  el("part").addEventListener("change", () => update(true));
  function preset(kind) {
    el("part").value = "";
    el("separation").value = kind === "exploded" ? "4" : "0";
    el("layers").value = kind === "base" ? "0" : String(panelCount);
    el("section").checked = false;
    el("transparent").checked = false;
    el("hardware").checked = kind !== "base";
    el("electronics").checked = true;
    update();
    fit(kind === "underside" ? new THREE.Vector3(0, -.01, -1).normalize() :
      kind === "top" ? new THREE.Vector3(0, -.001, 1).normalize() : viewDirection);
  }
  for (const name of ["assembled", "exploded", "base", "underside", "top"]) el(name).addEventListener("click", () => preset(name));
  preset("assembled");
  viewport.dataset.ready = "true";
  window.addEventListener("pagehide", () => {
    resize.disconnect(); controls.dispose(); renderer.dispose(); cancelAnimationFrame(frame);
    for (const { mesh } of parts) { mesh.geometry.dispose(); mesh.material.dispose(); }
  }, { once: true });
}

main().catch((error) => {
  status.textContent = `Preview unavailable: ${error.message}. Download the STL collection or STEP model using the links.`;
  viewport.dataset.ready = "error";
  console.error(error);
});
