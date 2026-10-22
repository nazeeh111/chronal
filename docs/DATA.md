# Data and availability

The CSV must contain exactly these columns, in any order:

```csv
asset,open_time,close_time,available_at,open,high,low,close,volume
SYN_A,2020-01-02T14:30:00Z,2020-01-02T21:00:00Z,2020-01-02T21:00:00Z,100,102,99,101,1000000
```

The one row illustrates syntax, not a runnable panel. Supply at least three sessions to load data and enough history for training, two development blocks and the holdout to run an experiment. The default configuration requires at least 506 sessions: 252 initial training + 2 gap + 126 development + 126 holdout.

Every asset needs exactly one row per synchronized session. Duplicate, absent or inconsistent rows fail. Prices must be positive and finite; high/low must contain open and close; volume must be finite and nonnegative. A zero-volume bar is valid data but is not fillable. No missing values are filled, backfilled or silently dropped. All assets share opening and closing instants. Sessions strictly increase and do not overlap. The loader sorts session instants; it preserves asset order from first appearance.

Timestamp strings require ISO 8601 seconds and `Z` or an explicit offset. Offsets are normalized to UTC microseconds before comparison. `available_at` cannot precede the complete bar's close. This field means when all fields of that bar were available to the modeled decision process. If historical evidence only supports a later time, use that later time. Do not manufacture precise historical times from present-day downloads.

At close t, a strategy sees a required trailing window only if every bar in that window has arrived. Otherwise it abstains and existing holdings remain. Ridge training additionally excludes label bars not published by its training cutoff. The risk circuit sees only recorded equity snapshots whose complete marking bars have been published by the current decision close; ex-post NAV remains available in the research report. Publication delay can delay risk action and is logged.

Provide a JSON object of string-to-string provenance fields with `--metadata`. Include origin/source, actual acquisition time, price basis, universe selection, calendar, usage rights and evidence supporting availability. Metadata is included in the semantic dataset fingerprint. The template is a form to complete, not verified provenance.

The simulator treats prices as unadjusted cash-instrument prices and does not process dividends or splits. Use instruments/periods without unmodeled actions, or prepare a consistent research price series and clearly explain its interpretation and historical adjustment limitations. Do not mix adjusted closes with raw opens/highs/lows. A split in raw prices would appear as an economic loss without a corresponding share adjustment.

The synthetic fixture uses four fictional assets, a seeded local random generator, correlated regime-dependent shocks, overnight gaps, intraday ranges and positive daily volume. Its weekday sessions ignore exchange holidays and daylight-saving changes. It is reproducible infrastructure data, not a realistic market sample or a price forecast. Its generation is prefix-stable and does not alter global NumPy RNG state.

## Exact timestamp normalization

The Python `MarketData` constructor accepts NumPy datetime arrays only when their instants are exactly representable in UTC microseconds. It rejects fractional-microsecond precision loss and storage overflow before simulation. Lossless nanosecond inputs are accepted. The CSV parser accepts up to six fractional digits; it does not silently truncate finer precision. A publication 500 ns after close must never become equal to close. See the independently reproduced [timestamp correction](TIMESTAMP_REVIEW.md).
