from math import isfinite
from numbers import Integral, Real
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "random_forest.joblib"
rf_w_lag_model = joblib.load(MODEL_PATH)


def predict_power(hour, month, day_of_week, lag_1h, lag_24h):
    for name, value, lower, upper in (
        ("hour", hour, 0, 23),
        ("month", month, 1, 12),
        ("day_of_week", day_of_week, 0, 6),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError(f"{name} must be an integer")
        if not lower <= value <= upper:
            raise ValueError(f"{name} must be between {lower} and {upper}")

    for name, value in (("lag_1h", lag_1h), ("lag_24h", lag_24h)):
        if value is None:
            raise ValueError("Missing required lag readings")
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite number")
        if not isfinite(value):
            raise ValueError(f"{name} must be a finite number")
        if value < 0:
            raise ValueError("lag readings must be non-negative")

    features = pd.DataFrame([{
        "hour": hour,
        "month": month,
        "day_of_week": day_of_week,
        "lag_1h": lag_1h,
        "lag_24h": lag_24h,
    }])
    return float(rf_w_lag_model.predict(features)[0])
