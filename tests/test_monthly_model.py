import unittest

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from src.monthly_model import load_model, make_features, predict_monthly


class MonthlyModelTests(unittest.TestCase):
    def test_deployed_artifact_is_trained_random_forest(self):
        model = load_model()
        self.assertIsInstance(model, RandomForestRegressor)
        self.assertEqual(len(model.estimators_), 150)
        self.assertGreaterEqual(predict_monthly([2.] * 12, 1), 0)
        self.assertAlmostEqual(predict_monthly([4.] * 12, 1), 2 * predict_monthly([2.] * 12, 1))

    def test_monthly_order_and_seasonal_features(self):
        rates = np.arange(1, 13)
        features, scale = make_features(rates, 3)
        self.assertEqual(scale, 6.5)
        self.assertAlmostEqual(features.history_1.iloc[0], 1/6.5)
        self.assertAlmostEqual(features.history_12.iloc[0], 12/6.5)
        self.assertAlmostEqual(features.month_sin.iloc[0], 1)
        with self.assertRaises(ValueError):
            make_features([1.] * 11, 1)
