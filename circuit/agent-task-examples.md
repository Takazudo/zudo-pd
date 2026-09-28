# Everyday agent requests for a circuit project

These are nine short requests an owner can give an agent in this project, each in English and Japanese. They are **task examples**, not an installed skill. The agent handles each one by following [WORKFLOW.md](./WORKFLOW.md); the "Workflow and commands" line under each example names the section and the project commands involved.

The everyday request should remain short. This project supplies the shared conventions for exact identity, evidence retention, asset checks, generated documentation, and truthful status reporting. The “completion expectations” below explain what those short requests should produce. Every task starts with the shared entry (`pnpm circuit:check` before editing) and ends with the four-part completion report.

Replace uppercase tokens such as `COMPONENT_ID`, `CLAIM_ID`, and `REVISION` with the actual project references. None of the examples selects a part or assumes a circuit rating. If a user names a component in ordinary language, the local agent should resolve it through the project's component evidence bundle and report ambiguity when there is more than one plausible match.

## 1. Download the exact datasheet

**English request**

> Download the datasheet for COMPONENT_ID and keep it with the component evidence. Check that it covers the exact manufacturer, MPN, and package suffix we are using. Update the source record and tell me which design-relevant information is still missing.

**日本語の依頼例**

> COMPONENT_ID のデータシートをダウンロードして、部品のエビデンスと一緒に保存して。採用候補のメーカー・正式型番・パッケージ末尾まで一致する資料か確認し、出典の記録を更新してほしい。設計上必要な情報で、まだ確認できていないものも教えて。

**Completion expectations**

- Resolve the exact component first. Prefer the manufacturer's document; record a distributor-hosted copy as such.
- Retain the actual downloaded file when available, its originating URL, access date, document identity or revision, checksum, and applicability to the exact part.
- Distinguish “source linked,” “file acquired,” and “relevant specification checked.” Downloading the PDF does not mean every claim has been audited.
- If the file cannot be obtained, preserve the actual attempted source and limitation. Do not create an empty file and call it a downloaded datasheet.

**Workflow and commands:** Workflow C. Cache the bytes under `.circuit-cache/sources/`, check for `%PDF-`, update `sources.json`, then `pnpm circuit:generate` and `pnpm circuit:check`.

## 2. Find and check a 3D model

**English request**

> Find 3D data for COMPONENT_ID and add it to the project. Check the body dimensions, mounting datum, and relevant pin or actuator positions against the exact part's drawing. If only a family model is available, make that limitation visible and tell me what must be corrected.

**日本語の依頼例**

> COMPONENT_ID の 3D データを探してプロジェクトに追加して。外形寸法、取り付け基準面、関係する端子や操作部の位置を、その型番の図面と照合してほしい。シリーズ共通モデルしかない場合は、そのことを明記して、修正が必要な箇所を教えて。

**Completion expectations**

- Preserve the acquired original and its provenance. Record the fidelity class (`exact-vendor`, `family`, `derived` or `unavailable`) in the CAD asset receipt.
- If conversion or correction is requested and possible, preserve the transformation and link the derived result to its source.
- Inspect orientation, scale, relevant dimensions, and mounting datum. A successful preview is a rendering result, not proof of dimensional correctness.
- Report unavailable drawings or unknown dimensions as gaps. Do not infer numeric pin mapping from visual resemblance.

**Workflow and commands:** Workflow D. Write a receipt in `circuit/cad-receipts/`, classify fidelity, then `pnpm previews:generate`, `pnpm exec zudo-circuit-doc footprints check` and `pnpm exec zudo-circuit-doc models --check` when CAD is enabled.

## 3. Verify a claimed specification

**English request**

> Check whether CLAIM_ID is actually supported for COMPONENT_ID in our intended use. Use the retained primary source, preserve the value's conditions and whether it is typical, guaranteed, recommended, or an absolute maximum, and update the canonical evidence. Explain whether the project conclusion still follows.

**日本語の依頼例**

