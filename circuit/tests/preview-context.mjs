// Only project paths/options adapt to the installed package; no preview engine is vendored.
import { mapped, readEvidenceIndex, CIRCUIT_SELECTION } from "./project-context.mjs";
import { internal } from "./compatibility-helpers.mjs";
export { CIRCUIT_SELECTION };
export const FOOTPRINT_MASTER_ROOT = mapped.paths.footprintMasterRoot;
export const FOOTPRINT_ROOT = mapped.paths.footprintLibraryRoot;
export const PREVIEW_ROOT = mapped.paths.footprintPreviewRoot;
const check = await internal("footprint-previews/check.js");
export const checkFootprintPreviews = (selections, previewRoot=PREVIEW_ROOT, footprintLibraryRoot=FOOTPRINT_ROOT, footprintMasterRoot=FOOTPRINT_MASTER_ROOT) => check.checkFootprintPreviews({selections,previewRoot,footprintLibraryRoot,footprintMasterRoot,renderer:mapped.config.cad.previewRenderer});
export const { assertFootprintLibraryParity } = await internal("footprint-previews/parity.js");
export const { suppressFootprintText } = await internal("footprint-previews/footprint.js");
export const { normalizeSvg, validateSvg } = await internal("footprint-previews/svg.js");
const { footprintSelectionsFromIndex } = await internal("footprint-previews/selection.js");
export const readFootprintSelections = async () => footprintSelectionsFromIndex(await readEvidenceIndex(), CIRCUIT_SELECTION);
