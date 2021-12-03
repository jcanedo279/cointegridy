"""
Basket Class:

This class represents a basket of crypto, it allows us to test for cointegration,
and other relevant performance metrics. This is the object we would trade in an
exchange. We feed the basket coins that we know are I(1), and check if resulting
basket is cointegrated. The basket class generates the regression coefficients
and contains its own trading strategy.

Attributes:

- coef_ represents the linear regression of our coins. This is the proportion we'd
use to buy our coins.

- coins_ array of coin names

- is_coint_ boolean

- intercept_ mean of basket spread, aka intercept of regression

- upper_band_ upper bollinger band

- lower_band_ lower bollinger band

- method_ either 'linear_regression' or 'ols'

Methods:

- is_stationary(series, pct='1%): tests the stationarity of the series, returns Boolean

- is_coint(self,): tests that 

# TODO: Should prices or residual data be stored in an attribute?
"""

import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

# Custom Imports
from data_loader import DataLoader
from coin import Coin
from ..utils import stats as stat


class Basket():

    def __init__(self, coins, target, dataloader, method='linear_regression'):

        self.coef_ = []
        self.coins_ = coins
        self.method_ = method
        self.target_ = target
        self.dataloader_ = dataloader
        self.is_coint_ = None
        self.intercept_ = None
        self.upper_band_ = None
        self.lower_band_ = None
        self.std_ = None
        self.prices_ = None
    
    def get_prices(self,start,end):
        '''
        Takes in start and end Time objects.

        Returns a pandas dataframe indexed by timestamps
        '''
        df = pd.DataFrame()
        
        for coin in self.coins_:
            df[coin.name_] = self.dataloader_[coin.name_.upper()  + 'USDT'][start:end]

        self.prices_ = df


    def fit(self, prices):
        """
        Returns coefficients and intercept of linear combination.
        
        Parameters:

        prices - timeseries df of coin prices

        Assumptions:

        - prices are normalized (?) # TODO: Is this valid?
        - coin prices are I(1)
        - y is target data # TODO: Ensure this with a test
        """

        y = prices[self.target_]
        X = prices.drop([self.target_], axis=1)

        if self.method_ == 'linear_regression':
            self.fit_linear_regression(X, y)
        elif self.method_ == 'ols':
            self.fit_ols(X, y)
        else:
            raise('Invalid method')

        print("Fitting", self.method_, "...")
        print("Found coefficients for basket: ", [1] + list(self.coef_))
        print("At intercept: ", self.intercept_)
        
        self.prices_['spread'] = self.prices_.dot(pd.Series(self.coef_))
        
        return self.coef_, self.intercept_
        
    def fit_linear_regression(self, X, y):
        lm = LinearRegression(copy_X=True)
        lm.fit(X, y)

        self.coef_ = lm.coef_
        self.intercept_ = lm.intercept_

    def fit_ols(self, X, y):
        
        X = sm.add_constant(X)
        ols = sm.OLS(y, X).fit()

        params = ols.params.values
        self.coef_ = params[1:]
        self.intercept_ = params[0] 

    def find_spread(self, prices):
        """
        Return the spread of our linear combination.

        Assumption:

        - Coefficient on target coin is 1
        - prices is price dataframe of coins_
        - Basket already ran fit() method
        """
        y = prices[self.target_]
        X = prices.drop([self.target_], axis=1)        

        spread = y - X.multiply(self.coef_).sum(axis=1)
        spread.name = 'Spread'

        self.std_ = spread.std()

        return spread
    
    def is_coint(self, spread, pct='1%'):
        """
        Check if resulting spread is stationary

        Assumption:

        - We already know individual coin data is I(1) so
        all we need to test is that spread is stationary
        """

        if not self.is_valid():
            raise("Basket is invalid, timeseries are not I(1)")

        return stats.is_stationary(spread, pct=pct)
    
    def is_valid(self):
        """
        Checks that coins in basket are valid, ie. I(1)
        """
        for coin in self.coins_:
            if coin.is_good_ != True:
                print("Basket is not valid. Found that the following coin is not I(1):", coin)
                return False
        
        print("Basket is valid, all coins are I(1).")
        return True

    def strat(self, spread, num_stds=1, plot=True):
        """
        USING BOLLINGER BANDS

        TODO: Should this be a property of basket or trader?

        Define bollinger band entry and exit points.
        """
        self.upper_band_ = self.intercept_ + num_stds * self.std_
        self.lower_band_ = self.intercept_ - num_stds * self.std_

        if plot:
            spread_mean = pd.Series(data=[self.intercept_]*len(spread), index=spread.index)
            upper_band = spread_mean + num_stds * self.std_
            lower_band = spread_mean - num_stds * self.std_
            self.processor_.plot_series([spread, spread_mean, upper_band, lower_band], \
                colors=['blue', 'red', 'green', 'green'])

        return self.upper_band_, self.lower_band_

    def __repr__(self):
        return "Basket:" + str(self.coins_)

    def __str__(self):
        return "Basket:" + str(self.coins_)


