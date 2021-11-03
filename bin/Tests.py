import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller    

    
"""
    A collection of statistical test utility functions
"""
    
def test_stationarity(series, pct='1%'):
    # We must observe significant p-value to convince ourselves that the series is stationary
    results = adfuller(series, store=True, regresults=True)
    t_stat = results[0]

    try:
        cutoff = results[2][pct]
    except:
        raise('Pct must be 1%, 5%, or 10%, but was given: ', pct)
        
    confidence = str(100 - int(pct[:-1]))+'%'

    if t_stat < cutoff:
        print(f't-stat = {t_stat}: The series {series.name} is stationary with confidence level ', confidence)
        return True
    else:
        print(f't-stat = {t_stat} The series {series.name} is not stationary with confidence level ', confidence)
        return False


def is_coint(series_1, series_2):
    """
        Perform Cointegrated Augmented Dickey-Fuller test.
        
        1) Determine optimal hedge ratio between two stocks using Ordinary Least Squares regression.
        
        2) Test for stationarity of residuals (Z)
        
        2) a. If the random variable Z is stationary, then it is order 1 integrable
        
        3) Check that 
        
        https://towardsdatascience.com/constructing-cointegrated-cryptocurrency-portfolios-d0a27922891e
        https://letianzj.github.io/cointegration-pairs-trading.html
    """
    results = sm.OLS(series_2, series_1).fit()
    beta = results.params[series_1.name]

    Z = series_2 - beta * series_1

    is_stationary = test_stationarity(Z)

    if not is_stationary:
        return False
    
    return coint(series_1, series_2)
    
    