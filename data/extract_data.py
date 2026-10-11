import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Load the dataset
# -----------------------------

df_electricity = pd.read_csv(
    "data/adrenalin.1h.L07.B01.EM01.P.csv"
)


# -----------------------------
# 2. Inspect the raw data
# -----------------------------

print(df_electricity.head())
print(df_electricity.columns)
print(df_electricity.shape)

df_electricity.info()


# -----------------------------
# 3. Convert timestamp to datetime
# -----------------------------

df_electricity["timestamp [UTC]"] = pd.to_datetime(
    df_electricity["timestamp [UTC]"]
)


# -----------------------------
# 4. Rename columns
# -----------------------------

df_electricity = df_electricity.rename(columns={
    "timestamp [UTC]": "timestamp",
    "value P [Total active power (kW)]": "power_kw"
})


# -----------------------------
# 5. Check data quality
# -----------------------------

print("Start:", df_electricity["timestamp"].min())
print("End:", df_electricity["timestamp"].max())

print("Zero values:", (df_electricity["power_kw"] == 0).sum())
print("Negative values:", (df_electricity["power_kw"] < 0).sum())

print("Minimum power:", df_electricity["power_kw"].min())
print("Maximum power:", df_electricity["power_kw"].max())


# -----------------------------
# 6. Check hourly continuity
# -----------------------------

time_diff = df_electricity["timestamp"].diff()

print(time_diff.value_counts())


# -----------------------------
# 7. Convert UTC to local Norway time
# -----------------------------

df_electricity["local_timestamp"] = (
    df_electricity["timestamp"]
    .dt.tz_convert("Europe/Oslo")
)


# -----------------------------
# 8. Create time features
# -----------------------------

df_electricity["hour"] = (
    df_electricity["local_timestamp"].dt.hour
)

df_electricity["day_of_week"] = (
    df_electricity["local_timestamp"].dt.day_name()
)

df_electricity["weekend"] = (
    df_electricity["day_of_week"]
    .isin(["Saturday", "Sunday"])
)


# -----------------------------
# 9. Analyze average power by hour
# -----------------------------

average_by_hour = (
    df_electricity
    .groupby("hour")["power_kw"]
    .mean()
)

print("Peak hour:", average_by_hour.idxmax())
print("Peak average power:", average_by_hour.max())

print("Lowest hour:", average_by_hour.idxmin())
print("Lowest average power:", average_by_hour.min())


# -----------------------------
# 10. Compare weekday vs weekend
# -----------------------------

average_by_weekend = (
    df_electricity
    .groupby("weekend")["power_kw"]
    .mean()
)

print(average_by_weekend)


# -----------------------------
# 11. Look at first 7 full days
# -----------------------------

first_seven_days = df_electricity[
    (df_electricity["timestamp"] >= "2021-11-29 06:00:00+00:00") &
    (df_electricity["timestamp"] < "2021-12-06 06:00:00+00:00")
]

print(first_seven_days.shape)


# -----------------------------
# 12. Plot first 7 days
# -----------------------------

plt.figure(figsize=(12, 5))

plt.plot(
    first_seven_days["local_timestamp"],
    first_seven_days["power_kw"]
)

plt.title("Grocery Store Power Demand - First 7 Days")
plt.xlabel("Local Time")
plt.ylabel("Power (kW)")

plt.show()