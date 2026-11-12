import unittest

import pandas as pd

from src.forecast import forecast_next_month


class ForecastTests(unittest.TestCase):
    def history(self, timezone='UTC'):
        months = []
        for start in pd.date_range('2024-03-01', '2025-02-01', freq='MS', tz=timezone):
            hours = len(pd.date_range(start, start + pd.DateOffset(months=1), freq='h', inclusive='left'))
            months.append(dict(month=start.strftime('%Y-%m'), expected_hours=hours,
                               valid_hours=hours, observed_kwh=hours * 2.))
        return months

    def test_forecast_adjusts_for_daylight_saving(self):
        result = forecast_next_month(self.history('US/Eastern'),
            pd.Timestamp('2025-03-01', tz='US/Eastern'), 'US/Eastern')
        self.assertEqual(result['predicted_kwh'], (31 * 24 - 1) * 2)
        self.assertIsNone(result['prediction_interval_kwh'])

    def test_partial_latest_month_has_no_forecast(self):
        result = forecast_next_month(self.history(), pd.Timestamp('2025-02-20', tz='UTC'), 'UTC')
        self.assertEqual(result['status'], 'unavailable')

    def test_missing_history_or_poor_coverage_has_no_forecast(self):
        months = self.history()
        end = pd.Timestamp('2025-03-01', tz='UTC')
        self.assertEqual(forecast_next_month(months[1:], end, 'UTC')['status'], 'unavailable')
        months[0]['valid_hours'] = 0
        self.assertEqual(forecast_next_month(months, end, 'UTC')['status'], 'unavailable')

    def test_small_gaps_use_observed_hourly_average(self):
        months = self.history()
        months[-1]['valid_hours'] -= 2
        months[-1]['observed_kwh'] = months[-1]['valid_hours'] * 2.
        result = forecast_next_month(months, pd.Timestamp('2025-03-01', tz='UTC'), 'UTC')
        self.assertEqual(result['predicted_kwh'], 31 * 24 * 2)