> COMPONENT_ID について、CLAIM_ID の仕様が本当に根拠付きで言えるか確認して。このプロジェクトの使用条件に対して成り立つか見てほしい。一次資料の該当箇所を確認して、typical・保証値・推奨条件・絶対最大定格の違いと条件を残したうえで部品のエビデンスを更新し、設計上の結論がそのまま成り立つか教えて。

**Completion expectations**

- State the exact claim, source locator, value, unit, qualifier, and conditions.
- Separate a direct source fact from derived reasoning. Preserve calculation inputs and assumptions when the conclusion combines facts.
- If the current narrative overstates the evidence, correct or qualify it and identify the affected decision or integration analysis.
- A typical characteristic must not be relabeled a worst-case guarantee. Missing evidence stays unresolved even if a similar part behaves as expected.

**Workflow and commands:** Workflow E. Update `facts.json` and `coverage.json`, then `pnpm circuit:generate`, `pnpm circuit:check` and `pnpm check`.

## 4. Check interactions between components

**English request**

> Review INTERFACE_ID at REVISION. Trace the relevant component facts and configuration through the complete connection, including startup, reset, and one-side-powered conditions where they apply. Record the conditioned calculations and identify what still requires measurement.

**日本語の依頼例**

> REVISION の INTERFACE_ID を確認して。関係する部品の仕様と設定を、接続全体として追ってほしい。関係する場合は起動時、リセット時、片側だけ給電されている状態も含めて確認し、計算に使った条件と根拠を残して。実測しないと分からない点も分けて教えて。

**Completion expectations**

- Link the exact design revision, endpoints, component records, input facts, and relevant configuration.
- Evaluate the requested conditions rather than assuming each component's individually valid rating proves the whole interface.
- Preserve unknowns such as source behavior, parasitics, actual wiring, or unmeasured transient response when they affect the conclusion.
- Create or update the integration evidence and concise authored interpretation. Do not claim bench verification from a paper analysis.

**Workflow and commands:** Workflow E with the integration rules in `.claude/skills/circuit-spec-integration/references/rules.json`; `pnpm circuit:check` and `pnpm check`.

## 5. Compare a possible replacement

**English request**

> PART_A is becoming hard to source. Assess PART_B as a replacement at the current placements. Compare the exact identities, relevant behavior, pins, package, mechanical fit, firmware effects, and assembly implications. Give me a change-impact note and a recommendation with any remaining conditions.

**日本語の依頼例**

> PART_A の入手が難しくなってきたので、今の実装箇所で PART_B に置き換えられるか調べて。正式型番、必要な動作、ピン、パッケージ、機械的な収まり、ファームウェアと実装方法への影響を比較してほしい。変更影響のメモを作って、残っている確認条件と一緒に採用の見立てを教えて。

**Completion expectations**

- Establish exact identity and evidence for both parts. Do not treat a matching short name or generic package as sufficient compatibility.
- Explain which required properties are equivalent, different, or still unknown for the intended conditions.
- Identify affected facts, integration records, schematic placements, assets, firmware, generated outputs, and prior verification.
- This wording requests an assessment. Applying the replacement becomes a separate concrete implementation task when the owner requests it.

**Workflow and commands:** Workflows B, C and E for the candidate, recorded as a change-impact note from `circuit/templates/project-docs/project/change-impact.mdx`; no inventory or selection change until the replacement is applied.

## 6. Implement an already selected change

**English request**

> Apply DECISION_ID to REVISION. Update the authoritative design inputs, dependent component and integration evidence, relevant CAD assets, generated documentation, and the change-impact note. Run the checks supported by this project and report the exact changes, results, and any hardware checks still pending.

**日本語の依頼例**

> DECISION_ID の変更を REVISION に反映して。設計の正本、関係する部品・組み合わせのエビデンス、必要な CAD データ、生成ドキュメント、変更影響メモまで揃えて更新してほしい。このプロジェクトで実行できる確認を行い、変更内容と結果、まだ必要な実機確認をまとめて。

