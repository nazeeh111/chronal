import csv
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from chronal.data import load_csv, make_demo, write_csv


class DataTests(unittest.TestCase):
    def setUp(self):
        self.data = make_demo(sessions=12)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "bars.csv"

    def rows(self):
        write_csv(self.data, self.path)
        with self.path.open(newline="") as stream:
            return list(csv.reader(stream))

    def save_rows(self, rows):
        with self.path.open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)

    def test_roundtrip_preserves_every_array_and_semantic_hash(self):
        write_csv(self.data, self.path)
        reread = load_csv(self.path, dict(self.data.metadata))
        self.assertEqual(reread.fingerprint, self.data.fingerprint)
        for name in ("open_time", "close_time", "available_at", "open", "high", "low", "close", "volume"):
            np.testing.assert_array_equal(getattr(reread, name), getattr(self.data, name))

    def test_explicit_offsets_normalize_to_utc(self):
        rows = self.rows()
        for row in rows[1:]:
            for col in (1, 2, 3):
                stamp = datetime.fromisoformat(row[col].replace("Z", "+00:00"))
                row[col] = stamp.astimezone(timezone(timedelta(hours=-4))).isoformat()
        self.save_rows(rows)
        reread = load_csv(self.path, dict(self.data.metadata))
        self.assertEqual(reread.fingerprint, self.data.fingerprint)

    def test_duplicate_missing_extra_and_nonrectangular_rows_rejected(self):
        rows = self.rows()
        cases = [
            rows + [rows[1]],
            rows[:2] + rows[3:],
            [rows[0] + ["extra"]] + [r + ["x"] for r in rows[1:]],
            [rows[0][:-1]] + [r[:-1] for r in rows[1:]],
            [rows[0]] + [rows[1][:-1]] + rows[2:],
        ]
        for malformed in cases:
            with self.subTest(case=malformed[:2]):
                self.save_rows(malformed)
                with self.assertRaises(ValueError):
                    load_csv(self.path)

    def test_timezone_missing_bad_number_and_empty_field_rejected(self):
        rows = self.rows()
        for column, value in (
            (1, rows[1][1][:-1]),
            (1, "2020-01-01"),
            (4, "NaN"),
            (4, "inf"),
            (4, "bad"),
            (4, ""),
        ):
            malformed = [r.copy() for r in rows]
            malformed[1][column] = value
            self.save_rows(malformed)
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                load_csv(self.path)

    def test_utc_duplicate_spellings_are_still_duplicates(self):
        rows = self.rows()
        duplicate = rows[1].copy()
        duplicate[1] = duplicate[1].replace("Z", "+00:00")
        self.save_rows(rows + [duplicate])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_csv(self.path)

    def test_unsynchronized_asset_closes_rejected(self):
        rows = self.rows()
        rows[2][2] = rows[2][2].replace("21:00", "21:01")
        # The fixture's recorded close is 21:00 UTC for every synthetic session.
        self.save_rows(rows)
        with self.assertRaises(ValueError):
            load_csv(self.path)

    def test_invalid_values_and_shapes_rejected(self):
        bad = self.data.close.copy()
        bad[0, 0] = 0
        cases = [
            {"close": bad},
            {"high": self.data.low},
            {"volume": -self.data.volume},
            {"close": self.data.close[:, :1]},
            {"assets": ("DUP",) * 4},
            {"assets": ("bad\nasset", "B", "C", "D")},
            {"metadata": {"bad": 1}},
        ]
        for changes in cases:
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                replace(self.data, **changes)

    def test_early_availability_nat_overlap_and_short_panels_rejected(self):
        available = self.data.available_at.copy()
        available[0, 0] -= np.timedelta64(1, "us")
        nat = self.data.open_time.copy()
        nat[0] = np.datetime64("NaT", "us")
        opened = self.data.open_time.copy()
        opened[1] = self.data.close_time[0]
        for changes in ({"available_at": available}, {"open_time": nat}, {"open_time": opened}):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                replace(self.data, **changes)
        with self.assertRaises(ValueError):
            self.data.subset(2)

    def test_owns_immutable_arrays_and_metadata(self):
        prices = self.data.close.copy()
        metadata = {"source": "test"}
        copied = replace(self.data, close=prices, metadata=metadata)
        prices[0, 0] *= 2
        metadata["source"] = "changed"
        self.assertNotEqual(prices[0, 0], copied.close[0, 0])
        self.assertEqual(copied.metadata["source"], "test")
        with self.assertRaises(ValueError):
            copied.close[0, 0] = 1
        with self.assertRaises(ValueError):
            copied.close.flags.writeable = True
        with self.assertRaises(TypeError):
            copied.metadata["source"] = "changed"

    def test_demo_is_deterministic_explicit_and_rng_local(self):
        state = np.random.get_state()
        first = make_demo(seed=3, sessions=30)
        after = np.random.get_state()
        self.assertEqual(state[0], after[0])
        np.testing.assert_array_equal(state[1], after[1])
        self.assertEqual(state[2:], after[2:])
        self.assertEqual(first.fingerprint, make_demo(seed=3, sessions=30).fingerprint)
        self.assertNotEqual(first.fingerprint, make_demo(seed=4, sessions=30).fingerprint)
        self.assertEqual(first.metadata["synthetic"], "true")
        self.assertTrue(all(a.startswith("SYN_") for a in first.assets))
        self.assertEqual(first.subset(12).fingerprint, make_demo(seed=3, sessions=30).subset(12).fingerprint)
        self.assertEqual(first.subset(12).fingerprint, make_demo(seed=3, sessions=12).fingerprint)

    def test_lossy_timestamp_normalization_rejected_without_enabling_signals(self):
        # Publication a fraction of a microsecond after close cannot become
        # observable at that close through downward precision truncation.
        for name in ("open_time", "close_time", "available_at"):
            values = getattr(self.data, name).astype("datetime64[ns]")
            values += np.timedelta64(500, "ns")
            with self.subTest(field=name), self.assertRaisesRegex(ValueError, "exactly representable"):
                replace(self.data, **{name: values})
        # Higher-precision containers remain accepted when no instant changes.
        precise = replace(
            self.data,
            **{
                name: getattr(self.data, name).astype("datetime64[ns]")
                for name in ("open_time", "close_time", "available_at")
            },
        )
        self.assertEqual(precise.fingerprint, self.data.fingerprint)

    def test_timestamp_cast_overflow_rejected(self):
        # Coarse NumPy units can express years beyond microsecond storage.
        times = np.array(["1000000", "1000001", "1000002"], dtype="datetime64[Y]")
        with self.assertRaisesRegex(ValueError, "exactly representable"):
            replace(self.data, open_time=times)

    def test_timestamps_normalized_to_microseconds_and_metadata_hashed(self):
        self.assertEqual(str(self.data.open_time.dtype), "datetime64[us]")
        self.assertEqual(str(self.data.available_at.dtype), "datetime64[us]")
        renamed = replace(self.data, metadata={**self.data.metadata, "source": "other"})
        self.assertNotEqual(self.data.fingerprint, renamed.fingerprint)

    def test_calendar_range_rejects_unreadable_exports_and_boundaries_roundtrip(self):
        for name in ("open_time", "close_time", "available_at"):
            for stamp in ("0000-12-31T23:59:59", "10000-01-01T00:00:00"):
                changed = getattr(self.data, name).copy()
                changed.flat[0] = np.datetime64(stamp, "us")
                with (
                    self.subTest(field=name, stamp=stamp),
                    self.assertRaisesRegex(ValueError, "calendar years"),
                ):
                    replace(self.data, **{name: changed})
        for stamp in ("0001-01-01T14:30:00", "9999-12-01T14:30:00"):
            shift = np.datetime64(stamp, "us") - self.data.open_time[0]
            shifted = replace(
                self.data,
                **{
                    name: getattr(self.data, name) + shift
                    for name in ("open_time", "close_time", "available_at")
                },
            )
            write_csv(shifted, self.path)
            with self.subTest(boundary=stamp):
                self.assertEqual(load_csv(self.path, dict(shifted.metadata)).fingerprint, shifted.fingerprint)


if __name__ == "__main__":
    unittest.main()
