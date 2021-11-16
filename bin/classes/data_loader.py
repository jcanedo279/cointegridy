import csv
import os
from datetime import datetime
from typing import Generator

import pandas as pd
import requests
from numpy import float64

from processor import Processor
from time import time
from ..utils.stats import sharpe_ratio


TXT_DEL=' '
CSV_DEL=','

HISOTICAL_DATA_PATH = 'data/historical_data'
DATABASE_PATH = 'data/database.csv'
METADATA_PATH = f'{HISOTICAL_DATA_PATH}/_metadata.txt'
SR_PATH = 'data/_sharpe_ratios.txt'
# DB_PATH = 'data/_cryptos_bnc.txt'


INT_TO_MULTIPLIER = {
    'm': 60,
    'h': 60*60,
    'd': 60*60*24,
    'w': 60*60*24*7,
    'M': 60*60*24*7*4
}





def parse_interval(interval):
    
    last_char = 0
    for _char in interval:
        if _char.isnumeric(): last_char += 1
        
    return int(interval[:last_char]) * INT_TO_MULTIPLIER[interval[last_char:]]



def pull_sharpe_ratios(start_Time=Time.date_to_Time(2021,1,1), end_Time=Time.date_to_Time(2021,11,1), interval_flag='5m', bnc_ids=None):
    """
        SR_PATH delimetered as [id, id_ind (assumes same bnc_ids), sharpe_ratio]
    """
    
    pc_bnc = Processor('bnc')
    if not bnc_ids:
        bnc_ids = pc_bnc.get_api_ids()
        
    with open(METADATA_PATH, "w") as f_writer:
        f_writer.write(TXT_DEL.join(bnc_ids))
        
    final_id_ind = -1
    if os.path.exists(SR_PATH):
        lines = None
        with open(SR_PATH, 'r') as f_reader:
            lines = f_reader.readlines()
        if lines:
            final_id_ind = int(lines[-1].split(CSV_DEL))[1]
    
    num_ids = len(bnc_ids)
    with open(SR_PATH, 'w+', newline ='') as f_writer:
        writer = csv.writer(f_writer)
        
        for id_num, id in enumerate(bnc_ids[final_id_ind+1:]):
            id_num_P = id_num + final_id_ind
            print(f'FETCHING     ID  [ {id_num_P+1} | {num_ids} ]     PULLING DATA FOR  {id}\t\r', end='')
            
            id_response = pc_bnc.id_to_ohlc_seq(id, start_Time, end_Time, interval_flag=interval_flag)
            open_ser = pd.Series([float(datum['open']) for datum in id_response], name=f'{id}', dtype=float64)
            open_sr = sharpe_ratio(open_ser)
            writer.writerow([id, id_num_P, open_sr])



def get_best_stocks_from_CSV(file_path, _del, num_symbols):
    """
        file_path: the path to a CSV file with columns: [id, id_index, id_sharpe_ratio]
        _del: CSV file delimiter
        num_symbols: the number of stocks to pick
    """
    
    lines = None
    with open(file_path, 'r') as f_reader:
        lines = f_reader.readlines()
        
    normed_lines = []
    for l in lines:
        l = l[:-1] if l.endswith('\n') else l
        l_n = l.split(_del)
        if l_n[0]=='BTCUSDT' or l_n[2]=='nan': continue
        normed_lines.append((l_n[0], int(l_n[1]), float(l_n[2])))
    
    sorted_normed_lines = sorted(normed_lines, key=lambda x: x[2])
    
    best_lines = sorted_normed_lines[max(-num_symbols+1, -len(sorted_normed_lines)):]
    
    return ['BTCUSDT'] + [line[0] for line in best_lines]
    
    
            

            



def pull_data(start_Time=Time.date_to_Time(2021,1,1), end_Time=Time.date_to_Time(2021,11,1), interval_flag='5m', bnc_ids=None):
    
    """
        1 day ~ 289 5 minute intervals   -->   1 year ~ 105,485 lines
        
        20 lines ~ 6.3 MB   -->   105,485 lines ~ 34 GB
        
        1 day ~ 5 minutes to compute   -->   11 months ~ 27.5 hrs to compute
    """
    
    interval = parse_interval(interval_flag)
    
    pc_bnc = Processor('bnc')
    if not bnc_ids:
        bnc_ids = pc_bnc.get_api_ids()
    
    
    with open(METADATA_PATH, "w") as f_writer:
        f_writer.write(TXT_DEL.join(bnc_ids))
    

    num_ids = len(bnc_ids)
    
    STEPS = 499
        
    for id_num, id in enumerate(bnc_ids):
        id_path = f'{HISOTICAL_DATA_PATH}/{id.upper()}.csv'
        
        with open(id_path, 'w+', newline ='') as f_writer:
            writer = csv.writer(f_writer)
            
            start_Time_P = start_Time
            if os.path.exists(id_path):
                lines = None
                with open(id_path, 'r') as f_reader:
                    lines = f_reader.readlines()
                if lines:
                    final_tmsp = float(lines[-1].split(CSV_DEL)[0])
                    start_Time_P = Time(utc_tmsp=final_tmsp)
        
            window_interval = STEPS * interval
            for iter_Time in Time.iter_Time(start_Time_P, end_Time, sec_interval=window_interval, conv=True):
                print(f'PROCESSING     ID  {id}  [ {id_num+1} | {num_ids} ]     DAY  [ {iter_Time} | {end_Time} ]\t\r', end='')
                
                cutoff_Time = iter_Time.add_seconds_from_Time(iter_Time, window_interval)
                id_response = pc_bnc.id_to_ohlc_seq(id, iter_Time, cutoff_Time, interval_flag=interval_flag)
                
                writer.writerows([[d['open_tmsp'], d['open']] for d in id_response])
                
                



