// ADR-016 seam: the package-owned island seed module. Importing it from the
// docs route (side-effect only) registers the footprint/WRL preview islands
// so they hydrate without this host forking a route stub of its own.
import "@takazudo/zudo-circuit-doc/islands";
