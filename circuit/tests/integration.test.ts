/**
 * The cross-component rules: projection and page.
 *
 * Split from `projection.test.ts` and `render.test.ts` because the rules are a
 * separate dataset with separate hazards. Two of them dominate:
 *
 *   - a rule published without its refusal, its conditions or a calculation's
 *     conditions is the friendly implied PASS this whole feature exists to
 *     refuse, so each is asserted present rather than merely "the page renders";
 *   - a rule references records and facts it does not own, so every reference
 *     has to resolve to a real anchor on a real page — the case the generator
 *     fails closed on.
 */

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, it } from "node:test";

import { ComponentDocsError } from "@takazudo/zudo-circuit-doc";
import { PublicationPolicy } from "@takazudo/zudo-circuit-doc";
import { parseIntegrationRules } from "@takazudo/zudo-circuit-doc";
import { projectIntegrationRules } from "@takazudo/zudo-circuit-doc";
import { INTEGRATION_INDEX_ANCHOR, renderIntegration } from "@takazudo/zudo-circuit-doc";
import { buildRecordIndex } from "@takazudo/zudo-circuit-doc";
import { assertAnchorIntegrity } from "@takazudo/zudo-circuit-doc";
import { GENERATED_ROOT } from "./project-context.mjs";
import {
  FIXTURE_MATRIX,
  FIXTURE_SELECTION,
  fixtureIntegrationRules,
} from "./provider-fixtures.ts";
import { FIXTURE_IDS, HOSTILE_TEXT, fixtureModel } from "./fixtures.ts";
import type {
  ProviderIntegrationRule,
  ProviderRuleCalculation,
} from "@takazudo/zudo-circuit-doc";
import type { PublicIntegrationRule } from "@takazudo/zudo-circuit-doc";

const CONTEXT = {
  publishedRecordIds: new Set(["rec-driver", "rec-sense", "rec-handfit"]),
  recordIdByFactId: new Map([
    ["fact-driver-identity", "rec-driver"],
    ["fact-driver-vin-max", "rec-driver"],
    ["fact-driver-current-min", "rec-driver"],
    ["fact-sense-resistance-max", "rec-sense"],
    ["fact-handfit-pitch", "rec-handfit"],
  ]),
  ownerSkill: "circuit-fixture-integration",
};

function project(
  transform: (rules: ProviderIntegrationRule[]) => ProviderIntegrationRule[] = (rules) => rules,
  context = CONTEXT,
): PublicIntegrationRule[] {
  return projectIntegrationRules(
    fixtureIntegrationRules(transform),
    context,
    new PublicationPolicy(FIXTURE_MATRIX, FIXTURE_SELECTION),
  );
}

function throwsWith(run: () => unknown, code: string): void {
  assert.throws(
    run,
    (error: unknown) => error instanceof ComponentDocsError && error.code === code,
  );
}

const model = fixtureModel();
const page = renderIntegration(model, buildRecordIndex(model)).contents;

