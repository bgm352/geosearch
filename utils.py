import pandas as pd
import numpy as np
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import time
from sklearn.linear_model import LinearRegression

# Initialize PyTrends
def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

# Get interest over time for keywords
def get_interest_over_time(keywords, timeframe, geo):
    if not keywords:
        return pd.DataFrame()
    
    # Break the request into smaller chunks if there are more than 5 keywords
    # because Google Trends only allows 5 keywords per request
    chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
    result_df = pd.DataFrame()
    
    pytrends = get_pytrends()
    
    for chunk in chunks:
        try:
            pytrends.build_payload(chunk, cat=0, timeframe=timeframe, geo=geo)
            interest_over_time_df = pytrends.interest_over_time()
            
            # If this is the first chunk, use it as the base
            if result_df.empty:
                result_df = interest_over_time_df.drop(columns=['isPartial'])
            else:
                # For subsequent chunks, join with the existing data
                temp_df = interest_over_time_df.drop(columns=['isPartial'])
                result_df = result_df.join(temp_df)
            
            # Wait to avoid hitting rate limits
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching interest over time for {chunk}: {e}")
    
    return result_df

# Get interest by region for keywords
def get_interest_by_region(keywords, timeframe, geo, resolution='COUNTRY'):
    if not keywords:
        return pd.DataFrame()
    
    pytrends = get_pytrends()
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        interest_by_region_df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True)
        return interest_by_region_df
    except Exception as e:
        print(f"Error fetching interest by region: {e}")
        return pd.DataFrame()

# Get interest by city/DMA (Designated Market Area)
def get_interest_by_dma(keywords, timeframe, geo):
    # For US only, we can get DMA level data, otherwise default to city
    resolution = 'DMA_CODE' if geo == 'US' else 'CITY'
    
    if not keywords:
        return pd.DataFrame()
    
    pytrends = get_pytrends()
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        interest_by_dma_df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True)
        return interest_by_dma_df
    except Exception as e:
        print(f"Error fetching interest by DMA: {e}")
        return pd.DataFrame()

# Get related queries for keywords
def get_related_queries(keywords, timeframe, geo):
    if not keywords:
        return None
    
    pytrends = get_pytrends()
    
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        related_queries = pytrends.related_queries()
        return related_queries
    except Exception as e:
        print(f"Error fetching related queries: {e}")
        return None

# Get trending searches
def get_trending_searches(geo='US'):
    pytrends = get_pytrends()
    
    try:
        if geo == 'US':
            trending_searches = pytrends.trending_searches(pn='united_states')
        else:
            # Default to US if location not supported
            trending_searches = pytrends.trending_searches(pn='united_states')
        
        # Format the data
        trending_searches.columns = ['query']
        trending_searches['value'] = 100 - (trending_searches.index * 5)  # Create a decreasing value for visualization
        
        return trending_searches
    except Exception as e:
        print(f"Error fetching trending searches: {e}")
        return None

# Forecast trends using simple linear regression
def forecast_trends(historical_df, keywords, forecast_period=90):
    if historical_df.empty or not keywords:
        return None
    
    result_df = pd.DataFrame()
    future_dates = pd.date_range(
        start=historical_df.index[-1] + timedelta(days=1),
        periods=forecast_period,
        freq='D'
    )
    
    for kw in keywords:
        if kw in historical_df.columns:
            try:
                # Prepare data for linear regression
                y = historical_df[kw].values
                X = np.array(range(len(y))).reshape(-1, 1)
                
                # Fit the model
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict future values
                future_X = np.array(range(len(y), len(y) + forecast_period)).reshape(-1, 1)
                future_y = model.predict(future_X)
                
                # Add to results dataframe
                if result_df.empty:
                    result_df = pd.DataFrame(index=future_dates)
                
                result_df[kw] = future_y
            except Exception as e:
                print(f"Error forecasting for {kw}: {e}")
    
    return result_df
