import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from experiments.compare_monthly import FEATURES, examples, summarize


class MonthlyTests(unittest.TestCase):
    def test_target_month_does_not_change_history_features(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            pd.DataFrame([dict(building_id='customer', timezone='UTC',
                               primaryspaceusage='Office')]).to_csv(folder / 'buildings_info.csv', index=False)
            times = pd.date_range('2016-01-01', '2017-02-01', freq='h', inclusive='left', tz='UTC')
            frame = pd.DataFrame({'time': times, 'power': 2.})
            with patch('experiments.compare_monthly.DATA', folder):
                frame.to_csv(folder / 'customer.csv', index=False)
                before = examples()
                frame.loc[frame.time >= '2017-01-01', 'power'] = 20
                frame.to_csv(folder / 'customer.csv', index=False)
                after = examples()
            self.assertEqual(len(before), 1)
            np.testing.assert_allclose(before[FEATURES], after[FEATURES])
            self.assertAlmostEqual(after.target_kwh.iloc[0], 10 * before.target_kwh.iloc[0])

    def test_zero_consumption_metrics_remain_finite(self):
        result = summarize(pd.DataFrame([dict(model='baseline', building_id='customer',
                                              actual_kwh=0., absolute_error_kwh=1.)]))
        self.assertTrue(np.isfinite(result.to_numpy()).all())
