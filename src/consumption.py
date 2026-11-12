import numpy as np
import pandas as pd

from src.forecast import forecast_next_month


def analyze_csv(path, *, unit, timezone='UTC', timestamp_column=None, value_column=None):
    if unit not in ('kWh', 'kW'):
        raise ValueError('Unit must be kWh per hourly interval or hourly average kW')
    raw = pd.read_csv(path)
    if len(raw.columns) < 2 or raw.empty:
        raise ValueError('CSV needs timestamp and consumption columns and at least one row')
    timestamp_column = timestamp_column or raw.columns[0]
    value_column = value_column or raw.columns[1]
    times = pd.to_datetime(raw[timestamp_column], errors='coerce')
    if times.isna().any():
        raise ValueError('CSV contains invalid timestamps')
    try:
        if times.dt.tz is None:
            times = times.dt.tz_localize(timezone, ambiguous='raise', nonexistent='raise')
        times = times.dt.tz_convert('UTC')
    except (AttributeError, ValueError) as exc:
        raise ValueError('Use consistent timestamps with explicit UTC offsets around daylight saving changes') from exc
    if times.duplicated().any():
        raise ValueError('Duplicate timestamps must be resolved before analysis')
    if ((times.dt.minute != 0) | (times.dt.second != 0) | (times.dt.microsecond != 0)).any():
        raise ValueError('This version requires readings on hourly boundaries')
    values = pd.to_numeric(raw[value_column], errors='coerce')
    invalid = ~np.isfinite(values) | (values < 0)
    series = pd.Series(values.mask(invalid).to_numpy(), index=times).sort_index()
    end = series.index.max() + pd.Timedelta(hours=1)
    cutoff = end - pd.DateOffset(months=12)
    series = series[series.index >= cutoff]
    if series.notna().sum() == 0:
        raise ValueError('No valid readings in the last 12 months')
    grid = pd.date_range(series.index.min(), series.index.max(), freq='h')
    missing = len(grid.difference(series.index))
    series = series.reindex(grid).tz_convert(timezone)
    # Hourly average kW over one hour and interval kWh have the same energy value.
    monthly = []
    for month, g in series.groupby(series.index.strftime('%Y-%m')):
        start = pd.Timestamp(month + '-01', tz=timezone)
        stop = start + pd.DateOffset(months=1)
        expected = len(pd.date_range(start, stop, freq='h', inclusive='left'))
        monthly.append(dict(month=month, observed_kwh=float(g.sum()),
                            valid_hours=int(g.count()), expected_hours=expected,
                            complete=bool(g.count() == expected)))
    days = []
    for day, g in series.groupby(series.index.strftime('%Y-%m-%d')):
        start = pd.Timestamp(day, tz=timezone)
        stop = start + pd.DateOffset(days=1)
        expected = len(pd.date_range(start, stop, freq='h', inclusive='left'))
        if g.count() == expected:
            days.append(dict(date=day, weekday=start.dayofweek, kwh=float(g.sum())))
    findings = []
    for row in days:
        peers = [d['kwh'] for d in days if d['weekday'] == row['weekday'] and d['date'] != row['date']]
        if len(peers) < 8:
            continue
        typical = float(np.median(peers))
        mad = float(np.median(np.abs(np.array(peers) - typical)))
        if abs(row['kwh'] - typical) > max(6 * 1.4826 * mad, .5 * typical, 1e-9):
            findings.append(dict(date=row['date'], kind='high' if row['kwh'] > typical else 'low',
                                 observed_kwh=row['kwh'], typical_same_weekday_kwh=typical))
    valid = series.dropna()
    return dict(schema_version=1, input_unit=unit, timezone=timezone,
        interval='hourly', window_start=str(series.index.min()), window_end_exclusive=str(end),
        quality=dict(input_rows=len(raw), retained_valid_hours=len(valid),
                     invalid_readings_in_input=int(invalid.sum()), missing_hours=missing,
                     unavailable_hours=int(series.isna().sum()), expected_hours=len(series),
                     coverage_fraction=float(len(valid)/len(series))),
        summary=dict(observed_kwh=float(valid.sum()), average_hourly_kwh=float(valid.mean()),
                     highest_hour=dict(timestamp=str(valid.idxmax()), kwh=float(valid.max())),
                     lowest_hour=dict(timestamp=str(valid.idxmin()), kwh=float(valid.min()))),
        monthly=monthly, unusual_days=findings,
        forecast=forecast_next_month(monthly, end, timezone),
        limitations=['Totals exclude unavailable readings; incomplete months are marked.',
                     'Unusual days are statistical flags, not diagnoses of faulty equipment.',
                     'Daily flags compare same weekdays without seasonal or weather adjustment.',
                     'The forecast assumes last month’s average usage continues; weather and operational changes are not predicted.'])
