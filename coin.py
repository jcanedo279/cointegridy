"""
Coin Class:

This class a coin, it keeps track of if a coin is I(1) and might be useful for
other methods.

Attributes:

- name_ name of coin on exchange

- is_good_ boolean, is the coin I(1)

- start_ first timestep considered in lookback window

- end_ last timestep considered in lookback window

Methods:

- is_good(price, pct='1%): tests that prices are non-stationary, and derivatives are.

# TODO: Should prices or residual data be stored in an attribute?
"""

import pandas as pd
import numpy as np

from processing import *

class Coin():

    def __init__(self, name, processor):

        self.name_ = name
        self.is_good_ = None
        self.start_ = None
        self.end_ = None
        self.processor = processor

    def is_good(self, prices, start, end):
        """
        Returns coefficients and intercept of linear combination.
        
        Parameters:

        prices - timeseries data of coin price

        Assumptions:

        """

        coin_is_stationary = self.processor.is_stationary(prices)
        coin_returns = self.processor.differentiate(prices)
        coin_returns_is_stationarity = self.processor.is_stationary(coin_returns)

        self.is_good_ = (not coin_is_stationary & coin_returns_is_stationarity)

        return self.is_good_