"""One modest residual model, compared with the latest-reading baseline."""
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from train_buildings import FEATURES as BASE_FEATURES, ROOT, load_data

FEATURES = BASE_FEATURES.copy()

OUT = ROOT / 'artifacts/change_training'


def add_weather(data, sites):
    meta = pd.read_csv(ROOT / 'data/bdg2/processed/buildings_info.csv')
    weather = pd.read_csv(ROOT / 'data/bdg2/weather.csv')
    columns = ['airTemperature', 'dewTemperature', 'windSpeed']
    frames = []
    for site, info in meta.groupby('site_id'):
        assert info.timezone.nunique() == 1
        w = weather[weather.site_id == site].copy()
        # Source weather.csv is local time, as documented by BDG2. Match the
        # existing meter preparation; discard ambiguous/nonexistent DST hours.
        utc = pd.to_datetime(w.timestamp).dt.tz_localize(
            info.timezone.iloc[0], ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
        w['timestamp'] = utc + pd.Timedelta(hours=1)
        w['site_code'] = np.float32(sites.index(site))
        frames.append(w[['timestamp', 'site_code'] + columns].dropna(subset=['timestamp']))
    weather = pd.concat(frames, ignore_index=True)
    weather[columns] = weather[columns].replace([np.inf, -np.inf], np.nan).astype('float32')
    weather.loc[weather.windSpeed < 0, 'windSpeed'] = np.nan
    weather = weather.rename(columns={c: 'weather_previous_hour_' + c for c in columns})
    joined = data.merge(weather, on=['timestamp', 'site_code'], how='left', validate='many_to_one')
    assert len(joined) == len(data)
    names = ['weather_previous_hour_' + c for c in columns]
    coverage = (1 - joined[names].isna().mean()).to_dict()
    return joined, names, coverage


def predict(model, features):
    return np.maximum(0, features.lag_1h.to_numpy() + model.predict(features[model.feature_names_in_]))


def evaluate(frame, model):
    rows = []
    for building, g in frame.groupby('building_id', sort=True):
        y = g.target.to_numpy()
        for name, pred in [('latest_baseline', g.lag_1h.to_numpy()),
                           ('change_model', predict(model, g))]:
            error = np.abs(y - pred)
            rows.append(dict(building_id=building, building_type=g.building_type.iloc[0],
                             model=name, rows=len(g), mae_kw=float(error.mean()),
                             normalized_mae=float(error.mean()/y.mean()) if y.mean() > 0 else np.nan))
    return pd.DataFrame(rows)


def summary(frame):
    return frame.groupby('model').agg(buildings=('building_id', 'nunique'),
        mae_kw=('mae_kw', 'mean'), normalized_mae=('normalized_mae', 'mean'))


def main(use_weather=False):
    global OUT
    if use_weather:
        OUT = ROOT / 'artifacts/weather_training'
    OUT.mkdir(parents=True, exist_ok=True)
    print('Preparing building histories...', flush=True)
    data, audit, types, sites = load_data()
    coverage = {}
    if use_weather:
        data, names, coverage = add_weather(data, sites)
        FEATURES.extend(names)
        print(f'Weather coverage: {coverage}', flush=True)
    previous = json.loads((ROOT / 'artifacts/building_training/run.json').read_text())
    val_start = pd.Timestamp(previous['validation_start_utc'])
    test_start = pd.Timestamp(previous['test_start_utc'])
    train = data[data.timestamp < val_start]
    allowance = max(1, 300_000 // train.building_id.nunique())
    sample = pd.concat([g.sample(min(len(g), allowance), random_state=42)
                       for _, g in train.groupby('building_id', sort=True)])
    assert sample.timestamp.max() < val_start < test_start
    model = HistGradientBoostingRegressor(loss='absolute_error', max_iter=80,
        max_leaf_nodes=15, l2_regularization=1.0, early_stopping=False,
        categorical_features=['type_code', 'site_code'], random_state=42)
    print(f'Training change model on {len(sample):,} rows...', flush=True)
    model.fit(sample[FEATURES], sample.target - sample.lag_1h)
    validation = evaluate(data[(data.timestamp >= val_start) & (data.timestamp < test_start)], model)
    # Keep the model only for types where both equal-building metrics improve.
    choices = {}
    for kind, g in validation.groupby('building_type'):
        metrics = summary(g)
        improved = ((metrics.loc['change_model', ['mae_kw', 'normalized_mae']] <
                     metrics.loc['latest_baseline', ['mae_kw', 'normalized_mae']]).all())
        choices[kind] = 'change_model' if improved else 'latest_baseline'
    print('Evaluating historical test period...', flush=True)
    test = evaluate(data[data.timestamp >= test_start], model)
    selected = test[test.apply(lambda r: r.model == choices[r.building_type], axis=1)].copy()
    selected['model'] = 'selected_on_validation'
    combined = pd.concat([test, selected])
    validation.to_csv(OUT / 'validation_per_building.csv', index=False)
    combined.to_csv(OUT / 'test_per_building.csv', index=False)
    summary(combined).to_csv(OUT / 'test_overall.csv')
    combined.groupby(['building_type', 'model']).agg(buildings=('building_id', 'nunique'),
        mae_kw=('mae_kw', 'mean'), normalized_mae=('normalized_mae', 'mean')).to_csv(OUT / 'test_by_type.csv')
    pairs = test.pivot(index='building_id', columns='model', values='mae_kw')
    wins = int((pairs.change_model < pairs.latest_baseline).sum())
    details = dict(forecast='one-hour-ahead using observed history', seed=42,
        training_rows=len(sample), source_buildings=len(audit), evaluated_buildings=len(pairs),
        validation_start_utc=str(val_start), test_start_utc=str(test_start),
        selected_by_type=choices, change_model_building_wins=wins,
        test_status='Previously inspected historical period; exploratory, not a fresh test')
    details['weather'] = dict(enabled=use_weather, coverage=coverage,
        alignment='previous elapsed hour; local weather timestamps converted to UTC; no filling')
    (OUT / 'run.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    bundle = dict(model=model, features=FEATURES, types=types, sites=sites,
                  selected_by_type=choices, prediction='max(0, lag_1h + predicted_change)')
    joblib.dump(bundle, OUT / 'model.joblib', compress=3)
    # Verify serialization reproduces the in-memory result, including the lag addition.
    loaded = joblib.load(OUT / 'model.joblib')
    check = sample.iloc[:100]
    np.testing.assert_allclose(predict(loaded['model'], check), predict(model, check))
    assert np.isfinite(predict(model, check)).all()
    print(summary(combined).to_string(), flush=True)
    print(f'Change model wins on {wins}/{len(pairs)} buildings. Saved model reload verified.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weather', action='store_true')
    args = parser.parse_args()
    with threadpool_limits(limits=4):
        main(args.weather)
