import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import sys
import traceback
from pytrends.request import TrendReq

# Set page config
st.set_page_config(
    page_title="Healthcare SEO & Trends Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize PyTrends with backoff retry logic
@st.cache_resource(ttl=3600)
def get_pytrends_client():
    # Use a more browser-like user agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    return TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.5, 
                    requests_args={'headers': {'User-Agent': user_agent}})

# Utility functions with improved error handling and caching
@st.cache_data(ttl=3600)
def get_interest_over_time(keywords, timeframe, geo):
    """Get interest over time for keywords"""
    if not keywords:
        return pd.DataFrame()
    
    try:
        pytrends = get_pytrends_client()
        # Add a small random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if df.empty:
            st.info(f"No data available for {', '.join(keywords)} in {geo} during {timeframe}")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error fetching interest over time: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_interest_by_region(keywords, timeframe, geo, resolution='COUNTRY'):
    """Get interest by region for keywords"""
    if not keywords:
        return pd.DataFrame()
    
    try:
        pytrends = get_pytrends_client()
        time.sleep(random.uniform(1, 3))
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True, inc_geo_code=True)
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error fetching interest by region: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_related_queries(keywords, timeframe, geo):
    """Get related queries for keywords"""
    if not keywords:
        return {}
    
    try:
        pytrends = get_pytrends_client()
        time.sleep(random.uniform(1, 3))
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        related_queries = pytrends.related_queries()
        return related_queries
    except Exception as e:
        st.error(f"Error fetching related queries: {str(e)}")
        return {}

@st.cache_data(ttl=3600)
def get_trending_searches(geo="united_states"):
    """Get trending searches"""
    try:
        pytrends = get_pytrends_client()
        time.sleep(random.uniform(1, 3))
        df = pytrends.trending_searches(pn=geo)
        return df
    except Exception as e:
        st.error(f"Error fetching trending searches: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_interest_by_dma(keywords, timeframe, geo="US"):
    """Get interest by DMA (Designated Market Area)"""
    if not keywords or geo != "US":
        return pd.DataFrame()
    
    try:
        pytrends = get_pytrends_client()
        time.sleep(random.uniform(1, 3))
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region(resolution='DMA', inc_low_vol=True, inc_geo_code=True)
        return df
    except Exception as e:
        st.error(f"Error fetching interest by DMA: {str(e)}")
        return pd.DataFrame()

def forecast_trends(df, keywords, days_to_forecast=90):
    """Simple forecasting using linear regression"""
    if df.empty or len(df) < 10:
        return None
    
    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        forecast_start = df.index[-1] + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=days_to_forecast)
        forecast_dates = pd.date_range(start=forecast_start, end=forecast_end, freq='D')
        
        # Create a DataFrame to store forecasts
        forecast_df = pd.DataFrame(index=forecast_dates)
        
        for kw in keywords:
            if kw in df.columns:
                # Prepare data for training
                X = np.array(range(len(df))).reshape(-1, 1)
                y = df[kw].values
                
                # Train model
                model = LinearRegression()
                model.fit(X, y)
                
                # Make predictions
                future_X = np.array(range(len(df), len(df) + len(forecast_dates))).reshape(-1, 1)
                forecast_values = model.predict(future_X)
                
                # Clip values to be between 0 and 100
                forecast_values = np.clip(forecast_values, 0, 100)
                
                # Add to forecast DataFrame
                forecast_df[kw] = forecast_values
        
        return forecast_df
    except Exception as e:
        st.error(f"Error forecasting trends: {str(e)}")
        return None

# Helper function to fallback on no data with improved error handling
def fetch_with_fallback(fetch_func, keywords, timeframe, geo, **kwargs):
    try:
        df = fetch_func(keywords, timeframe, geo, **kwargs)
        if df is not None and not df.empty:
            return df
        
        # Try fallback to US if using a state
        if geo.startswith("US-"):
            df = fetch_func(keywords, timeframe, "US", **kwargs)
            if df is not None and not df.empty:
                st.info(f"No data for {geo}. Showing data for US instead.")
                return df
        
        # Try fallback to different timeframe
        if timeframe != "today 12-m":
            df = fetch_func(keywords, "today 12-m", geo, **kwargs)
            if df is not None and not df.empty:
                st.info(f"No data for timeframe {timeframe}. Showing past 12 months instead.")
                return df
                
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error in fetch_with_fallback: {str(e)}")
        st.error(traceback.format_exc())
        return pd.DataFrame()

