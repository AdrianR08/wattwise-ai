from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

FEATURES = [f'history_{i}' for i in range(1, 13)] + ['month_sin', 'month_cos']
MODEL_PATH = Path(__file__).resolve().parents[1] / 'models/monthly_random_forest.joblib'


def make_features(rates, month):
    rates = np.asarray(rates, dtype=float)
    if rates.shape != (12,) or not np.isfinite(rates).all() or (rates < 0).any():
        raise ValueError('Twelve valid monthly averages are required')
    scale = max(float(rates.mean()), 1.)
    values = list(rates / scale) + [np.sin(2*np.pi*month/12), np.cos(2*np.pi*month/12)]
    return pd.DataFrame([values], columns=FEATURES), scale


@lru_cache(maxsize=1)
def load_model():
    bundle = joblib.load(MODEL_PATH)
    if bundle['features'] != FEATURES:
        raise ValueError('Monthly model feature mismatch')
    return bundle['model']


def predict_monthly(rates, month):
    features, scale = make_features(rates, month)
    prediction = float(load_model().predict(features)[0]) * scale
    if not np.isfinite(prediction):
        raise ValueError('Invalid model prediction')
    return max(0., prediction)
