import json
from io import BytesIO

import pandas as pd
import streamlit as st

from src.consumption import analyze_csv


@st.cache_data(ttl=1800, max_entries=8, show_spinner=False)
def analyze_upload(data, unit, timezone):
    return analyze_csv(BytesIO(data), unit=unit, timezone=timezone)


def render_analysis(uploaded_file, *, unit, timezone, electricity_rate, weather_location=None, weather_site=None):
    try:
        uploaded_file.seek(0)
        with st.spinner('Checking consumption patterns…'):
            result = analyze_upload(uploaded_file.getvalue(), unit, timezone)
    except (ValueError, KeyError, TypeError) as error:
        st.error(f'Unable to analyze this file: {error}')
        return
    summary = result['summary']
    energy = summary['observed_kwh']
    cols = st.columns(4)
    cols[0].metric('Observed consumption', f'{energy:,.0f} kWh')
    cols[1].metric('Estimated usage cost', f"${energy * electricity_rate:,.2f}")
    cols[2].metric('Average hourly consumption', f"{summary['average_hourly_kwh']:,.2f} kWh")
    cols[3].metric('Data coverage', f"{result['quality']['coverage_fraction']:.1%}")
    st.caption('Latest 12 months available in the file. Missing readings are excluded from totals. Cost excludes fixed fees and taxes.')
    st.subheader('Monthly consumption')
    months = pd.DataFrame(result['monthly'])
    st.bar_chart(months.set_index('month')[['observed_kwh']])
    if not months.complete.all():
        st.warning('Some months are incomplete. Their totals cover only the available readings.')
    st.subheader('Next-month forecast')
    forecast = result['forecast']
    if forecast['status'] == 'available':
        st.metric(f"Expected consumption · {forecast['month']}", f"{forecast['predicted_kwh']:,.0f} kWh")
        st.caption(f"Estimated usage cost: ${forecast['predicted_kwh'] * electricity_rate:,.2f}. Method used: Last-month baseline.")
        st.caption('Uses last month’s average hourly usage, adjusted for next month’s length. This simple rule had lower average error in historical monthly testing. It does not use weather or predict operational changes. An uncertainty range is not yet available.')
        comparison = forecast.get('random_forest_kwh')
        if comparison is not None:
            with st.expander('Experimental Random Forest comparison'):
                st.metric('Random Forest estimate', f'{comparison:,.0f} kWh')
                st.caption(f'Estimated usage cost: ${comparison * electricity_rate:,.2f}. This trained model uses twelve monthly averages. It is a comparison, not the active monthly estimate.')
        else:
            st.caption('The experimental Random Forest comparison is unavailable. The baseline estimate remains available.')
    else:
        st.info(forecast['reason'])
    st.subheader('Worth a closer look')
    anomalies = result['anomalies']
    st.markdown('**Unusual hourly usage**')
    if anomalies['status'] == 'available':
        st.write(f"Isolation Forest flagged **{anomalies['flagged_hours']} of {anomalies['evaluated_hours']} checked hours** for review.")
        st.caption(f"Checked period: {anomalies['evaluated_from']} to {anomalies['evaluated_to']}. Recent readings are compared with patterns learned from earlier in your file.")
        if anomalies['events']:
            events = pd.DataFrame(anomalies['events'])[['timestamp', 'observed_kw', 'expected_kw', 'difference_kw', 'kind']]
            st.dataframe(events.rename(columns={'observed_kw':'Actual kW', 'expected_kw':'Expected kW', 'difference_kw':'Difference kW', 'kind':'Flag'}), hide_index=True)
            st.caption('Showing up to 20 strongest flags. Check operating hours, meter records and equipment schedules at these times. Flags are not diagnoses, and detection accuracy has not been established with labeled faults.')
        else:
            st.caption('No hours crossed both the anomaly-score and usage-deviation thresholds. This does not rule out a problem.')
        with st.expander('How unusual usage is checked'):
            st.write('A Random Forest estimates expected usage from earlier readings. Isolation Forest looks for unusual differences between the estimates and actual consumption. Earlier data is used for fitting and setting the threshold; the final 15% of usable history is checked separately.')
            st.caption('Weather and schedule changes can create legitimate flags. No labeled faults were available to establish detection accuracy. Existing daily flags below are a separate statistical check.')
    else:
        st.info(anomalies['reason'])
    high = summary['highest_hour']
    low = summary['lowest_hour']
    st.write(f"Highest hour: **{high['kwh']:,.2f} kWh** at {high['timestamp']}.")
    st.write(f"Lowest hour: **{low['kwh']:,.2f} kWh** at {low['timestamp']}.")
    if result['unusual_days']:
        st.dataframe(pd.DataFrame(result['unusual_days']), hide_index=True)
        st.caption('Unusual days differ from typical usage on the same weekday. These flags do not diagnose equipment faults or account for weather and seasons.')
    else:
        st.info('No unusual days were flagged, or there is not enough complete history for comparison.')
    with st.expander('Data quality and monthly details'):
        st.json(result['quality'])
        st.dataframe(months, hide_index=True)
    st.download_button('Download analysis', json.dumps(result, indent=2, allow_nan=False),
                       file_name='wattwise-analysis.json', mime='application/json')
    return result
