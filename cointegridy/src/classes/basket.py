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
from cointegridy.src.classes.processor import Processor
from cointegridy.src.classes.coin import Coin
from cointegridy.src.classes.Time import Time
from cointegridy.src.utils import stats as stats
from cointegridy.src.classes.exceptions import *


class Basket():

    def __init__(self, coins, target, method='linear_regression',report=False):

        self.coef_ = []
        self.coins_ = coins
        self.method_ = method
        self.target_ = target
        #self.dataloader_ = dataloader
        self.is_coint_ = None
        self.intercept_ = None
        self.upper_band_ = None
        self.lower_band_ = None
        self.std_ = None
        self.prices_ = None
        self.report = report
    
    def load_prices(self,start,end,interval,denom='USD'):
        
        '''
        Takes in start and end Time objects.

        Returns a pandas dataframe of close prices indexed by timestamps

        Note that OHLCV data is not supported for the kind of analysis that we want to do,

        but CCXT only returns data in that format. 
        '''
        pc = Processor()

        df = pd.DataFrame()

        for coin in self.coins_:
            
            intermed = pd.DataFrame(pc.symbol_to_ohlc_seq(coin.name_,start,end,interval_flag='6h'),\
                columns=['TMSP','Open', 'High', 'Low', coin.name_, 'Volume']).set_index('TMSP')
            intermed = intermed.drop(columns=['Open','High','Low','Volume'])

            if not intermed[coin.name_].all:
                print('Warning: no data exists for coin in specified date range.')
            if df.empty:
                df = intermed
            else:
                df = df.join(intermed,on='TMSP')
            

        self.prices_ = df


        '''
        //TODO: add this code back in when issues with TreeLoader are resolved
        # This code uses Jorge's slicetree dataloader. It doesn't work right now so I'm using processor

        data = {(coin.name_,denom): [(start,end,interval,'v1')] for coin in self.coins_}
        data_loader = TreeLoader(data,mode='df')

        self.data_loader = data_loader
        self.prices_ = data_loader[:][:]'''


    def fit(self):
        """
        Returns coefficients and intercept of linear combination.
        
        Parameters:

        prices - timeseries df of coin prices

        Assumptions:

        - prices are normalized (?) # TODO: Is this valid?
        - coin prices are I(1)
        - y is target data # TODO: Ensure this with a test
        """

        y = self.prices_[repr(self.target_)]
        X = self.prices_.drop([repr(self.target_)], axis=1)

        if self.method_ == 'linear_regression':
            self.fit_linear_regression(X, y)
        elif self.method_ == 'ols':
            self.fit_ols(X, y)
        else:
            raise invalidMethod()
        
        #weights = pd.DataFrame([1] + list(self.coef_))
        if self.report:
            print("Fitting", self.method_, "...")
            print("Found coefficients for basket: ", [1] + list(self.coef_))
            print("At intercept: ", self.intercept_)

        #print(pd.Series([1] + list(self.coef_)))
        #self.prices_['Spread'] = self.prices_[repr(self.target_)] - self.prices_.drop(repr(self.target_)).dot(pd.Series(list(self.coef_)))
        #print(f'Prices: {self.prices_.shape}, Weights: {weights.shape}')
        #print(weights)

        #self.prices_['Spread'] = self.prices_.dot(weights.to_numpy())
        
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

    def find_spread(self):
        """
        Return the spread of our linear combination.

        Assumption:

        - Coefficient on target coin is 1
        - prices is price dataframe of coins_
        - Basket already ran fit() method
        """
        y = self.prices_[repr(self.target_)]
        X = self.prices_.drop([repr(self.target_)], axis=1)        

        spread = y - X.multiply(self.coef_).sum(axis=1)
        self.prices_['Spread'] = spread

        #spread.name = 'Spread'

        self.std_ = spread.std()

        return spread
    
    def is_coint(self, pct='1%'):
        """
        Check if resulting spread is stationary

        Assumption:

        - We already know individual coin data is I(1) so
        all we need to test is that spread is stationary
        """

        if not self.is_valid():
            
            #raise("Basket is invalid, timeseries are not I(1)")
            # This would make the program terminate. We probably  don't want to do this
            # because this would make it hard to search and sort baskets without exception handling.
            # Might as well return false here.
            if self.report:
                print("Basket is invalid, timeseries are not I(1)")
            return False

        return stats.is_stationary(self.prices_['Spread'], pct=pct)
    
    def is_valid(self):
        """
        Checks that coins in basket are valid, ie. I(1)
        """
        for coin in self.coins_:
            if not coin.is_good_:
                if self.report:
                    print("Basket is not valid. Found that the following coin is not I(1):", coin)
                return False
        if self.report:
            print("Basket is valid, all coins are I(1).")
        return True

    def strat(self, spread, num_stds=1, plot=False):
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

    def setup(self):
        '''
        Completely prepare the basket for use in backtesting. This entails fitting coefficients, 
        finding the spread, and finding bollinger bands to trade strategy 1. 
        '''

        self.fit()
        self.find_spread()
        return self.is_coint()


    def __repr__(self):
        return "Basket:" + str(self.coins_)

    def __str__(self):
        return "Basket:" + str(self.coins_)


if __name__ == "__main__":
    

    start_date, end_date = (2021,5,1), (2021,6,1)

    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    coins = [Coin('LTC'),Coin('ETH'),Coin('ADA'),Coin('LINK')]

    basket1 = Basket(coins,coins[0],report='True')

    print(basket1)

    basket1.load_prices(start_Time, end_Time,'1h')

    basket1.fit()
    basket1.find_spread()
    print(basket1.is_coint())
    print(basket1.prices_)

    basket2 = Basket(coins,coins[0])

    print(basket1)

    basket2.load_prices(start_Time, end_Time,'1h')
    basket2.setup()
    print(basket2.prices_)
    

