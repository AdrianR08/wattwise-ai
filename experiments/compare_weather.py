import json

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits

from experiments.train_buildings import ROOT, load_data
from experiments.train_changes import add_weather
from experiments.train_hourly import FEATURES, make_candidates, score

OUT = ROOT / 'artifacts/hourly_weather'


def predict(model, frame, features):
    return np.maximum(0, frame.lag_1h.to_numpy() + model.predict(frame[features]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data, audit, types, sites = load_data()
    data, weather_features, coverage = add_weather(data, sites)
    dates = data.timestamp.drop_duplicates().sort_values()
    val_start, test_start = dates.iloc[int(len(dates) * .6)], dates.iloc[int(len(dates) * .8)]
    train = data[data.timestamp < val_start]
    sample = pd.concat([g.sample(min(len(g), 800), random_state=42)
                        for _, g in train.groupby('building_id', sort=True)])
    validation = data[(data.timestamp >= val_start) & (data.timestamp < test_start)]
    test = data[data.timestamp >= test_start]
    models, results = {}, []
    for weather in (False, True):
        features = FEATURES + (weather_features if weather else [])
        for name, estimator in make_candidates().items():
            print(f'{name}, weather={weather}', flush=True)
            model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), estimator)
            model.fit(sample[features], sample.target - sample.lag_1h)
            models[name, weather] = model
            results.append(dict(model=name, weather=weather, split='validation',
                **score(validation, predict(model, validation, features))))
    validation_report = pd.DataFrame(results)
    choices = {}
    for weather in (False, True):
        choices[weather] = validation_report[validation_report.weather == weather].sort_values('mean_building_mae_kw').iloc[0].model
    no_weather_score = validation_report[(validation_report.model == choices[False]) & ~validation_report.weather].iloc[0].mean_building_mae_kw
    weather_score = validation_report[(validation_report.model == choices[True]) & validation_report.weather].iloc[0].mean_building_mae_kw
    selected_weather = bool(weather_score < no_weather_score)
    for (name, weather), model in models.items():
        features = FEATURES + (weather_features if weather else [])
        results.append(dict(model=name, weather=weather, split='test',
            **score(test, predict(model, test, features))))
    for split, frame in [('validation', validation), ('test', test)]:
        results.append(dict(model='Latest reading baseline', weather=False, split=split,
            **score(frame, frame.lag_1h.to_numpy())))
    report = pd.DataFrame(results)
    report.to_csv(OUT / 'metrics.csv', index=False)
    for weather in (False, True):
        name = choices[weather]
        features = FEATURES + (weather_features if weather else [])
        metadata = dict(model_name=name, buildings=int(sample.building_id.nunique()),
            building_types=types, training_rows=len(sample), features=features,
            validation_start=str(val_start), test_start=str(test_start), weather=weather,
            weather_selected_on_validation=selected_weather, weather_coverage=coverage,
            evaluation='Exploratory known-building historical split; prepared meter data may include interpolated readings.',
            weather_alignment='Previous elapsed hour only; local weather converted to UTC; ambiguous DST hours discarded; no future filling.')
        bundle = dict(model=models[name, weather], metadata=metadata)
        filename = 'hourly_weather.joblib' if weather else 'hourly_buildings.joblib'
        joblib.dump(bundle, ROOT / 'models' / filename, compress=3)
        if weather:
            (OUT / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    detail = []
    for kind, frame in test.groupby('building_type'):
        for weather in (False, True):
            name = choices[weather]
            features = FEATURES + (weather_features if weather else [])
            detail.append(dict(building_type=kind, model=name, weather=weather,
                **score(frame, predict(models[name, weather], frame, features))))
    pd.DataFrame(detail).to_csv(OUT / 'by_type.csv', index=False)
    print(report.to_string(index=False), flush=True)
    print(f'Weather selected on validation: {selected_weather}', flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
