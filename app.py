import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import sys
import traceback

# Set page config
st.set_page_config(
    page_title="Healthcare SEO & Trends Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple function to get mock interest over time data
@st.cache_data(ttl=3600)
def get_interest_over_time(keywords, timeframe, geo):
    """Generate mock interest over time data"""
    if not keywords:
        return pd.DataFrame()
    
    try:
        # Create date range
        if "now" in timeframe:
            days = int(timeframe.split("-")[1].strip("d"))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        elif "today" in timeframe:
            months = int(timeframe.split("-")[1].strip("m"))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months*30)
        else:
            dates = timeframe.split()
            start_date = datetime.strptime(dates[0], "%Y-%m-%d")
            end_date = datetime.strptime(dates[1], "%Y-%m-%d")
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create mock data
        data = {'date': date_range}
        for kw in keywords:
            # Generate realistic trending data with some randomness
            base = random.uniform(20, 60)
            trend = [base]
            for i in range(1, len(date_range)):
                # Add slight trend up or down
                direction = 0.1 if random.random() > 0.5 else -0.1
                new_val = trend[-1] + direction + random.uniform(-5, 5)
                # Keep within bounds
                new_val = max(0, min(100, new_val))
                trend.append(new_val)
            data[kw] = trend
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        st.error(f"Error generating mock data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_interest_by_region(keywords, timeframe, geo, resolution='COUNTRY'):
    """Generate mock interest by region data"""
    if not keywords:
        return pd.DataFrame()
    
    try:
        regions = {
            'COUNTRY': ['United States', 'Canada', 'United Kingdom', 'Australia', 'Germany', 
                      'France', 'Japan', 'Brazil', 'India', 'South Africa'],
            'REGION': ['California', 'Texas', 'New York', 'Florida', 'Illinois', 
                      'Pennsylvania', 'Ohio', 'Georgia', 'North Carolina', 'Michigan'],
            'DMA': ['New York', 'Los Angeles', 'Chicago', 'Philadelphia', 'Dallas', 
                  'San Francisco', 'Boston', 'Atlanta', 'Washington DC', 'Houston']
        }
        
        region_list = regions.get(resolution, regions['COUNTRY'])
        region_codes = ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'JP', 'BR', 'IN', 'ZA'] if resolution == 'COUNTRY' else \
                      ['US-CA', 'US-TX', 'US-NY', 'US-FL', 'US-IL', 'US-PA', 'US-OH', 'US-GA', 'US-NC', 'US-MI'] if resolution == 'REGION' else \
                      ['501', '803', '602', '504', '623', '807', '506', '524', '511', '618']
        
        data = []
        for i, region in enumerate(region_list):
            row = {'geoName': region, 'geoCode': region_codes[i]}
            for kw in keywords:
                row[kw] = random.uniform(0, 100)
            data.append(row)
            
        df = pd.DataFrame(data)
        df.set_index('geoName', inplace=True)
        return df
    except Exception as e:
        st.error(f"Error generating mock region data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_related_queries(keywords, timeframe, geo):
    """Generate mock related queries data"""
    if not keywords:
        return {}
    
    try:
        related_terms = {
            'doctor near me': ['best doctor near me', 'primary care doctor near me', 'walk in doctor near me', 'doctor open now'],
            'medical clinic': ['urgent care clinic', 'walk in clinic', 'free medical clinic', 'community health clinic'],
            'healthcare provider': ['healthcare provider network', 'healthcare provider lookup', 'healthcare provider number', 'find healthcare provider'],
            'physician': ['physician assistant', 'physician vs doctor', 'physician definition', 'physician salary']
        }
        
        result = {}
        for kw in keywords:
            if kw in related_terms:
                top_df = pd.DataFrame({
                    'query': related_terms[kw],
                    'value': [random.randint(50, 100) for _ in range(len(related_terms[kw]))]
                })
                rising_df = pd.DataFrame({
                    'query': [term + ' ' + random.choice(['2023', 'online', 'reviews', 'cost']) for term in related_terms[kw]],
                    'value': [random.choice(['Breakout', '+500%', '+400%', '+300%', '+200%']) for _ in range(len(related_terms[kw]))]
                })
                result[kw] = {'top': top_df, 'rising': rising_df}
            else:
                # Generate generic data for keywords not in our preset list
                terms = [kw + ' ' + term for term in ['near me', 'online', 'cost', 'reviews']]
                top_df = pd.DataFrame({
                    'query': terms,
                    'value': [random.randint(50, 100) for _ in range(len(terms))]
                })
                rising_df = pd.DataFrame({
                    'query': [term + ' ' + random.choice(['2023', 'best', 'cheap', 'local']) for term in terms],
                    'value': [random.choice(['Breakout', '+500%', '+400%', '+300%', '+200%']) for _ in range(len(terms))]
                })
                result[kw] = {'top': top_df, 'rising': rising_df}
                
        return result
    except Exception as e:
        st.error(f"Error generating mock related queries: {str(e)}")
        return {}

@st.cache_data(ttl=3600)
def get_trending_searches(geo="united_states"):
    """Generate mock trending searches"""
    try:
        trending_terms = [
            'covid booster shot', 'flu symptoms', 'telehealth appointment', 'mental health resources',
            'vaccine appointment', 'allergy symptoms', 'healthcare marketplace', 'best health insurance',
            'vitamin D deficiency', 'urgent care vs emergency room', 'medicare enrollment', 'healthcare app',
            'doctor reviews', 'telemedicine providers', 'health screening', 'wellness check', 
            'prescription delivery', 'health insurance quotes', 'medical second opinion', 'weight loss doctor'
        ]
        
        df = pd.DataFrame({0: trending_terms})
        return df
    except Exception as e:
        st.error(f"Error generating mock trending searches: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_interest_by_dma(keywords, timeframe, geo="US"):
    """Get interest by DMA (Designated Market Area)"""
    return get_interest_by_region(keywords, timeframe, geo, resolution='DMA')

def forecast_trends(df, keywords, days_to_forecast=90):
    """Simple forecasting using linear extrapolation"""
    if df.empty or len(df) < 10:
        return None
    
    try:
        import numpy as np
        
        forecast_start = df.index[-1] + timedelta(days=1)
        forecast_end = forecast_start + timedelta(days=days_to_forecast)
        forecast_dates = pd.date_range(start=forecast_start, end=forecast_end, freq='D')
        
        # Create a DataFrame to store forecasts
        forecast_df = pd.DataFrame(index=forecast_dates)
        
        for kw in keywords:
            if kw in df.columns:
                # Simple linear extrapolation
                values = df[kw].values
                last_value = values[-1]
                avg_change = np.mean(np.diff(values[-30:]) if len(values) > 30 else np.diff(values))
                
                # Generate forecast with some randomness
                forecast = []
                current = last_value
                for _ in range(len(forecast_dates)):
                    current += avg_change + random.uniform(-abs(avg_change)/2, abs(avg_change)/2)
                    # Keep within bounds
                    current = max(0, min(100, current))
                    forecast.append(current)
                
                # Add to forecast DataFrame
                forecast_df[kw] = forecast
        
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

# Add a note about mock data
st.info("⚠️ Using simulated data as a fallback since the Google Trends API is currently not responding. This data is for demonstration purposes only.")

st.header("Overview")

with st.spinner("Fetching data..."):
    interest_over_time_df = get_interest_over_time(keywords, timeframe_options[timeframe], geo)
    
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
        geo_data = get_interest_by_region(keywords, timeframe_options[timeframe], geo, resolution="REGION")
    elif geo.startswith("US-"):
        geo_data = get_interest_by_dma(keywords, timeframe_options[timeframe], geo="US")
    else:
        geo_data = get_interest_by_region(keywords, timeframe_options[timeframe], geo, resolution=geo_resolution)

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
st.markdown("Healthcare SEO & Trends Dashboard | Using Simulated Data")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Add an "About" expander at the bottom
with st.expander("About this dashboard"):
    st.markdown("""
    This dashboard uses simulated data to demonstrate how healthcare-related search trends would appear. In a production environment, this would use actual Google Trends data.
    
    **Note**: The data shown is simulated and does not represent actual Google Trends data.
    """)
