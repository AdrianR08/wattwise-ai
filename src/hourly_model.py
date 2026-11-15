from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


@lru_cache(maxsize=2)
def load_model(weather=False):
    filename = 'hourly_weather.joblib' if weather else 'hourly_buildings.joblib'
    return joblib.load(Path(__file__).resolve().parents[1] / 'models' / filename)


def predict_hourly(context, timezone, weather=None):
    bundle = load_model()
    weather_used = False
    if weather and weather.get('status') == 'available':
        try:
            weather_bundle = load_model(True)
            if weather_bundle['metadata'].get('weather_selected_on_validation'):
                bundle = weather_bundle
                weather_used = True
        except (OSError, ImportError):
            pass
    target = pd.Timestamp(context['timestamp'])
    if target.tzinfo is None:
        raise ValueError('Prediction timestamp needs a timezone')
    local = target.tz_convert(timezone)
    inputs = dict(hour=local.hour, month=local.month, weekday=local.dayofweek)
    for name in ('lag_1h', 'lag_24h', 'lag_168h'):
        value = context.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
            raise ValueError(f'Missing or invalid {name}: an observed reading at that exact elapsed hour is required.')
        inputs[name] = value
    if weather_used:
        target_observation = target.tz_convert('UTC') - pd.Timedelta(hours=1)
        if pd.Timestamp(weather['observed_at']) != target_observation:
            raise ValueError('Weather must be from exactly the previous elapsed hour')
        for name in bundle['metadata']['features']:
            if name.startswith('weather_previous_hour_'):
                value = weather['features'].get(name)
                inputs[name] = float(value) if value is not None and np.isfinite(value) else np.nan
    features = pd.DataFrame([inputs])[bundle['metadata']['features']]
    prediction = max(0., float(inputs['lag_1h'] + bundle['model'].predict(features)[0]))
    comparisons = {}
    for label, name in [('previous_hour', 'lag_1h'), ('24_hours_earlier', 'lag_24h'), ('168_hours_earlier', 'lag_168h')]:
        reading = inputs[name]
        comparisons[label] = dict(observed_kw=reading, difference_kw=prediction - reading,
            change_percent=100 * (prediction - reading) / reading if reading else None)
    return dict(predicted_kw=prediction, timestamp=local.isoformat(),
        estimated_hourly_kwh=prediction, comparisons=comparisons,
        local_time=local.strftime('%Y-%m-%d %H:%M %Z (UTC%z)'), timezone=timezone,
        utc_timestamp=target.tz_convert('UTC').isoformat(),
        model=bundle['metadata']['model_name'], training_buildings=bundle['metadata']['buildings'],
        weather_used=weather_used,
        weather=weather if weather_used else dict(status='not_used'),
        training_building_types=bundle['metadata']['building_types'],
        inputs={name: value if np.isfinite(value) else None for name, value in inputs.items()},
        limitation='Historical testing covers known buildings. Accuracy on new buildings is not established. Weather refers to the preceding hour; API weather may be a retrospective or recent model estimate. Open-Meteo input accuracy is not validated by the BDG2 comparison.')