describe("rule projection", () => {
  it("keeps every rule field, in the ruleset's own order", () => {
    const rules = project();
    assert.deepEqual(
      rules.map((rule) => rule.ruleId),
      ["rule-fixture-power-stage", "rule-fixture-chain", "rule-fixture-bare"],
    );

    const [powerStage] = rules;
    assert.ok(powerStage);
    assert.equal(powerStage.anchor, "rule-fixture-power-stage");
    // `integration.ownerSkill` is denied on zudo-pd's real matrix (`FIXTURE_MATRIX`
    // is `CIRCUIT_PUBLICATION_MATRIX` itself — see `matrix.ts`), so this always
    // resolves to `null` rather than the provider's `ownerSkill` context value —
    // `claudeResources` is `false`, so no `/docs/claude-skills/` route exists.
    assert.equal(powerStage.ownerSkill, null);
    assert.equal(powerStage.verdict, "NEEDS BENCH");
    assert.equal(
      powerStage.refusal,
      "Do not promote nominal arithmetic to a guaranteed assembled-stage PASS.",
    );
  });

  it("normalises both recorded calculation shapes into cases", () => {
    const [powerStage] = project();
    const [varied, single] = powerStage?.calculations ?? [];

    // A `results` list: one case per evaluated input, values carried verbatim.
    assert.equal(varied?.calculationId, "calc-fixture-current");
    assert.equal(varied?.resultKey, "current_a");
    assert.deepEqual(
      varied?.cases.map((entry) => entry.value),
      [0.48484848484848486, 0.45714285714285713],
    );
    assert.deepEqual(varied?.cases[0]?.inputs, [{ key: "r_sense_ohm", value: 0.198 }]);

    // A bare result under its own `result_key`: one case, no varied input.
    assert.equal(single?.calculationId, "calc-fixture-margin");
    assert.equal(single?.cases.length, 1);
    assert.deepEqual(single?.cases[0]?.inputs, []);
    assert.equal(single?.cases[0]?.value, 9.6);
  });

  it("never evaluates an expression itself", () => {
    // `0.096 / 0.198` is 0.48484848484848486 and `0.096 / 0.21` is
    // 0.45714285714285713 — the recorded values. Swapping one for a number the
    // expression does NOT produce must survive projection unchanged: this page
    // publishes the evidence, and a generator that silently "corrected" it
    // would be a second calculator disagreeing with the source of truth.
    const [powerStage] = project((rules) =>
      rules.map((rule) =>
        rule.rule_id === "rule-fixture-power-stage"
          ? {
              ...rule,
              conditioned_calculations: (rule.conditioned_calculations ?? []).map((entry) =>
                entry.calculation_id === "calc-fixture-current"
                  ? { ...entry, results: [{ r_sense_ohm: 0.198, current_a: 1.25 }] }
                  : entry,
              ),
            }
          : rule,
      ),
    );
    assert.equal(powerStage?.calculations[0]?.cases[0]?.value, 1.25);
  });

  it("keeps an evidence-chain stage that carries no facts", () => {
    const chain = project()[1]?.evidenceChain ?? [];
    assert.deepEqual(
      chain.map((stage) => [stage.stage, stage.status, stage.factIds.length]),
      [
        ["official-source", "MIXED", 1],
        ["as-built", "OPEN", 1],
        ["bench", "OPEN", 0],
      ],
    );
  });

  it("publishes a rule that has neither calculations nor a chain", () => {
    const bare = project()[2];
    assert.deepEqual(bare?.calculations, []);
    assert.deepEqual(bare?.evidenceChain, []);
    assert.equal(bare?.refusal, "Do not read the absence of a calculation as the absence of a risk.");
  });

  it("refuses a rule naming a record that is not published", () => {
    throwsWith(
      () =>
        project(undefined, {
          ...CONTEXT,
          publishedRecordIds: new Set(["rec-driver", "rec-handfit"]),
        }),
      "STALE_SELECTION",
    );
  });

  it("refuses a rule, calculation or chain stage naming an unpublished fact", () => {
    for (const mutate of [
      (rule: ProviderIntegrationRule) => ({ ...rule, fact_ids: [...rule.fact_ids, "fact-gone"] }),
      (rule: ProviderIntegrationRule) => ({
        ...rule,
        conditioned_calculations: (rule.conditioned_calculations ?? []).map((entry) => ({
          ...entry,
          fact_ids: [...entry.fact_ids, "fact-gone"],
        })),
      }),
      (rule: ProviderIntegrationRule) => ({
        ...rule,
        evidence_chain: (rule.evidence_chain ?? []).map((stage) => ({
          ...stage,
          fact_ids: [...stage.fact_ids, "fact-gone"],
        })),
      }),
    ]) {
      throwsWith(() => project((rules) => rules.map(mutate)), "STALE_SELECTION");
    }
  });

  it("refuses a calculation whose recorded result is missing or unusable", () => {
    const rewrite = (
      change: (entry: Record<string, unknown>) => Record<string, unknown>,
    ): ProviderIntegrationRule[] =>
      fixtureIntegrationRules((rules) =>
        rules.map((rule) =>
          rule.conditioned_calculations === undefined
            ? rule
            : {
                ...rule,
                conditioned_calculations: rule.conditioned_calculations.map(
                  (entry) => change({ ...entry }) as ProviderRuleCalculation,
                ),
              },
        ),
      );

    // No `results` and no bare result under `result_key`.
    throwsWith(
      () =>
        projectIntegrationRules(
          rewrite(({ results: _results, margin_v: _margin, ...rest }) => rest),
          CONTEXT,
          new PublicationPolicy(FIXTURE_MATRIX, FIXTURE_SELECTION),
        ),
      "ADAPTER_CONTRACT",
    );

    // A result row missing the key the calculation says carries the result.
    throwsWith(
      () =>
        projectIntegrationRules(
          rewrite((entry) => ({ ...entry, results: [{ r_sense_ohm: 0.198 }] })),
          CONTEXT,
          new PublicationPolicy(FIXTURE_MATRIX, FIXTURE_SELECTION),
        ),
      "ADAPTER_CONTRACT",
    );

    // A shape there is no honest rendering for.
    throwsWith(
      () =>
        projectIntegrationRules(
          rewrite((entry) => ({ ...entry, results: [{ current_a: [1, 2] }] })),
          CONTEXT,
          new PublicationPolicy(FIXTURE_MATRIX, FIXTURE_SELECTION),
        ),
      "ADAPTER_CONTRACT",
    );
  });
});

