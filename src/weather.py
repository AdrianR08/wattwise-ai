from functools import lru_cache
from pathlib import Path
import json
import math
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ['airTemperature', 'dewTemperature', 'windSpeed']


def read_api(base, params):
    with urlopen(base + '?' + urlencode(params), timeout=12) as response:
        return json.load(response)


def search_locations(query):
    if not 2 <= len(query.strip()) <= 120:
        raise ValueError('Enter a city or postal code of 2–120 characters.')
    data = read_api('https://geocoding-api.open-meteo.com/v1/search',
                    dict(name=query.strip(), count=8, language='en', format='json'))
    return [dict(name=row['name'], region=row.get('admin1', ''), country=row.get('country', ''),
                 latitude=row['latitude'], longitude=row['longitude'], timezone=row.get('timezone', 'UTC'))
            for row in data.get('results', [])]


def location_weather(location, target, now=None):
    instant = pd.Timestamp(target)
    if instant.tzinfo is None:
        raise ValueError('Weather needs a timezone-aware target')
    observed = instant.tz_convert('UTC') - pd.Timedelta(hours=1)
    now = pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now).tz_convert('UTC')
    if observed > now.floor('h') or observed.year < 1940:
        return dict(status='unavailable', reason='Weather for this file date is outside the supported historical period.')
    latitude, longitude = float(location['latitude']), float(location['longitude'])
    if not math.isfinite(latitude) or not math.isfinite(longitude) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError('Invalid weather location')
    date = observed.strftime('%Y-%m-%d')
    historical = observed < now.normalize() - pd.Timedelta(days=7)
    base = 'https://archive-api.open-meteo.com/v1/archive' if historical else 'https://api.open-meteo.com/v1/forecast'
    params = dict(latitude=latitude, longitude=longitude, start_date=date, end_date=date,
        hourly='temperature_2m,dew_point_2m,wind_speed_10m', timezone='GMT',
        temperature_unit='celsius', wind_speed_unit='ms')
    data = read_api(base, params)
    hourly = data.get('hourly', {})
    times = pd.to_datetime(hourly.get('time', []), utc=True)
    matches = [i for i, time in enumerate(times) if time == observed]
    if not matches:
        return dict(status='unavailable', reason='The weather service has no matching hour. Using consumption-only forecasting.')
    index = matches[0]
    features = {}
    for source, column in zip(['temperature_2m', 'dew_point_2m', 'wind_speed_10m'], COLUMNS):
        values = hourly.get(source, [])
        value = values[index] if index < len(values) else None
        features['weather_previous_hour_' + column] = float(value) if value is not None and math.isfinite(value) else None
    if all(value is None for value in features.values()):
        return dict(status='unavailable', reason='Matching weather readings are missing. Using consumption-only forecasting.')
    return dict(status='available', observed_at=observed.isoformat(), features=features,
        location=location, source='Open-Meteo', kind='historical_reanalysis' if historical else 'recent_model_estimate',
        attribution='Weather data by Open-Meteo (https://open-meteo.com/), CC BY 4.0',
        limitation='Gridded weather estimates, not on-site measurements. The energy model was validated with BDG2 weather, not this provider. Historical reanalysis was not available in real time and is unsuitable for leakage-free operational backtesting.')


@lru_cache(maxsize=20)
def site_weather(site):
    metadata = pd.read_csv(ROOT / 'data/bdg2/processed/buildings_info.csv')
    matches = metadata[metadata.site_id == site]
    if matches.empty:
        raise ValueError('Unknown weather site')
    frame = pd.read_csv(ROOT / 'data/bdg2/weather.csv')
    frame = frame[frame.site_id == site].copy()
    frame['timestamp'] = pd.to_datetime(frame.timestamp).dt.tz_localize(
        matches.timezone.iloc[0], ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    frame = frame.dropna(subset=['timestamp']).set_index('timestamp')
    return frame[COLUMNS]


def previous_hour_weather(site, target):
    instant = pd.Timestamp(target)
    if instant.tzinfo is None:
        raise ValueError('Weather needs a timezone-aware target')
    observed = instant.tz_convert('UTC') - pd.Timedelta(hours=1)
    frame = site_weather(site)
    if observed not in frame.index:
        return dict(status='unavailable', reason='No weather observation at the required previous hour for this site.')
    row = frame.loc[observed]
    values = {f'weather_previous_hour_{column}': float(row[column]) if pd.notna(row[column]) else None
              for column in COLUMNS}
    if values['weather_previous_hour_windSpeed'] is not None and values['weather_previous_hour_windSpeed'] < 0:
        values['weather_previous_hour_windSpeed'] = None
    return dict(status='available', site=site, observed_at=observed.isoformat(),
                source='BDG2 historical weather; previous-hour observation, not a future forecast', features=values)
