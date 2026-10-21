# WattWise AI

Predict hourly grocery-store power demand using a trained random forest and observed power readings.

## Setup

The current model and dependency snapshot were verified with Python 3.14.6.
From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The example prints approximately `43.441628311492515` kW. Runtime dependencies are pinned in `requirements.txt`; the notebook and development environment are in `requirements-dev.txt`:

```sh
python -m pip install -r requirements-dev.txt
```

## Prediction inputs

Call `src.predictor.predict_power(hour, month, day_of_week, lag_1h, lag_24h)`.

- `hour`: integer 0–23 for the target hour in Europe/Oslo time.
- `month`: integer 1–12 for that target hour.
- `day_of_week`: integer 0–6, Monday = 0 and Sunday = 6.
- `lag_1h`: observed power in kW one elapsed hour before the target.
- `lag_24h`: observed power in kW 24 elapsed hours before the target.

Lag readings must be finite, non-negative numbers. Booleans are rejected for all inputs. The function returns a Python float in kW. Calendar inputs describe the hour being predicted; the function does not advance the hour. Forecasting several hours ahead requires supplying appropriate lags for each target hour.

## Project structure

- `src/predictor.py`: model loading and validated prediction function.
- `main.py`: runnable example.
- `models/random_forest.joblib`: trained 100-tree random forest, approximately 66 MB.
- `data/`: source CSV and analysis/training notebook.
- `artifacts/`: analysis graphs.
- `tests/`: automated prediction and validation checks.

The model is kept in regular Git for this snapshot. Repeated retraining can grow repository history; consider Git LFS if model versions become frequent. Load only trusted joblib model files.

## Regenerate the model

Install development dependencies, open `data/wattwise_grocery_analysis.ipynb` in a notebook editor, and select the `.venv` kernel. Set its working directory to the repository root or `data/`, then run every cell in order. The notebook resolves the dataset and model paths from either location, trains on the first 80% of observations, evaluates the remaining chronological 20%, and exports `models/random_forest.joblib`.

The notebook uses the same prediction implementation as the application and checks that the exported model reproduces its in-memory prediction. Regeneration overwrites the saved model. Commit corresponding dependency changes when changing the training environment.

## Tests

```sh
python -B -m unittest discover -s tests -v
```

Tests cover the saved model, known example, calendar boundaries, zero lags, invalid inputs, and running the example from a different working directory. Notebook error examples catch and check expected validation failures, so they do not interrupt a full run.
