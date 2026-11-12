import json

import pandas as pd
import streamlit as st

from src.consumption import analyze_csv


def render_analysis(uploaded_file, *, unit, timezone, electricity_rate):
    try:
        uploaded_file.seek(0)
        result = analyze_csv(uploaded_file, unit=unit, timezone=timezone)
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
        st.caption(f"Estimated usage cost: ${forecast['predicted_kwh'] * electricity_rate:,.2f}. Based on {forecast['source_month']}'s average hourly usage, adjusted for month length. Weather and changes in operations may affect actual use. An uncertainty range is not yet available.")
    else:
        st.info(forecast['reason'])
    st.subheader('Worth a closer look')
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
