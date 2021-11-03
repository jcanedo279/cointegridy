import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller    

"""
    A collection of statistical metrics
"""

def sharpe_ratio(series_dr):
    adr, sddr = series_dr.mean(), series_dr.std()

    sr = np.sqrt(252)*adr/sddr # we use risk-free rate = 0
    
    return sr

"""
    A collection of statistical test utility functions
"""
def is_stationary(series, pct='1%', verbose=False):
    # We must observe significant p-value to convince ourselves that the series is stationary
    results = adfuller(series, store=True, regresults=True)
    t_stat = results[0]

    try:
        cutoff = results[2][pct]
    except:
        raise('Pct must be 1%, 5%, or 10%, but was given: ', pct)
        
    confidence = str(100 - int(pct[:-1]))+'%'

    if t_stat < cutoff:
        printif(verbose, 'ft-stat = ' + str(t_stat) +'}: The series ' + str(series.name) + 'is stationary with confidence level' + str(confidence))
        return True
    else:
        printif(verbose, 'ft-stat = ' + str(t_stat) +'}: The series ' + str(series.name) + 'is NOT stationary with confidence level' + str(confidence))
        return False

def printif(verbose, obj):
    if verbose:
        print(obj)
