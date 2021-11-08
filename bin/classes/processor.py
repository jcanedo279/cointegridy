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

from datetime import date, timedelta


from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
import math
# import backtester

# Custom imports
print(sys.path)
from utils import stats, transforms
from utils.time import Time
from utils.util import BinanceException
sys.path.pop() 

ENV_PATH = '.env'

VALID_APIS = ['cg', 'ftx', 'bnc', 'av']

API_TO_ENV_NAME = {
    'av': 'ALPHAVANTAGE',
    'bnc': 'BINANCE',
    'cg': 'COINGECKO'
}

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
        
        
        self.routes = API_TO_ROUTES[api]
        self.api_headers = API_TO_HEADERS[api](self.api_key)
        
        self.base_url = self.routes['base']

        if api in TIMED_APIS:
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
        if self.api == 'bnc':
            id_url = urljoin(self.base_url, self.routes['ids'])
            data = self.get_request(id_url, params=None)
            return [asset['symbol'] for asset in data['symbols']]
        if self.api == 'cg':
            id_url = self.base_url+self.routes['ids']
            data = self.get_request(id_url, params=None)
            return [asset['id'] for asset in data]

    
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
    
    def id_to_hist_tmsp_seq(self, id, start_Time, end_Time, limit=None):
        """
            Returns: A list of (tmsp, price) pairs
        """
        sT_P, eT_P = start_Time.get_psx_tmsp(), end_Time.get_psx_tmsp()
        
        if self.api == 'bnc':
            hist_data_url = urljoin(self.base_url, self.routes['hist_data'])
            
            params = {'symbol': id, 'startTime': int(sT_P)*1000, 'endTime': int(eT_P)*1000, 'limit': 1000}
            if limit: params.update({'limit': limit})
            
            data = self.get_request(hist_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_hist_prices(self, id, start_Time, end_Time, limit=None):
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
            for date in Processor.iter_date(start_date, end_date):
                data = self.get_request(daily_url, params={'date':date, 'localization':'false'})
                if not data: continue
                daily_seq.append((Time.date_to_Time(int(date[6:]), int(date[3:5]), int(date[:2])).get_psx_tmsp(), data["market_data"]['current_price']['usd']))
        
            return daily_seq
    
    @staticmethod
    def iter_date(start_date, end_date):
        """
            start_date, end_date in (YYYY,M,D) format
        """
        
        def norm_date(d):
            return d if len(d)==2 else f'0{d}'
        
        s_y, s_m, s_d = [str(v) for v in start_date]
        e_y, e_m, e_d = [str(v) for v in end_date]
        
        s_m, s_d, e_m, e_d = norm_date(s_m), norm_date(s_d), norm_date(e_m), norm_date(e_d)
        
        start_date = date(int(s_y), int(s_m), int(s_d))
        end_date = date(int(e_y), int(e_m), int(e_d))
        delta = timedelta(days=1)
        
        while start_date <= end_date:
            s_d, s_m = f'{start_date.day}', f'{start_date.month}'
            yield f'{norm_date(s_d)}-{norm_date(s_m)}-{start_date.year}'
            start_date += delta


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
            
            params = {'symbol': id, 'limit': limit} if limit else {'symbol': id}
            data = self.get_request(curr_data_url, params=params)
            return [(float(datum['T'])/1000, float(datum['p'])) for datum in data]
        
    def id_to_curr_prices(self, id, limit=None):
        """
            Returns: A list of prices
        """
        return [price for _, price in self.id_to_curr_tmsp_seq(id, limit=limit)]
<<<<<<< HEAD:bin/classes/processor.py
=======


    ##########################
    ## OHLC DATA PROCESSORS ##
    ##########################
    
    def id_to_ohlc_seq(self, id, start_Time, end_Time, tmsp_interval="10M", limit=1000):
        """
            tmsp_interval: int + {"S", "M", "H" "D"}
        """
        
        if self.api == 'bnc':
            ohlc_url = self.base_url + self.routes['ohlc_data']
            
            start_tmsp, end_tmsp = int(start_Time.get_psx_tmsp())*1000, int(end_Time.get_psx_tmsp())*1000
            
            params = {'symbol': id, 'startTime': start_tmsp, 'endTime': end_tmsp, 'interval':'5m', 'limit': limit}
            
            data = self.get_request(ohlc_url, params=params)
            
            output = [{'open_tmsp':d[0], 'open':d[1], 'high':d[2], 'low':d[3], 'close':d[4], 'vol':d[5], 'close_tmsp':d[6]} for d in data]
            
            return output
    
    
    
    
    
    
>>>>>>> 775c9a225070ec93fa5bafca9fc9f6deb7365414:processor.py
    
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


    