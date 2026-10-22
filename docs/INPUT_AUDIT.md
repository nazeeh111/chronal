# Fresh runtime audit, 2026-10-22

## Scope and result
Read current runtime implementation (data, engine, strategies, specs, chronological evaluation, artifact registration/verification, analytics, ledger diagnostics) and existing tests rather than treating historical review as authority. Repository state was wholly untracked, no staged files, commits or remotes changed. Parent owns report.py and concurrent UI changes; no report.py edits made here.

One demonstrated input-causality bug fixed: MarketData accepted higher-resolution NumPy timestamps and silently truncated them to microseconds. Publication 500 ns after close became equal to close, permitting four next-open fills for a decision which could not observe that bar at the declared close. All three timestamp arrays are now accepted only if conversion to UTC microseconds round-trips exactly to their original dtype. This also rejects coarse-unit dates overflowing microsecond storage. Lossless datetime64[ns] inputs remain accepted and retain their semantic fingerprint.

## Changes and checks
- Changed chronal/data.py only in runtime; added two meaningful tests in tests/test_data.py.
- Before-fix reproducer: 2018-01-02T21:00:00.000000500 converted to 2018-01-02T21:00:00.000000, four fills. After fix, constructor rejects precision loss before simulation.
- Full current suite Python3.14: 75 tests / 120 subtests passed in 6.18 s.
- Focused Python3.11 data suite: 13 tests / 24 subtests passed.
- Ruff lint and format check for both edited files passed.
- New tests cover fractional-microsecond loss in open_time, close_time, available_at; exact lossless nanosecond equivalence; year1000000 coarse-unit overflow.

## Limits
This is a focused source audit plus demonstrated input-edge-case correction, not proof of universal correctness or real-market alpha. Existing source hashes must change and examples must be regenerated before final delivery. Parent UI/report editing continues concurrently. Full replay is still necessary to verify simulation semantics; a local unsigned manifest is not authenticity proof. No paid APIs, credentials, live trading, commits, pushes or publication used.

Snapshot package fingerprint (includes concurrently edited report.py): `75d23d4f9dee842e00fc4c4e6909fe9b79bec7082a99a734968d0d0f8e920009`.

Audited runtime file hashes excluding parent-owned report.py:

```json
{
  "chronal/__init__.py": "4de88ba255c19407cb9f0679c18cde92578bc3d3aa685b154fdccce3cd80a35b",
  "chronal/__main__.py": "935a1c1166b0c1ea35a82256345000bf2c73ded718d77773bc27a71ecce28f7d",
  "chronal/analytics.py": "ccbec49d617e94cc1ffa4ebdc9e4748564961a32002448a092b8e56afb550c61",
  "chronal/artifacts.py": "8bfb9e928bbada80b8781c0b0e84bc78f0f3cd7f7f701ecbdb0c549e8b81dfec",
  "chronal/cli.py": "527d27bcc10920a7f45a5e7c1b705a61f2320b70a42801e843627784c535e73a",
  "chronal/data.py": "4bdc67fbad302d36d41612daa2626a4218a1df4d9d2258d7957fa049d112ff2e",
  "chronal/engine.py": "bc08c540aceb4bfba5f06ff2b386db8a94625a8ee68412578e26788fb1698107",
  "chronal/evaluation.py": "b0e2af4a048154540d83069fc0c7c20a65b05f348589169ae24949a1db1f10c0",
  "chronal/ledger.py": "5d5d85a530fc842fcfe474b65838cc9daa81ca358d5c8b4d14fc5217677d648e",
  "chronal/spec.py": "47a78720faae67abde0ee389a1fa5cbf00d81b9df97cbfa492d33498284b8f03",
  "chronal/strategies.py": "1080f750e8a6e78e52fd046b19010f0fcbf8364a8e537daf11bd7303d2e6f0e8",
  "chronal/study.py": "8e4c681bf030c75ecd9a4e23c474fb77d84ed75fab4d372374be5bdfc6a84e00"
}
```
