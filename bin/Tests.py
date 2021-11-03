# import statsmodels.api as sm
# from statsmodels.tsa.stattools import coint, adfuller    

# def is_coint(series_1, series_2):
#     """
#         Perform Cointegrated Augmented Dickey-Fuller test.
        
#         1) Determine optimal hedge ratio between two stocks using Ordinary Least Squares regression.
        
#         2) Test for stationarity of residuals (Z)
        
#         2) a. If the random variable Z is stationary, then it is order 1 integrable
        
#         3) Check that 
        
#         https://towardsdatascience.com/constructing-cointegrated-cryptocurrency-portfolios-d0a27922891e
#         https://letianzj.github.io/cointegration-pairs-trading.html
#     """
#     results = sm.OLS(series_2, series_1).fit()
#     beta = results.params[series_1.name]

#     Z = series_2 - beta * series_1

#     is_stationary = is_stationary(Z)

#     if not is_stationary:
#         return False
    
#     return coint(series_1, series_2)
    
    