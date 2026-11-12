import json

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestRegressor

from experiments.compare_monthly import examples
from src.monthly_model import FEATURES, MODEL_PATH, make_features


def main():
    print('Preparing twelve-month training examples...', flush=True)
    data = examples()
    model = RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=1)
    model.fit(data[FEATURES], data.target_rate/data.scale)
    bundle = dict(model=model, features=FEATURES, sklearn_version=sklearn.__version__)
    joblib.dump(bundle, MODEL_PATH, compress=3)
    loaded = joblib.load(MODEL_PATH)['model']
    np.testing.assert_allclose(model.predict(data[FEATURES].iloc[:20]), loaded.predict(data[FEATURES].iloc[:20]))
    details = dict(model='RandomForestRegressor', trees=150, seed=42,
        sklearn_version=sklearn.__version__, training_examples=len(data),
        training_buildings=int(data.building_id.nunique()),
        first_target_month=data.month.min(), last_target_month=data.month.max(),
        target='Next-month mean hourly power normalized by preceding twelve-month mean (floor 1 kW)',
        training_data='BDG2 non-residential buildings; monthly coverage at least 95%',
        validation='See experiments/rolling_results.md. Model did not consistently beat last-month baseline.',
        deployment='Refit on all eligible historical examples; refit predictions are not new validation results.')
    MODEL_PATH.with_suffix('.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    print(json.dumps(details, indent=2), flush=True)


if __name__ == '__main__':
    main()
