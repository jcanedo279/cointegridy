import sys
import numpy as np
import sys
import os
import pandas as pd
import datetime
from datetime import timezone
import matplotlib.pyplot as plt
from datetime import timezone
import copy
from urllib.parse import urljoin, urlencode
import requests
import math


from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
import math
# import backtester

# Custom imports
from .time import Time
from ..utils import stats, transforms

ENV_PATH = '.env'

VALID_APIS = ['cg', 'ftx', 'bnc', 'av']

API_TO_ENV_NAME = {
    'av': 'ALPHAVANTAGE',
    'bnc': 'BINANCE',
    'cg': 'COINGECKO'
}

MAX_USED_WEIGHT_1M = 1099

def api_to_env_names(api):
    assert api in API_TO_ENV_NAME
    name = API_TO_ENV_NAME[api]
    return f'{name}_KEY_LABEL', f'{name}_API_KEY', f'{name}_PRIVATE_KEY'


API_TO_ROUTES = {
    'av': {
        'base': 'https://www.alphavantage.co',
        
        'daily_data': '/query'
    },
    
    'bnc': {
        'base': 'https://api.binance.com',
        
        'ids': '/api/v3/exchangeInfo',
        'limits': '/api/v3/exchangeInfo',
        'time': '/api/v3/time',
        
        'hist_data': '/api/v3/aggTrades',
        'ohlc_data': '/api/v3/klines'
    },
    
    'cg': {
        'base': 'https://api.coingecko.com/api/v3',
        
        'ids': '/coins/list',
        
        'daily_data': lambda _id: f'/coins/{_id}/history'
        
    }
}

API_TO_HEADERS = {
    'av': lambda a: {},
    'bnc': lambda a: {'X-MBX-APIKEY': a},
    'cg': lambda a: {}
}

TIMED_APIS = {
    'bnc'
}