def get_data():
    """
        Returns: A DataFrame where the index are timestamps and the columns are the open prices of each id
    """
    df = pd.DataFrame()
    
    ids = None
    with open(METADATA_PATH, "r") as f_reader:
        ids = f_reader.read().split(TXT_DEL)
    
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r') as f_reader:
            lines = csv.reader(f_reader)
            formed_line = next(lines, None)
            df = pd.DataFrame([[float(v) for v in formed_line[1:]]], columns=ids, index=[int(formed_line[0])])
            for line in lines:
                formed_line = line
                df = pd.concat([pd.DataFrame([[float(v) for v in formed_line[1:]]], columns=df.columns, index=[int(formed_line[0])]), df])
    
    return df



def load_custom_ids(db_path, interval_flag="12H"):
    
    start_date, end_date = (2021,1,1), (2021,2,1)
    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    
    baseAssets = None
    with open(db_path, 'r') as f_reader:
        baseAssets = f_reader.read().split(TXT_DEL)
    print(f'{len(baseAssets)} assets loaded from file')
    
    r = requests.get('https://api.binance.com/api/v3/exchangeInfo', params=None)
    data = r.json()['symbols']
    baseAsset_to_symbol = {datum['baseAsset']:datum['symbol'] for datum in data}
    print(data[0])
    
    existent_symbols = set()
    for baseAsset in baseAssets:
        if baseAsset.upper() in baseAsset_to_symbol:
            existent_symbols.add(baseAsset_to_symbol[baseAsset.upper()])
            
            
    pc = Processor('bnc')
    yikes, yikes_set = 0, set()
    for symbol in existent_symbols:
        try:
            pc.id_to_ohlc_seq(symbol.upper(), start_Time, end_Time, interval_flag=interval_flag)
        except:
            yikes += 1
            yikes_set.add(symbol)
    
    print(f'Yikes: {yikes}    out of    {len(baseAssets)}')
    print(yikes_set)
    
    return existent_symbols




def binary_search_tmsp(csv_lines, tmsp):
    low = 0
    high = len(csv_lines) - 1

    while low <= high:
        
        mid = (high + low) // 2
        csv_line = csv_lines[mid].split(CSV_DEL)
        _tmsp = float(csv_line[0])

        if _tmsp < tmsp:
            low = mid+1
        elif _tmsp > tmsp:
            high = mid-1
        else:
            return mid

    return min(mid+1, len(csv_lines)-1)




class SymbolLoader:
    
    """
        Acts as a wrapper to grab data timestamp data as a class item
    """
    
    def __init__(self, _id):
        self.id = _id
        self.data_path = f'data/historical_data/{_id.upper()}.csv'
    
    def __getitem__(self, _slice: slice) -> Generator:
        assert isinstance(_slice, slice)
        start, stop, interval = _slice.start, _slice.stop, _slice.step
        
        
        if isinstance(start, Time):
            start = start.get_psx_tmsp()
        if isinstance(stop, Time):
            stop = stop.get_psx_tmsp()
            
        
        if os.path.exists(self.data_path):
            
            lines = None
            with open(self.data_path, 'r') as f_reader:
                lines = f_reader.readlines()
            
            if lines:
                start_ind, stop_ind = binary_search_tmsp(lines, start), binary_search_tmsp(lines, stop)
                ## TODO: ADD STEP SIZE TO DENOTE INTERVAL SOMEHOW ????
                for line in lines[start_ind:stop_ind]:
                    split = line.split(CSV_DEL)
                    yield (float(split[0]), float(split[1]))
                
            else:
                print(f'No data located inside {self.data_path}')
                
        else:
            print(f'No data file {self.data_path} located')
        
    

class DataLoader:
    
    def __init__(self):
        pass
    
    
    def __getitem__(self, _id: str ) -> SymbolLoader:
        assert isinstance(_id,str)
        
        id_loader = SymbolLoader(_id)
        return id_loader


    




if __name__=='__main__':
    
    VALID_INTERVALS = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
    
    interval_flag = '5m'
    
    
    ## UNCOMMENT TO UPDATE SHARPE RATIOS
    # pull_sharpe_ratios(start_Time=start_Time, end_Time=end_Time, interval_flag=interval_flag)
    
    
    # num_symbols = 100
    # crypto_ids = get_best_stocks_from_CSV(SR_PATH, CSV_DEL, num_symbols)
    
    
    ## UNCOMMENT TO UPDATE HISTORICAL DATA
    # pull_data(start_Time=start_Time, end_Time=end_Time, interval_flag=interval_flag, bnc_ids=crypto_ids)
    
    
    # df = get_data()
    # print(df.head())
    
    
    # ids = load_custom_ids(DB_PATH)
    
    # load_data(interval=interval, bnc_ids=ids)
    
    
    start_date, end_date = (2021,1,28,9,30), (2021,2,1,10,0)
    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    sample_symbol = 'BTCUSDT'
    
    loader = DataLoader()
    
    data = loader[sample_symbol][start_Time:end_Time]
    
    for datum in data:
        print(datum)
    
    
    
        
    
    
    
