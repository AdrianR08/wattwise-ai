# Rolling next-month evaluation

Recommendation: retain the last-month baseline as the default. Neither learned
model consistently improves both raw error and typical relative error.

| Method | Mean building MAE (kWh/month) | Median building WAPE |
|---|---:|---:|
| Last-month baseline | 10,916 | 7.93% |
| Extra Trees | 11,305 | 7.20% |
| Random forest | 11,366 | 7.30% |

There are 1,339 forecasts for 244 eligible buildings across July–December 2017.
Each month retrains on earlier target dates using five customer folds. The model
predicting a customer never trains on that customer's target records. Historical
inputs remain the customer's preceding twelve observed months. Hyperparameters
are unchanged from the initial comparison.

The predefined consistency check requires improvement on both mean building MAE
and median building WAPE in at least four of six months. Both models win only
one month (November). Extra Trees lowers MAE for 141/244 buildings; random forest
for 137/244. Gains are therefore uneven rather than absent.

Random forest improves aggregate raw and relative error for retail (10 buildings)
and manufacturing (8 buildings). These small exploratory subgroups do not establish
a stable selection policy. Offices (191 buildings) still favor the baseline in
raw error. The low-use subgroup has only two buildings/eight forecasts and strongly
favors baseline; there is insufficient coverage to generalize this result.

Targets are estimated kWh from months with at least 95% hourly coverage; all twelve
history months must qualify. WAPE is sum absolute errors divided by sum actual
consumption, with a 1 kWh denominator floor. Coverage filters exclude many source
buildings and can vary by month. Buildings may share sites; sites are not held out.
These data have already been explored, so this is a historical backtest rather than
independent prospective validation. No app model was replaced.

Run `python -m experiments.rolling_monthly`. Detailed predictions, monthly/type/
usage/building scores, fold counts, and checks stay in ignored
`artifacts/rolling_monthly/`. Tests verify customer/time separation and that changing
a future target cannot change its history features.
