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
import sys

# Custom Imports
from cointegridy.src.classes.processor import *
import cointegridy.src.utils.stats as stats
import cointegridy.src.utils.transforms as transforms

class Coin():

    def __init__(self, name):

        self.name_ = name
        self.is_good_ = None
        self.start_ = None
        self.end_ = None

    def is_good(self, prices, start, end):
        """
        Validity check: coin is I(1) during start:end
        
        Parameters:

        prices - timeseries data of coin price
        start - first datetime in prices
        end - last datetime in prices

        Assumptions:

        """

        coin_is_stationary = stats.is_stationary(prices)
        coin_returns = transforms.differentiate(prices)
        coin_returns_is_stationarity = stats.is_stationary(coin_returns)

        self.is_good_ = (not coin_is_stationary & coin_returns_is_stationarity)

        return self.is_good_

    def __lt__(self, other):
         return self.name_ < other.name_

    def __repr__(self):
        return "Coin: " + str(self.name_)

    def __str__(self):
        return "Coin: " + str(self.name_)