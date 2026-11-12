import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.consumption import analyze_csv


class ConsumptionTests(unittest.TestCase):
    def analyze(self, frame, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'customer.csv'
            frame.to_csv(path, index=False)
            return analyze_csv(path, unit='kWh', **kwargs)

    def test_missing_values_are_not_zero_usage(self):
        frame = pd.DataFrame({'time': ['2025-01-01 00:00Z', '2025-01-01 02:00Z',
                                       '2025-01-01 03:00Z'], 'usage': [10, -1, 20]})
        result = self.analyze(frame)
        self.assertEqual(result['summary']['observed_kwh'], 30)
        self.assertEqual(result['quality']['unavailable_hours'], 2)
        self.assertEqual(result['quality']['missing_hours'], 1)
        self.assertFalse(result['monthly'][0]['complete'])

    def test_duplicate_timestamps_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.analyze(pd.DataFrame({'time': ['2025-01-01', '2025-01-01'], 'usage': [1, 2]}))

    def test_complete_month_and_spike(self):
        times = pd.date_range('2025-01-01', '2025-05-01', freq='h', inclusive='left', tz='UTC')
        values = pd.Series(1., index=times)
        values.loc['2025-04-15'] = 100
        result = self.analyze(pd.DataFrame({'time': times, 'usage': values.to_numpy()}))
        self.assertTrue(all(m['complete'] for m in result['monthly']))
        self.assertIn('2025-04-15', [d['date'] for d in result['unusual_days']])

    def test_only_last_twelve_months(self):
        times = pd.date_range('2024-01-01', '2025-02-01', freq='h', inclusive='left', tz='UTC')
        result = self.analyze(pd.DataFrame({'time': times, 'usage': 1.}))
        self.assertEqual(result['monthly'][0]['month'], '2024-02')
        self.assertEqual(len(result['monthly']), 12)
