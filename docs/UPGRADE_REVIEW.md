# Independent incremental review

Reviewed source fingerprint: `26a381e8414ed18df0698813d325c142fd077195389e5d6d746ec6d131f76bba`.

Scope: `chronal/analytics.py`, report integration and HTML rendering in `chronal/report.py`, `tests/test_analytics.py`, artifact chronology regression, and source-pinned `work/research-upgrade.md`. Runtime files were not edited by this reviewer.

## Result

Accepted within this incremental scope. No unresolved consequential findings identified. This is not proof of universal correctness or investable performance.

## Evidence

- Python 3.11 targeted suite: 20 tests plus 40 subtests passed (analytics and artifacts).
- Independent checks on 360 randomized paths at lengths 1, 2, 19, 20, 21, 39, 40, 41 and 252 compared underwater runs against a separate running-peak/run-length calculation, episode counts against those runs, monthly product against terminal NAV divided by initial cash, and effective historical tail count against ceil(n/20). All passed.
- Read and checked explicit hand examples: first-session loss enters January compounding, month transitions preserve the preceding observed NAV, recovered spells exclude recovery sessions, and unrecovered spells include the endpoint. Equal peaks reset the episode anchor to the latest equal peak. Initial cash enters the drawdown peak.
- Rendered an existing payload in its original and JSON-sorted key order: byte-identical HTML. Inserted a script-closing string into dataset metadata: escaped JSON prevented an executable script boundary.
- Diagnostics import/use is restricted to the report; no evaluation, engine, strategy or selection code invokes it. The report computes diagnostics on already evaluated session-aligned paths. No diagnostic chooses or retunes a strategy.
- Source research distinguishes empirical tail conventions across repositories and explicitly says no upstream execution or implementation equivalence was established. The local signed return tail mean is clearly defined as the worst ceil(5% times sessions) observations, with sample count displayed; it does not claim equivalence to fractional-tail CVaR.
- Artifact chronology regression changes dates, re-renders the report and reseals the manifest; verification rejects the false dates against locked data.

## Limits

The report renderer expects the internal validated artifact schema; it is not a general arbitrary-payload validation boundary. It assumes all strategy/baseline indices share the evaluated region, as produced by evaluation and checked through bundle replay. Independent browser visual/accessibility checks are owned by the parent and were not performed here. No real market experiment, alpha claim, live adapter, covariance model, upstream package execution or full repository security assessment was included. Historical expected shortfall and underwater duration describe observed sessions and do not bound future losses.
