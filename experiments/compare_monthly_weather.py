import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from threadpoolctl import threadpool_limits

from experiments.compare_monthly import examples, held_out
from experiments.train_buildings import ROOT
from src.monthly_model import FEATURES
from src.monthly_weather import WEATHER_FEATURES, temperature_summary
from src.weather import site_weather

OUT = ROOT / 'artifacts/monthly_weather'


def weather_examples():
    data = examples()
    meta = pd.read_csv(ROOT / 'data/bdg2/processed/buildings_info.csv').set_index('building_id')
    summaries = {}
    for site, group in meta.groupby('site_id'):
        weather = site_weather(site).airTemperature.tz_convert(group.timezone.iloc[0])
        for month, values in weather.groupby(weather.index.strftime('%Y-%m')):
            summaries[site, month] = temperature_summary(values)
    rows = []
    for row in data.itertuples():
        site = meta.loc[row.building_id, 'site_id']
        target = pd.Period(row.month, freq='M')
        values = []
        for lag in (1, 12):
            values.extend(summaries.get((site, str(target - lag)), [np.nan] * 3))
        rows.append(values)
    data[WEATHER_FEATURES] = rows
    data = data.dropna(subset=WEATHER_FEATURES)
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = weather_examples()
    holdout = data.building_id.map(held_out)
    train = data[~holdout & (data.month <= '2017-06')]
    validation = data[holdout & data.month.between('2017-07', '2017-09')]
    test = data[holdout & (data.month >= '2017-10')]
    assert not set(train.building_id) & set(test.building_id)
    assert train.month.max() < validation.month.min() < test.month.min()
    models, results = {}, []
    def evaluate(frame, prediction, name, split):
        error = np.abs(frame.target_kwh.to_numpy() - prediction)
        grouped = pd.DataFrame(dict(building=frame.building_id.to_numpy(), error=error))
        return dict(model=name, split=split, mae_kwh=float(mean_absolute_error(frame.target_kwh, prediction)),
                    r2=float(r2_score(frame.target_kwh, prediction)), mean_building_mae_kwh=float(grouped.groupby('building').error.mean().mean()))
    for weather in (False, True):
        features = FEATURES + (WEATHER_FEATURES if weather else [])
        for name, constructor in [('Random Forest', RandomForestRegressor), ('Extra Trees', ExtraTreesRegressor)]:
            label = name + (' + weather' if weather else '')
            model = constructor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=4)
            model.fit(train[features], train.target_rate / train.scale)
            models[label] = (model, features)
            prediction = np.maximum(0, model.predict(validation[features])) * validation.scale * validation.hours
            results.append(evaluate(validation, prediction, label, 'validation'))
    results.append(evaluate(validation, validation.last_month, 'Last month baseline', 'validation'))
    winner = min(results, key=lambda row: row['mean_building_mae_kwh'])['model']
    for label, (model, features) in models.items():
        prediction = np.maximum(0, model.predict(test[features])) * test.scale * test.hours
        results.append(evaluate(test, prediction, label, 'test'))
    results.append(evaluate(test, test.last_month, 'Last month baseline', 'test'))
    report = pd.DataFrame(results)
    report.to_csv(OUT / 'metrics.csv', index=False)
    weather_winner = min((r for r in results if r['split'] == 'validation' and '+ weather' in r['model']), key=lambda r:r['mean_building_mae_kwh'])['model']
    model, features = models[weather_winner]
    bundle = dict(model=model, features=features, model_name=weather_winner,
        selected_on_validation=winner == weather_winner,
        validation_note='Weather model selected only if its equal-building validation MAE beats both consumption models and last-month baseline. Exploratory historical held-out-building comparison.')
    joblib.dump(bundle, ROOT / 'models/monthly_weather.joblib', compress=3)
    metadata = dict(selected=winner, weather_enabled=bundle['selected_on_validation'], training_rows=len(train),
        training_buildings=train.building_id.nunique(), validation_rows=len(validation), test_rows=len(test),
        weather_inputs='Previous month and same month last year only. No target-month actual weather.',
        caveat='Prepared meter data may contain interpolated values. Historical data previously explored. Seasonal proxy, not a future weather forecast.')
    (OUT / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(report.to_string(index=False), flush=True)
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
