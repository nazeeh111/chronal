# Independent timestamp normalization review

Reviewed `chronal/data.py` and `tests/test_data.py` on 2026-10-22 without editing either file. Review source SHA256 for data.py: `4bdc67fbad302d36d41612daa2626a4218a1df4d9d2258d7957fa049d112ff2e`.

## Outcome

No unresolved consequential finding in the timestamp precision correction. The new conversion round-trip check rejects input instants that cannot be represented exactly in UTC microseconds, before a MarketData instance can enter simulation. Valid lossless datetime64[ns] inputs remain accepted and preserve the semantic fingerprint.

## Independent evidence

- Reconstructed only the previous normalization helper in a process-local monkeypatch. A synthetic 30-session equal-weight fixture with publication 500 ns after every close produced **8 fills** under the previous truncation behavior. Current construction rejects this same input with `ValueError: timestamps must be exactly representable as UTC microseconds`.
- Tested **98 independently computed cases** against a Python arbitrary-precision rational-duration oracle, covering W, D, h, m, s, ms, us, ns, ps, fs, as and scaled units 3us, 3ns, 7D. Cases included zero, positive and negative small counts and positive/negative 2**62 counts. Acceptance exactly matched divisibility into microseconds and the signed-int64 storage range excluding NaT.
- Tested **12 extreme calendar dates** across year, month and day units, at years +/-1000000 and +/-1000000000. All rejected before use.
- Exact us/ns conversions preserve the fixture semantic fingerprint.
- Ran current focused data suite: **13 tests and 24 subtests passed** on task-local Python 3.14.
- Reproducer retained in `work/timestamp_independent.py`.

## Calibration and limits

This is an actual information-availability bug correction, not merely a formatting change: premature publication can enable decisions and fills. The current check closes that demonstrated path. Some especially extreme unit conversions raise NumPy `OverflowError` directly rather than the custom ValueError; they still reject invalid input safely. This is a minor exception-type consistency detail, not a surviving precision or causal bypass.

Review does not establish general trading correctness or real-market profitability. Package-wide source hash is intentionally omitted because the parent is concurrently editing report.py. Regeneration/replay of final artifacts remains the parent delivery gate.
