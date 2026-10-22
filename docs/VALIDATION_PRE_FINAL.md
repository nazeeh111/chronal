# Current verification record

Validated locally on 2026-10-22 on macOS. Runtime source SHA-256:

```text
488e48e04d09ad174c10e0362b733e1672f350fe07b0a90685214adf26389ffd
```

## Current checks

- **83 tests plus 123 subtests passed** on Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4. Scoped Ruff lint and formatting passed across 24 Python files. Tests cover contracts, timestamp precision, fitting/label/publication boundaries, cash-aware fills, capacity, liquidation, portfolio continuity, artifact preservation, selection, derived exports, diagnostics and replay. New intent scenarios cover capacity clipping/zero fills, shared cash scaling, sells before buys, delayed signals, risk retries, unavailable targets, signed expiration and exact fill joins.
- The [independent financial and interaction review](EXECUTION_REVIEW.md) records 100 fresh accounting/causality cases, an 80-case exact before/after instrumentation comparison and a resealed intent-tampering rejection by full replay. No new consequential financial defect was reproduced within this scope.
- Current development and holdout reports passed Node syntax, static ID/anchor checks and actual-helper logic regressions for commands, frozen selection, intervals, dates, chart coordinates, fill filters, refit boundaries, model state and execution/event drilldown. The checker has dependency stubs and is not a browser test. Local Node 24.14.0 was used; CI Node 22 remains unrun remotely.
- Actual browser checks verified 1280 x 720 and 390 x 844 layouts, fit command/native selector, training cutoff/scaler/coefficients, event navigation, signed intent records, null sell scaling, combined fill filters and explicit empty state. The model inspector clears regression evidence for non-regression rules. Mobile document width matched 390; wide tables stay inside scroll containers. Holdout invalid-fit requests preserve state. Current screenshots: [overview](assets/research-terminal.png), [model](assets/model-inspector.png), [execution](assets/intent-inspector.png), [mobile model](assets/model-mobile.png), [mobile execution](assets/intent-mobile.png).
- Fresh demo and all 12 study replications were generated at this hash. Complete cross-version replay passed from Python 3.14 outputs under Python 3.11. Synthetic outcomes are unchanged: selected trend60 loses 1.46% on its holdout; 3/12 selected candidates beat baseline, mean excess -1.99 percentage points. Every registered seed 100–111 is retained.

## Research and interpretation

[New implementation research](research/NEXT.md) inspected 13 pinned source/license/test files across Backtrader, backtesting.py and ABIDES, bringing the registry to 26 unique projects. Source findings are static inspection, not independently replicated upstream behavior. No upstream trading code was copied, installed or executed. Request/capacity/cash/fill/expiry inspection fits this daily simulator; queue priority and order-book impact require different data.

Intent records are simulator-authored eligible nonzero requests, not exchange acknowledgments or persistent pending orders. Signed remaining quantities expire after the attempted open. Absent intent does not identify the strategy's motivation. Currency execution friction is observed adverse fill cost plus commission, not counterfactual NAV drag. Recorded coefficients are standardized predictive model parameters, not causal importance. All browser controls inspect saved evidence and retain the frozen candidate.

## Packaging and preservation

Current wheel/sdist and source archive are rebuilt from this source. Wheel runtime bytes, source-distribution required documentation/examples/checker/screenshots, relative Markdown links, archive contents and ZIP CRC are checked before delivery. The installed wheel is separately imported from site-packages outside the source tree and used for complete demo/study replay. Delivery checksums are local consistency checks, not signed authenticity.

Before replacing examples and packages, the prior source ZIP was extracted to a separate recovery folder and every one of 107 archived files compared exactly. Prior examples, distributions, checksums and task state remain in work/next-baseline. Earlier backups remain intact. No commits, pushes, publishing or deployment occurred.

## Limits

Configured Python 3.11–3.14 / Node 22 GitHub CI has not run remotely. Local 3.12/3.13, other operating systems, other BLAS implementations, arbitrary data sizes and exhaustive security remain untested. Numerical replay permits small floating-point differences. No upstream-engine benchmark, real-market alpha, historical language-model skill, selection-adjusted edge, exchange adapter, live execution, PyPI publication or hosted deployment is established. All seeds use one synthetic generator.

Fixed-universe daily OHLCV, opening-price sizing, realized-volume capacity, no corporate actions/dividends and 252-session annualization remain explicit assumptions. Unsigned local manifests cannot prove historical preregistration, external publication truth, absence of earlier trials or an operator's inability to read holdout CSVs. Full replay checks intents; lightweight accounting alone does not. Browser inspection used a task-only loopback server; direct saved-file opening in an ordinary browser remains untested. The generated report contains its scripts/styles/data inline and uses no external requests.

The [previous verification record](VALIDATION_PRE_INTENTS.md) retains earlier corrections, counts and hashes as history. Earlier specialist reports do not independently certify later edits. Nothing here establishes universal perfection or a measured 10 x improvement.

## Reproduce

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check chronal tests tools
ruff format --check chronal tests tools
python -m chronal demo --out fresh-demo
python -m chronal verify fresh-demo --replay
node tools/check_report.cjs fresh-demo/development/report.html
node tools/check_report.cjs fresh-demo/holdout/report.html
python -m chronal study --out fresh-study --replications 12 --first-seed 100
python -m chronal verify fresh-study --replay
python -m build
```

Use fresh destinations. An opened holdout is observed data, not a new confirmatory test.
