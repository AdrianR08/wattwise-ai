import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="WattWise AI",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ WattWise: Energy Consumption Analysis")

st.write(
    "Welcome to WattWise! This application helps you analyze and visualize your "
    "energy consumption data. Upload your energy usage files, and let's get started!"
)

st.divider()

with st.sidebar:
    st.subheader("Electricity Settings")

    electricity_rate = st.number_input(
        "Enter your electricity rate ($/kWh):",
        min_value=0.0,
        value=0.15,
        step=0.01
    )

    st.write(f"Your electricity rate is: ${electricity_rate:.2f}/kWh")

    energy_consumed = st.number_input(
        "How many kWh of energy did you consume this month?",
        min_value=0.0,
        value=100.0,
        step=1.0
    )

    energy_cost = energy_consumed * electricity_rate

    st.write(f"Your estimated electricity cost this month is: ${energy_cost:.2f}")

st.subheader("Electricity Data Analysis")

uploaded_file = st.file_uploader(
    "Upload your electricity consumption CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.write("Here is a preview of your electricity dataset:")

    st.dataframe(df.head())

    df["timestamp [UTC]"] = pd.to_datetime(df["timestamp [UTC]"])

    df = df.rename(columns={
        "timestamp [UTC]": "Timestamp",
        "value P [Total active power (kW)]": "Power (kW)"
    })

    average_power = df["Power (kW)"].mean()

    peak_power = df["Power (kW)"].max()

    seven_day_energy = df.head(168)["Power (kW)"].sum()

    seven_day_cost = seven_day_energy * electricity_rate

    st.subheader("Energy Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Total Energy Used (First 7 Days)",
            value=f"{seven_day_energy:,.2f} kWh"
        )

    with col2:
        st.metric(
            label="Estimated Cost (First 7 Days)",
            value=f"${seven_day_cost:,.2f}"
        )

    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            label="Average Power Demand (Full Dataset)",
            value=f"{average_power:,.2f} kW"
        )

    with col4:
        st.metric(
            label="Peak Power Demand (Full Dataset)",
            value=f"{peak_power:,.2f} kW"
        )

    st.divider()

    st.subheader("Electricity Demand Over Seven Days")

    st.line_chart(
        data=df.head(168),
        x="Timestamp",
        y="Power (kW)"
    )

else:
    st.info("Upload an electricity CSV file to view your energy analysis.")