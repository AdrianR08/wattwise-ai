import pandas as pd

from src.monthly_model import predict_monthly


def forecast_next_month(monthly, end, timezone):
    last = monthly[-1]
    source_start = pd.Timestamp(last['month'] + '-01', tz=timezone)
    target_start = source_start + pd.DateOffset(months=1)
    target_end = target_start + pd.DateOffset(months=1)
    result = dict(status='unavailable', method='last_month_baseline', model_name='Last-month baseline',
                  month=target_start.strftime('%Y-%m'), predicted_kwh=None,
                  prediction_interval_kwh=None)
    if end.tz_convert(timezone) != target_start:
        return dict(result, reason='Upload readings through the end of a calendar month.')
    history = {m['month']: m for m in monthly}
    rates = []
    for lag in range(1, 13):
        label = (target_start - pd.DateOffset(months=lag)).strftime('%Y-%m')
        month = history.get(label)
        if month is None or month['valid_hours'] / month['expected_hours'] < .95:
            return dict(result, reason='Twelve consecutive months with at least 95% hourly coverage are required.')
        rates.append(month['observed_kwh'] / month['valid_hours'])
    hours = len(pd.date_range(target_start, target_end, freq='h', inclusive='left'))
    comparison = None
    try:
        comparison = float(predict_monthly(rates, target_start.month) * hours)
    except (OSError, ValueError, ImportError):
        pass
    return dict(result, status='available',
                predicted_kwh=float(rates[0] * hours), random_forest_kwh=comparison,
                baseline_kwh=float(rates[0] * hours),
                source_month=last['month'], source_coverage=last['valid_hours']/last['expected_hours'],
                expected_hours=hours,
                weather_used=False,
                selection_reason='The last-month baseline had lower mean building error in the expanded historical monthly comparison. It is a simple rule, not a trained model.',
                reason='Uses the last observed month’s mean hourly consumption, adjusted for the target month’s calendar hours. No calibrated uncertainty interval is available.')
