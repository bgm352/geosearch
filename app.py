import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from datetime import datetime, timedelta
from utils import (
    get_interest_over_time,
    get_interest_by_region,
    get_related_queries,
    get_trending_searches,
    get_interest_by_dma,
    forecast_trends
)

# --- Helper Functions ---

def fetch_with_fallback(fetch_func, *args, **kwargs):
    """Try fetching data, fallback to broader region/time if empty."""
    df = fetch_func(*args, **kwargs)
    if df is not None and not df.empty:
        return df
    geo = kwargs.get('geo', 'US')
    timeframe = kwargs.get('timeframe', 'today 12-m')
    if geo != 'US':
        kwargs['geo'] = 'US'
        df = fetch_func(*args, **kwargs)
        if df is not None and not df.empty:
            st.info("No data for selected region. Showing US-wide data instead.")
            return df
    if timeframe != 'today 12-m':
        kwargs['timeframe'] = 'today 12-m'
        df = fetch_func(*args, **kwargs)
        if df is not None and not df.empty:
            st.info("No data for selected timeframe. Showing 12 months instead.")
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

# --- Page Config ---

st.set_page_config(
    page_title="Healthcare SEO & Trends Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Healthcare SEO & Trends Dashboard")

# --- Sidebar ---

st.sidebar.title("Dashboard Controls")

# Time range selector
timeframe_options = {
    "Past 7 days": "now 7-d",
    "Past 30 days": "today 1-m",
    "Past 90 days": "today 3-m",
    "Past 12 months": "today 12-m",
    "Past 5 years": "today 5-y",
    "2010 to present": "2010-01-01 " + datetime.now().strftime("%Y-%m-%d")
}
timeframe = st.sidebar.selectbox("Select Time Range", list(timeframe_options.keys()), help="Choose how far back to analyze trends.")

# Location selector
geo_options = ["US", "World"]
us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
geo_options.extend([f"US-{state}" for state in us_states])
geo = st.sidebar.selectbox("Select Location", geo_options, help="Choose a country, state, or 'World'.")

# Default keywords for healthcare/medical professionals
default_keywords = ["doctor near me", "medical clinic", "healthcare provider", "physician"]
keywords_input = st.sidebar.text_area("Enter keywords (one per line)", "\n".join(default_keywords), help="Enter up to 5 keywords. Use common terms for best results.")
keywords = [kw.strip() for kw in keywords_input.split("\n") if kw.strip()]

if st.sidebar.button("Suggest Popular Keywords"):
    st.sidebar.info("Try: doctor, hospital, urgent care, telehealth, flu, covid")

if not keywords:
    st.warning("Please enter at least one keyword to analyze.")
    st.stop()

if any(len(kw) < 2 for kw in keywords):
    st.warning("Please enter more descriptive keywords (at least 2 characters each).")
    st.stop()

if len(keywords) > 5:
    st.sidebar.warning("Google Trends only supports up to 5 keywords per request. Only the first 5 will be used.")
    keywords = keywords[:5]

# Compare with competitors option
compare_competitors = st.sidebar.checkbox("Compare with top competitors", True)

# Additional options in sidebar
st.sidebar.subheader("Additional Options")
show_forecast = st.sidebar.checkbox("Show forecast", True)
forecast_period = st.sidebar.slider("Forecast period (days)", 30, 365, 90) if show_forecast else 90
map_opacity = st.sidebar.slider("Map opacity", 0.2, 1.0, 0.7, 0.1)

# --- Main Content ---

st.header("Overview")

with st.spinner("Fetching Google Trends data..."):
    interest_over_time_df = fetch_with_fallback(
        get_interest_over_time, keywords, timeframe_options[timeframe], geo=geo
    )

col1, col2, col3, col4 = st.columns(4)

