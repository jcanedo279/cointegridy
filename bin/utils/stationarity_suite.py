import numpy as np
import pandas as pd
# import backtester
import datetime
import statsmodels
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller
import matplotlib.pyplot as plt
from datetime import timezone
import pytz
import copy

class Processor():

def stationarity_suite(series,pct='1%'):

    # Apply a range of stationarity tests to come up with a more complex picture of stationarity

    t_stat,_,cutoff = adfuller(series, store=True, regresults=True)

    #t_stat = adf[0]

    try:
        cutoff = adf[2][pct]
    except:
        raise('Pct must be 1%, 5%, or 10%, but was given: ', pct)
        
    confidence = str(100 - int(pct[:-1]))+'%'
    
    if t_stat < cutoff:
        print(f't-stat = {t_stat}: The series {series.name} is stationary with confidence level ', confidence)
        return True
    else:
        print(f't-stat = {t_stat} The series {series.name} is not stationary with confidence level ', confidence)
        return False