describe("rule parsing", () => {
  it("refuses a duplicate rule or calculation id", () => {
    const duplicateRule = {
      schema_version: 1,
      rules: [...fixtureIntegrationRules(), ...fixtureIntegrationRules()],
    };
    throwsWith(() => parseIntegrationRules(duplicateRule), "ADAPTER_CONTRACT");

    const duplicateCalculation = {
      schema_version: 1,
      rules: fixtureIntegrationRules((rules) =>
        rules.map((rule) =>
          rule.rule_id === "rule-fixture-bare"
            ? {
                ...rule,
                rule_id: "rule-fixture-bare-copy",
                conditioned_calculations:
                  rules[0]?.conditioned_calculations ?? [],
              }
            : rule,
        ),
      ),
    };
    throwsWith(() => parseIntegrationRules(duplicateCalculation), "ADAPTER_CONTRACT");
  });

  it("refuses a ruleset declaring another schema version", () => {
    throwsWith(
      () => parseIntegrationRules({ schema_version: 2, rules: fixtureIntegrationRules() }),
      "ADAPTER_CONTRACT",
    );
  });

  it("refuses a rule that lists the same record or fact twice", () => {
    // Nothing downstream deduplicates: a repeated record would render twice on
    // the integration page and twice again on that record's own page.
    for (const mutate of [
      (rule: ProviderIntegrationRule) => ({
        ...rule,
        record_ids: [...rule.record_ids, rule.record_ids[0] as string],
      }),
      (rule: ProviderIntegrationRule) => ({
        ...rule,
        fact_ids: [...rule.fact_ids, rule.fact_ids[0] as string],
      }),
    ]) {
      throwsWith(
        () =>
          parseIntegrationRules({
            schema_version: 1,
            rules: fixtureIntegrationRules((rules) => rules.map(mutate)),
          }),
        "ADAPTER_CONTRACT",
      );
    }
  });

  it("refuses a missing reference list rather than crashing later", () => {
    // `rules.json` is the one provider file `validate.py` does not cover, so a
    // missing array has to fail here, named, instead of as a TypeError from a
    // `.map` somewhere in the projection.
    throwsWith(
      () =>
        parseIntegrationRules({
          schema_version: 1,
          rules: fixtureIntegrationRules((rules) =>
            rules.map(({ fact_ids: _factIds, ...rest }) => rest as ProviderIntegrationRule),
          ),
        }),
      "ADAPTER_CONTRACT",
    );
  });

  it("refuses a result key that only exists on the prototype", () => {
    // `in` would find `toString`; `Object.hasOwn` does not. Without that the
    // "result" would be an inherited function.
    throwsWith(
      () =>
        projectIntegrationRules(
          fixtureIntegrationRules((rules) =>
            rules.map((rule) =>
              rule.conditioned_calculations === undefined
                ? rule
                : {
                    ...rule,
                    conditioned_calculations: rule.conditioned_calculations.map((entry) => ({
                      ...entry,
                      result_key: "toString",
                      results: undefined,
                    })),
                  },
            ),
          ),
          CONTEXT,
          new PublicationPolicy(FIXTURE_MATRIX, FIXTURE_SELECTION),
        ),
      "ADAPTER_CONTRACT",
    );
  });
});

