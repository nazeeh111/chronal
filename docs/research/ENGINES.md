# Simulation engine research
Reviewed 2026-10-21. Scope: decisive public implementation and test inspection, licensing, and practical integration choices. No upstream application or test suite was executed. Source-test assertions below are observations of source, not locally replicated passes.

## Decision

For a cohesive local daily research platform, implement a deliberately bounded long-only cash simulator only if its core product is the auditability of research: causal information access, explicit next-session execution, reproducible evaluation, and an inspectable cash/holdings ledger. Do not claim a new daily engine replaces mature order-matching infrastructure. Use NautilusTrader as the strongest expansion route when intraday order types, richer market data, derivatives, or venue simulation become requirements. LEAN is the strongest alternative when comprehensive asset/brokerage reality models justify a C#/.NET host and its data conventions. For portfolio trees and asset-allocation research, the underrated MIT project bt is a viable existing-engine alternative or conformance reference.

The important discovery is that a mature engine does not by itself make research causal or fills realistic. LEAN's equity market fill assumes full quantity; Nautilus needs deliberate liquidity-consumption settings and has deterministic residual-liquidity assumptions; bt executes strategy after updating current-date prices; Freqtrade shifts signals but still exposes full-history frames during indicator construction. These are configurable modeling choices, not proof that any project is generally incorrect.

## Pinned public revisions

| Repository | Inspected SHA | License at SHA | Role |
|---|---|---|---|
| QuantConnect/Lean | de116c0de654108bc9b3bcb643571ab0b754cbb4 | Apache-2.0 | Broad event-driven execution reference |
| nautechsystems/nautilus_trader | d9669fc23a9499b337e2be4e62d7a10e7db9610d | LGPL-3.0 | Rich execution extension candidate |
| polakowo/vectorbt | dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb | Apache-2.0 with Commons Clause | Research-scale comparison; avoid copying into unrestricted core |
| freqtrade/freqtrade | 0db79d391f646eafbdf3c0976dd55dc90b296522 | GPL-3.0 | Crypto workflow and lookahead-check mechanism |
| pmorissette/bt | 3adebef0316c5165ee0fb1fb27b2ec9866c30e3c | MIT | Underrated portfolio-allocation alternative |

