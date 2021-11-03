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

from pycoingecko import CoinGeckoAPI

class CGProcessor:
    
    
    def __init__(self):
        
        self.cg = CoinGeckoAPI()
        
        
    def create_portfolio(self, ids, start_date, end_date):
        
        self.get_data(ids, start_date, end_date)
        
        port = self.data.sum(axis=1)
        
        self.portfolio = port

        return port
    
    def get_data(self, ids, start_date, end_date):
        
        dfs = []
    
        for idx in ids:
            market_df = CGProcessor.id_to_df(self.cg, idx, start_date, end_date)
            market_df.columns = [idx]
            dfs.append(market_df)

        df = dfs[0].join(dfs[1:], how='outer') # Use outer join to keep all available dates

        df.interpolate(limit_direction='both', inplace=True)

        self.data = df

        return df
        
    def normalize(self, cols, port=False): 
        
        for col in cols:
            self.data[col] /= self.data[col].iloc[0]
        
        if port:
            self.portfolio /= self.portfolio.iloc[0]
            
    ###############
    ## COINGECKO ##
    ###############
    
    @staticmethod
    def id_to_tmsp_seq(cg, idx, start_date, end_date):
        trg_tzobj  = timezone.utc
        start_tmsp = datetime.datetime(*start_date, tzinfo=trg_tzobj).timestamp()
        end_tmsp   = datetime.datetime(*end_date, tzinfo=trg_tzobj).timestamp()
        
        return cg.get_coin_market_chart_range_by_id(id=idx, 
                                                    vs_currency='usd', 
                                                    from_timestamp=start_tmsp, 
                                                    to_timestamp=end_tmsp)['prices']
    
    @staticmethod
    def id_to_prices(cg, idx, start_date, end_date):
        prices = CGProcessor.id_to_tmsp_seq(cg, idx, start_date, end_date)
        
        return np.array([price[1] for price in prices])
    
    @staticmethod
    def id_to_df(cg, idx, start_date, end_date, plot=False):
        market = CGProcessor.id_to_tmsp_seq(cg, idx, start_date, end_date)
        tmsps, prices = list(zip(*market))

        df = pd.DataFrame(index=tmsps)
    
        df[idx] = prices
        df.head()

        if plot:
            CGProcessor.plot_df(df)
        
        return df
    
    ################
    ## TRANSFORMS ##
    ################

    @staticmethod
    def differentiate(series):
        series_d = series.diff()[1:]
        series_d.name = f'{series.name}_D'
        return series_d

    @staticmethod
    def integrate(series):
        series_i = series.cumsum()
        series_i.name = f'{series.name}_I'
        return series_i

    @staticmethod
    def daily_ret(series):
        series_dr = (series/series.shift(1) - 1)
        series_dr.name = f'{series.name}_DR'
        return series_dr

    @staticmethod
    def cum_ret(series):
        series_cr = series/series.iloc[0] - 1
        series_cr.name = f'{series.name}_CR'
        return series_cr

    def take_roll_avg(self, window, plot=True):
        series_ma = self.portfolio.rolling(window).mean()
        series_ma.fillna(method='bfill', inplace=True)
        series_ma.name = f'{self.portfolio.name}_MA{window}'

        if plot:
            CGProcessor.plot_series([self.portfolio, series_ma], 
                             x_label='Time', 
                             y_label='Value', 
                             linestyles=[None, 'dashed'], 
                             colors=['b', 'r'], 
                             title=f"{self.portfolio.name}+MA vs. Time")
            
        self.series_ma = series_ma
        
        return series_ma

    ################
    ## STATISTICS ##
    ################

    @staticmethod
    def take_mean(series, plot=True):
        s_m = series.mean()
        series_m = pd.Series(s_m, index=series.index, name=f'{series.name}_M')

        if plot:
            CGProcessor.plot_series([series, series_m],
                        x_label='Time', 
                        y_label='Value', 
                        linestyles=[None, 'dashed'], 
                        colors=['b', 'r'], 
                        title=f"{series.name}+Mean vs. Time")
            
        return s_m

    @staticmethod
    def sharpe_ratio(series_dr):
        adr, sddr = series_dr.mean(), series_dr.std()

        sr = np.sqrt(252)*adr/sddr # we use risk-free rate = 0
        
        return sr

    ######################
    ## STATISTICS TESTS ##
    ######################

    @staticmethod
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

    @staticmethod
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

        is_stationary = CGProcessor.test_stationarity(Z)

        if not is_stationary:
            return False
        
        return coint(series_1, series_2)


    ##############
    ## TIMEZONE ##
    ##############

    @staticmethod
    def to_timezone(dtobj, trg_tz):
        trg_tzobj = trg_tz if type(trg_tz) is str else pytz.timezone(trg_tz)
        return dtobj.astimezone(trg_tzobj)


    @staticmethod
    def from_tmsp(tmsp, trg_tz, short=False):
        trg_tzobj = trg_tz if type(trg_tz)!=str else pytz.timezone(trg_tz)
        if not type(tmsp) is int: tmsp = tmsp.timestamp()
        tmsp = tmsp/1000 if short else tmsp
        return datetime.datetime.fromtimestamp(tmsp, trg_tzobj)

    @staticmethod
    def get_loc_time():
        return datetime.datetime.now()

    @staticmethod
    def get_utc_time():
        return datetime.datetime.utcnow()

    ################
    ## GENERATORS ##
    ################

    @staticmethod
    def series_to_moving_feats(series, ma_lookbacks, plot=False):
        """
            Extract a dataframe of moving fixed features from a timeseries
        """
        
        df = series.to_frame()

        for lookback_wind in ma_lookbacks:
            series_w = CGProcessor.take_roll_avg(series, lookback_wind, plot=False)
            df = df.join(series_w.to_frame())

        df = df.join(CGProcessor.cum_ret(series))
        df = df.join(CGProcessor.daily_ret(series))

        if plot:
            CGProcessor.plot_df(df[list(df.columns)[:len(ma_lookbacks)+1]], title=f'{series.name} MAs vs. Time')
        return df

    ##############
    ## PLOTTING ##
    ##############

    @staticmethod
    def plot_df(df, x_label='Time', y_label='Value', title=None):
        plt.clf()
        plt.figure(figsize=(15,7))
        plt.plot(df)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend(df.columns)
        plt.title(title)
        plt.show()


    @staticmethod
    def plot_series(series_seq, x_label='Time', y_label='Value', linestyles=None, colors=None, title=None):
        working_series_seq = copy.deepcopy(series_seq)

        for series in working_series_seq:
            series.index = [CGProcessor.from_tmsp(ind, timezone.utc, short=True) for ind in series.index]

        plt.clf()
        plt.figure(figsize=(15,7))

        if linestyles==None:
            linestyles = ['-']*len(working_series_seq)
        if colors==None:
            colors = ['b']*len(working_series_seq)

        for series, linestyle, color in zip(working_series_seq, linestyles, colors):
            plt.plot(series, linestyle=linestyle, color=color)

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.xlim(min([series.index[0] for series in working_series_seq]) , max([series.index[-1] for series in working_series_seq]))
        plt.legend([series.name for series in working_series_seq])
        plt.title(title)
        plt.show()
        