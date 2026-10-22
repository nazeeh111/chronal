# CHRONAL independent gap review

## Final focused acceptance

**Accepted for the reviewed engineering scope on 2026-10-21**, current runtime source SHA-256 `319513391636baf3d633d06a9f8088c37ff0f1d2eeae507195f2901906bff215`.

Presentation-only follow-up: inspected the added `.panel{min-width:0;...}` rule in `report.py`. Removing that exact declaration while hashing reconstructs the previously accepted source hash `c6d3f6266cff767bc19e3941d0d325efec2560fb238c3652545dd6375d3bf44b`, confirming the runtime source change is limited to this CSS declaration. It allows grid children to shrink so the existing scrolling wrapper can contain wide tables. Re-ran only `tests/test_artifacts.py::ArtifactTests::test_complete_workflow_and_full_replay`: **1 passed**, including fresh development/holdout HTML and complete replay under the current hash. The parent owns visual verification at 390px. The financial review below was not repeated for this CSS edit.

All three findings below are resolved in this accepted revision. They are retained as a historical reproduction record, not outstanding defects. No unresolved consequential issue was identified in the final focused checks.

Independent rerun on Python 3.14: **63 tests passed, 66 subtests passed**. The parent-reported Python 3.11 run was not independently repeated by this reviewer.

Additional independent acceptance script: `work/venv/bin/python work/gap-review/acceptance.py` from task root. It passed all of the following against the hash above:

- Base development and complete replay survive both accepted 6,000-bps commission and accepted 14,000-bps spread. Their invalid doubled-cost scenarios explicitly retain `status: unavailable` and a reason; their delay scenarios complete.
- Separate resealed modifications to each of `equity.csv`, `fills.csv`, report dates, assets and provenance are rejected. These were independent tamper paths, so an early date failure did not mask export verification.
- Unequal bootstrap path lengths, one/bool resample count, zero/fractional block size and negative seed are rejected with specific input errors.
- A new two-seed study completes and fully replays through the public `verify_bundle` entry point.
- Separate resealed numeric study CSV corruption, summary corruption and omitted registered seed are rejected on replay.

The new study verifier was read directly. Its replay rebuilds the registered consecutive seed range, compares the complete registration/results except historical environment strings, and checks CSV cells numerically when platform float spelling differs. The lightweight verification path checks hashes and recipe/seed consistency; regenerated numerical results require `--replay`. No new consequential flaw was identified in this bounded inspection. Root hashes remain unauthenticated and do not prove a historical preregistration or complete external search history.

This acceptance covers runtime and test source, independently generated fresh temporary runs, and the focused probes. It does not certify examples awaiting regeneration, final distribution artifacts, PaperBanana image quality, cross-platform behavior, market predictive value or exhaustive security. No runtime/test files were edited by this reviewer.

## Initial review and resolved findings

Reviewed the runtime source and all five test modules directly on 2026-10-21. This review did not use the prior review's conclusions. No runtime or test files were edited. Parent is separately extending study verification, so study changes were excluded from acceptance.

## Evidence

- Python: `work/venv/bin/python`, with current local NumPy/pytest.
- Running pytest from `outputs/chronal`: **57 passed, 60 subtests passed**.
- Repro: `work/venv/bin/python work/gap-review/probe.py` from task root. It uses temporary directories below `work/gap-review` and removes them after the probe.
- Read `data.py`, `strategies.py`, `engine.py`, `evaluation.py`, `artifacts.py`, `cli.py`, the method/validation documents and tests. Study source was read for context but is being changed separately.

## Historical findings, all resolved at accepted hash

### P2: Full replay does not validate all displayed/exported evidence

`artifacts.verify_bundle` replays evaluated results, uncertainty and stress and rerenders HTML from the saved payload. It does not compare `dates`, `assets` or `dataset` against the locked input, and does not regenerate and compare `equity.csv` or `fills.csv`.

Reproduced a valid development run, then replaced its `equity.csv` with arbitrary text, replaced every payload date with `1900-01-01T00:00:00Z`, rerendered the report from that payload and resealed the development directory. `verify_bundle(..., replay=True)` returned `valid: true`. Simulation/accounting remained unchanged; the displayed dates and exported ledger were false.

Local hashes are explicitly unauthenticated, so this is **not** a claim that a cryptographic or tamper-proof guarantee was broken. It identifies a consequential limit to semantic full replay: numerical portfolio results replay, but evidence a reader may import or use for date interpretation does not. Consider comparing these derived representations and payload identity fields to canonical regenerated output, at least in replay mode. Otherwise narrow the documented verification scope.

### P2: Valid execution configurations cannot complete mandatory development stress

`ExecutionConfig` permits commission below 10,000 bps and adverse spread/slippage below 10,000 bps. `stress_suite` doubles these values with a newly validated configuration. For example, `ExecutionConfig(commission_bps=6000)` is accepted by `make_plan`, but `run_development` fails with `ValueError: commission_bps must be in [0, 10000)` when constructing the mandatory stress configuration. The diagnostic refers to the user's accepted configuration without explaining that only its doubled scenario is invalid.

The probe confirmed that failed development does **not** publish a partial result directory, so work preservation passed. Options are to reject non-stressable plans up front with an explicit explanation, or retain the primary run and record unavailable stress scenarios with a reason. Add a case for the combined half-spread-plus-slippage constraint as well as commission.

### P3: Paired-bootstrap public helper silently broadcasts unpaired paths

`evaluation.paired_block_interval([110.0], [101.0, 102.0, 103.0], 100.0, samples=10)` succeeds. NumPy broadcasts the single return to three unrelated sessions, producing an estimated daily excess of roughly 9.01%. This violates the helper's pairing/alignment premise. Standard workflow paths have equal lengths, so this does not affect the current demonstration. Reject unequal path lengths before subtraction and validate sample/block controls if retaining this as a supported public helper.

## Positive findings and limits

No additional core chronological leakage or ordinary cash-accounting error was identified in this bounded review. The inspected implementation uses published history for signals, fit-only scaler/labels, delayed-open fills with explicit fees/capacity, account continuity across test folds, training-only candidate selection and a separately funded holdout. Documentation explicitly discloses current-day realized volume as an ex-post capacity proxy, opening-NAV sizing as an execution idealization, conditional resampling, and prospective holdout refits.

This is useful focused risk coverage, not exhaustive mathematical, statistical, security or market-performance certification. The probe above deliberately reseals inconsistent derived artifacts to test semantic replay, not adversarial authenticity. The high-cost case is extreme but expressly accepted by the supported configuration bounds. Current-source changes after this review require rechecking affected findings and tests.
