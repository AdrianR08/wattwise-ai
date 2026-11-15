# Training and evaluation

Run commands from the project root. Data is in `data/bdg2/processed/`; historical weather is in `data/bdg2/weather.csv`.

| Command | Purpose |
|---|---|
| `python -m experiments.train_hourly` | Train consumption-only hourly models |
| `python -m experiments.compare_weather` | Compare hourly models with and without weather |
| `python -m experiments.compare_monthly_weather` | Monthly weather validation and test comparison |
| `python -m experiments.rolling_weather` | Four model families, with/without weather, across six dates and five customer folds |
| `python -m experiments.train_monthly_model` | Refit the original active monthly Random Forest |

Reports live in `docs/reports/`; generated metrics and predictions live in ignored `artifacts/` subfolders. Training commands can overwrite their corresponding model bundles.

Earlier experiments remain for reproducibility: `train_buildings`, `train_changes`, `compare_monthly` and `rolling_monthly`. Newer scripts import shared helpers from some of these files; they are not unused duplicates.

Results are exploratory historical evaluations. See the reports for coverage, date/customer separation and prepared-data limitations.
