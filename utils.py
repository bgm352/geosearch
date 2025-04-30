# utils.py

import pandas as pd
from pytrends.request import TrendReq
import time
from sklearn.linear_model import LinearRegression
import numpy as np

def get_pytrends():
    return TrendReq(hl='en-US', tz=360)

def get_interest_over_time(keywords, timeframe, geo):
    if not keywords:
        return pd.DataFrame()
    pytrends = get_pytrends()
    # Google Trends allows max 5 keywords per request
    keywords = keywords[:5]
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if 'isPartial' in df.columns:
            df = df.drop(columns=['isPartial'])
        return df
    except Exception as e:
        print(f"Error in get_interest_over_time: {e}")
        return pd.DataFrame()

def get_interest_by_region(keywords, timeframe, geo, resolution='COUNTRY'):
    if not keywords:
        return pd.DataFrame()
    pytrends = get_pytrends()
    keywords = keywords[:5]
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True)
        return df
    except Exception as e:
        print(f"Error in get_interest_by_region: {e}")
        return pd.DataFrame()

def get_interest_by_dma(keywords, timeframe, geo):
    # For US only, we can get DMA level data, otherwise default to city
    resolution = 'DMA' if geo == 'US' else 'CITY'
    if not keywords:
        return pd.DataFrame()
    pytrends = get_pytrends()
    keywords = keywords[:5]
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True)
        return df
    except Exception as e:
        print(f"Error in get_interest_by_dma: {e}")
        return pd.DataFrame()

def get_related_queries(keywords, timeframe, geo):
    if not keywords:
        return None
    pytrends = get_pytrends()
    keywords = keywords[:5]
    try:
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        related = pytrends.related_queries()
        return related
    except Exception as e:
        print(f"Error in get_related_queries: {e}")
        return None

def get_trending_searches(geo='US'):
    pytrends = get_pytrends()
    try:
        if geo == 'US':
            trending = pytrends.trending_searches(pn='united_states')
        else:
            trending = pytrends.trending_searches(pn='united_states')
        trending.columns = ['query']
        trending['value'] = 100 - (trending.index * 5)
        return trending
    except Exception as e:
        print(f"Error in get_trending_searches: {e}")
        return pd.DataFrame()

def forecast_trends(historical_df, keywords, forecast_period=90):
    if historical_df.empty or not keywords:
        return None
    result_df = pd.DataFrame()
    future_dates = pd.date_range(
        start=historical_df.index[-1] + pd.Timedelta(days=1),
        periods=forecast_period,
        freq='D'
    )
    for kw in keywords:
        if kw in historical_df.columns:
            try:
                y = historical_df[kw].values
                X = np.array(range(len(y))).reshape(-1, 1)
                model = LinearRegression()
                model.fit(X, y)
                future_X = np.array(range(len(y), len(y) + forecast_period)).reshape(-1, 1)
                future_y = model.predict(future_X)
                if result_df.empty:
                    result_df = pd.DataFrame(index=future_dates)
                result_df[kw] = future_y
            except Exception as e:
                print(f"Error forecasting for {kw}: {e}")
    return result_df

