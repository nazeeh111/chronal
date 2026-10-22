# Current upgrade verification, 2026-10-22

Runtime SHA-256: `26a381e8414ed18df0698813d325c142fd077195389e5d6d746ec6d131f76bba`.

- 69 tests and 98 subtests passed on Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4. Ruff checks and formatting passed across 20 Python files.
- Added hand-calculated diagnostics tests. The [independent incremental review](UPGRADE_REVIEW.md) checked 360 additional paths, monthly compound identities, open/recovered episodes, tail sample counts, deterministic HTML and script escaping. No unresolved consequential finding within that scope.
- Fresh demo and all 12 study seeds regenerated. Full Python 3.11 replay of Python 3.14 outputs passed. Financial results match the predecessor; this change does not modify candidate selection or execution.
- Redesigned current-source reports inspected at 1280×720 and 390×844. Strategy changes update diagnostics/monthly data; chart switching and fill pagination work. See [desktop](assets/research-desk.png), [risk view](assets/risk-desk.png), [mobile risk](assets/risk-desk-mobile.png) and [mobile holdout](assets/holdout-desk-mobile.png). CSV export links target the accompanying verified exports.
- Additional exact-source inspection covers four repositories and eleven files; no upstream execution or copied code. Current archive/package verification is recorded in task state.

The earlier financial review and environment evidence follows as history. Its old source hash and screenshots describe the prior build. Current checks above supersede counts and presentation claims, while the disclosed market, platform and authenticity limits still apply.

---

# Verification record

Validated locally on 2026-10-21 on macOS. The final runtime package source SHA-256 is:

```text
319513391636baf3d633d06a9f8088c37ff0f1d2eeae507195f2901906bff215
```

## Passed

- **63 tests and 66 subtests** passed on both Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4, using pytest 9.1.1. Coverage includes strict data/spec contracts, immutable ownership, train-only preprocessing and label endpoints, unavailable observations, future-suffix invariance, independent hand-calculated cost/gap ledgers, shared cash, partial capacity, expiring orders, delayed execution and publication-causal risk liquidation.
- Evaluation checks cover purged chronological folds, continuous development accounting, per-fold cost reconciliation, baseline exclusion from selection, paired-bootstrap alignment and control validation, holdout-price invariance during development, and unavailable stress scenarios without loss of valid base results.
- Artifact checks cover output preservation, failed-write cleanup, changed content/source, symlink rejection, resealed selection substitution, report dates/assets/provenance, canonical CSV exports and full numerical replay. Study checks validate registered seeds, every retained observation and numerical CSV/summary replay.
- Ruff 0.17.1 error/import and formatting checks passed for all **18 Python files**, including the figure generator. This is the scoped project lint configuration, not exhaustive static analysis.
- The checked-in demo completed with independent ledger checks and full development/holdout replay. Its selected trend60 loses **1.46%** on the fictional holdout. The [12-seed study](EXPERIMENT.md) completed with all seeds 100–111 retained: 3/12 positive holdout excess and mean excess −1.99 percentage points.
- A wheel and source distribution built successfully with build 1.6.1 and setuptools 84.2.1, explicit MIT metadata and one runtime dependency, NumPy. The wheel installed offline into a fresh Python 3.11 environment. Its imported module was confirmed inside that environment's `site-packages`, outside the source tree.
- From outside the source tree, that installed wheel completed a fresh demo with full replay, then fully replayed both the checked-in demo and all 12 study replications generated under Python 3.14. The fresh installed demo took 2.943 seconds in one observation; this is illustrative local timing, not a controlled speed benchmark.
- Browser interaction checks exercised strategy switching, equity/drawdown selection, session inspection and fill pagination. Current reports were inspected at **1280×720** and **390×844**. Narrow-grid table containment was corrected and rechecked. The holdout visibly discloses synthetic prices and its negative result. See the actual [wide chart](assets/report-preview.png), [narrow chart](assets/report-narrow-chart.png) and [holdout screen](assets/holdout-narrow.png).
- Three editable figures were generated from implementation/results through the requested PaperBanana-derived Flowcraft workflow. Their fresh PNG renders were inspected for source correspondence, arrow direction, text clipping and complete numerical coverage. [Figure provenance](figures/README.md) records sources and iteration.

## Independent review

The [initial review](research/INITIAL_REVIEW.md) found publication-causal risk, selection consistency and fold-cost issues that were corrected. A separate [fresh gap review](INDEPENDENT_REVIEW.md) independently inspected source, reproduced additional defects and accepted their fixes. Its focused probes covered resealed derived evidence, accepted extreme-cost inputs, invalid bootstrap pairing and complete study replay. It independently reran 63 tests and 66 subtests on Python 3.14. No unresolved consequential finding remained within that reviewed scope.

The final runtime change was one CSS declaration for narrow layout. The reviewer verified its exact source scope and reran the complete workflow/replay test; both full test suites, current examples and clean-wheel checks subsequently passed on the final hash above. The reviewer did not certify distribution packaging, figure quality or the parent-owned browser checks. These are recorded separately here.

## Not established

The Python 3.11–3.14 CI matrix is configured but has not run on GitHub. Local tests cover 3.11 and 3.14; 3.12, 3.13, other operating systems and different BLAS implementations remain untested. Replay tolerates small floating-point differences and does not promise cross-platform bitwise identity.

The in-app browser permits HTTP/HTTPS and blocked a direct file-URL test. Visual and interaction checks used a temporary loopback HTTP preview. Direct saved-file opening in an ordinary browser was not tested; no alternate-browser or raw-protocol workaround was attempted. The report source contains its assets inline and makes no network requests.

No upstream trading engine or adapter was executed or performance-benchmarked. No real-market predictive value, historical language-model skill, selection-adjusted alpha, exhaustive security, live venue, real-money execution, PyPI distribution, hosted deployment or GitHub publication was validated. All study replications share one synthetic generator. Unsigned local hashes do not prove authenticity, historical preregistration or a complete external search history, and cannot prevent an operator from viewing a holdout.

## Reproduce the checks

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check chronal tests tools
ruff format --check chronal tests tools
python -m chronal verify examples/demo --replay
python -m chronal verify examples/selection-study --replay
python -m chronal demo --out fresh-demo
python -m chronal study --out fresh-study --replications 12 --first-seed 100
python -m chronal verify fresh-study --replay
python -m build
```

Use fresh destinations for generated runs. Checked-in examples include an already opened synthetic holdout; it cannot be represented as a future confirmatory test.
