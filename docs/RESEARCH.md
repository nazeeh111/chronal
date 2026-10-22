# Research and design decision

Inspected 2026-10-21. The investigation read **72 selected source and license files at exact commits across 12 repositories**, beyond README summaries. It did not execute upstream systems or replicate their investment performance. [SOURCES.json](research/SOURCES.json) retains URLs and SHA-256 hashes, including an initial failed license-path lookup subsequently resolved.

The design question was which combination creates a useful coherent free research product without importing incompatible dependency stacks, legal obligations or unverified performance claims.

| Foundation | Decisive implementation observation | Adopted idea or boundary |
|---|---|---|
| [TradingAgents](https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/backtest.py) | Current rating evaluation explicitly differs from a carried cash portfolio; current source also has improved filing and settlement-time guards | Evidence-bearing proposals; do not claim older timing criticisms still describe every current path |
| [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund/blob/4e1657ddc689e3939c481a8f0955444b10f02dc9/hedge_fund/brokers/sim.py) | Session records and deterministic construction are strong foundations; inspected sim broker fills at reference without costs | Retain a deterministic boundary and a complete cash/cost ledger |
| [Qlib](https://github.com/microsoft/qlib/blob/54355232463878d2eebb91fe0ee5fa7fa1f5976c/qlib/contrib/evaluate.py) | Metric accumulation conventions are explicit and configurable, not interchangeable | State simple-return, compounding, sample-volatility and annualization definitions |
| [LEAN](https://github.com/QuantConnect/Lean/blob/de116c0de654108bc9b3bcb643571ab0b754cbb4/Common/Orders/Fills/EquityFillModel.cs) | Broad execution/risk infrastructure; default selected equity market path assumes full fills | Mature expansion alternative; never imply volume fidelity comes automatically |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader/blob/d9669fc23a9499b337e2be4e62d7a10e7db9610d/docs/concepts/backtesting/fill-prices-and-matching.md) | Rich order states and partial liquidity; recorded-book reuse depends on explicit consumption settings | Best candidate for a future richer execution adapter, not a promised dependency |
| [vectorbt](https://github.com/polakowo/vectorbt/blob/dd8eb3a3fe9ed918b1cdaf177455759ae4ac68cb/LICENSE.md) | Strong numerical portfolio simulation, but the current license includes Commons Clause | Inspect license before reuse; do not copy restricted kernels |
| [FinRL](https://github.com/AI4Finance-Foundation/FinRL/blob/c0018c25de864157dc8470f0047b0d10ec721715/finrl/meta/preprocessor/preprocessors.py) | Gym-style research seam is useful; inspected preprocessing includes backward fill | Preserve unavailable data; keep heavy RL outside the default scope |
| [Freqtrade](https://github.com/freqtrade/freqtrade/blob/0db79d391f646eafbdf3c0976dd55dc90b296522/freqtrade/optimize/analysis/lookahead.py) | Full-versus-truncated comparison can reveal indicator lookahead | Independently implement prefix/future-perturbation tests; no GPL copying |
| [bt](https://github.com/pmorissette/bt/blob/3adebef0316c5165ee0fb1fb27b2ec9866c30e3c/bt/backtest.py) | MIT portfolio trees compose allocation well; execution chronology remains a caller responsibility | Strong alternative for allocation workflows; own explicit signal/fill clocks |
| [skfolio](https://github.com/skfolio/skfolio/blob/9effd863f19ec969ee93f654db1e8770343a4215/src/skfolio/model_selection/_walk_forward.py) | Window and purge semantics are explicit, including insufficient-data failures | Exclusive training endpoints, retained folds and honest forward-only claims |
| [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt/blob/a6638d2e06dae6f444fd022cfd4b3c528902a85b/pypfopt/risk_models.py) | Multiple covariance estimators distinguish risk assumptions | Separate estimated risk from realized outcomes; avoid unnecessary solver stacks |
| [InvestorBench](https://github.com/felis33/INVESTOR-BENCH/blob/87e0f7bc83baf7d89fbdc1a51f92458f8d4ee11a/src/memory_db.py) | Evidence IDs, memory decay and outcome feedback merit study; retrieval chronology still needs a boundary | Keep agent evidence and outcomes separated; do not add mandatory embedding services |

Detailed findings, limits and counterexamples: [investment agents](research/INVESTMENT_AGENTS.md), [simulation engines](research/ENGINES.md), [quantitative workflows](research/QUANT.md). All comparisons above are scoped source observations and engineering inference, not live-system benchmarks.

Three serious routes were considered: a full execution host plus language-agent graph; a portfolio/optimization front end over an existing engine; and a narrow hypothesis-to-evidence workflow. The last was chosen because its difficult integration mechanisms can be exercised and independently checked with one runtime dependency. That choice remains revisable if the supported scope expands.

AutoResearchClaw was explicitly used for two bounded scoping stages through existing Codex access. Its generated questions sharpened the distinction between reproducible accounting, historically admissible information and economic performance. No generated experiment code or autonomous paper run executed. Generated misattribution and suggested quotas/schedules were not treated as evidence or requirements. The implemented study is separately specified and executed in this repository.

The contribution is the particular coherent local workflow, constraints and inspectable product, not invention of its underlying research methods. No source investigation can establish the strongest possible trading repository or absence of prior art. Further mechanisms should earn their maintenance cost through actual user benefit and comparative evidence.

## 2026-10-22 expansion

Four additional pinned implementations were inspected. See [findings and tradeoffs](research/UPGRADE.md) and [source registry](research/UPGRADE_SOURCES.json). Original diagnostics were added without new dependencies or copied upstream source.

## Terminal investigation

The next [source investigation](research/TERMINAL.md) examined Fincept Terminal, OpenBB backend examples, Microsoft RD-Agent, Hummingbot, skfolio and the user-supplied workflow article's repository at pinned revisions. A terminal command field, shared inspection context, real ledger detail and reusable verification were retained. Autonomous generated factor code, exchange adapters and alpha-confidence badges were not claimed implemented. No source code was copied.

## Linked evidence inspection

[TradingView and pyfolio source](research/INTERACTIVE.md) informed screen-to-session mapping, native month/trough links and bounded interval diagnostics. Their chart library and trading code were not installed or copied. CHRONAL retains initial capital, exact evaluated sessions and explicit unrecovered endpoints instead of importing incompatible conventions.

## Execution evidence follow-up

[Backtrader, backtesting.py and ABIDES inspection](research/NEXT.md) adds thirteen pinned source/license/test files with [hashes and exact revisions](research/NEXT_SOURCES.json). This informed transparent request/capacity/cash/fill/expiration records while retaining the daily simulator scope. No upstream implementation was copied or executed.

## Command and investigation workflows

[Final terminal source research](research/FINAL.md) inspects 14 pinned files from Gloomberb, Longbridge Terminal and a Bloomberg-inspired terminal, with [exact revisions and hashes](research/FINAL_SOURCES.json). These support explicit command discovery/history and linked investigation. No upstream implementation was copied or executed. One project has no discovered license file at the pinned revision; its implementation was not reused.

## Typed inspection and publication pass

[Perspective, Panel and Datasette implementation research](research/PUBLICATION.md) adds 14 pinned source/license/test files across three projects, with [exact versions and hashes](research/PUBLICATION_SOURCES.json). The selected implementation is exact shared asset focus. Transactional saved-view restore remains a documented proposal, not a shipped feature.