def show_download_button(df, label, filename):
    if not df.empty:
        st.download_button(
            label=label,
            data=df.to_csv().encode('utf-8'),
            file_name=filename,
            mime='text/csv'
        )

# App title
st.title("Healthcare SEO & Trends Dashboard")

# Sidebar options
timeframe_options = {
    "Past 7 days": "now 7-d",
    "Past 30 days": "today 1-m",
    "Past 90 days": "today 3-m",
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

# Add debug mode
debug_mode = st.sidebar.checkbox("Debug Mode", False)
if debug_mode:
    st.sidebar.info(f"Python version: {sys.version}")
    st.sidebar.info(f"Using keywords: {keywords}")
    st.sidebar.info(f"Timeframe: {timeframe_options[timeframe]}")
    st.sidebar.info(f"Geo: {geo}")

st.header("Overview")

# Disable caching during development if needed
# st.cache_data.clear()
# st.cache_resource.clear()

with st.spinner("Fetching Google Trends data..."):
    interest_over_time_df = fetch_with_fallback(get_interest_over_time, keywords, timeframe_options[timeframe], geo)
    
    if debug_mode and not interest_over_time_df.empty:
        st.sidebar.subheader("Interest Over Time Data Sample")
        st.sidebar.dataframe(interest_over_time_df.head())

# Display metrics
cols = st.columns(4)
try:
    if not interest_over_time_df.empty:
        for i, kw in enumerate(keywords[:4]):
            if kw in interest_over_time_df.columns:
                current = interest_over_time_df[kw].iloc[-1]
                prev = interest_over_time_df[kw].iloc[-2] if len(interest_over_time_df) > 1 else 0
                pct_change = ((current - prev) / max(prev, 1)) * 100
                cols[i].metric(f"Interest in '{kw}'", f"{current:.1f}", f"{pct_change:.1f}%")
    else:
        st.warning("No data found for your keywords, region, or timeframe. Try more popular keywords or a broader region/time period.")
except Exception as e:
    st.error(f"Error calculating metrics: {e}")
    if debug_mode:
        st.error(traceback.format_exc())

# Interest over time chart
st.subheader("Search Interest Over Time")
try:
    if not interest_over_time_df.empty:
        fig = px.line(
            interest_over_time_df, x=interest_over_time_df.index, y=keywords,
            title="Search Interest Trends",
            labels={"value": "Search Interest", "variable": "Keyword", "date": "Date"}
        )
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
        fig.update_layout(xaxis_title="Date", yaxis_title="Search Interest", legend_title="Keywords", height=500)
        st.plotly_chart(fig, use_container_width=True)
        show_download_button(interest_over_time_df, "Download CSV", "interest_over_time.csv")
    else:
        st.warning("No interest over time data available for the selected parameters.")
except Exception as e:
    st.error(f"Error displaying interest over time chart: {e}")
    if debug_mode:
        st.error(traceback.format_exc())

# Geographic Insights section
st.header("Geographic Insights")

geo_resolution = "COUNTRY" if geo == "World" else "REGION" if geo == "US" else "DMA"
with st.spinner("Fetching geographic data..."):
    if geo == "US":
        geo_data = fetch_with_fallback(get_interest_by_region, keywords, timeframe_options[timeframe], geo, resolution="REGION")
    elif geo.startswith("US-"):
        geo_data = fetch_with_fallback(get_interest_by_dma, keywords, timeframe_options[timeframe], geo="US")
    else:
        geo_data = fetch_with_fallback(get_interest_by_region, keywords, timeframe_options[timeframe], geo, resolution=geo_resolution)

try:
    if not geo_data.empty:
        tab1, tab2 = st.tabs(["Map View", "Table View"])
        
        with tab1:
            for kw in keywords:
                if kw in geo_data.columns:
                    if geo == "World":
                        fig = px.choropleth(
                            geo_data.reset_index(), 
                            locations="geoCode",
                            color=kw,
                            hover_name="geoName",
                            title=f"Geographic Interest for '{kw}'",
                            color_continuous_scale=px.colors.sequential.Plasma,
                            projection="natural earth"
                        )
                    elif geo == "US" or geo.startswith("US-"):
                        scope = "usa"
                        fig = px.choropleth(
                            geo_data.reset_index(), 
                            locations="geoCode",
                            locationmode="USA-states",
                            color=kw,
                            hover_name="geoName",
                            title=f"Geographic Interest for '{kw}'",
                            color_continuous_scale=px.colors.sequential.Plasma,
                            scope=scope
                        )
                    else:
                        continue  # Skip if we can't properly map
                        
                    fig.update_layout(
                        geo=dict(showframe=False, showcoastlines=True),
                        margin={"r":0,"t":40,"l":0,"b":0},
                        coloraxis_colorbar=dict(title="Interest")
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(geo_data)
            show_download_button(geo_data, "Download Geographic Data", "geo_interest.csv")
    else:
        st.warning("No geographic data available for the selected parameters.")
except Exception as e:
    st.error(f"Error displaying geographic insights: {e}")
    if debug_mode:
        st.error(traceback.format_exc())

# Related Queries section
st.header("Related Queries")

with st.spinner("Fetching related queries..."):
    related_queries = get_related_queries(keywords, timeframe_options[timeframe], geo)

try:
    if related_queries and any(related_queries.get(kw, {}) for kw in keywords):
        for kw in keywords:
            if kw in related_queries and related_queries[kw]:
                st.subheader(f"Related to '{kw}'")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Top Related Queries")
                    if 'top' in related_queries[kw] and not related_queries[kw]['top'].empty:
                        st.dataframe(related_queries[kw]['top'])
                        show_download_button(related_queries[kw]['top'], f"Download Top Queries for {kw}", f"top_queries_{kw}.csv")
                    else:
                        st.info("No top related queries data available")
                
                with col2:
                    st.subheader("Rising Related Queries")
                    if 'rising' in related_queries[kw] and not related_queries[kw]['rising'].empty:
                        st.dataframe(related_queries[kw]['rising'])
                        show_download_button(related_queries[kw]['rising'], f"Download Rising Queries for {kw}", f"rising_queries_{kw}.csv")
                    else:
                        st.info("No rising related queries data available")
                
                st.markdown("---")
    else:
        st.warning("No related queries data available for the selected parameters.")
except Exception as e:
    st.error(f"Error displaying related queries: {e}")
    if debug_mode:
        st.error(traceback.format_exc())

# Trending Searches section (only for US)
if geo == "US" or geo.startswith("US-"):
    st.header("Trending Healthcare Searches")
    
    with st.spinner("Fetching trending searches..."):
        trending_searches = get_trending_searches()
    
    try:
        if not trending_searches.empty:
            st.dataframe(trending_searches.head(20))
            show_download_button(trending_searches, "Download Trending Searches", "trending_searches.csv")
        else:
            st.warning("No trending searches data available.")
    except Exception as e:
        st.error(f"Error displaying trending searches: {e}")
        if debug_mode:
            st.error(traceback.format_exc())

# Competitor Analysis (if enabled)
if compare_competitors:
    st.header("Competitor Analysis")
    
    with st.spinner("Analyzing competitors..."):
        # Get related topics to identify potential competitors
        try:
            pytrends = get_pytrends_client()
            time.sleep(random.uniform(1, 3))
            
            # Just use the first keyword for competitor analysis
            main_keyword = keywords[0]
            pytrends.build_payload([main_keyword], cat=0, timeframe=timeframe_options[timeframe], geo=geo)
            related_topics = pytrends.related_topics()
            
            competitors = []
            if main_keyword in related_topics and 'rising' in related_topics[main_keyword]:
                rising_df = related_topics[main_keyword]['rising']
                if not rising_df.empty:
                    # Get company names from rising topics
                    for _, row in rising_df.iterrows():
                        if 'Hospital' in row['topic_title'] or 'Clinic' in row['topic_title'] or 'Health' in row['topic_title']:
                            competitors.append(row['topic_title'])
                    
                    # Limit to top 3 competitors
                    competitors = competitors[:3]
            
            # Add some default competitors if we didn't find any
            if len(competitors) < 3:
                default_competitors = ["Mayo Clinic", "Cleveland Clinic", "Johns Hopkins Hospital", "Kaiser Permanente"]
                for comp in default_competitors:
                    if comp not in competitors:
                        competitors.append(comp)
                        if len(competitors) >= 3:
                            break
            
            # Compare with competitors
            if competitors:
                compare_keywords = [main_keyword] + competitors[:3]  # Main keyword + top 3 competitors
                
                # Get interest over time for competitor comparison
                pytrends.build_payload(compare_keywords, cat=0, timeframe=timeframe_options[timeframe], geo=geo)
                competitor_df = pytrends.interest_over_time()
                
                if not competitor_df.empty:
                    fig = px.line(
                        competitor_df, x=competitor_df.index, y=compare_keywords,
                        title=f"Competitor Comparison: Search Interest for '{main_keyword}' vs. Competitors",
                        labels={"value": "Search Interest", "variable": "Entity", "date": "Date"}
                    )
                    fig.update_layout(xaxis_title="Date", yaxis_title="Search Interest", legend_title="Entity", height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    show_download_button(competitor_df, "Download Competitor Data", "competitor_comparison.csv")
                else:
                    st.warning("No competitor comparison data available for the selected parameters.")
            else:
                st.warning("No competitors identified for comparison.")
                
        except Exception as e:
            st.error(f"Error performing competitor analysis: {e}")
            if debug_mode:
                st.error(traceback.format_exc())

# Healthcare Insights section
st.header("Healthcare Search Insights")

healthcare_tabs = st.tabs(["Key Takeaways", "Search Patterns", "Recommendations"])

with healthcare_tabs[0]:
    st.subheader("Key Takeaways")
    
    if not interest_over_time_df.empty:
        # Generate basic insights
        insights = []
        
        # Look for trends
        for kw in keywords:
            if kw in interest_over_time_df.columns:
                series = interest_over_time_df[kw]
                avg = series.mean()
                current = series.iloc[-1]
                pct_diff = ((current - avg) / avg) * 100
                
                if pct_diff > 20:
                    insights.append(f"'{kw}' is trending significantly higher than its average ({pct_diff:.1f}% above average)")
                elif pct_diff < -20:
                    insights.append(f"'{kw}' is currently well below its average search interest ({-pct_diff:.1f}% below average)")
                
                # Check seasonality (very simple approach)
                if len(series) > 30:
                    max_month = series.groupby(series.index.month).mean().idxmax()
                    month_name = datetime(2020, max_month, 1).strftime('%B')
                    insights.append(f"'{kw}' tends to peak in {month_name}")
        
        if insights:
            for insight in insights:
                st.markdown(f"• {insight}")
        else:
            st.info("Not enough data to generate meaningful insights. Try more popular keywords or a longer time range.")
    else:
        st.warning("No data available to generate insights.")

with healthcare_tabs[1]:
    st.subheader("Search Patterns")
    st.markdown("""
    Common healthcare search patterns:
    
    1. **Symptom-based searches**: Users often search for symptoms first before looking for specific conditions
    2. **Local healthcare searches**: Searches with "near me" tend to have higher conversion rates
    3. **Insurance-related searches**: Peak during open enrollment periods
    4. **Seasonal health concerns**: Flu-related searches peak in winter, allergy searches in spring
    5. **Health news impact**: Major health news can cause significant spikes in related searches
    """)

with healthcare_tabs[2]:
    st.subheader("Recommendations")
    st.markdown("""
    Based on healthcare search trends:
    
    1. **Optimize for local search**: Ensure your Google My Business profile is complete and updated
    2. **Content calendar**: Plan content around seasonal health topics
    3. **Mobile optimization**: Most healthcare searches happen on mobile devices
    4. **FAQ content**: Create content answering common health questions
    5. **Video content**: Healthcare video content has higher engagement rates
    6. **Testimonials**: Feature patient testimonials to build trust
    7. **Symptom-based content**: Create content that addresses symptom searches and connects them to your services
    """)

# Add footer
st.markdown("---")
st.markdown("Healthcare SEO & Trends Dashboard | Data from Google Trends")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Add an "About" expander at the bottom
with st.expander("About this dashboard"):
    st.markdown("""
    This dashboard uses Google Trends data to analyze healthcare-related search trends. The data is not guaranteed to be completely accurate and should be used for informational purposes only.
    
    **Data sources**:
    - Search interest over time: Google Trends
    - Geographic interest data: Google Trends
    - Related queries: Google Trends
    - Trending searches: Google Trends
    
    **Note**: Google Trends data is normalized and presented on a scale from 0-100, where 100 represents the peak popularity of a term during the specified time period.
    """)