Licenses were read directly: [LEAN](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/LICENSE), [Nautilus](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/LICENSE), [vectorbt](https://github.com/polakowo/vectorbt/blob/dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb/LICENSE.md), [Freqtrade](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/LICENSE), [bt](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/LICENSE). Preserve license, copyright, attribution, and applicable notices when redistributing or adapting code. Avoid merging GPL/LGPL code into a permissive core without honoring the resulting obligations. Using separately installed optional dependencies is a distinct choice from copying implementation. This is implementation guidance, not a legal opinion.

23 selected public files were retained in the build workspace and checked against Git blob hashes. SOURCES.json lists pinned URLs and SHA-256 digests; source bytes are not vendored into this repository.

## Implementation findings

### QuantConnect LEAN

[EquityFillModel.MarketFill](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/Common/Orders/Fills/EquityFillModel.cs#L124-L180) checks cancellation and exchange hours, applies side-specific best-effort bid/ask plus slippage, and checks staleness. It then assigns the full order quantity and Filled status. Volume-constrained partial equity execution is therefore not guaranteed by the default market-fill path.

Staleness is nuanced: coarse bars wait for fresh data; a minute quote within one resolution can still fill with a warning. [Source tests](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/Tests/Common/Orders/Fills/EquityFillModelTests.cs#L1322-L1410) explicitly assert no fill when data is older than one resolution and full fill once fresh data arrives, plus permitted stale fills within one resolution. Adopt the explicit freshness contract and tests, rather than the vague statement that stale prices are always rejected.

[SecurityPortfolioModel.ProcessFill](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/Common/Securities/SecurityPortfolioModel.cs#L36-L174) converts fees into account currency, applies fees and settlement cashflows, distinguishes upfront-payment assets from margin products, handles FX/base-currency swaps, and updates average holdings cost including position reversals. This illustrates why a general multiasset ledger is substantially harder than a daily cash ledger.

[InteractiveBrokersFeeModel](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/Common/Orders/Fees/InteractiveBrokersFeeModel.cs) is a concrete brokerage fee implementation, preferable to pretending a single fixed bps fee universally models every asset.

Integration: keep LEAN external and compare standardized target schedules/ledger exports if adding it. Hosting the full engine introduces .NET/Python interoperability, exchange calendar and symbol conventions, and data preparation. Its open-source engine does not imply every QuantConnect dataset or cloud/CLI workflow is free.

### NautilusTrader

Current implementation has execution-layer [FillModel trait and implementations](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/crates/execution/src/models/fill.rs#L48-L98) and [FeeModel](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/crates/execution/src/models/fee.rs#L33-L60). Fill models can supply synthetic books, and matching interprets their liquidity. Seeded probabilistic state validates probabilities in [0,1]; fixed fee handling [charges once per order by default](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/crates/execution/src/models/fee.rs#L190-L229) using filled quantity, with configurable per-fill charging. That distinction matters whenever an order partially fills more than once.

The [integration test for a custom liquidity book](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/crates/execution/tests/integration/matching_engine/fill_models.rs#L134-L231) submits a three-unit market order against a one-unit custom side and asserts exactly one unit filled, PartiallyFilled status, and two units remaining. Another test in the same file asserts a custom fee model was called and its commission reached the fill event.

Crucial limitations: [pinned matching documentation](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/docs/concepts/backtesting/fill-prices-and-matching.md) says historical books are immutable; liquidity_consumption=True tracks consumed level sizes, while default matching can reuse recorded size. L1 market-style residuals may fill one tick worse after displayed liquidity is exhausted. This is an explicit synthetic residual rule, not discovered historical depth. Seeded fill probabilities do not establish determinism of unrelated components. Queue priority requires its own model and appropriate data.

Integration: the best optional richer execution adapter, with explicit data units/precision, account/venue types, fee schedule, liquidity-consumption, and bar-path settings. Do not casually describe a daily-bars adapter as microstructure realism. Dependencies and adapter parity need their own runtime verification before promising compatibility.

### vectorbt

[buy_nb](https://github.com/polakowo/vectorbt/blob/dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb/vectorbt/portfolio/nb.py#L78-L208) applies side-specific slippage, fee-inclusive cash constraints, size granularity, rejection reasons, and configurable partial sizing. Shared cash, debt, and free cash are separate state fields; this is stronger accounting than multiplying signal returns. [Tests](https://github.com/polakowo/vectorbt/blob/dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb/tests/test_portfolio.py#L1012-L1195) assert fee, fixed fee, slippage, partial-size and cash-sharing behavior. Its matrix broadcasting and compiled numerical loops are useful architecture inspiration for screening many candidates, but screening needs trial accounting and untouched evaluation.

Current [license](https://github.com/polakowo/vectorbt/blob/dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb/LICENSE.md#L1-L13) contains Commons Clause, including sale/service limitations and a requirement to retain the condition notice. Do not call current vectorbt unqualified Apache-2.0 or unrestricted open source. Avoid copying kernels into a permissive project. A locally optional comparison adapter is possible after documenting its distinct license; it is not necessary for the default demo.

### Freqtrade

[Backtesting signal preparation](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/freqtrade/optimize/backtesting.py#L535-L570) shifts entry and exit signal columns by one candle before execution. [Trade creation](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/freqtrade/optimize/backtesting.py#L1214-L1227) stores both opening and closing fee rates. The same implementation contains explicit within-candle stop/ROI assumptions, demonstrating that OHLC bars require a path convention rather than reveal actual event order.

The valuable transfer is [lookahead analysis](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/freqtrade/optimize/analysis/lookahead.py#L66-L97), which compares full-frame indicator values against cut runs, and checks moved entries/exits. [Biased/unbiased strategy test](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/tests/optimize/test_lookahead_analysis.py#L464-L498) drives known scenarios and asserts detection. This mechanism can be independently implemented without copying GPL code.

Do not overstate the guarantee: checking executed signals does not prove all untriggered branches causal; cross-sectional multiasset signals require preserving the same universe in full/prefix runs. Signal shifting cannot fix an indicator that already used future data. A stronger platform contract hands strategies only a validated historical prefix and additionally tests future-perturbation invariance. Use Freqtrade itself only if delivering a crypto-centric system whose GPL and exchange-specific workflows are intentional.

### Underrated alternative: bt

The MIT portfolio-tree architecture composes sleeves and allocation rules without creating a separate trading bot per sleeve. [Backtest.run](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/bt/backtest.py#L440-L481) updates current-date market prices, runs the strategy, then updates state. Consequently same-close decisions and same-close trades are possible if the caller feeds current closes directly. A causal adapter must lag target weights or provide a separate decision/execution schedule.

[Spread accounting tests](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/tests/test_core.py#L4538-L4590) assert buy/sell outlays at the appropriate half spread and separately track commissions. Nonlinear quantity sizing is covered by a test at line 3239. This makes bt a useful portfolio-rebalancing comparison.

A substantive counterexample to blindly inheriting defaults: [SqrtCostModel and AlmgrenChrissCostModel](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/bt/core.py#L2316-L2425) explicitly return zero impact cost when volume is zero; [tests](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/tests/test_core.py#L5592-L5638) preserve that behavior. This is a cost-function convention, not proof that zero-volume orders are executable. Our simulator should reject zero-volume trading or leave unfilled quantity pending, independent of a cost estimate. Model liquidity separately from fees/impact.

## Existing engine versus narrow daily engine

| Choice | Benefit | Cost or material limitation | Appropriate use |
|---|---|---|---|
| LEAN host | Broad asset-specific settlement, calendars, brokerage/fill models | .NET host and data conventions; default equity fills are not capacity constrained | Full asset/brokerage simulation |
| Nautilus adapter | Rich order state, synthetic/depth books, partial fills, fee event plumbing | Venue/instrument precision and execution assumptions require explicit setup; dependency/runtime verification | Intraday and richer order execution |
| bt foundation | MIT, portfolio trees, spread/fee/cost hooks | Same-timestamp execution requires disciplined caller; liquidity is separate | Asset allocation and nested sleeves |
| Narrow daily engine | Small inspectable ledger, consistent causal timing, no live adapters, simple reproducibility | Team owns all accounting tests; only supports declared asset/execution scope | Evidence-centered daily research product |

A narrow engine is not justified merely to avoid dependencies. It is justified when the chosen workflow requires a small trusted simulation contract, and neither broad live-broker functionality nor sophisticated order types are promised. Prefer an existing engine once scope expands beyond what can be transparently verified. If bandwidth permits, a bt or Nautilus adapter used as a second implementation can expose accounting mistakes, but parity only applies under aligned assumptions and is not a universal oracle.

## Concrete mechanisms to carry into the build

1. Timestamp every decision and execution separately. Make close[t] observations produce orders eligible at open[t+1]. Never use high/low/close[t+1] to size an open[t+1] decision. If using actual open to resolve dollar-target quantity, document that as an execution-time sizing assumption.
2. Maintain one shared cash account, sell before buying, reserve fees, and record requested/filled/unfilled quantities and reasons. Define whether residual orders persist or expire.
3. Track fee, spread, and slippage separately without double counting. A capacity limit is distinct from impact cost. Use volume known at the signal instant for a causal capacity estimate. If realized execution-session volume is additionally used as a capacity ceiling, label that ceiling as an ex-post daily proxy, not a quantity known at the open.
4. Reconcile each event and each equity mark: equity = cash + sum(quantity * current valid mark). Reject nonfinite/negative prices and invalid quantities; define stale/missing mark policy. Declare treatment of splits/dividends or restrict to internally consistent adjusted datasets.
5. Test hand-calculated fee/slippage round trips, a price gap, no-cash buys, sell-to-buy rebalance, minimum/fixed fee constraints, zero volume, partial capacity, final-day pending orders, missing prices, and exact ledger reconciliation.
6. Test prefix/future-perturbation invariance: appending or changing future rows cannot alter earlier signals/orders/fills. Keep cross-sectional universe identical when slicing. Run the actual strategy through this interface, not a mock that mirrors the engine.
7. Store the source data hash, configuration, declared fill assumptions, engine version, evaluated dates, and full candidate/trial count alongside every research result. Separate screening from untouched evaluation and retain negative results.
8. Treat an LLM as a cited research/proposal interface. It should not bypass position limits, create authoritative performance claims, or call real execution. Free local/subscription routes can work through evidence packets without provider API credentials.

## Limits

This investigation verified source revisions, inspected decisive implementation/tests, and verified snapshot bytes. It did not benchmark speed, install any engine, run upstream tests, or establish adapter compatibility. Comparative integration recommendations are engineering inference from the inspected contracts. No claim of alpha, live-trading readiness, or broad superiority follows from these observations.

