import streamlit as st

from src.weather import location_weather

cached_weather = st.cache_data(ttl=3600, show_spinner=False)(location_weather)


def default_weather_location():
    st.caption('Weather defaults to Miami, Florida for this demo. Weather is matched to the dates in your file.')
    st.caption('Weather by [Open-Meteo](https://open-meteo.com/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).')
    return dict(name='Miami', region='Florida', country='United States',
                latitude=25.7617, longitude=-80.1918, timezone='America/New_York')
