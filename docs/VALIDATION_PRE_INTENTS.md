# Current verification record

Validated locally on **2026-10-22** on macOS. Final runtime source SHA-256:

```text
f3785a53808b331a25d4bd8ae8a844b32bea604b5cf96fe4163df820b4e8a6d4
```

## Runtime and numerical checks

- **75 tests and 120 subtests passed** on Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4. Scoped Ruff error/import and formatting checks passed across 22 Python files. This is not exhaustive static analysis.
- Tests cover data/spec contracts, immutable ownership, train-only preprocessing, label endpoints and publication timing; hand-calculated fills, costs, gaps, shared cash, capacity, liquidation and portfolio continuity; frozen selection, paired bootstrap validation, failed-write preservation, source/content/symlink checks, derived report/CSV identity and numerical replay.
- Diagnostics tests cover initial-cash daily returns, UTC monthly compounding, recovered/open drawdown duration, tail convention/count, aligned benchmark paths and invalid input. Ledger tests cover session-level weights, share inventory, signed fills, cumulative fees, sparse/empty fills and shape/type validation.
- A prior [full-runtime specialist review](TERMINAL_REVIEW.md) independently exercised **360 randomized financial paths** with 1/2/4 assets, delays 0/1/3, late publications, thin/zero capacity and risk stops. It independently reconstructed fills, capacity, cash, shares, NAV and causal prefixes. A separate ledger probe recalculated 360 paths. No new consequential financial defect was reproduced within that prior scope. This iteration found and fixed a separate timestamp-normalization defect, described below.
- Fresh demo and all 12 study seeds were regenerated at the final hash and fully replayed under Python 3.11 from Python 3.14 outputs. Outcomes remain unchanged: selected trend60 loses 1.46% on the fictional holdout; 3/12 study selections beat their holdout baseline and mean excess is −1.99 percentage points. No seed was discarded for a loss.
- The wheel installed into a separate task-local Python 3.11 environment. Its module import was confirmed in `site-packages`; outside the source tree, the installed CLI fully replayed the checked-in demo and all 12 study replications. No account or API was involved.

## Current timestamp and interaction correction

A fresh [runtime input audit](INPUT_AUDIT.md) reproduced publication timestamps 500 ns after close becoming equal to close through lossy normalization. The constructor now accepts only exact, in-range conversions to UTC microseconds. A separate [independent review](TIMESTAMP_REVIEW.md) reconstructed the legacy helper and observed eight premature fills on its fixture; the current code rejects that input before simulation. Its independent rational-duration oracle passed 98 cases over coarse/fine/scaled datetime units, plus 12 extreme calendar dates. Lossless nanosecond inputs retain the fingerprint. Some extreme invalid casts raise NumPy OverflowError directly; they still reject safely.

The [interaction specialist review](INTERACTIVE_REVIEW.md) accepted the final runtime hash above. Durable Node checks now include actual session/range/navigation helpers, hand-calculated prior-start NAV, inclusive endpoint fees and notional, local drawdown, single-session/no-fill intervals, invalid-range state preservation, malformed/blank/ambiguous dates, positional session lookup, chart point mapping and repeated same-hash navigation.

Browser testing found and corrected a duplicate `interval` identifier that collided with uncertainty text, then a same-hash navigation no-op. The checker now rejects duplicate static identifiers and invalid native hash targets, and ensures repeated navigation explicitly scrolls. It rejects the previously broken generated report in a negative regression.

Current desktop/mobile browser checks verified: monthly button → January 2019's 23 actual sessions and 6.74% candidate return; matched baseline comparison; reversed ranges retain prior calculated values; cleared session date restores prior date; worst trough → matching account; chart center click maps to session position 180 at both widths. The SVG inverse screen transform handles scaling. The interval remains post hoc and does not change full-region metrics or the frozen winner. Same-date sessions use explicit positional addressing and full timestamp readouts.