class Processor:
    
    
    def __init__(self, api):
        
        assert api in VALID_APIS
        self.api = api
        
        load_dotenv()
        akl, ak, pk = api_to_env_names(api)
        self.api_key_label, self.api_key, self.private_key = os.getenv(akl), os.getenv(ak), os.getenv(pk)
        
        self.lifetime_requests, self.next_available_tmsp = 0, 0
        
        self.routes = API_TO_ROUTES[api]
        self.api_headers = API_TO_HEADERS[api](self.api_key)
        
        self.base_url = self.routes['base']

        # if api in TIMED_APIS:
        #     print(f'The epoch of the {self.api} processor is {Time.get_epoch()}')
        #     print(f'The latency of the {self.api} processor is {self.get_api_latency()}')
        
        # self.timeshift = self.get_api_timeshift()
    
    
    ##################
    ## API INTERACE ##
    ##################
    
    def get_request(self, url, params=None, return_status=False, re_request=True, max_re_requests=7, re_request_sleep=10):
        
        cur_request = 0
        if not re_request: max_re_requests=1 
        data_out, status = {}, 666
        
        while cur_request<max_re_requests:
            cur_request += 1
            self.lifetime_requests += 1
            
            if Time.utcnow() < self.next_available_tmsp:
                if not re_request: break
                Time.sleep(re_request_sleep)
                continue
            
            r = requests.get(url, params=params)
            headers, status = r.headers, r.status_code
            
            # previous_weight = headers['x-mbx-used-weight']
            used_weight_1m = headers['x-mbx-used-weight-1m']
            # connection = headers['Connection']
            
            ### 418 -> IP BAN       429 -> RATE LIMIT VIOLATION
            if self.api=='bnc' and status in {418, 429}:
                retry_after = headers['Retry-After'] if status==429 else 60*60*24*3
                self.next_available_tmsp = Time.utcnow() + retry_after + 1
                if not re_request: break
                continue
            
            if status == 200:
                data_out = r.json()
                break
                
            elif self.api == 'bnc':
                raise BinanceException(status_code=status, data=r.json())
            
            if not re_request: break
        
        
        if return_status:
            return data_out, status
        return data_out
        
        
    
    
    ######################
    ## BUILTIN API UTIL ##
    ######################
        
    def get_api_ids(self):
        if self.api == 'bnc':
            id_url = urljoin(self.base_url, self.routes['ids'])
            data = self.get_request(id_url, params=None)
            return [asset['symbol'] for asset in data['symbols']]
        if self.api == 'cg':
            id_url = self.base_url+self.routes['ids']
            data = self.get_request(id_url, params=None)
            return [asset['id'] for asset in data]
        
    def get_api_limits(self, return_status=False):
        limits_url = self.base_url + self.routes['limits']
        response = self.get_request(limits_url, return_status=return_status)
        if return_status: return response[0]['rateLimits'], response[1]
        return response['rateLimits']

    
    #######################
    ## BUILTIN TIME UTIL ##
    #######################
        
    def get_api_time(self):
        """
            Returns: the Posix timestamp (in UCT) of the API
        """
        time_url = urljoin(self.base_url, self.routes['time'])
        data = self.get_request(time_url, params=None)
        return data['serverTime']/1000
    
    def get_api_latency(self):
        loc_tmsp, api_tmsp = Time.utcnow(), self.get_api_time()
        return api_tmsp - loc_tmsp
    
    
    ################################
    ## HISTORICAL DATA PROCESSORS ##
    ################################
    
    def id_to_hist_tmsp_seq(self, id, start_Time, end_Time, limit=1000):
        """
            Returns: A list of (tmsp, price) pairs
        """
        sT_P, eT_P = start_Time.get_psx_tmsp(), end_Time.get_psx_tmsp()
        
        if self.api == 'bnc':
            hist_data_url = urljoin(self.base_url, self.routes['hist_data'])
            
            params = {'symbol': id, 'startTime': int(sT_P)*1000, 'endTime': int(eT_P)*1000, 'limit': limit}
            
            data = self.get_request(hist_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_hist_prices(self, id, start_Time, end_Time, limit=1000):
        """
            Returns: A list of prices
        """
        return [price for _, price in self.id_to_hist_tmsp_seq(id, start_Time, end_Time, limit=limit)]


    ###########################
    ## DAILY DATA PROCESSORS ##
    ###########################

    def id_to_daily_seq(self, _id, start_date, end_date):
        """
            Takes: A crypto id, a start date and an end date
                        dates are in (YYYY,M,D) format
        """
        
        if self.api == 'cg':
            daily_url = self.base_url + self.routes['daily_data'](_id)
            
            daily_seq = []
            for date in Time.iter_date(start_date, end_date):
                data = self.get_request(daily_url, params={'date':date, 'localization':'false'})
                if not data: continue
                daily_seq.append((Time.date_to_Time(int(date[6:]), int(date[3:5]), int(date[:2])).get_psx_tmsp(), data["market_data"]['current_price']['usd']))
        
            return daily_seq


    #############################
    ## CURRENT DATA PROCESSORS ##
    #############################
    
    def id_to_curr_tmsp_seq(self, id, limit=1000):
        """
            Returns: A list of (tmsp, price) pairs
        """
        params = {}
        if self.api == 'bnc':
            curr_data_url = urljoin(self.base_url, self.routes['hist_data'])
            
            params = {'symbol': id, 'limit': limit}
            data = self.get_request(curr_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_curr_prices(self, id, limit=1000):
        """
            Returns: A list of prices
        """
        return [price for _, price in self.id_to_curr_tmsp_seq(id, limit=limit)]


    ##########################
    ## OHLC DATA PROCESSORS ##
    ##########################
    
    def id_to_ohlc_seq(self, id, start_Time, end_Time, tmsp_interval="10M", limit=1000):
        """
            tmsp_interval: int + {"S", "m", "h" "D"}
        """
        
        if self.api == 'bnc':
            ohlc_url = self.base_url + self.routes['ohlc_data']
            
            start_tmsp, end_tmsp = int(start_Time.get_psx_tmsp())*1000, int(end_Time.get_psx_tmsp())*1000
            
            params = {'symbol': id, 'startTime': start_tmsp, 'endTime': end_tmsp, 'interval':tmsp_interval, 'limit': limit}
            
            data = self.get_request(ohlc_url, params=params)
            
            output = [{'open_tmsp':float(d[0])/1000, 'open':float(d[1]), 'high':float(d[2]), 'low':float(d[3]), 'close':float(d[4]), 'vol':float(d[5]), 'close_tmsp':float(d[6])/1000} for d in data]
            
            return output
    
    
    
    
    
    
    ## TODO: FIX THESE

    @staticmethod
    def id_to_df(cg, idx, start_date, end_date, plot=False):
        market = cg.id_to_tmsp_seq(cg, idx, start_date, end_date)
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
            market_df = self.id_to_df(self.cg, idx, start_date, end_date)
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
            market_df = self.id_to_df(self.cg, idx, start_date, end_date)
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
    def id_to_prices(idx, start_date, end_date):
        prices = Processor.id_to_tmsp_seq(idx, start_date, end_date)
        
        return np.array([price[1] for price in prices])
    
    @staticmethod
    def id_to_df(cg, idx, start_date, end_date, plot=False):
        market = cg.id_to_tmsp_seq(cg, idx, start_date, end_date)
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
        series_ma = transforms.roll_avg(self.portfolio, window)

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
            series_w = transforms.roll_avg(series, lookback_wind)
            df = df.join(series_w.to_frame())

        df = df.join(transforms.cum_ret(series))
        df = df.join(transforms.daily_ret(series))

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



class BinanceException(Exception):
    def __init__(self, status_code, data):

        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        # Python 2.x
        # super(BinanceException, self).__init__(message)
        super().__init__(message)
