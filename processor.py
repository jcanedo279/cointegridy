import numpy as np
import sys
import os
import pandas as pd
# import backtester
import datetime
from datetime import timezone
import matplotlib.pyplot as plt
from datetime import timezone
import copy
from urllib.parse import urljoin, urlencode
import requests
import math


from dotenv import load_dotenv

from bin import Statistics, Transforms

from bin.Time import Time

from pycoingecko import CoinGeckoAPI

from bin.util import BinanceException


ENV_PATH = '.env'

VALID_APIS = ['cg', 'ftx', 'bnc']

API_TO_ENV_VARS = {
    'bnc': {
        'label': 'BINANCE_KEY_LABEL',
        'api_key': 'BINANCE_API_KEY',
        'secret_key': 'BINANCE_PRIVATE_KEY'
        }
}

API_TO_ROUTES = {
    'bnc': {
        'base': 'https://api.binance.com',
        
        'ids': '/api/v3/exchangeInfo',
        'time': '/api/v3/time',
        
        'hist_data': '/api/v3/aggTrades'
    }
}

API_TO_HEADERS = {
    'bnc': lambda api_key: {'X-MBX-APIKEY': api_key}
}



class Processor:
    
    
    def __init__(self, api):
        
        assert api in VALID_APIS
        self.api = api
        
        load_dotenv()
        self.api_key_label = os.getenv(API_TO_ENV_VARS[api]['label'])
        self.api_key, self.secret_key = os.getenv(API_TO_ENV_VARS[api]['api_key']), os.getenv(API_TO_ENV_VARS[api]['secret_key'])
        
        
        self.routes = API_TO_ROUTES[api]
        self.api_headers = API_TO_HEADERS[api](self.api_key)
        
        self.base_url = self.routes['base']
        self.time_url = urljoin(self.base_url, self.routes['time'])
        self.hist_data_url = urljoin(self.base_url, self.routes['hist_data'])

        print(f'The epoch of the {self.api} processor is {Time.get_epoch()}')
        print(f'The latency of the {self.api} processor is {self.get_api_latency()}')
        
        # self.timeshift = self.get_api_timeshift()
        
    
    
    ##################
    ## API INTERACE ##
    ##################
    
    def get_request(self, url, params=None):
        r = requests.get(url, params=params)
        if r.status_code == 200:
            # print(json.dumps(r.json(), indent=2))
            data = r.json()
            return data
            
        elif self.api == 'bnc':
            raise BinanceException(status_code=r.status_code, data=r.json())
        
    
    ######################
    ## BUILTIN API UTIL ##
    ######################
        
    def get_api_ids(self):
        id_url = urljoin(self.base_url, self.routes['ids'])
        data = self.get_request(id_url, params=None)
        if self.api == 'bnc':
            return [asset['symbol'] for asset in data['symbols']]

    
    #######################
    ## BUILTIN TIME UTIL ##
    #######################
        
    def get_api_time(self):
        """
            Returns: the Posix timestamp (in UCT) of the API
        """
        data = self.get_request(self.time_url, params=None)
        return data['serverTime']/1000
    
    def get_api_latency(self):
        loc_tmsp, api_tmsp = Time.utcnow(), self.get_api_time()
        return api_tmsp - loc_tmsp
    
    
    ################################
    ## HISTORICAL DATA PROCESSORS ##
    ################################
    
    def id_to_hist_tmsp_seq(self, id, start_Time, end_Time, limit=None):
        """
            Returns: A list of (tmsp, price) pairs
        """
        sT_P, eT_P = start_Time.get_psx_tmsp(), end_Time.get_psx_tmsp()
        
        if self.api == 'bnc':
            
            params = {'symbol': id, 'startTime': int(sT_P)*1000, 'endTime': int(eT_P)*1000}
            if limit: params.update({'limit': limit})
            
            data = self.get_request(self.hist_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_hist_prices(self, id, start_Time, end_Time, limit=None):
        """
            Returns: A list of prices
        """
        return [price for _, price in self.id_to_hist_tmsp_seq(id, start_Time, end_Time, limit=limit)]


    #############################
    ## CURRENT DATA PROCESSORS ##
    #############################
    
    def id_to_curr_tmsp_seq(self, id, limit=None):
        """
            Returns: A list of (tmsp, price) pairs
        """
        params = {}
        if self.api == 'bnc':
            params = {'symbol': id, 'limit': limit} if limit else {'symbol': id}
            data = self.get_request(self.hist_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_curr_prices(self, id, limit=None):
        """
            Returns: A list of prices
        """
        return [price for _, price in self.id_to_curr_tmsp_seq(id, limit=limit)]

    
    
    
    
    ## TODO: FIX THESE

    @staticmethod
    def id_to_df(cg, idx, start_date, end_date, plot=False):
        market = CGProcessor.id_to_tmsp_seq(cg, idx, start_date, end_date)
        tmsps, prices = list(zip(*market))

        df = pd.DataFrame(index=tmsps)
    
        df[idx] = prices
        df.head()

        if plot:
            Processor.plot_df(df)
        
        return df
    
    def get_data(self, ids, start_date=None, end_date=None):
        """
            Returns: A DataFrame containing cleaned up historical prices
        """
        
        dfs = []
    
        for idx in ids:
            market_df = Processor.id_to_df(self.cg, idx, start_date, end_date)
            market_df.columns = [idx]
            dfs.append(market_df)

        df = dfs[0].join(dfs[1:], how='outer') # Use outer join to keep all available dates

        df.interpolate(limit_direction='both', inplace=True)

        self.data = df

        return df
    
    
    
    
    
    
    
    ## TODO: 
        
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
            Processor.plot_df(df)
        
        return df
    
    
    
    
    
    
    
    
    ################
    ## TRANSFORMS ##
    ################

    def roll_avg(self, window, plot=True):
        series_ma = Transforms.roll_avg(self.portfolio, window)

        if plot:
            Processor.plot_series([self.portfolio, series_ma], 
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
        series_m = pd.Series(series.mean(), index=series.index, name=f'{series.name}_M')

        if plot:
            Processor.plot_series([series, series_m],
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
            Processor.plot_df(df[list(df.columns)[:len(ma_lookbacks)+1]], title=f'{series.name} MAs vs. Time')
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


    