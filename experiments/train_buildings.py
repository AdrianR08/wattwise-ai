"""Small, reproducible comparison of shared and building-type hourly models."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/bdg2/processed'
OUT = ROOT / 'artifacts/building_training'
FEATURES = ['hour', 'weekday', 'month', 'sqm', 'type_code', 'site_code',
            'lag_1h', 'lag_24h', 'lag_168h']


def load_data():
    meta = pd.read_csv(DATA / 'buildings_info.csv').set_index('building_id')
    types = sorted(meta.primaryspaceusage.unique())
    sites = sorted(meta.site_id.unique())
    frames, audit = [], []
    for path in sorted(DATA.glob('*.csv')):
        if path.stem == 'buildings_info':
            continue
        info = meta.loc[path.stem]
        raw = pd.read_csv(path)
        times = pd.to_datetime(raw.iloc[:, 0], utc=True, errors='coerce')
        values = pd.to_numeric(raw.iloc[:, 1], errors='coerce')
        valid_time = times.notna()
        s = pd.Series(values[valid_time].to_numpy(), index=times[valid_time]).sort_index()
        duplicates = int(s.index.duplicated().sum())
        s = s[~s.index.duplicated(keep='first')]
        invalid = ~np.isfinite(s) | (s < 0)
        bad_values = int(invalid.sum())
        s[invalid] = np.nan
        full = pd.date_range(s.index.min(), s.index.max(), freq='h')
        missing_hours = len(full.difference(s.index))
        s = s.reindex(full)
        local = s.index.tz_convert(info.timezone)
        f = pd.DataFrame({'timestamp': s.index, 'building_id': path.stem,
                          'building_type': info.primaryspaceusage, 'target': s.to_numpy(),
                          'hour': local.hour, 'weekday': local.dayofweek, 'month': local.month,
                          'sqm': info.sqm, 'type_code': types.index(info.primaryspaceusage),
                          'site_code': sites.index(info.site_id)})
        for lag in (1, 24, 168):
            f[f'lag_{lag}h'] = s.shift(lag).to_numpy()
        f = f.dropna(subset=['target', 'lag_1h', 'lag_24h', 'lag_168h'])
        f[FEATURES + ['target']] = f[FEATURES + ['target']].astype('float32')
        frames.append(f)
        audit.append({'building_id': path.stem, 'input_rows': len(raw),
                      'invalid_timestamps': int((~valid_time).sum()),
                      'duplicate_timestamps': duplicates, 'invalid_readings': bad_values,
                      'missing_hours': missing_hours, 'usable_rows': len(f)})
    return pd.concat(frames, ignore_index=True), pd.DataFrame(audit), types, sites


def fit(frame, limit):
    # Equal allowance per building keeps long records from taking over the sample.
    allowance = max(1, limit // frame.building_id.nunique())
    sample = pd.concat([g.sample(min(len(g), allowance), random_state=42)
                        for _, g in frame.groupby('building_id', sort=True)])
    model = HistGradientBoostingRegressor(max_iter=80, max_leaf_nodes=15,
        l2_regularization=1.0, categorical_features=['type_code', 'site_code'],
        early_stopping=False, random_state=42)
    model.fit(sample[FEATURES], sample.target)
    return model, len(sample)


def evaluate(frame, shared, specialists):
    rows = []
    for building, group in frame.groupby('building_id', sort=True):
        kind = group.building_type.iloc[0]
        y = group.target.to_numpy()
        predictions = {'latest_baseline': group.lag_1h.to_numpy(),
                       'weekly_baseline': group.lag_168h.to_numpy(),
                       'shared': shared.predict(group[FEATURES]),
                       'by_type': specialists[kind].predict(group[FEATURES])}
        for name, pred in predictions.items():
            error = y - pred
            rows.append({'building_id': building, 'building_type': kind, 'model': name,
                         'rows': len(group), 'mae_kw': float(np.abs(error).mean()),
                         'rmse_kw': float(np.sqrt(np.square(error).mean())),
                         'normalized_mae': float(np.abs(error).mean() / y.mean())
                         if y.mean() > 0 else np.nan})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('Preparing building histories...', flush=True)
    data, audit, types, sites = load_data()
    audit.to_csv(OUT / 'data_audit.csv', index=False)
    dates = data.timestamp.drop_duplicates().sort_values()
    validation_start, test_start = dates.iloc[int(len(dates)*.6)], dates.iloc[int(len(dates)*.8)]
    train = data[data.timestamp < validation_start]
    print(f'{len(audit)} buildings; {len(data):,} usable rows. Training...', flush=True)
    shared, shared_rows = fit(train, 300_000)
    specialists, counts = {}, {}
    for kind, group in train.groupby('building_type', sort=True):
        print(f'Training {kind}...', flush=True)
        specialists[kind], counts[kind] = fit(group, 100_000)
    validation = evaluate(data[(data.timestamp >= validation_start) &
                               (data.timestamp < test_start)], shared, specialists)
    validation.to_csv(OUT / 'validation_per_building.csv', index=False)
    # Choose on validation only. Keep test untouched until the choice is frozen.
    scores = validation.groupby(['building_type', 'model']).normalized_mae.mean().unstack()
    choices = scores.idxmin(axis=1).to_dict()
    print('Evaluating final held-out dates...', flush=True)
    test = evaluate(data[data.timestamp >= test_start], shared, specialists)
    test.to_csv(OUT / 'test_per_building.csv', index=False)
    selected = test[test.apply(lambda row: row.model == choices[row.building_type], axis=1)].copy()
    selected['model'] = 'selected_on_validation'
    report = pd.concat([test, selected]).groupby(['building_type', 'model']).agg(
        buildings=('building_id', 'nunique'), mean_building_mae_kw=('mae_kw', 'mean'),
        mean_building_normalized_mae=('normalized_mae', 'mean')).reset_index()
    report.to_csv(OUT / 'test_by_type.csv', index=False)
    overall = pd.concat([test, selected]).groupby('model')[['mae_kw', 'normalized_mae']].mean()
    overall.to_csv(OUT / 'test_overall.csv')
    joblib.dump({'shared': shared, 'by_type': specialists, 'selected_by_type': choices,
                 'features': FEATURES, 'types': types, 'sites': sites}, OUT / 'models.joblib', compress=3)
    details = {'seed': 42, 'forecast': 'one-hour-ahead with observed history',
               'validation_start_utc': str(validation_start), 'test_start_utc': str(test_start),
               'shared_training_rows': shared_rows, 'type_training_rows': counts,
               'selected_by_type': choices, 'usable_rows': len(data), 'buildings': len(audit)}
    (OUT / 'run.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    print(overall.to_string(), flush=True)
    print(f'Saved results to {OUT}', flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