describe("integration page", () => {
  it("renders every rule's refusal, verdict and conditions", () => {
    for (const rule of model.integration) {
      assert.ok(
        page.includes(`<EvidenceAnchor id="${rule.anchor}" />`),
        `${rule.ruleId} has no anchor`,
      );
      assert.ok(
        page.includes("**This rule refuses to conclude:**"),
        "a rule rendered without its refusal",
      );
    }
    // One domain, one refusal and one conditions line per rule, plus one
    // conditions line per conditioned calculation — none dropped, including on
    // the rule whose every recorded string is MDX-active.
    assert.equal(page.split("**Domain:**").length - 1, 3);
    assert.equal(page.split("**This rule refuses to conclude:**").length - 1, 3);
    assert.equal(page.split("**Conditions:**").length - 1, 5);
  });

  it("links every rule to its records and facts, and marks the unpublished one", () => {
    assert.ok(
      page.includes(`(/docs/components/records/${FIXTURE_IDS.driverSlug}/)`),
      "a spanned record is not linked",
    );
    assert.ok(
      page.includes(
        `(/docs/components/records/${FIXTURE_IDS.driverSlug}/#${FIXTURE_IDS.crossRecordFact})`,
      ),
      "a cited fact is not linked to its anchor",
    );
    // A fact the model does not publish is still printed, marked as such.
    assert.ok(page.includes("`fact-fixture-absent` (not published)"));
  });

  it("publishes each calculation's expression, inputs, results and conditions", () => {
    assert.ok(page.includes('<EvidenceAnchor id="calc-fixture-current" />'));
    assert.ok(page.includes("0.096 / r_sense_ohm"));
    assert.ok(page.includes("nominal division only"));
    // Values carried verbatim, not re-rounded.
    assert.ok(page.includes("0.48484848484848486"));
    // The no-varied-input case still gets a table, with just the result column.
    assert.ok(page.includes("margin\\_v"));
    assert.ok(page.includes("9.6"));
  });

  it("says so when a rule records no conditioned arithmetic", () => {
    assert.ok(page.includes("**Conditioned calculations:** none are recorded for this rule."));
  });

  it("keeps the evidence chain's stages, statuses and empty stage", () => {
    assert.ok(page.includes("## Source-to-bench evidence chain") || page.includes("### Source-to-bench evidence chain"));
    assert.ok(page.includes("official-source"));
    assert.ok(page.includes("| bench "));
    assert.ok(page.includes("no fact is recorded at this stage"));
    // The wording this replaced ("none recorded") read as an unfilled cell
    // rather than as an established absence — see the barren-stage suite below.
    assert.ok(!page.includes("none recorded"));
  });

  it("never synthesises a rolled-up verdict", () => {
    for (const banned of ["rules passed", "overall verdict", "PASS overall", "all rules"]) {
      assert.equal(page.includes(banned), false, `page synthesises "${banned}"`);
    }
  });

  it("links back to the bundle when the owner skill is known", () => {
    // Generic renderer coverage: `agentResourceSection` in
    // `core/render/integration.ts` still has to render a real link when
    // `ownerSkill` IS populated — `fixtures.ts` hardcodes one, exercising
    // that branch. zudo-pd's real projection never actually reaches it
    // (`integration.ownerSkill` is denied — see the next test), but the
    // renderer is provider-neutral core code and both branches are load-bearing.
    assert.ok(page.includes("(/docs/claude-skills/circuit-fixture-integration/)"));
  });

  it("states an absence rather than a wrong link when the owner skill is unknown", () => {
    // The branch zudo-pd's real projection always takes: `integration.ownerSkill`
    // is denied (see `matrix.ts`), so `/docs/claude-skills/circuit-spec-integration/`
    // does not exist as a route on this site.
    const noOwner: PublicIntegrationRule = { ...(model.integration[0] as PublicIntegrationRule), ownerSkill: null };
    const withoutOwner = { ...model, integration: [noOwner] };
    const rendered = renderIntegration(withoutOwner, buildRecordIndex(withoutOwner), {agentResources: false, integrationDomainGloss: {}, generatedNotice: true}).contents;
    assert.ok(!rendered.includes("/docs/claude-skills/"));
    assert.ok(rendered.includes("No owning bundle is identified in the published model."));
  });

  it("keeps the index anchor other pages link by", () => {
    assert.equal(INTEGRATION_INDEX_ANCHOR, "integration-index");
    assert.ok(page.includes('<EvidenceAnchor id="integration-index" />'));
  });

  it("escapes MDX-active evidence text in a refusal", () => {
    // The hostile rule's refusal is HOSTILE_TEXT. `buildPage` has already run
    // `assertMdxSafe` over this page, so reaching here at all is the assertion;
    // this pins the text down so a future renderer cannot quietly drop it.
    assert.ok(page.includes("brace"), "the hostile refusal was dropped");
    // Every active delimiter is backslash-escaped, and no line opens a
    // directive. `assertMdxSafe` already ran inside `buildPage`; these pin the
    // exact escaping down so a serializer change shows up here.
    assert.ok(page.includes("\\{expr}"), "a brace reached the page unescaped");
    assert.equal(/^\s*:::/mu.test(page), false, "a line opens a directive");
    assert.equal(/(?<!\\)\{/u.test(page), false, "an unescaped brace survived");
  });

  it("survives a corpus with no rules at all", () => {
    const empty = renderIntegration(
      { ...model, integration: [] },
      buildRecordIndex({ ...model, integration: [] }),
    ).contents;
    assert.ok(empty.includes("No cross-component integration rule is declared."));
    assert.ok(empty.includes('<EvidenceAnchor id="integration-index" />'));
  });

  it("is deterministic", () => {
    assert.equal(renderIntegration(model, buildRecordIndex(model)).contents, page);
  });
});

describe("record pages link back to the rules that name them", () => {
  it("names each rule once on each participating record page", () => {
    const index = buildRecordIndex(model);
    const driverRules = index.rulesByRecordId.get(FIXTURE_IDS.driverRecord) ?? [];
    assert.deepEqual(
      driverRules.map((rule) => rule.ruleId),
      ["rule-fixture-power-stage", "rule-fixture-chain"],
    );
    // A record no rule names is a real state, not an omission.
    assert.equal(index.rulesByRecordId.get("rec-fixture-nobody"), undefined);
  });

  it("keeps rule and calculation anchors unique across the integration page", () => {
    assertAnchorIntegrity(model);
    const collided = {
      ...model,
      integration: model.integration.map((rule) =>
        rule.ruleId === "rule-fixture-chain"
          ? { ...rule, anchor: model.integration[0]?.anchor ?? rule.anchor }
          : rule,
      ),
    };
    throwsWith(() => assertAnchorIntegrity(collided), "IDENTITY_COLLISION");
  });
});

describe("evidence-chain stages with nothing recorded against them", () => {
  it("says what an empty stage means instead of leaving the row bare", () => {
    // Structurally the same case as an open coverage domain with no blocking
    // fact, which the record pages already handle explicitly: nothing addresses
    // the stage, so the surrounding text is the only content the row has, and a
    // bare cell reads as "not filled in yet" rather than "not established".
    const barren = model.integration.flatMap((rule) =>
      rule.evidenceChain.filter((stage) => stage.factIds.length === 0),
    );
    // Guard against a vacuous pass: with no empty stage this proves nothing.
    assert.ok(barren.length > 0, "the fixture has no empty evidence-chain stage");

    for (const stage of barren) {
      assert.ok(page.includes(stage.stage), `${stage.stage} is missing from the page`);
      assert.ok(page.includes(stage.status), `${stage.stage} does not state its status`);
    }
    assert.equal(page.split("no fact is recorded at this stage").length - 1, barren.length);
    assert.ok(page.includes("nothing has been established there yet"));
  });

  it("marks every barren stage on the committed page for the real corpus", async () => {
    // The fixture carries one; the real chain carries five, and those five are
    // the ones a reader actually meets. The committed page is deterministic and
    // `check:components` proves it is fresh, so asserting on it is cheap.
    const committed = await readFile(
      join(GENERATED_ROOT, "integration", "index.mdx"),
      "utf8",
    );
    for (const stage of ["pcb-orientation", "bom-cpl", "as-built", "programmed", "bench"]) {
      assert.ok(
        // Leading whitespace tolerated: the chain table sits inside an
        // `<EvidenceTable>` scroll container, so its rows are indented.
        new RegExp(
          `^\\s*\\| ${stage}\\s+\\| OPEN\\s+\\| no fact is recorded at this stage`,
          "mu",
        ).test(committed),
        `${stage} does not render as an explicitly-empty OPEN stage`,
      );
    }
    assert.equal(committed.split("no fact is recorded at this stage").length - 1, 5);
  });
});
