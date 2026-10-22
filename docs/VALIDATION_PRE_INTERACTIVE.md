# Current verification record

Validated locally on **2026-10-22** on macOS. Final runtime source SHA-256:

```text
6ee5713642056a0e27733752fd529fd4a0be55ba43affc6b46334b0a69cdc8aa
```

## Runtime and numerical checks

- **73 tests and 117 subtests passed** on Python 3.11.15 / NumPy 2.4.6 and Python 3.14.7 / NumPy 2.5.4. Scoped Ruff error/import and formatting checks passed across 22 Python files. This is not exhaustive static analysis.
- Tests cover data/spec contracts, immutable ownership, train-only preprocessing, label endpoints and publication timing; hand-calculated fills, costs, gaps, shared cash, capacity, liquidation and portfolio continuity; frozen selection, paired bootstrap validation, failed-write preservation, source/content/symlink checks, derived report/CSV identity and numerical replay.
- Diagnostics tests cover initial-cash daily returns, UTC monthly compounding, recovered/open drawdown duration, tail convention/count, aligned benchmark paths and invalid input. Ledger tests cover session-level weights, share inventory, signed fills, cumulative fees, sparse/empty fills and shape/type validation.
- A fresh [full-runtime specialist review](TERMINAL_REVIEW.md) independently exercised **360 randomized financial paths** with 1/2/4 assets, delays 0/1/3, late publications, thin/zero capacity and risk stops. It independently reconstructed fills, capacity, cash, shares, NAV and causal prefixes. A separate ledger probe recalculated 360 paths. No new consequential financial defect was reproduced within that scope.
- Fresh demo and all 12 study seeds were regenerated at the final hash and fully replayed under Python 3.11 from Python 3.14 outputs. Outcomes remain unchanged: selected trend60 loses 1.46% on the fictional holdout; 3/12 study selections beat their holdout baseline and mean excess is −1.99 percentage points. No seed was discarded for a loss.
- The wheel installed into a separate task-local Python 3.11 environment. Its module import was confirmed in `site-packages`; outside the source tree, the installed CLI fully replayed the checked-in demo and all 12 study replications. No account or API was involved.

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