**Completion expectations**

- Read the accepted decision and remain within its scope. Continue the routine edits and generation already requested without another approval loop.
- Change authoritative inputs before derived outputs. Use only the commands listed in WORKFLOW.md.
- Refresh project-state evidence and dependencies where the implementation changed. Keep previous hardware observations attached to their original revision.
- Report a materially different choice if the implementation reveals one; do not silently reinterpret the selected design to make a check pass.

**Workflow and commands:** Workflows B and G. Update evidence, inventory and `circuit/publication/selection.json` in one diff, then `pnpm circuit:generate`, `pnpm check`, `pnpm build` and `pnpm check:site`.

## 7. Prepare a bring-up procedure

**English request**

> Prepare a bring-up plan for BUILD_ID from the current evidence and open questions. Define the setup, prerequisites, staged checks where needed, expected criteria, and evidence to capture. Keep it clearly marked as an unperformed plan; I will run the physical measurements locally.

**日本語の依頼例**

> BUILD_ID の立ち上げ手順を、今ある根拠と未解決事項から作って。接続や測定器の準備、前提条件、必要なら段階的な確認、判定基準、残すべき測定データをまとめてほしい。実測は手元で行うので、まだ実行していない計画であることを明記して。

**Completion expectations**

- Derive the procedure from this project's design, hardware revision, intended configuration, and documented operating conditions.
- Separate evidence review, predicted behavior, and physical checks.
- Explain dependencies between stages where a result determines whether the next stage is meaningful or appropriate.
- Leave observed values and outcomes unfilled. Do not carry over another project's voltage, current, timing, or temperature limits.

**Workflow and commands:** Workflow F (planning half), using `circuit/templates/project-docs/verification/bring-up.mdx` copied into `doc/src/content/docs/verification/`; `pnpm check` after editing.

## 8. Turn bench observations into evidence

**English request**

> Organize the attached measurements for BUILD_ID into a verification report. Preserve the raw observations, setup, revision, and configuration. Compare only against criteria we have evidence for, update the relevant coverage, and list any questions the results reopen.

**日本語の依頼例**

> 添付した BUILD_ID の測定結果を検証レポートに整理して。生の観測値、測定条件、基板のリビジョン、設定内容を残してほしい。根拠がある判定基準だけと比較して、関係する確認状況を更新し、結果から再確認が必要になった点も挙げて。

**Completion expectations**

- Use only supplied or actually observed measurements. Ask for missing setup information when it prevents interpretation, while organizing the material already available.
- Distinguish results from proposed explanations. Mark an ambiguous result inconclusive rather than forcing pass or fail.
- Scope any evidence update to the tested configuration and physical unit.
- Preserve separate runs and rework states so a later successful measurement does not erase an earlier failure.

**Workflow and commands:** Workflow F. Record `BENCH-OBSERVED` facts from a `BENCH_RECORD` source where a measurement becomes evidence, then `pnpm circuit:generate` and `pnpm circuit:check`.

## 9. Continue the project without rediscovering it

**English request**

> Read the current project snapshot and next actions, then complete the next unblocked research task. Keep the component evidence and authored rationale consistent, update the handoff, and tell me the result and the next unresolved decision.

**日本語の依頼例**

> 現在のプロジェクト状況と次の作業を読んで、着手可能な調査タスクを一つ完了して。部品のエビデンスと説明文の整合を取り、引き継ぎメモを更新してほしい。今回分かったことと、次に決める必要がある未解決事項を教えて。

**Completion expectations**

- Use the current snapshot and linked authoritative records as the starting point.
- Select the next bounded task according to the project's recorded priorities and dependencies.
- Resolve or reopen questions only with supporting evidence or a recorded decision.
- End with a concrete next result, not a broad request to “continue investigating.”

**Workflow and commands:** Shared entry, then whichever workflow the next action needs; update `doc/src/content/docs/project/next-actions.mdx` and run `pnpm check`.
