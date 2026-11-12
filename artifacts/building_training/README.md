# Building forecasting: initial comparison

Trained one shared gradient-boosted tree model and eight building-type models.
Prepared 5,903,515 usable hourly observations from 368 building files. All buildings
contribute training data; training is capped at approximately 300,000 rows for the
shared model and 100,000 per type to keep this first experiment modest.
The final evaluation window contains 353 buildings with eligible target/lag rows;
15 buildings do not have eligible rows in that window.

## Results

Mean of each building's absolute prediction error on the final date window:

| Approach | Average building MAE (kW) |
|---|---:|
| Same hour last week | 19.01 |
| Shared model | 8.37 |
| Separate models by type | 8.02 |
| Latest observed reading | 7.63 |
| Choice per type using validation | 7.47 |

The selected approach improves raw MAE by only about 2.1% over the latest-reading
baseline. Its average normalized error is worse (10.83% versus 7.83%). Near-zero
consumption makes normalized errors particularly large for some learned models.
Do not replace the application's current model based on this experiment.

Validation selected type models for food, manufacturing, services, and science;
it selected the latest-reading baseline for healthcare, offices, retail, and
warehouses. These are experimental choices, not guarantees of future gains.

## Method and limits

- Forecast the next hourly power reading (kW), using observed history. This is
  rolling one-hour forecasting, not a 24-hour forecast made all at once.
- Calendar features use each building's timezone. Lags use elapsed UTC hours
  from that same building at 1, 24, and 168 hours before the target.
- Missing hours remain missing. Negative/non-finite readings are excluded;
  zero readings are retained. Duplicate timestamps keep the first reading.
  Rows without all required lag readings are excluded. See `data_audit.csv`.
- Training uses the first 60% of unique timestamps; validation starts at
  2017-03-17 14:00 UTC; evaluation starts at 2017-08-09 11:00 UTC.
- Model choices use average per-building normalized MAE on validation. Reported
  raw MAE and normalized MAE answer different questions, so both are retained.
- The latest-reading baseline was added after inspecting the first experiment.
  Treat these results as exploratory; confirm choices on a fresh evaluation
  window before deployment. No parameter search was performed.
- Models are saved as trained on the training window, without refitting on later
  dates. This evaluates existing buildings with history, not unseen buildings.
- Weather was omitted from this small first run. The main remaining issue is
  poor performance on low-use or changed-operation buildings.

## Files and rerun

`models.joblib` contains the shared model, models by type, category mappings,
feature order, and validation selections. A baseline selection means return the
corresponding observed lag; it is not a learned model. Load with the separate
training environment, not the app's existing dependency environment.

From the repository root, create a Python 3.13 environment and install
`requirements-training.txt`, then run `python train_buildings.py`. Rerunning
overwrites only the files in this output folder. Existing application code and
`models/random_forest.joblib` are unchanged.

`test_per_building.csv`, `test_by_type.csv`, and `test_overall.csv` contain
evaluation results; `validation_per_building.csv` contains selection evidence;
`run.json` records split dates, sample sizes, and selected approaches.
