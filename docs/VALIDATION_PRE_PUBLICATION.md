# Current verification record

Validated locally on **2026-10-22**, macOS. Runtime source SHA-256:

```text
27fdf2032fb776674dcf72a3641b098470a2abb615df27581260c2cb2c5f9b04
```

## Current source checks

- **84 tests plus 126 subtests passed** on Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4. Ruff lint and formatting passed across 24 Python files. Contracts, precision, fitting/label/publication boundaries, cash/fills/capacity/liquidation, portfolio continuity, artifact preservation, selection, exports, diagnostics and replay are covered. The new parser regression rejects exponent overflow without changing valid finite decoding.
- [Final specialist review](FINAL_REVIEW.md) records the reproduced core/display defects, corrections and refreshed 100-case independent accounting/causality/ridge probe. No additional consequential financial defect was reproduced within that scope. Prior exact before/after intent instrumentation and tamper-replay evidence remains in [execution review](EXECUTION_REVIEW.md).
- Both current development and holdout reports pass Node syntax, static ID/hash checks and actual-helper logic regressions for commands, intervals, dates, coordinate mapping, filters, model/intent/event context, detailed numeric precision, execution finder, history, palette and repeated navigation. Node 24.14.0 was used; configured CI Node 22 has not run remotely. The helper checker uses dependency stubs and is not browser certification.
- Actual final-source browser checks passed at 1280x720, 390x844 and 320x740. Repeated mobile section selections consistently position headings below the fixed header; document widths match the mobile viewport. Desktop same-section links, command palette selection without execution, finder intersections and session jumps, history draft restoration, holdout empty/reset states and pagination were separately exercised. See [final screenshots and observations](FINAL_REVIEW.md).
- Demo and all 12 synthetic study seeds 100–111 were regenerated at this source hash and fully replayed under Python 3.11 from Python 3.14 outputs. Synthetic outcomes are unchanged: selected trend60 loses 1.46% on its holdout; 3/12 selected candidates beat baseline and mean excess is -1.99 percentage points. Every registered seed is retained.

## Research and interpretation

The source registry now covers 29 unique public projects. [Final terminal research](research/FINAL.md) adds 14 pinned files from Gloomberb, Longbridge Terminal and a Bloomberg-inspired terminal, with exact commit URLs/hashes. These findings are static code/license/test inspection, not upstream runtime replication or endorsement. No upstream code was copied, installed or executed. One inspected project has no discovered license file at its pinned revision; its implementation was not reused.

CHRONAL's integrated value is a replayable experiment connecting registered hypotheses, training-only models, requested execution, actual cash/share evidence and chronological evaluation. Its models and simulation assumptions are deliberately bounded. A richer interface does not establish investable performance or parity with an institutional market-data terminal.

Detailed values are display approximations with up to eight significant digits; canonical JSON/CSV retains stored precision. Portfolio headlines remain rounded. Returns are per session with 252 assumed sessions/year for annualization; no intraday calendar is inferred. Intents are eligible simulator requests with expiring residuals, not exchange acknowledgments. Currency friction is not counterfactual NAV drag. Browser controls retain the frozen candidate and do not fit models. Lightweight accounting alone does not authenticate intents; full replay checks them.

## Release verification and preservation

Wheel/sdist and source ZIP are rebuilt from current source. Wheel runtime bytes, required source-distribution docs/examples/checker/screenshots, relative Markdown links, ZIP contents/CRC and delivery checksums are verified. The wheel is installed in a separate Python 3.11 environment, imported from site-packages outside the source tree and used for complete demo/study replay. Checksums are consistency checks, not signed authenticity.

Before replacement, the prior source ZIP was recovered into a separate destination and all 118 archived files compared exactly. Prior examples, distributions, checksums and task state remain in work/final-baseline. Earlier backups remain intact. No commits, pushes, publication, deployment, credentials or live orders were used.

## Limits

Python 3.11–3.14 / Node 22 GitHub CI is configured but unrun remotely. Local 3.12/3.13, other operating systems, other BLAS implementations, arbitrary dataset sizes and exhaustive security remain untested. Numerical replay permits small floating-point differences. Browser checks used a task-only loopback server; direct saved-file opening in an ordinary browser remains untested. Scripts/styles/data are inline and require no external requests.

No real-market alpha, historical language-model skill, selection-adjusted edge, external-engine benchmark, order-book fidelity, live adapter, PyPI publication or hosted deployment is established. All study seeds share one synthetic generator. Fixed-universe daily OHLCV, opening-price sizing, realized-volume capacity, absent corporate actions/dividends and 252-session annualization remain explicit assumptions. Unsigned hashes cannot prove historical preregistration, truthful external timestamps, completeness of prior search or that an operator never read the holdout.

The [previous verification record](VALIDATION_PRE_FINAL.md) retains earlier counts and hashes as history. Earlier reviews do not independently certify later revisions. There is no claim of universal perfection or a measured 10x improvement.

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
