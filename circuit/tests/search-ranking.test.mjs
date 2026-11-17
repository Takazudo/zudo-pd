import test from "node:test";
import assert from "node:assert/strict";
import { prepareLc, scoreEntry } from "../../node_modules/@takazudo/zudo-doc/dist/search-widget-script/scoring.js";

test("a broad board-p query exposes distinct PD and LED pages ahead of incidental component mentions", () => {
  const entries = [
    { title: "BZT52C11-7-F", url: "/docs/components/records/bzt52c11", description: "Used on board-p", body: "board-p placement" },
    { title: "Board P — Variants and Lineage", url: "/docs/architecture/board-p", description: "", body: "" },
    { title: "Historical LED Board P net table", url: "/docs/led-lamp/architecture/board-p", description: "", body: "" },
    { title: "Unrelated", url: "/docs/project", description: "", body: "" },
  ];
  prepareLc(entries);
  const scores = entries.map((entry) => scoreEntry(entry, ["board-p"]));
  assert.ok(scores[1] > scores[0]);
  assert.ok(scores[2] > scores[0]);
  assert.equal(scores[3], 0);
  assert.ok(scoreEntry(entries[2], ["led", "board-p"]) > scoreEntry(entries[1], ["led", "board-p"]));
});
