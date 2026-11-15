import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from experiments.train_buildings import ROOT, load_data

FEATURES = ['hour', 'month', 'weekday', 'lag_1h', 'lag_24h', 'lag_168h']
OUT = ROOT / 'artifacts/hourly_training'


def score(frame, prediction):
    errors = pd.DataFrame({'building': frame.building_id.to_numpy(),
                           'error': np.abs(frame.target.to_numpy() - prediction)})
    return dict(mae_kw=float(mean_absolute_error(frame.target, prediction)),
                r2=float(r2_score(frame.target, prediction)),
                mean_building_mae_kw=float(errors.groupby('building').error.mean().mean()))


def make_candidates():
    return {
        'HistGradientBoosting': HistGradientBoostingRegressor(loss='absolute_error',
            max_iter=100, max_leaf_nodes=15, l2_regularization=1., early_stopping=False, random_state=42),
        'ExtraTrees': ExtraTreesRegressor(n_estimators=60, max_depth=16, min_samples_leaf=10,
                                         n_jobs=4, random_state=42),
        'RandomForest': RandomForestRegressor(n_estimators=60, max_depth=16, min_samples_leaf=10,
                                             n_jobs=4, random_state=42),
        'Ridge': make_pipeline(StandardScaler(), Ridge(alpha=10.)),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data, audit, types, sites = load_data()
    dates = data.timestamp.drop_duplicates().sort_values()
    val_start, test_start = dates.iloc[int(len(dates) * .6)], dates.iloc[int(len(dates) * .8)]
    train = data[data.timestamp < val_start]
    sample = pd.concat([g.sample(min(len(g), 800), random_state=42)
                        for _, g in train.groupby('building_id', sort=True)])
    validation = data[(data.timestamp >= val_start) & (data.timestamp < test_start)]
    test = data[data.timestamp >= test_start]
    candidates = make_candidates()
    print(f'Training on {sample.building_id.nunique()} buildings, {len(sample):,} sampled hours.', flush=True)
    results = []
    for name, model in candidates.items():
        print(name, flush=True)
        model.fit(sample[FEATURES], sample.target - sample.lag_1h)
        for split, frame in [('validation', validation), ('test', test)]:
            prediction = np.maximum(0, frame.lag_1h.to_numpy() + model.predict(frame[FEATURES]))
            results.append(dict(model=name, split=split, **score(frame, prediction)))
    for split, frame in [('validation', validation), ('test', test)]:
        results.append(dict(model='Latest reading baseline', split=split,
                            **score(frame, frame.lag_1h.to_numpy())))
    report = pd.DataFrame(results)
    selected = report[(report.split == 'validation') & (report.model != 'Latest reading baseline')].sort_values('mean_building_mae_kw').iloc[0].model
    metadata = dict(model_name=selected, buildings=int(sample.building_id.nunique()),
        building_types=types, training_rows=len(sample), features=FEATURES,
        validation_start=str(val_start), test_start=str(test_start),
        selection='Lowest equal-building validation MAE among regression models',
        evaluation='Exploratory historical split, already inspected; not unseen-building validation',
        prediction='max(0, lag_1h + predicted_change)', weather=False)
    bundle = dict(model=candidates[selected], metadata=metadata)
    destination = ROOT / 'models/hourly_buildings.joblib'
    joblib.dump(bundle, destination, compress=3)
    check = sample.iloc[:20][FEATURES]
    np.testing.assert_allclose(joblib.load(destination)['model'].predict(check), candidates[selected].predict(check))
    report.to_csv(OUT / 'metrics.csv', index=False)
    (OUT / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    audit.to_csv(OUT / 'data_audit.csv', index=False)
    print(report.to_string(index=False), flush=True)
    print(f'Selected {selected}; saved {destination}', flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
