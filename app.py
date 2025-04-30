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

# Set page config
st.set_page_config(
    page_title="Healthcare SEO & Trends Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar configuration
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
timeframe = st.sidebar.selectbox("Select Time Range", list(timeframe_options.keys()))

# Location selector
geo_options = ["US", "World"]
us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
geo_options.extend([f"US-{state}" for state in us_states])
geo = st.sidebar.selectbox("Select Location", geo_options)

# Default keywords for healthcare/medical professionals
default_keywords = ["doctor near me", "medical clinic", "healthcare provider", "physician"]
keywords_input = st.sidebar.text_area("Enter keywords (one per line)", "\n".join(default_keywords))
keywords = [kw.strip() for kw in keywords_input.split("\n") if kw.strip()]

# Compare with competitors option
compare_competitors = st.sidebar.checkbox("Compare with top competitors", True)

# Additional options in sidebar
st.sidebar.subheader("Additional Options")
show_forecast = st.sidebar.checkbox("Show forecast", True)
forecast_period = st.sidebar.slider("Forecast period (days)", 30, 365, 90) if show_forecast else 90
map_opacity = st.sidebar.slider("Map opacity", 0.2, 1.0, 0.7, 0.1)

# Main content
st.title("Healthcare SEO & Trends Dashboard")

# Overview tab with metrics
st.header("Overview")

# Fetch the interest over time data
interest_over_time_df = get_interest_over_time(keywords, timeframe_options[timeframe], geo)

col1, col2, col3, col4 = st.columns(4)

try:
    # Calculate metrics for the overview
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
    else:
        st.info("No interest over time data available for the selected parameters.")
except Exception as e:
    st.error(f"Error displaying interest over time chart: {e}")

# Geographical Insights
st.header("Geographical Insights")

# Tabs for different geographical visualizations
geo_tab1, geo_tab2 = st.tabs(["Interest by Region", "Interest by City/DMA"])

with geo_tab1:
    st.subheader("Interest by Region")
    
    # Allow the user to select which keyword to display on the map
    selected_keyword_for_map = st.selectbox(
        "Select keyword to display on map:", 
        keywords,
        key="region_map_keyword"
    )
    
    # Fetch interest by region
    interest_by_region_df = get_interest_by_region(
        [selected_keyword_for_map], 
        timeframe_options[timeframe], 
        geo
    )
    
    try:
        if not interest_by_region_df.empty:
            # Create a choropleth map
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
            
            # Also show the data as a bar chart for the top regions
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
        else:
            st.info("No regional data available for the selected parameters.")
    except Exception as e:
        st.error(f"Error displaying regional map: {e}")

with geo_tab2:
    st.subheader("Interest by City/DMA")
    
    # Allow the user to select which keyword to display on the map
    selected_keyword_for_dma = st.selectbox(
        "Select keyword to display by city/DMA:", 
        keywords,
        key="dma_map_keyword"
    )
    
    # Fetch interest by DMA (Designated Market Area)
    interest_by_dma_df = get_interest_by_dma(
        [selected_keyword_for_dma], 
        timeframe_options[timeframe], 
        geo
    )
    
    try:
        if not interest_by_dma_df.empty:
            # Show the data as a bar chart for the top cities/DMAs
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
        else:
            st.info("No city/DMA data available for the selected parameters.")
    except Exception as e:
        st.error(f"Error displaying city/DMA chart: {e}")

# Keyword Insights
st.header("Keyword Insights")

keyword_tab1, keyword_tab2 = st.tabs(["Related Queries", "Trending Searches"])

with keyword_tab1:
    st.subheader("Related Queries")
    
    # Allow user to select keyword to analyze
    selected_keyword_for_related = st.selectbox(
        "Select keyword to find related queries:", 
        keywords,
        key="related_queries_keyword"
    )
    
    # Fetch related queries
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
                        
                        # Visualize top related queries
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
                        
                        # Visualize rising related queries
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
                    else:
                        st.info("No rising related queries data available.")
                else:
                    st.info("No rising related queries data available.")
        else:
            st.info("No related queries data available for the selected parameters.")
    except Exception as e:
        st.error(f"Error displaying related queries: {e}")

with keyword_tab2:
    st.subheader("Trending Searches")
    
    # Fetch trending searches
    trending_searches = get_trending_searches(geo)
    
    try:
        if trending_searches is not None and not trending_searches.empty:
            # Display trending searches
            st.dataframe(trending_searches.head(20), use_container_width=True)
            
            # Visualize top trending searches
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
        else:
            st.info("No trending searches data available for the selected parameters.")
    except Exception as e:
        st.error(f"Error displaying trending searches: {e}")

# Competitor Analysis
if compare_competitors:
    st.header("Competitor Analysis")
    
    # Top healthcare providers/websites based on keywords
    st.subheader("Top Healthcare Providers by Search Interest")
    
    # Healthcare providers to compare
    providers = [
        "Cleveland Clinic", 
        "Mayo Clinic", 
        "Johns Hopkins Medicine", 
        "Massachusetts General Hospital",
        "UCSF Medical Center"
    ]
    
    # Allow the user to edit the list of providers
    providers_input = st.text_area("Enter healthcare providers to compare (one per line)", "\n".join(providers))
    providers = [p.strip() for p in providers_input.split("\n") if p.strip()]
    
    # Fetch interest over time for providers
    providers_interest = get_interest_over_time(providers, timeframe_options[timeframe], geo)
    
    try:
        if not providers_interest.empty:
            # Line chart for provider comparison
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
            
            # Compare average interest
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
        else:
            st.info("No competitor data available for the selected parameters.")
    except Exception as e:
        st.error(f"Error displaying competitor analysis: {e}")

# Footer
st.markdown("---")
st.markdown("Healthcare SEO & Trends Dashboard | Data from Google Trends")
st.markdown("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
