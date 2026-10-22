# Model and execution review

Reviewed 2026-10-22. Final integrated runtime fingerprint: `488e48e04d09ad174c10e0362b733e1672f350fe07b0a90685214adf26389ffd`.

## Independent financial review

A specialist read the data, specification, strategy, simulator, evaluation, analytics, ledger, study, artifact locking, independent accounting and replay paths. No new consequential financial defect was reproduced within that scope.

Its independent probe ran 80 randomized four-asset simulations with publication delays, skipped decisions, capital from 0.01 to 100 million, commissions up to 9,999 bps, large adverse prices, thin capacity, execution delays and drawdown stops. It reconstructed prices, fees, cash, inventory, marked NAV and causal prefixes. Another 20 ridge cases perturbed future OHLC prices and required exact equality of all preceding targets. All 100 cases passed. These establish tested invariants, not a trading edge or absence of all bugs.

After instrumentation settled, the reviewer loaded actual prior engine bytes from the preserved source ZIP and required exact equality of every pre-existing Simulation field in the 80 randomized cases. All prior indices, NAV, cash, positions, fills, events, capital, fees and notional matched. Intent fills were independently matched to actual fills; signed request/expiration identities, capacity bounds and proportional cash scaling passed. A fresh registered bundle was replayed, then one requested intent quantity was altered while its HTML and manifest were regenerated. Full replay rejected it despite unchanged financial paths. Lightweight accounting alone does not validate intent provenance.

Reproducible probes and complete reviewer notes remain task-local under work/fresh_fund_probe.py, work/fresh_fund_instrumentation_probe.py, work/fresh_intent_replay_probe.py and work/FRESH_FUND_AUDIT.md in the delivery workspace. The product regression suite separately retains durable contract scenarios.

## Interaction review

A separate reviewer extended the dependency-free Node checker to extract the actual model, fit, event and execution helper functions. It tests half-open fit boundaries, invalid ordinals preserving state, model feature/scaler/coefficient data, clearing regression state on rule strategies, unavailable fit context, exact recorded test-start navigation, deduplicated next/previous event lookup, no-event boundaries, signed intent fields and reasons, absent intents/events, and combined session/asset/side filtering. The frozen winner remains unchanged.

Actual browser testing caught null sell cash scales rendered as zero by Number(null). The original helper fixture incorrectly used 1 for sells and missed this. The report now says **Not applied**, and the fixture represents the actual null value while separately preserving numeric zero. The earlier report fails the new regression; current development and holdout reports pass. Browser verification and helper tests remain distinct evidence.

Parent browser checks exercised fit#2, native refit selection, chronological cutoff/coefficients, next/previous event buttons and commands, actual sell-null display, cash-constrained partial buys, combined fill intersection and empty state. At 390 x 844, document width equals 390, while wide tables scroll inside their containers. At 1280 x 720, model and execution tables are readable. Holdout fit#2 selects 2020-08-28 and invalid fit#3 preserves the selection. Screenshots in assets/model-inspector.png, intent-inspector.png, model-mobile.png and intent-mobile.png record this build. Scheduled holdout refits retain the frozen candidate recipe; inspection never fits a model.
