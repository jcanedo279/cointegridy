import numpy as np
import sys
import pandas as pd
# import backtester
import datetime
import matplotlib.pyplot as plt
from datetime import timezone
import copy

from bin import Statistics, Tests, Time, Transforms

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

    def roll_avg(self, window, plot=True):
        series_ma = Transforms.roll_avg(self.portfolio, window)

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
    

    ################
    ## GENERATORS ##
    ################

    @staticmethod
    def series_to_df_feats(series, ma_lookbacks, plot=False):
        """
            Extract a dataframe of moving fixed features from a timeseries
        """
        
        df = series.to_frame()

        for lookback_wind in ma_lookbacks:
            series_w = Transforms.roll_avg(series, lookback_wind)
            df = df.join(series_w.to_frame())

        df = df.join(Transforms.cum_ret(series))
        df = df.join(Transforms.daily_ret(series))

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
            series.index = [Time.from_tmsp(ind, timezone.utc, short=True) for ind in series.index]

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
        