try:
    if not interest_over_time_df.empty:
        for i, kw in enumerate(keywords[:4]):
            if kw in interest_over_time_df.columns:
                current_value = interest_over_time_df[kw].iloc[-1]
                previous_value = interest_over_time_df[kw].iloc[-2] if len(interest_over_time_df) > 1 else 0
                percent_change = ((current_value - previous_value) / max(previous_value, 1)) * 100
                if i == 0:
                    col1.metric(f"Interest in '{kw}'", f"{current_value:.1f}", f"{percent_change:.1f}%")
                elif i == 1:
                    col2.metric(f"Interest in '{kw}'", f"{current_value:.1f}", f"{percent_change:.1f}%")
                elif i == 2:
                    col3.metric(f"Interest in '{kw}'", f"{current_value:.1f}", f"{percent_change:.1f}%")
                elif i == 3:
                    col4.metric(f"Interest in '{kw}'", f"{current_value:.1f}", f"{percent_change:.1f}%")
    else:
        st.warning("No data found for your keywords, region, or timeframe. Try using more popular keywords or a broader region/time period.")
        st.info("Example keywords: doctor, hospital, flu, covid")
except Exception as e:
    st.error(f"Error calculating metrics: {e}")

# Interest Over Time Chart
st.subheader("Search Interest Over Time")
try:
    if not interest_over_time_df.empty:
        fig = px.line(interest_over_time_df, x=interest_over_time_df.index, y=keywords,
                      title="Search Interest Trends",
                      labels={"value": "Search Interest", "variable": "Keyword", "date": "Date"})
        # Add forecast if requested
        if show_forecast:
            forecast_data = forecast_trends(interest_over_time_df, keywords, forecast_period)
            if forecast_data is not None:
                for kw in keywords:
                    if kw in forecast_data.columns:
                        fig.add_trace(go.Scatter(
                            x=forecast_data.index, 
                            y=forecast_data[kw],
                            mode='lines',
                            line=dict(dash='dot'),
                            name=f"{kw} (Forecast)"
                        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Search Interest",
            legend_title="Keywords",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        show_download_button(interest_over_time_df, "Download CSV", "interest_over_time.csv")
    else:
        st.warning("No interest over time data available for the selected parameters. Try more popular keywords or a broader region/time period.")
except Exception as e:
    st.error(f"Error displaying interest over time chart: {e}")

# Geographical Insights
st.header("Geographical Insights")

geo_tab1, geo_tab2 = st.tabs(["Interest by Region", "Interest by City/DMA"])

with geo_tab1:
    st.subheader("Interest by Region")
    selected_keyword_for_map = st.selectbox(
        "Select keyword to display on map:", 
        keywords,
        key="region_map_keyword"
    )
    with st.spinner("Fetching regional data..."):
        interest_by_region_df = fetch_with_fallback(
            get_interest_by_region,
            [selected_keyword_for_map], 
            timeframe_options[timeframe], 
            geo=geo
        )
    try:
        if not interest_by_region_df.empty:
            fig = px.choropleth(
                interest_by_region_df,
                locations=interest_by_region_df.index,
                color=selected_keyword_for_map,
                hover_name=interest_by_region_df.index,
                title=f"Search Interest for '{selected_keyword_for_map}' by Region",
                color_continuous_scale="YlOrRd",
                locationmode='USA-states' if geo == "US" else 'country names'
            )
            fig.update_layout(
                geo=dict(
                    scope='usa' if geo == "US" else 'world',
                    projection_type='albers usa' if geo == "US" else 'natural earth',
                    showcoastlines=True,
                    showland=True,
                    landcolor="rgb(229, 229, 229)",
                    countrycolor="white",
                    showlakes=True,
                    lakecolor="white",
                    showsubunits=True,
                    showcountries=True,
                    opacity=map_opacity
                ),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
            top_n = min(10, len(interest_by_region_df))
            top_regions = interest_by_region_df.sort_values(by=selected_keyword_for_map, ascending=False).head(top_n)
            fig_bar = px.bar(
                top_regions,
                x=top_regions.index,
                y=selected_keyword_for_map,
                title=f"Top {top_n} Regions by Search Interest for '{selected_keyword_for_map}'",
                color=selected_keyword_for_map,
                color_continuous_scale="YlOrRd"
            )
            fig_bar.update_layout(
                xaxis_title="Region",
                yaxis_title="Search Interest",
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            show_download_button(interest_by_region_df, "Download CSV", "interest_by_region.csv")
        else:
            st.warning("No regional data available for the selected parameters. Try more popular keywords or a broader region/time period.")
    except Exception as e:
        st.error(f"Error displaying regional map: {e}")

with geo_tab2:
    st.subheader("Interest by City/DMA")
    selected_keyword_for_dma = st.selectbox(
        "Select keyword to display by city/DMA:", 
        keywords,
        key="dma_map_keyword"
    )
    with st.spinner("Fetching city/DMA data..."):
        interest_by_dma_df = fetch_with_fallback(
            get_interest_by_dma,
            [selected_keyword_for_dma], 
            timeframe_options[timeframe], 
            geo=geo
        )
    try:
        if not interest_by_dma_df.empty:
            top_n = min(20, len(interest_by_dma_df))
            top_dmas = interest_by_dma_df.sort_values(by=selected_keyword_for_dma, ascending=False).head(top_n)
            fig_bar = px.bar(
                top_dmas,
                x=top_dmas.index,
                y=selected_keyword_for_dma,
                title=f"Top {top_n} Cities/DMAs by Search Interest for '{selected_keyword_for_dma}'",
                color=selected_keyword_for_dma,
                color_continuous_scale="YlOrRd"
            )
            fig_bar.update_layout(
                xaxis_title="City/DMA",
                yaxis_title="Search Interest",
                height=500,
                xaxis={'categoryorder':'total descending'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            show_download_button(interest_by_dma_df, "Download CSV", "interest_by_dma.csv")
        else:
            st.warning("No city/DMA data available for the selected parameters. Try more popular keywords or a broader region/time period.")
    except Exception as e:
        st.error(f"Error displaying city/DMA chart: {e}")

# Keyword Insights
st.header("Keyword Insights")

keyword_tab1, keyword_tab2 = st.tabs(["Related Queries", "Trending Searches"])

with keyword_tab1:
    st.subheader("Related Queries")
    selected_keyword_for_related = st.selectbox(
        "Select keyword to find related queries:", 
        keywords,
        key="related_queries_keyword"
    )
    with st.spinner("Fetching related queries..."):
        related_queries = get_related_queries(
            [selected_keyword_for_related], 
            timeframe_options[timeframe], 
            geo
        )
    try:
        if related_queries and selected_keyword_for_related in related_queries:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top Related Queries")
                if 'top' in related_queries[selected_keyword_for_related]:
                    top_queries = related_queries[selected_keyword_for_related]['top']
                    if not top_queries.empty:
                        st.dataframe(top_queries, use_container_width=True)
                        fig = px.bar(
                            top_queries.head(10),
                            x='value',
                            y='query',
                            orientation='h',
                            title=f"Top Related Queries for '{selected_keyword_for_related}'",
                            color='value',
                            color_continuous_scale="YlOrRd"
                        )
                        fig.update_layout(
                            xaxis_title="Search Interest",
                            yaxis_title="Query",
                            height=400,
                            yaxis={'categoryorder':'total ascending'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        show_download_button(top_queries, "Download CSV", "top_related_queries.csv")
                    else:
                        st.info("No top related queries data available.")
                else:
                    st.info("No top related queries data available.")
            with col2:
                st.subheader("Rising Related Queries")
                if 'rising' in related_queries[selected_keyword_for_related]:
                    rising_queries = related_queries[selected_keyword_for_related]['rising']
                    if not rising_queries.empty:
                        st.dataframe(rising_queries, use_container_width=True)
                        fig = px.bar(
                            rising_queries.head(10),
                            x='value',
                            y='query',
                            orientation='h',
                            title=f"Rising Related Queries for '{selected_keyword_for_related}'",
                            color='value',
                            color_continuous_scale="YlOrRd"
                        )
                        fig.update_layout(
                            xaxis_title="Search Interest",
                            yaxis_title="Query",
                            height=400,
                            yaxis={'categoryorder':'total ascending'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        show_download_button(rising_queries, "Download CSV", "rising_related_queries.csv")
                    else:
                        st.info("No rising related queries data available.")
                else:
                    st.info("No rising related queries data available.")
        else:
            st.warning("No related queries data available for the selected parameters. Try more popular keywords or a broader region/time period.")
    except Exception as e:
        st.error(f"Error displaying related queries: {e}")

with keyword_tab2:
    st.subheader("Trending Searches")
    with st.spinner("Fetching trending searches..."):
        trending_searches = get_trending_searches(geo)
    try:
        if trending_searches is not None and not trending_searches.empty:
            st.dataframe(trending_searches.head(20), use_container_width=True)
            fig = px.bar(
                trending_searches.head(10),
                x='value',
                y='query',
                orientation='h',
                title=f"Top Trending Searches",
                color='value',
                color_continuous_scale="YlOrRd"
            )
            fig.update_layout(
                xaxis_title="Search Interest",
                yaxis_title="Query",
                height=400,
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
            show_download_button(trending_searches, "Download CSV", "trending_searches.csv")
        else:
            st.warning("No trending searches data available for the selected parameters. Try more popular keywords or a broader region/time period.")
    except Exception as e:
        st.error(f"Error displaying trending searches: {e}")

# Competitor Analysis
if compare_competitors:
    st.header("Competitor Analysis")
    st.subheader("Top Healthcare Providers by Search Interest")
    providers = [
        "Cleveland Clinic", 
        "Mayo Clinic", 
        "Johns Hopkins Medicine", 
        "Massachusetts General Hospital",
        "UCSF Medical Center"
    ]
    providers_input = st.text_area("Enter healthcare providers to compare (one per line)", "\n".join(providers))
    providers = [p.strip() for p in providers_input.split("\n") if p.strip()]
    if len(providers) > 5:
        st.warning("Google Trends only supports up to 5 keywords per request. Only the first 5 will be used.")
        providers = providers[:5]
    with st.spinner("Fetching competitor data..."):
        providers_interest = fetch_with_fallback(
            get_interest_over_time, providers, timeframe_options[timeframe], geo=geo
        )
    try:
        if not providers_interest.empty:
            fig = px.line(
                providers_interest,
                x=providers_interest.index,
                y=providers,
                title="Search Interest Comparison: Healthcare Providers",
                labels={"value": "Search Interest", "variable": "Provider", "date": "Date"}
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Search Interest",
                legend_title="Healthcare Providers",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            avg_interest = providers_interest.mean().reset_index()
            avg_interest.columns = ['Provider', 'Average Interest']
            avg_interest = avg_interest.sort_values('Average Interest', ascending=False)
            fig_bar = px.bar(
                avg_interest,
                x='Provider',
                y='Average Interest',
                title="Average Search Interest by Provider",
                color='Average Interest',
                color_continuous_scale="YlOrRd"
            )
            fig_bar.update_layout(
                xaxis_title="Provider",
                yaxis_title="Average Search Interest",
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            show_download_button(providers_interest, "Download CSV", "competitor_interest.csv")
        else:
            st.warning("No competitor data available for the selected parameters. Try more popular providers or a broader region/time period.")
    except Exception as e:
        st.error(f"Error displaying competitor analysis: {e}")

st.markdown("---")
st.markdown("Healthcare SEO & Trends Dashboard | Data from Google Trends")
st.markdown("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
