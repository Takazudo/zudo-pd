// Project configuration only; all evidence projection is supplied by the installed package.
import { join } from "node:path";
import { root, mapping, json } from "./compatibility-helpers.mjs";
import { readEvidenceIndex as packageRead, createCircuitAdapter as packageAdapter } from "@takazudo/zudo-circuit-doc";
export const mapped = await mapping(root);
export const REPO_ROOT = root;
export const DOC_ROOT = join(root, "doc");
export const GENERATED_ROOT = mapped.paths.generatedRoot;
export const PREFLIGHT_FILE = mapped.paths.preflightFile;
export const CIRCUIT_PUBLICATION_MATRIX = mapped.matrix;
export const CIRCUIT_SELECTION = mapped.selection;
export const CIRCUIT_DOCUMENT_VERIFICATION = await json(join(root, "circuit/publication/document-verification.json"));
export const readEvidenceIndex = (options = {}) => packageRead({paths: mapped.paths, selection: mapped.selection, reference: mapped.reference, ...options});
export const createCircuitAdapter = (options = {}) => packageAdapter({paths: mapped.paths, selection: mapped.selection, reference: mapped.reference, ...options});

export * from "@takazudo/zudo-circuit-doc";
