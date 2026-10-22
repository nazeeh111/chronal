# Quantitative workflow and portfolio implementation research

2026-10-21. Static source inspection, no upstream execution or performance replication. Selected pinned source URLs and hashes are in SOURCES.json; source bytes are retained outside this repository in the build workspace. This document distinguishes observations from architecture inference.

## Qlib

Pinned microsoft/qlib at 54355232463878d2eebb91fe0ee5fa7fa1f5976c, MIT.

- `qlib/data/dataset/handler.py` separates learning and inference processors, supports shared or independent processor pipelines and explicit fit start/end times. Transfer: preprocessing is fitted state that must be locked to training, not an innocuous whole-frame transformation. Merely setting a dataset test segment does not prove every processor was fitted causally.
- `qlib/workflow/record_temp.py` records model predictions, labels, IC and portfolio analysis as separate artifacts with dependencies. Transfer: predictions, learned state, evaluation and financial accounting belong to one traceable experiment.
- `qlib/backtest/exchange.py` supports distinct buy/sell deal expressions, asymmetric fees, minimum cost, volume and price-limit rules. These configurable conventions establish a need to record exact assumptions, not a universal fidelity guarantee.
- `qlib/contrib/evaluate.py:26-97` explicitly offers arithmetic sum mode as default and geometric product mode. Product mode uses log-return volatility and geometric mean for its ratio. These are intentional definitions. Chronal will instead report conventional simple-return sample volatility, arithmetic-mean Sharpe and geometric capital growth, with initial capital included in drawdown. The choice is about explicit interpretation, not labeling Qlib wrong.
- `long_short_backtest` has explicit shift=1 semantics to map a prediction to a later trading day. A date shift alone does not make upstream features causal.

Inference: Qlib is a stronger starting point for large model/data research and expression-based features. Making its ecosystem mandatory would add much more machinery than the selected local, small-universe daily research workflow needs. Chronal implements a transparent ridge baseline using NumPy's standard linear solver; it does not claim to integrate Qlib or outperform its models.

## skfolio

Pinned skfolio/skfolio at 9effd863f19ec969ee93f654db1e8770343a4215, BSD-3-Clause.

`src/skfolio/model_selection/_walk_forward.py` has explicit train/test observation windows, expanding training, optional partial final test and purging. It validates positive window sizes and rejects empty training folds. Integer purging shortens training without moving the test start. Transfer: state exact exclusive boundaries and retain every fold, rather than presenting a single average score. Current official docs also distinguish combinatorial CV paths from strictly forward simulations; do not call arbitrary purged folds historically executable.

`optimization/convex/_mean_risk.py` composes portfolio objectives, transaction costs, constraints and convex solvers. It is a plausible optional extension when optimization warrants a solver stack. Default Chronal uses bounded equal weights over selected positive scores and a simple shrunk covariance only to reduce exposure. It does not claim optimal portfolios, risk parity or learned allocation uncertainty.

## PyPortfolioOpt

Pinned robertmartin8/PyPortfolioOpt at a6638d2e06dae6f444fd022cfd4b3c528902a85b. Selected `risk_models.py` distinguishes sample, semivariance, exponentially weighted and shrunk covariance estimates and treats PSD correction explicitly. `efficient_cvar.py` formulates tail-risk optimization through CVXPY and explicit confidence/weight bounds. Transfer: separate estimated risk from realized risk and state estimator conventions. A volatility target based on history is not a future risk guarantee. Chronal uses a fixed 80% sample plus 20% diagonal shrinkage, does not estimate an optimal shrinkage parameter, never increases leverage to hit a target, and reports realized historical CVaR independently of allocation.

The first assumed LICENSE.txt path returned 404; the actual LICENSE file was then inspected at the pinned revision and is MIT, copyright Robert Andrew Martin. Do not infer licensing from a package's name or a previous version. No source bytes were copied into Chronal.

## Competing directions and chosen mechanism

1. Full existing execution host plus agent graph: broad asset and live-order functionality, but high data/model/provider/setup burden, and no automatic guarantee that the joined experiment is causal.
2. A portfolio-tree research front end over bt or solver-centric skfolio: excellent allocation primitives, but a separate contract is still required for observation availability, next-open execution and model selection. Existing library integration remains a reasonable future route when scope expands.
3. A narrow hypothesis-to-evidence workflow: constrained strategy JSON, train-only statistical learning, daily cash accounting, development-only selection, separate holdout and replayable reports. Chosen because it exercises the integration mechanism and is independently hand-checkable with one runtime dependency.

This is a practical engineering decision, not a proof of global superiority. The originality is the particular coherent workflow and product experience, not invention of backtesting, ridge regression, walk-forward validation, portfolio caps, hashing or agent review.

## AutoResearchClaw contribution and limits

The explicitly requested tool was run through TOPIC_INIT and PROBLEM_DECOMPOSE only. Both stages completed through existing Codex access after a native permission-scoped retry. No generated experiment code or full paper pipeline ran. The output distinguished replayability, historical admissibility and investment performance and proposed independent reference ledgers, timing mutation tests and selection-aware studies. These sharpened acceptance checks.

Its generated problem_tree attributed its input to a named draft not supplied in this task and suggested a four-week schedule and fixture quotas. These were not verified source claims or binding requirements and were not adopted. The launcher attempted a hardware advisory PyTorch installation, which failed because pip was absent; CPU dependencies remained available. Generated research prose is advisory evidence, not a scientific result. Chronal's actual synthetic study is separately designed, executed, and reported with all replications and explicit limitations.
