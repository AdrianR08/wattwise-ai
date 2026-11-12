# Predicting the change from the latest reading

One shared gradient-boosted model predicts `target - lag_1h`. Final power is
`max(0, lag_1h + predicted_change)`. The absolute-error training objective targets
MAE. No parameter search or new building-type models were added.

## Historical results

Each building receives equal weight in these averages. 353 buildings have usable
rows in the evaluation period; the source contains 368 buildings.

| Approach | Mean building MAE (kW) | Mean building normalized MAE |
|---|---:|---:|
| Latest reading | 7.634 | 7.83% |
| Change model everywhere | 6.835 | 24.18% |
| Validation-selected model/baseline by type | 7.515 | 7.75% |

The change model lowers raw MAE by 10.5% and wins on 301/353 buildings, but large
relative errors on a few low-use buildings make its normalized average worse.
The conservative selection lowers raw MAE by 1.55% and normalized average error
by about 1.06% relative to baseline. This is a modest gain, not a reason to deploy
the learned model everywhere.

Validation retains the latest-reading baseline for offices and services. It uses
the shared change model for food, healthcare, manufacturing, retail, science,
and warehouses. A type qualifies only if both average raw MAE and average
normalized MAE improve on validation. These choices are frozen before this run's
test evaluation. Warehouses have slightly worse normalized error on test despite
passing validation, illustrating that improvement is not guaranteed.

## Scope and reproducibility

- Reuses the original data preparation, features, and chronological split.
  Exact UTC lags stay within each building; calendar features use local time.
- Trains on 298,875 sampled rows before 2017-03-17 14:00 UTC. Validation ends
  at 2017-08-09 11:00 UTC; the remaining observations form the comparison period.
- The comparison period was inspected during the previous experiment. These are
  exploratory historical results, **not a fresh independent test**. New later
  observations are needed to confirm gains before deployment.
- Uses actual prior readings at each forecast step. It does not evaluate a
  multi-hour forecast issued all at once, or buildings without history.
- No application integration or replacement of the existing model was made.

Run `python train_changes.py` in the Python 3.13 environment installed from
`requirements-training.txt`. It writes only this output directory. The saved
`model.joblib` includes the learned change model, category mappings, feature
order, and validation selections. `train_changes.predict` performs lag addition
and clips negative predictions; it does not apply the type-based baseline choice.
For offices/services, the selected approach simply returns `lag_1h` instead.

Saved-model reload and prediction equivalence were checked on 100 training rows;
finite predictions and chronological training boundaries were checked. Full
per-building, per-type, validation, and overall metrics accompany this report.
