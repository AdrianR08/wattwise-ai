# WattWise AI

## Dashboard

Install `requirements.txt`, then run `streamlit run app.py`.
The dashboard calls the CSV-analysis backend directly and displays consumption,
data quality, unusual days, and the next-month random forest forecast. Uploads are
processed in memory; this integration does not save them. Ask WattWise remains
powered by your PC's Ollama model when the connection is configured.

### Local AI

Ollama must be running with `qwen3:4b` installed. Run `start_ai.ps1` on the PC
to start the authenticated bridge and temporary Cloudflare connection. The setup
uses `.venv/Scripts/python.exe` and `.local/cloudflared.exe` installed on this PC.
Copy `.local/streamlit-cloud-secrets.toml` into the live app's **Settings → Secrets**.
Do not commit that file or share its access key. No per-token API service is used.
Keep the PC awake; restarting the tunnel changes its URL and requires updating
the website settings. The tunnel is for demos, not a permanent production setup.
Questions and analysis summaries pass through Cloudflare to this PC. Raw CSV files
are not sent to the model. Local dashboard use connects directly to the bridge.

Predict hourly grocery-store power demand using a trained random forest and observed power readings.

## Customer CSV analysis

`python analyze_consumption.py customer.csv --unit kWh --timezone Europe/Oslo --output analysis.json`

Accepts hourly interval kWh or hourly average kW (`--unit kW`), not cumulative
meter readings. The first two columns default to timestamp and consumption;
override with `--timestamp-column` and `--value-column`. Uses the latest 12 months
and returns data quality, monthly totals, high/low hours, and unusual-day flags.
Incomplete totals are marked. Output includes a next-month ML forecast when
12 consecutive months have at least 95% hourly coverage and the upload ends at a
calendar-month boundary. Otherwise it gives a reason the forecast is unavailable.
The trained random forest uses twelve monthly consumption averages and the target
month. The last-month baseline is shown separately for comparison; random forest
did not consistently outperform it in historical testing. No calibrated uncertainty
interval is available. Qwen explains the results; it does not generate forecasts.
The deployed model is `models/monthly_random_forest.joblib`; its training details
are in the adjacent JSON file. Rebuild with `python -m experiments.train_monthly_model`
using `requirements.txt`. Its training buildings are non-residential; performance
on other customer populations is not established.

Experimental training scripts and their separate dependencies are in `experiments/`.

## Setup

The current model and dependency snapshot were verified with Python 3.14.6.
From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-predictor.txt
python main.py
```

The example prints approximately `43.441628311492515` kW. Legacy model dependencies are pinned in `requirements-predictor.txt`; use a separate environment from the dashboard. The notebook and development environment are in `requirements-dev.txt`:

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
