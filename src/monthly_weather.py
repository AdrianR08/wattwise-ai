from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.monthly_model import make_features
from src.weather import read_api, site_weather

WEATHER_FEATURES = ['previous_month_temperature', 'previous_month_heating', 'previous_month_cooling',
                    'seasonal_temperature', 'seasonal_heating', 'seasonal_cooling']
MODEL_PATH = Path(__file__).resolve().parents[1] / 'models/monthly_weather.joblib'


def temperature_summary(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        raise ValueError('Monthly weather is missing')
    return [float(values.mean()), float(np.maximum(18 - values, 0).mean()),
            float(np.maximum(values - 18, 0).mean())]


def site_monthly_features(site, month):
    weather = site_weather(site).airTemperature
    metadata = pd.read_csv(Path(__file__).resolve().parents[1] / 'data/bdg2/processed/buildings_info.csv')
    timezone = metadata.loc[metadata.site_id == site, 'timezone'].iloc[0]
    local = weather.tz_convert(timezone)
    periods = local.index.strftime('%Y-%m')
    target = pd.Period(month, freq='M')
    values = []
    for lag in (1, 12):
        sample = local[periods == str(target - lag)]
        values.extend(temperature_summary(sample))
    return values


def api_monthly_features(location, month, now=None):
    target = pd.Period(month, freq='M')
    now = pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    values = []
    for lag in (1, 12):
        period = target - lag
        start, end = period.start_time.date(), period.end_time.date()
        if pd.Timestamp(end, tz='UTC') > now - pd.Timedelta(days=7):
            raise ValueError('Complete historical monthly weather is not yet available; using the consumption-only forecast.')
        data = read_api('https://archive-api.open-meteo.com/v1/archive',
            dict(latitude=location['latitude'], longitude=location['longitude'], start_date=str(start),
                 end_date=str(end), hourly='temperature_2m', temperature_unit='celsius', timezone=location['timezone']))
        temperatures = np.asarray(data['hourly']['temperature_2m'], dtype=float)
        if np.isfinite(temperatures).mean() < .95:
            raise ValueError('Monthly weather coverage is insufficient')
        values.extend(temperature_summary(temperatures))
    return values


@lru_cache(maxsize=1)
def load_monthly_weather():
    return joblib.load(MODEL_PATH)


def forecast_with_weather(forecast, monthly, weather_features):
    bundle = load_monthly_weather()
    if not bundle['selected_on_validation']:
        return forecast
    month = pd.Period(forecast['month'], freq='M')
    history = {row['month']: row for row in monthly}
    rates = [history[str(month - lag)]['observed_kwh'] / history[str(month - lag)]['valid_hours'] for lag in range(1, 13)]
    features, scale = make_features(rates, month.month)
    if len(weather_features) != 6 or not np.isfinite(weather_features).all():
        raise ValueError('Six valid monthly weather features are required')
    for name, value in zip(WEATHER_FEATURES, weather_features):
        features[name] = value
    prediction = max(0., float(bundle['model'].predict(features[bundle['features']])[0])) * scale * forecast['expected_hours']
    return dict(forecast, predicted_kwh=prediction, method='monthly_weather', weather_used=True,
        model_name=bundle['model_name'],
        weather_basis='Previous-month temperature and the target calendar month one year earlier; seasonal proxy, not a next-month weather forecast.',
        validation_note=bundle['validation_note'])
