import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np

df_electricity = pd.read_csv("data/adrenalin.1h.L07.B01.EM01.P.csv")


print(df_electricity.head())
print(df_electricity.columns)
print(df_electricity.shape)

df_electricity.info()

df_electricity["timestamp [UTC]"] = pd.to_datetime(df_electricity["timestamp [UTC]"])

df_electricity.info()

time_diff = df_electricity["timestamp [UTC]"].diff()

print(df_electricity["timestamp [UTC]"].max())
print(df_electricity["timestamp [UTC]"].min())

print((df_electricity["value P [Total active power (kW)]"] == 0).sum())

print(df_electricity["value P [Total active power (kW)]"].max())
print(df_electricity["value P [Total active power (kW)]"].min())
print((df_electricity["value P [Total active power (kW)]"] < 0).sum())

print(df_electricity.head())

first_seven_days = df_electricity[
    (df_electricity["timestamp [UTC]"] >= "2021-11-29") &
    (df_electricity["timestamp [UTC]"] < "2021-12-06 06:00:00+00:00")
]

print(first_seven_days)

x = first_seven_days["timestamp [UTC]"]
y = first_seven_days["value P [Total active power (kW)]"]


plt.plot(x,y)
plt.title("time vs kW")
plt.show()

print(first_seven_days.head())
print(first_seven_days.tail())
print(first_seven_days.shape)


df_electricity["hour"] = df_electricity["timestamp [UTC]"].dt.hour

print(df_electricity.head())

df_electricity = df_electricity.rename(columns={
    "timestamp [UTC]": "timestamp",
    "value P [Total active power (kW)]": "power_kw"
})

average_by_hour = df_electricity.groupby("hour").power_kw.mean()

print(average_by_hour)

max_average_by_hour = average_by_hour.idxmax()
min_average_by_hour = average_by_hour.idxmin()
df_electricity["day_of_week"] = df_electricity["timestamp"].dt.day_name()
df_electricity["weekend"] = df_electricity["day_of_week"].isin(["Saturday", "Sunday"])
average_by_weekend = df_electricity.groupby("weekend").power_kw.mean()
df_electricity["local_timestamp"] = df_electricity["timestamp"].dt.tz_convert(tz="Europe/Oslo")



df_electricity["hour"] = df_electricity["local_timestamp"].dt.hour
df_electricity["day_of_week"] = df_electricity["local_timestamp"].dt.day_name()
df_electricity["weekend"] = df_electricity["day_of_week"].isin(["Saturday", "Sunday"])

average_by_hour = df_electricity.groupby("hour")["power_kw"].mean()

max_average_by_hour = average_by_hour.idxmax()
min_average_by_hour = average_by_hour.idxmin()
df_electricity["day_of_week"] = df_electricity["timestamp"].dt.day_name()
df_electricity["weekend"] = df_electricity["day_of_week"].isin(["Saturday", "Sunday"])
average_by_weekend = df_electricity.groupby("weekend").power_kw.mean()

print(average_by_hour.idxmax())
print(average_by_hour.idxmin())