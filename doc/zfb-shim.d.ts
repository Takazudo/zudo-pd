// Local type shim for the bare `zfb/config` specifier.
//
// `@takazudo/zfb` is consumed as a published npm package (version pinned in
// `package.json`). It exposes its real config types AND `defineConfig` under
// the *scoped* subpath `@takazudo/zfb/config` → `dist/config.d.ts`. But
// `zfb.config.ts` imports from the *bare* specifier `zfb/config`, which zfb's
// build tool aliases to a runtime-only stub at parse time (`zfb-config-stub.mjs`
// — `defineConfig` is identity, carrying no types). No real file backs the bare
// `zfb/config` in `node_modules`, so this ambient declaration is what supplies
// the `defineConfig` + `ZfbConfig` types to `zfb.config.ts`.
//
// Per zfb next.48, instead of hand-maintaining a parallel `ZfbConfig`
// declaration here (which drifted and failed `pnpm check` with TS2353 whenever
// it lagged the engine — e.g. `bundle` then `codeHighlight.themeLight/themeDark`
// were missing; see Takazudo/zudo-front-builder#678 + zudolab/zudo-doc#1834), we
// re-export the published `@takazudo/zfb/config` surface from inside the
// bare-module declaration. This must stay INSIDE `declare module "zfb/config"`:
// the bare specifier has no backing file, so a top-level `export *` would not
// attach to it. Re-exporting keeps the bare-specifier types in lockstep with the
// installed engine automatically — no more hand reconciliation on bumps.
declare module "zfb/config" {
  export * from "@takazudo/zfb/config";
}
