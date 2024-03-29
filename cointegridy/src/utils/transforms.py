"""
    A collection of transformation utility functions
"""

import numpy as np

#######################
## SERIES TRANSFORMS ##
#######################


def differentiate(series):
    series_d = series.diff()[1:]
    series_d.name = f'{series.name}_D'
    return series_d


def integrate(series):
    series_i = series.cumsum()
    series_i.name = f'{series.name}_I'
    return series_i


def daily_ret(series):
    series_dr = (series/series.shift(1) - 1)
    series_dr.name = f'{series.name}_DR'
    return series_dr


def cum_ret(series):
    series_cr = series/series.iloc[0] - 1
    series_cr.name = f'{series.name}_CR'
    return series_cr


def roll_avg(series, window):
    series_ma = series.rolling(window).mean()
    series_ma.fillna(method='bfill', inplace=True)
    series_ma.name = f'{series.name}_MA{window}'
    return series_ma
    
def sigmoid(x):
    return 1/(1 + np.exp(-1*x))
    
def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)
