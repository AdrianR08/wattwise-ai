import unittest

import pandas as pd

from experiments.rolling_monthly import customer_fold, split


class RollingTests(unittest.TestCase):
    def test_future_rows_and_customer_targets_are_excluded(self):
        buildings = [f'customer_{i}' for i in range(30)]
        frame = pd.DataFrame([dict(building_id=b, month=m) for b in buildings
                              for m in ['2017-06', '2017-07', '2017-08']])
        seen = []
        for fold in range(5):
            train, test = split(frame, '2017-07', fold)
            self.assertTrue((train.month < '2017-07').all())
            self.assertFalse(set(train.building_id) & set(test.building_id))
            self.assertTrue(test.building_id.map(customer_fold).eq(fold).all())
            seen.extend(test.building_id)
        self.assertCountEqual(seen, buildings)
