# Forecasting experiments

From the repository root, install `experiments/requirements.txt` in a Python 3.13
environment, then run:

```sh
python -m experiments.train_buildings
python -m experiments.train_changes
python -m experiments.train_changes --weather
```

Generated models and reports stay in ignored `artifacts/` subfolders.
Each script runs independently with the tracked building CSVs.

Initial historical mean building errors: latest-reading baseline 7.63 kW,
shared model 8.37 kW, models by type 8.02 kW, change model 6.83 kW,
change model with weather 6.86 kW. Low-use buildings remain problematic.
The comparison period has already been inspected; new data is needed for an
independent evaluation. These experiments do not replace the application model.
