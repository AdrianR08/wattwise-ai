import pandas as pd


def forecast_next_month(monthly, end, timezone):
    last = monthly[-1]
    source_start = pd.Timestamp(last['month'] + '-01', tz=timezone)
    target_start = source_start + pd.DateOffset(months=1)
    target_end = target_start + pd.DateOffset(months=1)
    result = dict(status='unavailable', method='last_month_average',
                  month=target_start.strftime('%Y-%m'), predicted_kwh=None,
                  prediction_interval_kwh=None)
    if end.tz_convert(timezone) != target_start:
        return dict(result, reason='Upload readings through the end of a calendar month.')
    history = {m['month']: m for m in monthly}
    for lag in range(1, 13):
        label = (target_start - pd.DateOffset(months=lag)).strftime('%Y-%m')
        month = history.get(label)
        if month is None or month['valid_hours'] / month['expected_hours'] < .95:
            return dict(result, reason='Twelve consecutive months with at least 95% hourly coverage are required.')
    hours = len(pd.date_range(target_start, target_end, freq='h', inclusive='left'))
    return dict(result, status='available',
                predicted_kwh=float(last['observed_kwh'] / last['valid_hours'] * hours),
                source_month=last['month'], source_coverage=last['valid_hours']/last['expected_hours'],
                expected_hours=hours,
                reason='Uses the last month’s average hourly consumption, adjusted for next month’s hours. No calibrated uncertainty interval is available.')
