# WattWise AI

A Streamlit app for understanding electricity readings, estimating usage costs and explaining forecasts with local Qwen3 through Ollama.

## Run locally on Windows

Install `requirements.txt` in your Python environment. With Ollama running and `qwen3:4b` installed, open two terminals in this folder:

```powershell
.\.venv\Scripts\python.exe -m src.llm_server
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. Upload a CSV, review Electricity Settings, and click Continue. The first two columns must contain timestamps and hourly average kW or interval kWh. Monthly forecasting needs twelve consecutive months with at least 95% coverage, ending at a calendar-month boundary. Cumulative meter readings are not supported.

Weather defaults to Miami for the demo and follows the file's dates. The supplied office sample retains its original matched site. A default location is not evidence that the building is in Miami. See [weather setup](docs/weather-api.md).

## Models

| File or service | Purpose |
|---|---|
| `models/hourly_buildings.joblib` | Next-hour forecast using observed 1-, 24- and 168-hour lags |
| `models/hourly_weather.joblib` | Next-hour forecast with matched previous-hour weather |
| `models/monthly_random_forest.joblib` | Active next-month model |
| `models/monthly_weather.joblib` | Inactive monthly weather candidate; did not win validation |
| Ollama `qwen3:4b` | Explains analysis and calls the prediction tool |

The last-month baseline is a separate comparison. Expanded monthly testing found lower average kWh error for this baseline than for learned models. No calibrated prediction interval is available. Historical results do not establish accuracy on new customers.

## Project layout

| Folder | Contents |
|---|---|
| `src/` | Analysis, forecasting, weather, chat and local AI server |
| `data/bdg2/processed/` | Prepared building CSVs and building metadata |
| `models/` | Trained models |
| `samples/` | Uploadable office example |
| `experiments/` | Training and evaluation scripts |
| `docs/reports/` | Written evaluation results |
| `artifacts/` | Generated predictions, metrics and plots |
| `tests/` | Automated checks |
| `.local/` | Private keys, service logs and backups; not committed |

Historical site weather is `data/bdg2/weather.csv`. Start with the [expanded monthly results](docs/reports/rolling_weather_results.md), [monthly weather results](docs/reports/monthly_weather_results.md), or [hourly weather results](docs/reports/weather_results.md). Reproduction commands are in [experiments/README.md](experiments/README.md).

## Other entry points

`analyze_consumption.py` analyzes a CSV from the command line. `main.py`, `src/predictor.py`, `models/random_forest.joblib` and the grocery notebook preserve the original single-building experiment; they are not the active chat predictor. See [legacy grocery notes](docs/legacy-grocery-setup.md).

`start_ai.ps1` is the earlier hosted-demo launcher and starts a temporary Cloudflare tunnel. Local use does not require it. Keep access keys and secret settings private.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Original grocery-model tests require the legacy pinned dependencies; see the legacy notes.
