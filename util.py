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




###############
## COINGECKO ##
###############

def id_to_tmsp_seq(cg, id, start_date, end_date):
    trg_tzobj = timezone.utc
    start_tmsp, end_tmsp = datetime.datetime(*start_date, tzinfo=trg_tzobj).timestamp(), datetime.datetime(*end_date, tzinfo=trg_tzobj).timestamp()
    return cg.get_coin_market_chart_range_by_id(id=id, vs_currency='usd', from_timestamp=start_tmsp, to_timestamp=end_tmsp)['prices']


def id_to_prices(cg, id, start_date, end_date):
    prices = id_to_tmsp_seq(cg, id, start_date, end_date)
    return np.array([price[1] for price in prices])


def id_to_df(cg, id, start_date, end_date, norm=True, plot=False):
    market = id_to_tmsp_seq(cg, id, start_date, end_date)
    tmsps, prices = list(zip(*market))
    
    df = pd.DataFrame(index=tmsps)
    
    df[id] = prices
    df.head()
    
    if norm:
        df = df/df.iloc[0]
    if plot:
        plot_df(df)
    return df


def create_portfolio_from_ids(cg, ids, start_date, end_date, norm_port=True):
    ref_id, asset_ids = ids[0], ids[1:]
    
    df = id_to_df(cg, ref_id, start_date, end_date)
    df.columns = [ref_id]
    
    for asset_id in asset_ids:
        new_df = id_to_df(cg, asset_id, start_date, end_date)
        new_df.columns = [asset_id]
        df = df.join(new_df)
        
    df = clean_df(df, df.columns[1:])
    ## Evaluate portfolio
    df['port_val'] = eval_port(df, norm=norm_port)
    return df


################
## TRANSFORMS ##
################

def differentiate(series):
    series_d = series.diff()[1:]
    series_d.name = f'{series.name}_D'
    return series_d


def integrate(series):
    series_i = series.cumsum()
    series_i.name = f'{series.name}_I'
    return series_i


def eval_port(df, norm=True):
    port = df.sum(axis=1)
    port.name = 'port_val'
    
    if norm:
        port = port/port.iloc[0]
    return port


def daily_ret(series):
    series_dr = (series/series.shift(1) - 1)
    series_dr.name = f'{series.name}_DR'
    return series_dr


def cum_ret(series):
    series_cr = series/series.iloc[0] - 1
    series_cr.name = f'{series.name}_CR'
    return series_cr


def take_roll_avg(series, window, plot=True):
    series_ma = series.rolling(window).mean()
    series_ma.fillna(method='bfill', inplace=True)
    series_ma.name = f'{series.name}_MA{window}'
    
    if plot:
        plot_series([series, series_ma], x_label='Time', y_label='Value', linestyles=[None, 'dashed'], colors=['b', 'r'], title=f"{series.name}+MA vs. Time")
    return series_ma


################
## STATISTICS ##
################

def take_mean(series, plot=True):
    s_m = series.mean()
    series_m = pd.Series(s_m, index=series.index)
    series_m.name = f'{series.name}_M'
    
    if plot:
        plot_series([series, series_m], x_label='Time', y_label='Value', linestyles=[None, 'dashed'], colors=['b', 'r'], title=f"{series.name}+Mean vs. Time")
    return s_m


def sharpe_ratio(series_dr):
    adr, sddr = series_dr.mean(), series_dr.std()

    sr = np.sqrt(252)*adr/sddr # we use risk-free rate = 0
    return sr


######################
## STATISTICS TESTS ##
######################

def test_stationarity(series, cutoff=0.01):
    # We must observe significant p-value to convince ourselves that the series is stationary
    pvalue = adfuller(series)[1]
    if pvalue < cutoff:
        print(f'p-value = {pvalue} The series {series.name} is likely stationary.')
        return True
    else:
        print(f'p-value = {pvalue} The series {series.name} is likely non-stationary.')
        return False
    
    
def is_coint(series_1, series_2):
    
    results = sm.OLS(series_2, series_1).fit()
    beta = results.params[series_1.name]

    Z = series_2 - beta * series_1

    is_stationary = test_stationarity(Z)
    
    if not is_stationary: return False
    
    if not is_stationary:
        return False
    else: ## cointegrate is series are not stationary
        return coint(series_1, series_2)


##############
## TIMEZONE ##
##############

def to_timezone(dtobj, trg_tz):
    trg_tzobj = trg_tz if type(trg_tz) is str else pytz.timezone(trg_tz)
    return dtobj.astimezone(trg_tzobj)


def from_tmsp(tmsp, trg_tz, short=False):
    trg_tzobj = trg_tz if type(trg_tz)!=str else pytz.timezone(trg_tz)
    if not type(tmsp) is int:
        tmsp = tmsp.timestamp()
    tmsp = tmsp/1000 if short else tmsp
    return datetime.datetime.fromtimestamp(tmsp, trg_tzobj)


def get_loc_time():
    return datetime.datetime.now()
def get_utc_time():
    return datetime.datetime.utcnow()


################
## GENERATORS ##
################

def series_to_df_feats(series, ma_lookbacks, plot=False):
    df = series.to_frame()
    
    for lookback_wind in ma_lookbacks:
        series_w = take_roll_avg(series, lookback_wind, plot=False)
        df = df.join(series_w.to_frame())
        
    df = df.join(cum_ret(series))
    df = df.join(daily_ret(series))
    
    if plot:
        plot_df(df[list(df.columns)[:len(ma_lookbacks)+1]], title=f'{series.name} MAs vs. Time')
    return df


##############
## PLOTTING ##
##############

def plot_df(df, x_label='Time', y_label='Value', title=None):
    plt.clf()
    plt.figure(figsize=(15,7))
    plt.plot(df)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(df.columns)
    plt.title(title)
    plt.show()
    

def plot_series(series_seq, x_label='Time', y_label='Value', linestyles=None, colors=None, title=None):
    working_series_seq = copy.deepcopy(series_seq)
    
    for series in working_series_seq:
        series.index = [from_tmsp(ind, timezone.utc, short=True) for ind in series.index]
    
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


#############
## UTILITY ##
#############

def clean_df(df, columns):
    for column in columns:
        df[column].fillna(method='ffill', inplace=True)
        df[column].fillna(method='bfill', inplace=True)
    return df


