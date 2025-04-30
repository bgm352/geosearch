import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import (
    get_interest_over_time,
    get_interest_by_region,
    get_related_queries,
    get_trending_searches,
    get_interest_by_dma,
    forecast_trends
)

# Helper function to fallback on no data
def fetch_with_fallback(fetch_func, keywords, timeframe, geo, **kwargs):
    df = fetch_func(keywords, timeframe, geo, **kwargs)
    if df is not None and not df.empty:
        return df
    if geo.startswith("US-"):
        df = fetch_func(keywords, timeframe, "US", **kwargs)
        if df is not None and not df.empty:
            st.info(f"No data for {geo}. Showing data for US instead.")
            return df
    if timeframe != "today 12-m":
        df = fetch_func(keywords, "today 12-m", geo, **kwargs)
        if df is not None and not df.empty:
            st.info(f"No data for timeframe {timeframe}. Showing past 12 months instead.")
            return df
    return pd.DataFrame()

def show_download_button(df, label, filename):
    if not df.empty:
        st.download_button(
            label=label,
            data=df.to_csv().encode('utf-8'),
            file_name=filename,
            mime='text/csv'
        )

st.set_page_config(
    page_title="Healthcare SEO & Trends Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Healthcare SEO & Trends Dashboard")

# Correct timeframe options with valid PyTrends formats
timeframe_options = {
    "Past 7 days": "now 7-d",
    "Past 30 days": "now 1-m",
    "Past 90 days": "now 3-m",
    "Past 12 months": "today 12-m",
    "Past 5 years": f"{(datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')} {datetime.now().strftime('%Y-%m-%d')}",
    "2010 to present": f"2010-01-01 {datetime.now().strftime('%Y-%m-%d')}"
}

timeframe = st.sidebar.selectbox("Select Time Range", list(timeframe_options.keys()))

geo_options = ["US", "World"]
us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
             "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
             "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
             "VA", "WA", "WV", "WI", "WY"]
geo_options.extend([f"US-{state}" for state in us_states])
geo = st.sidebar.selectbox("Select Location", geo_options)

default_keywords = ["doctor near me", "medical clinic", "healthcare provider", "physician"]
keywords_input = st.sidebar.text_area("Enter keywords (one per line)", "\n".join(default_keywords))
keywords = [kw.strip() for kw in keywords_input.split("\n") if kw.strip()]

if len(keywords) > 5:
    st.warning("Google Trends supports up to 5 keywords per request. Using only the first 5.")
    keywords = keywords[:5]

if not keywords:
    st.error("Please enter at least one keyword.")
    st.stop()

compare_competitors = st.sidebar.checkbox("Compare with top competitors", True)

st.sidebar.subheader("Additional Options")
show_forecast = st.sidebar.checkbox("Show forecast", True)
forecast_period = st.sidebar.slider("Forecast period (days)", 30, 365, 90) if show_forecast else 90
map_opacity = st.sidebar.slider("Map opacity", 0.2, 1.0, 0.7, 0.1)

st.header("Overview")

with st.spinner("Fetching Google Trends data..."):
    interest_over_time_df = fetch_with_fallback(get_interest_over_time, keywords, timeframe_options[timeframe], geo)

cols = st.columns(4)
try:
    if not interest_over_time_df.empty:
        for i, kw in enumerate(keywords[:4]):
            if kw in interest_over_time_df.columns:
                current = interest_over_time_df[kw].iloc[-1]
                prev = interest_over_time_df[kw].iloc[-2] if len(interest_over_time_df) > 1 else 0
                pct_change = ((current - prev) / max(prev, 1)) * 100
                cols[i].metric(f"Interest in '{kw}'", f"{current:.1f}", f


