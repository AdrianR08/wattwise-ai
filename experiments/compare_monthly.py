"""Compare next-month forecasts made from twelve prior calendar months."""
import hashlib
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from experiments.train_buildings import DATA, ROOT
from src.monthly_model import FEATURES, make_features

OUT = ROOT / 'artifacts/monthly_comparison'


def examples():
    meta = pd.read_csv(DATA / 'buildings_info.csv').set_index('building_id')
    rows = []
    for building, info in meta.iterrows():
        raw = pd.read_csv(DATA / f'{building}.csv')
        times = pd.to_datetime(raw.iloc[:, 0], utc=True, errors='coerce')
        values = pd.to_numeric(raw.iloc[:, 1], errors='coerce')
        s = pd.Series(values.to_numpy(), index=times)
        s = s[s.index.notna() & ~s.index.duplicated()].sort_index()
        s = s.where(np.isfinite(s) & (s >= 0)).tz_convert(info.timezone)
        months = {}
        for label, group in s.groupby(s.index.strftime('%Y-%m')):
            start = pd.Timestamp(label + '-01', tz=info.timezone)
            hours = len(pd.date_range(start, start + pd.DateOffset(months=1), freq='h', inclusive='left'))
            coverage = group.count() / hours
            if coverage >= .95:
                months[pd.Period(label, freq='M')] = (float(group.mean()), hours, coverage)
        for period, (target_rate, hours, coverage) in sorted(months.items()):
            history = [months.get(period - lag) for lag in range(1, 13)]
            if any(item is None for item in history):
                continue
            rates = np.array([item[0] for item in history])
            scale = max(float(rates.mean()), 1.)
            row = dict(building_id=building, building_type=info.primaryspaceusage,
                       month=str(period), target_kwh=target_rate * hours,
                       target_rate=target_rate, hours=hours, scale=scale,
                       coverage=coverage, last_month=rates[0] * hours,
                       seasonal=rates[-1] * hours, annual_average=rates.mean() * hours)
            row.update(make_features(rates, period.month)[0].iloc[0].to_dict())
            rows.append(row)
    return pd.DataFrame(rows)


def held_out(building):
    return int(hashlib.sha256(building.encode()).hexdigest()[:8], 16) % 5 == 0


def evaluate(frame, models):
    rows = []
    predictions = {name: frame[name].to_numpy() for name in ['last_month', 'seasonal', 'annual_average']}
    for name, model in models.items():
        predictions[name] = np.maximum(0, model.predict(frame[FEATURES])) * frame.scale * frame.hours
    for name, pred in predictions.items():
        for (_, r), value in zip(frame.iterrows(), pred):
            rows.append(dict(building_id=r.building_id, building_type=r.building_type,
                month=r.month, model=name, actual_kwh=r.target_kwh, predicted_kwh=float(value),
                absolute_error_kwh=abs(r.target_kwh-float(value))))
    return pd.DataFrame(rows)


def summarize(results):
    rows = []
    for name, g in results.groupby('model'):
        per_building = g.groupby('building_id').agg(error=('absolute_error_kwh', 'sum'),
            actual=('actual_kwh', 'sum'), mae=('absolute_error_kwh', 'mean'))
        rows.append(dict(model=name, buildings=len(per_building), forecasts=len(g),
            mean_building_mae_kwh=float(per_building.mae.mean()),
            median_building_wape=float((per_building.error / per_building.actual.clip(lower=1)).median()),
            portfolio_wape=float(g.absolute_error_kwh.sum()/max(g.actual_kwh.sum(), 1))))
    return pd.DataFrame(rows).set_index('model')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('Preparing twelve-month histories...', flush=True)
    data = examples()
    customer_holdout = data.building_id.map(held_out)
    train = data[(~customer_holdout) & (data.month <= '2017-06')]
    validation = data[customer_holdout & data.month.between('2017-07', '2017-09')]
    test = data[customer_holdout & (data.month >= '2017-10')]
    assert not train.empty and not validation.empty and not test.empty
    assert not set(train.building_id) & set(test.building_id)
    assert train.month.max() < validation.month.min() <= validation.month.max() < test.month.min()
    models = {
        'ridge': make_pipeline(SimpleImputer(), StandardScaler(), Ridge(alpha=10)),
        'random_forest': RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=4),
        'extra_trees': ExtraTreesRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=4),
        'gradient_boosting': HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=7,
            min_samples_leaf=15, l2_regularization=1, early_stopping=False, random_state=42),
    }
    print(f'Training four models on {len(train)} examples from {train.building_id.nunique()} buildings...', flush=True)
    for name, model in models.items():
        model.fit(train[FEATURES], train.target_rate/train.scale)
    validation_results = evaluate(validation, models)
    validation_scores = summarize(validation_results)
    winner = validation_scores.median_building_wape.idxmin()
    test_results = evaluate(test, models)
    test_scores = summarize(test_results)
    for name, result in [('validation_predictions', validation_results), ('test_predictions', test_results),
                         ('validation_scores', validation_scores), ('test_scores', test_scores)]:
        result.to_csv(OUT / f'{name}.csv', index=name.endswith('scores'))
    joblib.dump(dict(models=models, selected_on_validation=winner, features=FEATURES,
                     scale='max(mean twelve monthly mean hourly kW, 1)',
                     prediction='max(0, predicted rate ratio) * scale * next month hours'),
                OUT / 'models.joblib', compress=3)
    loaded = joblib.load(OUT / 'models.joblib')
    for name in models:
        np.testing.assert_allclose(models[name].predict(test[FEATURES].iloc[:10]),
                                   loaded['models'][name].predict(test[FEATURES].iloc[:10]))
    details = dict(training_examples=len(train), training_buildings=train.building_id.nunique(),
        validation_examples=len(validation), test_examples=len(test),
        test_buildings=test.building_id.nunique(), selected_on_validation=winner,
        training_end=train.month.max(), validation_start=validation.month.min(),
        validation_end=validation.month.max(), test_start=test.month.min(), test_end=test.month.max(),
        minimum_month_coverage=.95,
        target='Monthly kWh estimated from observed mean hourly kW times calendar hours',
        evaluation='Rolling monthly forecasts; each uses the preceding 12 observed months; held-out buildings',
        caveat='Historical data explored in earlier hourly experiments; not independent prospective validation')
    (OUT / 'run.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    print(f'Selected on validation: {winner}', flush=True)
    print(test_scores.to_string(), flush=True)
    print('Saved models reload verified.', flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
