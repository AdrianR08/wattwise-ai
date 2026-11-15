import json
import unittest

import numpy as np
import pandas as pd

from src.anomalies import detect_anomalies, forecast_watch


class AnomalyTests(unittest.TestCase):
    def series(self):
        times = pd.date_range('2025-01-01', periods=168 * 12, freq='h', tz='America/New_York')
        rng = np.random.default_rng(42)
        values = 25 + 5 * np.sin(2 * np.pi * times.hour / 24) + rng.normal(0, .4, len(times))
        return pd.Series(values, index=times)

    def test_injected_late_spike_is_flagged(self):
        series = self.series()
        instant = series.index[-10]
        series.loc[instant] = 250.
        result = detect_anomalies(series)
        self.assertEqual(result['status'], 'available')
        self.assertIn(instant.isoformat(), [row['timestamp'] for row in result['events']])
        self.assertLess(pd.Timestamp(result['fitted_through']), pd.Timestamp(result['evaluated_from']))
        self.assertLess(pd.Timestamp(result['threshold_calibrated_through']), pd.Timestamp(result['evaluated_from']))
        json.dumps(result, allow_nan=False)

    def test_future_readings_do_not_change_fitting_or_threshold(self):
        series = self.series()
        before = detect_anomalies(series)
        series.iloc[-10:] *= 5
        after = detect_anomalies(series)
        self.assertEqual(before['score_threshold'], after['score_threshold'])
        self.assertEqual(before['fitted_through'], after['fitted_through'])

    def test_missing_and_zero_readings_do_not_become_fault_claims(self):
        series = self.series()
        series.iloc[1000:1004] = np.nan
        result = detect_anomalies(series)
        self.assertNotIn(series.index[1001].isoformat(), [row['timestamp'] for row in result['events']])
        zero = detect_anomalies(pd.Series(0., index=series.index))
        self.assertEqual(zero['flagged_hours'], 0)
        json.dumps(zero, allow_nan=False)
        self.assertEqual(detect_anomalies(series.iloc[:48])['status'], 'unavailable')

    def test_forecast_watch_is_separate_from_observed_flags(self):
        result = detect_anomalies(self.series())
        watch = forecast_watch(result, 250.)
        self.assertEqual(watch['relation'], 'above')
        self.assertIn('not an observed anomaly', watch['note'])