[Current interval/episode screenshot](assets/interactive-interval.png) and [current mobile trough/account screenshot](assets/interactive-mobile.png) show the final source at 1280×720 and 390×844. Mobile document width matched the viewport. The earlier screenshots below describe the retained terminal design; current screenshots above supersede them for new interactions. Browser geometry and event wiring are verified separately from the dependency-stub Node logic tests. Direct CDP capture on an older preview tab timed out; a fresh tab in the same browser completed the remaining checks.

## Terminal checks

Current-source reports were inspected at **1280×720** and **390×844**. [Desktop](assets/terminal-desktop.png), [calendar/risk](assets/terminal-risk.png), [mobile](assets/terminal-mobile.png) and [selected-session account](assets/terminal-account-mobile.png) are actual screenshots. Overall mobile document width matched the viewport; wide tables remain scrollable within their panels.

Browser checks verified strategy and chart commands, exact-session lookup, rejection of missing dates without changing the inspected session, explicit rejection of unsupported buy commands, slash focus, keyboard help/Escape, shared chart/account context, and combined asset/sell filtering. Monthly missing cells remain distinct from observed zero returns. Frozen selection stays visible while inspecting another candidate. No live price or verification badge is fabricated.

A specialist found the valid asset name `all` collided with the original All assets filter value. The empty-string sentinel fixes it. Large-history chart bounds now use reductions instead of argument spreading. Command errors stay visible on narrow screens; an invalid date restores the prior date control value.

`tools/check_report.cjs` uses actual functions extracted from trusted generated HTML with small dependency stubs. It passed command allowlist/unknown/prototype cases, frozen-selection preservation, valid/invalid dates, named-`all` assets, signed sell quantities, no-match states and pagination on both generated region reports. Node syntax checks passed locally on Node 24.14.0. CI configures Node 22; that exact Node version has not run locally. This is a **logic check**, not a browser, event-wiring, layout or accessibility certification. Actual browser interaction checks are separate above.

The new editable terminal cover was rendered with the installed Flowcraft helper and visually inspected. Existing source-grounded architecture/timing/study SVGs retain their scientific content. Their provenance is in [figures/README.md](figures/README.md).

## Packaging and preservation

Wheel source bytes match the current runtime. The source distribution includes documentation, current examples, SVG/PNG figures, CI and the optional Node checker. Relative Markdown links, archive contents and ZIP CRC were checked. Release checksums are supplied outside this repository in the delivery folder. These checks establish local consistency, not signed authenticity.

Before changes, the full prior repository including Git state was archived. A separate recovery extraction matched all 235 saved files. Earlier valid examples and release archives were retained task-locally. No commits, pushes or publication were performed.

## Limits

The GitHub Python 3.11–3.14 / Node 22 CI is configured but has not run remotely. Local 3.12/3.13, other operating systems, different BLAS implementations, arbitrary dataset sizes and exhaustive security remain untested. Numerical replay permits small floating-point differences, not universal bitwise identity.

An earlier direct file URL preview was blocked by the in-app browser policy. Browser verification used a task-only loopback HTTP preview; direct saved-file opening in an ordinary browser remains untested. The report embeds its scripts/styles/data and makes no network requests.

No upstream trading engine or adapter was executed or benchmarked. No real-market predictive value, historical language-model skill, selection-adjusted alpha, order-book fidelity, exchange adapter, real-money execution, PyPI distribution, hosted deployment or GitHub publication was established. All study seeds share one hand-designed synthetic generator. Fixed-universe daily data, open-price sizing, realized-volume capacity, absent corporate actions/dividends and 252-session annualization remain explicit assumptions. Local unsigned hashes cannot prove historical preregistration, complete external search history or that an operator never inspected a holdout.

Previous validation is retained as [history](VALIDATION_PRE_TERMINAL.md); its hashes/counts describe prior builds. Earlier reviews remain linked for resolved findings, not as acceptance of later revisions.

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

Use fresh output directories. An opened holdout is observed data, never a new confirmatory test.
