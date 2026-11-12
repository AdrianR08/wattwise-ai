# Weather comparison

Added previous-hour air temperature, dew point, and wind speed to the same small
change-prediction model. Training sample, seed, parameters, target, and date splits
match the no-weather experiment. No parameter search was performed.

| Approach | Mean building MAE (kW) | Mean normalized MAE |
|---|---:|---:|
| Latest-reading baseline | 7.634 | 7.83% |
| Change model, no weather | 6.835 | 24.18% |
| Change model, with weather | 6.856 | 31.13% |
| Validation selection, no weather | 7.515 | 7.75% |
| Validation selection, with weather | 7.521 | 7.76% |

Weather did not improve this experiment. Keep the simpler no-weather result;
the existing app and original models were not replaced. The weather model wins
against persistence on 299/353 buildings (301 without weather).

## Weather preparation

Source: `data/bdg2/weather.csv`. Its timestamps are local time, as described in
the [BDG2 publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7591488/).
Each site's metadata timezone converts readings to UTC. Ambiguous/nonexistent
daylight-saving hours are discarded, matching existing meter preparation.
Weather at UTC hour t-1 joins to the power target at t for the same site.
No future weather observations, forward/backward filling, or weather forecasts
are used. Missing weather is handled natively by the tree model. This assumes
the previous hourly observation is available when issuing a forecast; operational
reporting delays would require a longer lag.

Coverage among eligible building rows is 99.76% temperature, 99.74% dew point,
and 99.63% wind speed. Cloud and precipitation fields were omitted because of
substantial missingness. The local-time source and existing meter conversion
carry daylight-saving alignment limitations; this run is not a full timestamp
provenance audit.

## Reproduce and interpret

Run `python train_changes.py --weather` in the training environment. Outputs stay
in this directory; previous no-weather outputs remain in `../change_training`.
The bundle stores the model, exact feature order/category mappings, and
validation selection by type. Use `train_changes.predict` to add predicted
change to the latest power reading and clip at zero. Apply the baseline choice
separately for offices/services. Model reload/prediction equivalence is checked.

Evaluation covers the same 353 buildings and previously inspected historical
period as earlier experiments. These exploratory results do not establish that
weather is unhelpful for other horizons or models. Fresh later observations are
still needed before deployment. Near-zero buildings continue to cause poor
relative errors when the learned model is applied everywhere.
