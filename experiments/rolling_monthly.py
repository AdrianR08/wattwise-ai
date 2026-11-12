import json

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from threadpoolctl import threadpool_limits

from experiments.compare_monthly import FEATURES, evaluate, examples, summarize
from experiments.train_buildings import ROOT
import hashlib

OUT = ROOT / 'artifacts/rolling_monthly'


def customer_fold(building):
    return int(hashlib.sha256(building.encode()).hexdigest()[:8], 16) % 5


def split(data, month, fold):
    folds = data.building_id.map(customer_fold)
    train = data[(folds != fold) & (data.month < month)]
    test = data[(folds == fold) & (data.month == month)]
    if not train.empty and not test.empty:
        assert train.month.max() < test.month.min()
        assert not set(train.building_id) & set(test.building_id)
    return train, test


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('Preparing monthly histories...', flush=True)
    data = examples()
    results, folds = [], []
    for month in pd.period_range('2017-07', '2017-12', freq='M').astype(str):
        print(f'Evaluating {month} across five customer folds...', flush=True)
        for fold in range(5):
            train, test = split(data, month, fold)
            if train.empty or test.empty:
                continue
            models = dict(random_forest=RandomForestRegressor(n_estimators=150,
                min_samples_leaf=5, random_state=42, n_jobs=4),
                extra_trees=ExtraTreesRegressor(n_estimators=150,
                min_samples_leaf=5, random_state=42, n_jobs=4))
            for model in models.values():
                model.fit(train[FEATURES], train.target_rate / train.scale)
            scored = evaluate(test, models)
            scored = scored[scored.model.isin(['last_month', 'random_forest', 'extra_trees'])]
            usage = test[FEATURES[:12]].mean(axis=1) * test.scale
            groups = dict(zip(test.building_id, np.where(usage < 1, 'below_1kw', 'at_least_1kw')))
            scored['usage_group'] = scored.building_id.map(groups)
            scored['fold'] = fold
            results.append(scored)
            folds.append(dict(month=month, fold=fold, training_rows=len(train),
                              training_buildings=train.building_id.nunique(), test_rows=len(test)))
    results = pd.concat(results, ignore_index=True)
    assert not results.duplicated(['building_id', 'month', 'model']).any()
    overall = summarize(results)
    monthly = pd.concat([summarize(g).assign(month=month) for month, g in results.groupby('month')])
    by_type = pd.concat([summarize(g).assign(building_type=kind)
                        for kind, g in results.groupby('building_type')])
    by_usage = pd.concat([summarize(g).assign(usage_group=kind)
                         for kind, g in results.groupby('usage_group')])
    per_building = results.groupby(['building_id', 'building_type', 'model']).agg(
        forecasts=('month', 'size'), mae_kwh=('absolute_error_kwh', 'mean'),
        error=('absolute_error_kwh', 'sum'), actual=('actual_kwh', 'sum')).reset_index()
    per_building['wape'] = per_building.error / per_building.actual.clip(lower=1)
    checks = {}
    for name in ['random_forest', 'extra_trees']:
        baseline = monthly.loc['last_month'].set_index('month')
        candidate = monthly.loc[name].set_index('month')
        both = ((candidate.mean_building_mae_kwh < baseline.mean_building_mae_kwh) &
                (candidate.median_building_wape < baseline.median_building_wape))
        errors = per_building.pivot(index='building_id', columns='model', values='mae_kwh')
        checks[name] = dict(months_winning_both_metrics=int(both.sum()), months=len(both),
            buildings_with_lower_mae=int((errors[name] < errors.last_month).sum()),
            buildings=len(errors), passes_four_of_six_month_rule=bool(both.sum() >= 4))
    for filename, frame in [('predictions', results), ('overall', overall), ('by_month', monthly),
                            ('by_type', by_type), ('by_usage', by_usage), ('per_building', per_building)]:
        frame.to_csv(OUT / f'{filename}.csv', index=filename in ['overall', 'by_month', 'by_type', 'by_usage'])
    pd.DataFrame(folds).to_csv(OUT / 'folds.csv', index=False)
    (OUT / 'run.json').write_text(json.dumps(dict(checks=checks,
        rule='At least four of six months improve both mean building MAE and median building WAPE',
        evaluation='Five customer folds, expanding training dates before each July-December 2017 origin',
        caveat='Exploratory historical backtest; no prospective data; coverage-adjusted monthly targets'),
        indent=2), encoding='utf-8')
    print(overall.to_string(), flush=True)
    print(json.dumps(checks, indent=2), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
