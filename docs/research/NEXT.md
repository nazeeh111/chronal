# Execution intent, rather than another ratio

Static source inspection on 2026-10-22. No upstream package was installed or executed. Thirteen exact source/license/test files are pinned and hashed in [NEXT_SOURCES.json](NEXT_SOURCES.json). Task-local source snapshots are retained outside the distributable repository. Findings describe inspected source, not independently replicated upstream behavior. No implementation is proposed for copying.

## Highest-value transfer

CHRONAL already records fills, capacity events, global proportional cash scaling, and portfolio snapshots. The preceding release could not answer one natural terminal question in a single row: **what did this asset request, what constrained it, what actually filled, and what expired?**

Add an execution-intent ledger to the existing deterministic simulator. For each eligible nonzero asset request retain session, source signal, risk-versus-strategy origin, signed requested quantity, capacity, capacity-limited quantity, actual signed fill, and signed expired remainder. Include specific causes such as capacity and cash scaling. Use the simulator's own intermediate quantities, not reconstruction from ending positions. Join by session and asset (optionally a deterministic order identifier); the daily model allows a single attempt per asset per eligible open. Expose this in the terminal as a cursor-linked table, filterable by constraint, asset and session, with CSV export. Keep “no target”, “unavailable target” and actual zero-capacity attempts distinct. A no-op request should not inflate an order fill denominator.

Why now: a good equity curve can hide failure to implement the intended portfolio. An order-intent view makes capacity and commission assumptions inspectable without pretending to estimate exchange queue positions. Aggregate only with explicit denominators: attempt counts, fully/partially/unfilled counts, and signed per-asset quantities. A cross-asset sum of shares is not an economic execution rate. Dollar-weighted rates require specifying reference prices, weights and whether they include buys and sells.

Validation: at each attempt abs(requested) = abs(filled) + abs(expired) to numerical tolerance; signs agree; fills do not exceed capacity; intent fills match the cash ledger's fills; verify/replay rejects altered intent rows; exercise simultaneous sells and cash-scaled buys, zero volume, delayed fills, risk liquidation and unavailable source signals. Keep current financial paths unchanged. Do not silently convert expiring requests into persistent pending orders.

## 1. Backtrader: distinguish lifecycle and execution bits

Pinned revision: `mementum/backtrader@b853d7c90b6721476eb5a5ea3135224e33db1f14`.

- [order.py](https://github.com/mementum/backtrader/blob/b853d7c90b6721476eb5a5ea3135224e33db1f14/backtrader/order.py): explicit Created, Submitted, Accepted, Partial, Completed, Canceled, Expired, Margin and Rejected states; creation data separate from execution data/remainder. `Order.execute` selects partial versus completed from remsize.
- [bbroker.py](https://github.com/mementum/backtrader/blob/b853d7c90b6721476eb5a5ea3135224e33db1f14/backtrader/brokers/bbroker.py): `check_submitted` pseudo-executes against cash before accepting; `_execute` uses the remaining size by default and delegates volume quantity to an optional filler. Source does not justify claiming volume-aware fills by default.
- [test_order.py](https://github.com/mementum/backtrader/blob/b853d7c90b6721476eb5a5ea3135224e33db1f14/tests/test_order.py): after multiple partial executions, cloned notifications retain only newly pending execution bits, preventing historical fills being counted repeatedly.

Transfer: explicit requested/executed/remainder fields and one authoritative accounting record. Counterevidence: copying the full broker state machine would add persistent-order semantics CHRONAL does not promise. CHRONAL should say “attempt expired after open”, not “exchange rejected”. Root LICENSE is GPL v3; source headers permit v3 or later. No code copied.

## 2. backtesting.py: rejected requests must remain visible

Pinned revision: `kernc/backtesting.py@ca2e2611621e472542ba90f7243a1fa06a7d7108`.

- [backtesting.py](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/backtesting/backtesting.py): `_process_orders` adjusts entry prices for spread and commissions, converts relative sizing into whole units, and warns/removes orders that cannot fit available margin. FIFO closing and contingent-order handling are materially richer than CHRONAL's target-weight model.
- [test/_test.py](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/backtesting/test/_test.py): `test_absolute_size_order_warns_on_insufficient_margin` checks both warning and zero executed trades; `test_spread_commission` asserts exact entry price and equity values across commission forms.

Transfer: failure to execute is a first-class observable outcome, and cost behavior deserves exact cash assertions. Counterevidence: CHRONAL deliberately scales buys proportionally rather than canceling them, and permits fractional shares. Adopt transparent explanations, not another engine's different semantics. LICENSE.md is AGPL v3. No code copied.

## 3. ABIDES: visible depth is not daily volume

Pinned revision: `jpmorganchase/abides-jpmc-public@f9cbe51342b7dedd9587e4e069040d68a5c6477f`.

- [order_book.py](https://github.com/jpmorganchase/abides-jpmc-public/blob/f9cbe51342b7dedd9587e4e069040d68a5c6477f/abides-markets/abides_markets/order_book.py): `handle_limit_order` repeatedly matches or rests the remainder; `handle_market_order` repeatedly matches until exhausted or no match; `execute_order` chooses best price then FIFO among eligible orders, reducing or removing resting quantities. `get_transacted_volume` explicitly measures past transactions over a time window, a separate object from current resting depth.
- [test_market_orders.py](https://github.com/jpmorganchase/abides-jpmc-public/blob/f9cbe51342b7dedd9587e4e069040d68a5c6477f/abides-markets/tests/orderbook/test_market_orders.py): `test_handle_market_order_bid_4` sends 70 units and asserts separate 30@100 and 40@200 executions and notifications. Limit-order and empty-book tests were also read.

Transfer: preserve each actual execution and explain model limitations. Counterevidence to a tempting upgrade: CHRONAL OHLCV contains no queue priority, resting depth or intraday arrivals. Adding an “orderbook impact” indicator would manufacture information. Continue labeling current volume clipping an ex-post daily capacity proxy. A genuine microstructure simulator would need a separate dataset and validation project. Root LICENSE and LICENSE.txt are BSD-3-Clause notices for JPMorgan and Georgia Tech respectively. No code copied.

## Decision

Implement execution-intent inspection within current daily scope; retain current cost and expiration semantics. Defer queue modeling and exchange order types. The sources support better auditability, not a claim that these UI additions improve returns or make CHRONAL production trading infrastructure.

## Delivered implementation

The current simulator now persists eligible nonzero requests as `Simulation.intents`. The terminal links the selected session to capacity, proportional cash scaling, actual fills, signed expiration and recorded events. `next-event` and `previous-event` navigate event sessions. Full replay checks the persisted intents against a new numerical run. Intent rows are retained in `results.json`; CSV exports remain the complete equity and fill ledgers. Dedicated intent constraint filters and intent CSV exports were not added. The linked model inspector exposes the registered rule and actual recorded ridge preprocessing, coefficients, cutoff and test window. Neither interface refits or changes selection.
