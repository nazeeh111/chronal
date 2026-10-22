# Historical predecessor review

This review predates the CHRONAL rebrand and later gap fixes. Its exact hashes and check counts are historical, not current acceptance. The current review is ../INDEPENDENT_REVIEW.md.

# Independent correctness review

Reviewer scope: read current Chronal source and tests directly; independently exercise mathematical, timing, selection, integrity and failure boundaries. No source edits, network calls, credentials, live trades or external publication. Scratch evidence is under `work/reviewer/`.

## Findings and current disposition

1. **P1: unavailable closes influenced drawdown-stop execution** (`chronal/engine.py`, end-of-session risk decision). A panel with all prices 100 and a second panel differing only in delayed, unavailable closes of 50 generated different stop events and fills: the hidden crash caused a stop at session 2 and sale at session 3. This violates the available-information rule even though the risk-capacity volume lookup already respected availability. Independent reproduction: `work/reviewer/risk_causality.py`. The engine author was already implementing this fix when the review began. **Resolved and independently verified** in final checks below.

2. **P2: replay accepted a selection inconsistent with development results** (`chronal/artifacts.py`, former `run_holdout` / `verify_bundle`). A 170-session seed-17 development run selected `ridge20`. Editing only `development/selection.json` to registered `momentum20`, then refreshing its local manifest with the package's own seal function, passed full replay; holdout evaluated momentum20 and full replay still returned valid. This is a semantic consistency defect, separate from the explicitly acknowledged inability of unsigned local hashes to prove authenticity. Independent reproduction: `work/reviewer/selection_consistency.py`; original evidence bundle at `work/reviewer/selection-consistency-evidence/plan`. Source now validates exact registered specs and recomputes the winner before accepting holdout; **Resolved and independently verified** in final checks below.

3. **P2: per-fold cost and turnover fields reported zero despite trading** (`chronal/evaluation.py`, fold metrics). The first fold 102:112 reported zero commission and notional despite ledger commission 51.0929452453 and notional 102185.89049. Whole-region totals were correct. Independent reproduction: `work/reviewer/fold_costs.py`. Source now totals the actual fills in each fold and passes them into the metrics calculation; **Resolved and independently verified** in final checks below.

4. **P2: synthetic report identification did not match fixture metadata** (`chronal/report.py`). The generator recorded `synthetic: "true"`, whereas the report only checked `origin == "synthetic"`. The demo therefore displayed user-supplied market data and lacked the intended conspicuous synthetic notice. Source now recognizes both declarations, uses the actual asset count, and supports the generator's provenance/price metadata fields. A related claim, "risk-matched equal weight", was inaccurate for supported proposals with custom risk settings; source/report labeling now describes a fixed risk-controlled baseline.

5. **P2 regression introduced during remediation: HTML regeneration used inconsistent JSON ordering** (`chronal/report.py`, `verify_bundle`). After report verification was added, the complete-workflow test failed because results JSON is saved with sorted keys, whereas the original embedded report JSON retained insertion order. Recreating HTML from reloaded results therefore produced a different string. Report this separately from hash integrity: it blocked legitimate holdout runs. Deterministic sorted embedded JSON now fixes the mismatch. **Resolved and independently verified** in final checks below.

## Evidence and limits

The original 37 tests passed (49 subtests). A later expanded run during source changes produced 54 passed, 1 failed (60 subtests), identifying finding 5. This is not final acceptance.

Source inspection supports correct default close-to-next-open timing, train-only ridge preprocessing, label endpoint exclusion, chronological development truncation before holdout, expanding fits, and continuous cash/holdings across development folds. Simulation accounting explicitly handles adverse buy/sell prices, commission, sells before cash-scaled buys, fractional positions, positive-only holdings, expiring unfilled orders and capacity. Current-session volume is an explicitly disclosed ex-post proxy, not causal opening liquidity. Holdout starts a separate portfolio, as documented. Local manifests are unsigned and replaceable; they cannot prove external timestamps, prevent peeking or certify importer-supplied timestamps/provenance.

No result here establishes profitability, broad security, market realism, predictive skill or comparative superiority. Daily unadjusted prices, fixed universe and absent corporate actions/dividends remain stated limits.

## Final verification

Original accepted package source SHA-256: `894c134bee320ac7a288d61af8fbbfe9788c6c1651134e2f82806db71bcb9a05`.

- Complete current suite: **57 tests passed, 60 subtests passed**, 3.03 seconds, using the existing AutoResearchClaw Python environment requested by the parent.
- Independent `work/reviewer/risk_causality.py`: passed. Hidden unavailable crash prices change ex-post marks, but do not change risk decisions or fills before publication. Current implementation retains historical equity snapshots until published; it does not reconstruct old marks from current holdings.
- Independent `work/reviewer/final_acceptance.py`: passed. Fresh 170-session bundle completes development, holdout, independent ledger checks and full replay. Every candidate's fold commissions/notional reconcile to whole-region ledger totals. A resealed changed selection is rejected by both full verification and holdout entry.
- Synthetic disclosure, dynamic asset count, fixed risk-controlled benchmark wording, and deterministic sorted report JSON confirmed in current source. Full workflow exercises the new report-to-results consistency check successfully.
- Existing-output preservation and exception cleanup are exercised by artifact tests; the separate dangling-symlink destination probe preserved the original link and raised rather than overwriting it.

No unresolved consequential finding remains in the reviewed source. Acceptance is bounded to these requirements, paths and evidence; later source changes invalidate the exact reviewed hash. The scratch acceptance bundle is under `work/reviewer/final-sn334edh/plan`; its selection was deliberately altered after successful full replay to demonstrate rejection, so it should not be delivered as a valid user experiment.


### Final presentation revision acceptance

Final accepted package source SHA-256: `23109119c20531ca6c0f2ca7929bc4cbaf8e1ad9116daafc1d733477c177dd2d`.

Directly inspected the final `report.py` revisions: the invented experiment number is removed, and the conditional uncertainty sentence explicitly names the frozen development candidate through `D.winner`. Changing the inspected strategy therefore cannot imply the fixed interval was recomputed for that selection. The candidate name is a validated slug. These changes do not alter calculation or execution semantics.

Ran the targeted complete-workflow/full-replay artifact test against this final source: **1 passed in 0.76 seconds**. This exercises development/holdout generation and exact report regeneration with the changed strings. The 57-test suite and independent mathematical probes above belong to the original accepted hash; the parent is separately rerunning the complete suite against the final package. No additional unresolved finding arises from the presentation revision.
