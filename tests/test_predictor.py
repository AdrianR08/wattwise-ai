import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.predictor import predict_power, rf_w_lag_model


class PredictorTests(unittest.TestCase):
    def test_saved_model_and_example(self):
        self.assertEqual(list(rf_w_lag_model.feature_names_in_),
                         ["hour", "month", "day_of_week", "lag_1h", "lag_24h"])
        result = predict_power(14, 10, 2, 45.0, 49.5)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 43.441628311492515)

    def test_calendar_boundaries_and_zero_lags(self):
        for values in [(0, 1, 0, 0, 0), (23, 12, 6, 45, 49.5)]:
            with self.subTest(values=values):
                self.assertTrue(math.isfinite(predict_power(*values)))

    def test_invalid_inputs(self):
        for position in range(5):
            invalid = [None, True, "2", float("nan"), float("inf"), -float("inf")]
            invalid += [-1, 24, 1.5] if position == 0 else []
            invalid += [0, 13, 1.5] if position == 1 else []
            invalid += [-1, 7, 1.5] if position == 2 else []
            invalid += [-0.1] if position >= 3 else []
            for value in invalid:
                args = [14, 10, 2, 45.0, 49.5]
                args[position] = value
                with self.subTest(position=position, value=value):
                    with self.assertRaises(ValueError):
                        predict_power(*args)

    def test_example_from_another_directory(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-B", str(root / "main.py")],
                                    cwd=directory, capture_output=True, text=True,
                                    check=True)
        self.assertAlmostEqual(float(result.stdout.strip()), 43.441628311492515)


if __name__ == "__main__":
    unittest.main()
