import json

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from experiments.compare_monthly import summarize
from experiments.compare_monthly_weather import weather_examples
from experiments.rolling_monthly import split
from experiments.train_buildings import ROOT
from src.monthly_model import FEATURES
from src.monthly_weather import WEATHER_FEATURES

OUT = ROOT / 'artifacts/rolling_weather'


def candidates():
    return dict(random_forest=RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=4),
        extra_trees=ExtraTreesRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=4),
        gradient_boosting=HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=7,
            min_samples_leaf=15, l2_regularization=1, early_stopping=False, random_state=42),
        ridge=make_pipeline(StandardScaler(), Ridge(alpha=10)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = weather_examples()
    results, audit = [], []
    for month in pd.period_range('2017-07', '2017-12', freq='M').astype(str):
        print(f'Evaluating {month} across five held-out customer folds...', flush=True)
        for fold in range(5):
            train, test = split(data, month, fold)
            if train.empty or test.empty:
                continue
            predictions = dict(last_month=test.last_month.to_numpy())
            for weather in (False, True):
                features = FEATURES + (WEATHER_FEATURES if weather else [])
                for name, model in candidates().items():
                    model.fit(train[features], train.target_rate / train.scale)
                    label = name + ('_weather' if weather else '')
                    predictions[label] = np.maximum(0, model.predict(test[features])) * test.scale.to_numpy() * test.hours.to_numpy()
            for name, prediction in predictions.items():
                for row, value in zip(test.itertuples(), prediction):
                    results.append(dict(building_id=row.building_id, building_type=row.building_type,
                        month=month, fold=fold, model=name, actual_kwh=row.target_kwh,
                        predicted_kwh=float(value), absolute_error_kwh=abs(row.target_kwh - float(value))))
            audit.append(dict(month=month, fold=fold, training_rows=len(train), test_rows=len(test),
                latest_training_month=train.month.max(), customer_overlap=len(set(train.building_id) & set(test.building_id))))
    results = pd.DataFrame(results)
    assert not results.duplicated(['building_id', 'month', 'model']).any()
    counts = results.groupby(['building_id', 'month']).model.nunique()
    assert counts.eq(9).all()
    overall = summarize(results)
    overall['r2'] = results.groupby('model').apply(lambda g:r2_score(g.actual_kwh, g.predicted_kwh), include_groups=False)
    monthly = pd.concat([summarize(group).assign(month=month) for month, group in results.groupby('month')])
    baseline = monthly.loc['last_month'].set_index('month')
    checks = {}
    for name in overall.index:
        if name == 'last_month':
            continue
        candidate = monthly.loc[name].set_index('month')
        wins = (candidate.mean_building_mae_kwh < baseline.mean_building_mae_kwh) & (candidate.median_building_wape < baseline.median_building_wape)
        checks[name] = dict(months_winning_both_metrics=int(wins.sum()), months=len(wins), passes_four_of_six_rule=bool(wins.sum() >= 4))
    results.to_csv(OUT / 'predictions.csv', index=False)
    overall.to_csv(OUT / 'overall.csv')
    monthly.to_csv(OUT / 'by_month.csv')
    pd.DataFrame(audit).to_csv(OUT / 'folds.csv', index=False)
    details = dict(forecasts=int(len(results) / 9), buildings=results.building_id.nunique(),
        rule='Improve equal-building MAE and median-building WAPE in at least four of six months.',
        checks=checks, raw_meter_files_available=False,
        caveat='Exploratory historical evaluation. Prepared meter files can include interpolation; original raw readings are not available locally. Sites are shared between folds. No untouched prospective test.')
    (OUT / 'run.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    print(overall.to_string(), flush=True)
    print(json.dumps(details, indent=2), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
