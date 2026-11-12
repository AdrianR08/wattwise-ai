# Next-month comparison

Four shared models predict the next month's average hourly power from the prior
12 monthly averages, normalized by the customer's history. Multiplying by the
next month's calendar hours gives estimated kWh. No future weather is used.

| Model | Mean building error (kWh/month) | Median building percentage error |
|---|---:|---:|
| Random forest | 10,532 | 5.67% |
| Extra Trees | 11,203 | 4.94% |
| Last-month baseline | 11,271 | 6.46% |
| Gradient boosting | 11,554 | 5.53% |
| Annual-average baseline | 12,857 | 8.19% |
| Ridge regression | 13,697 | 8.04% |
| Same-month-last-year baseline | 14,263 | 9.33% |

Test: 141 monthly forecasts for 47 held-out buildings, October–December 2017.
Training: 955 examples from 183 other buildings, targets through June 2017.
Validation: July–September 2017 on held-out buildings. Selection uses median
per-building WAPE (sum absolute errors / sum actual kWh; denominator floor 1 kWh).
The last-month baseline wins validation, so it remains the selected candidate.
Random forest's test advantage is about 6.6% in average raw error; it is not a
consistent win across validation and test. The app's hourly model is unchanged.

Only months with at least 95% hourly coverage qualify; all 12 history months
must qualify. Monthly totals are coverage-adjusted estimates, not billing totals.
This leaves a limited, filtered sample. Raw kWh errors vary with building size.
Test customers may recur in validation, but never in training. Forecasts roll
forward using actual observations available at each month boundary. The historical
data was explored in prior experiments; fresh later data is still needed.

Run `python -m experiments.compare_monthly`. Saved models and detailed scores
remain in ignored `artifacts/monthly_comparison/`. Reload equivalence, date and
customer separation, and independence of history features from future target
values were checked. These models do not produce calibrated uncertainty ranges.
