import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor

FEATURES = ['hour', 'weekday', 'month', 'lag_1h', 'lag_24h', 'lag_168h']


def anomaly_features(frame, expected, scale):
    actual = frame.actual_kw.to_numpy()
    return np.column_stack([(actual - expected) / scale,
        (actual - frame.lag_1h.to_numpy()) / scale,
        (actual - frame.lag_24h.to_numpy()) / scale,
        (actual - frame.lag_168h.to_numpy()) / scale])


def detect_anomalies(series):
    frame = pd.DataFrame(dict(actual_kw=series, hour=series.index.hour,
        weekday=series.index.dayofweek, month=series.index.month))
    for lag in (1, 24, 168):
        frame[f'lag_{lag}h'] = series.shift(lag)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 1008:
        return dict(status='unavailable', reason='At least seven weeks of usable hourly readings, including a preceding week for lag readings, are needed for the anomaly model.')
    n = len(frame)
    a, b, c = int(n * .5), int(n * .7), int(n * .85)
    train, fit, calibration, recent = frame.iloc[:a], frame.iloc[a:b], frame.iloc[b:c], frame.iloc[c:]
    predictor = RandomForestRegressor(n_estimators=60, max_depth=12,
        min_samples_leaf=5, random_state=42, n_jobs=1)
    predictor.fit(train[FEATURES], train.actual_kw)
    scale = max(float(train.actual_kw.median()), 1.)
    expected_fit = np.maximum(0, predictor.predict(fit[FEATURES]))
    detector = IsolationForest(n_estimators=100, contamination='auto', random_state=42, n_jobs=1)
    detector.fit(anomaly_features(fit, expected_fit, scale))
    expected_calibration = np.maximum(0, predictor.predict(calibration[FEATURES]))
    calibration_scores = -detector.score_samples(anomaly_features(calibration, expected_calibration, scale))
    threshold = float(np.quantile(calibration_scores, .99))
    residuals = calibration.actual_kw.to_numpy() - expected_calibration
    residual_mad = float(np.median(np.abs(residuals - np.median(residuals))))
    expected = np.maximum(0, predictor.predict(recent[FEATURES]))
    scores = -detector.score_samples(anomaly_features(recent, expected, scale))
    deviations = recent.actual_kw.to_numpy() - expected
    flagged = (scores > threshold) & (np.abs(deviations) > np.maximum(3 * 1.4826 * residual_mad, np.maximum(.2 * expected, 1.)))
    events = []
    for index in np.flatnonzero(flagged):
        observed, projection, delta = float(recent.actual_kw.iloc[index]), float(expected[index]), float(deviations[index])
        events.append(dict(timestamp=recent.index[index].isoformat(), observed_kw=observed,
            expected_kw=projection, difference_kw=delta,
            difference_percent=100 * delta / projection if projection > 0 else None,
            kind='higher_than_expected' if delta > 0 else 'lower_than_expected',
            anomaly_score=float(scores[index])))
    events.sort(key=lambda row:row['anomaly_score'], reverse=True)
    target = series.index.max() + pd.Timedelta(hours=1)
    reference = series[(series.index >= target - pd.Timedelta(days=28)) & (series.index.hour == target.hour)].dropna()
    forecast_reference = None
    if len(reference) >= 7:
        forecast_reference = dict(timestamp=target.isoformat(), reference_hours=len(reference),
            low_kw=float(reference.quantile(.05)), high_kw=float(reference.quantile(.95)),
            description='Observed 5th–95th percentile for this local clock hour over the previous 28 days; not a prediction interval.')
    return dict(status='available', model='Isolation Forest', expectation_model='Random Forest fitted to earlier uploaded readings',
        fitted_through=fit.index[-1].isoformat(), threshold_calibrated_through=calibration.index[-1].isoformat(),
        evaluated_from=recent.index[0].isoformat(), evaluated_to=recent.index[-1].isoformat(),
        training_rows=len(train), detector_fit_rows=len(fit), calibration_rows=len(calibration), evaluated_hours=len(recent),
        flagged_hours=len(events), events=events[:20], displayed_events=min(len(events), 20),
        score_threshold=threshold, forecast_reference=forecast_reference,
        limitation='Exploratory flags without labeled faults; precision and recall are unknown. Weather, equipment and schedules can cause legitimate deviations. Missing hours are excluded. Scores are not probabilities. Earlier model fitting and threshold calibration precede the evaluated readings.')


def forecast_watch(anomalies, predicted_kw):
    reference = anomalies.get('forecast_reference') if anomalies else None
    if not reference:
        return dict(status='unavailable', reason='Not enough comparable recent clock-hour readings.')
    direction = 'above' if predicted_kw > reference['high_kw'] else 'below' if predicted_kw < reference['low_kw'] else 'within'
    return dict(status='available', relation=direction, **reference,
        note='This compares a forecast with recent observed usage; it is not an observed anomaly or evidence of a fault.')
