import numpy as np

"""
    A collection of statistical metrics
"""

def sharpe_ratio(series_dr):
    adr, sddr = series_dr.mean(), series_dr.std()

    sr = np.sqrt(252)*adr/sddr # we use risk-free rate = 0
    
    return sr

    