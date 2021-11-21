import csv
import os
from datetime import datetime
from typing import Generator

from intervaltree import IntervalTree
from ncls import NCLS

import pandas as pd
import numpy as np
import requests

from .bin.classes.processor import Processor

# Custom imports
# from .time import Time
from .bin.classes.Time import Time
from .bin.utils.stats import sharpe_ratio



TXT_DEL=' '
CSV_DEL=','


DYNAMMIC_DATA_PATH = 'data/dynammic_data'
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




def get_ids():
    with open(METADATA_PATH, "r") as f_reader:
        return f_reader.read().split(TXT_DEL)


def parse_interval(interval):
    last_char = 0
    for _char in interval:
        if _char.isnumeric(): last_char += 1
        
    return int(interval[:last_char]) * INT_TO_MULTIPLIER[interval[last_char:]]


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


##################################
## UPDATE SHARPE RATIO DATABASE ##
##################################

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
            open_ser = pd.Series([float(datum['open']) for datum in id_response], name=f'{id}', dtype=np.float64)
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
    
    
            

            






###########################
## DYNAMMIC DATA LOADERS ##
###########################

class TreeSymbolLoader:
    """
        Acts as a wrapper to grab data timestamp data as a class item
    """
    
    def __init__(self, _id, processor):
        self.pc = processor
        self.id = _id.upper()
        self.data_dir = f'{DYNAMMIC_DATA_PATH}/{_id.upper()}/'
        ## A mapping: tmsp interval [inclusive, non-inclusive) -> filename
        self.interval_tree = IntervalTree()

        ## IF id does not have a data directory, create it
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        
        for filename in os.listdir(self.data_dir):
            del_ind = filename.index('_')
            start, stop = int(filename[:del_ind]), int(filename[del_ind+1:-4])
            self.interval_tree[start:stop] = filename
    
    
    def __getitem__(self, _slice: slice) -> Generator:
        assert isinstance(_slice, slice)
        start, stop, interval = _slice.start, _slice.stop, _slice.step
        if isinstance(start, Time):
            start = start.get_psx_tmsp()
        if isinstance(stop, Time):
            stop = stop.get_psx_tmsp()
        
        ## Pull loaded overlapping intervals -> trim intervals
        ## This takes O(k log_k)     where k = #overlapping_intervals + log_#intervals
        file_paths, last_tmsp = [], float('-inf')  
        for start_P,stop_P,f_name in sorted(self.interval_tree[start:stop]): 
            if stop_P > last_tmsp:
                file_paths.append((start_P,stop_P,f_name))
                last_tmsp = stop_P
        
        ## Calculate missing intervals to complete querry (if any)
        first_start = stop if not file_paths else file_paths[0][0]
        missing_paths = [(start,first_start)] if start<first_start else []
        for int_ind in range(len(file_paths)-1):
            _,stop_P1,f_name = file_paths[int_ind]
            start_P2,_,_ = file_paths[int_ind+1]
            if stop_P1<start_P2:
                missing_paths.append(stop_P1,start_P2)
        if file_paths and file_paths[-1][1]<stop:
            missing_paths.append((file_paths[-1][1],stop))

        ## Merge loaded and missing intervals
        loaded_ptr, missing_ptr = 0, 0
        merged_paths = []
        while loaded_ptr<len(file_paths) and missing_ptr<len(missing_paths):
            loaded, missing = file_paths[loaded_ptr][0], missing_paths[missing_ptr][0]
            if loaded < missing:
                merged_paths.append(loaded)
                loaded_ptr += 1
            else:
                merged_paths.append(missing)
                missing_ptr += 1 
        if loaded_ptr<len(file_paths):
            merged_paths.extend(file_paths[missing_ptr:])
        if missing_ptr<len(missing_paths):
            merged_paths.extend(missing_paths[missing_ptr:])
        
        ## Compile merged intervals into a contiguous timestamp sequence
        for path in merged_paths:
            if len(path)==2:
                for tmsp, price in self.pull_seq_from_bnc(self.id, path[0], path[1]):
                    yield tmsp, price
            else:
                for tmsp, price in self.pull_seq_from_loaded(path[2]):
                    yield tmsp, price
        
    
    def pull_seq_from_loaded(self, filename):
        
        lines = []
        with open(self.data_dir+filename, 'r') as f_reader:
            lines = [line.split(CSV_DEL) for line in f_reader.readlines()]
            
        return [(int(line[0]), float(line[1])) for line in lines]
    
    
    def pull_seq_from_bnc(self, id, start_tmsp, stop_tmsp, interval_flag='5m'):
        
        id_response = self.pc.id_to_ohlc_seq(id, Time(utc_tmsp=start_tmsp), Time(utc_tmsp=stop_tmsp), interval_flag=interval_flag)
        tmsp_seq = [(int(float(d['open_tmsp'])), float(d['open'])) for d in id_response]
        
        filename = f'{int(float(start_tmsp))}_{int(float(stop_tmsp))}.csv'
        seq_path = f'{self.data_dir}{filename}'
        with open(seq_path, 'w+', newline ='') as f_writer:
            writer = csv.writer(f_writer)
            writer.writerows(tmsp_seq)
        self.interval_tree[start_tmsp:stop_tmsp] = filename
        
        return tmsp_seq
        

class TreeLoader:
    
    def __init__(self):
        self.pc = Processor('bnc')
        self.id_to_load_ind = {}
        self.loaded_symbol_loaders = []
    
    
    def __getitem__(self, _id: str ) -> TreeSymbolLoader:
        assert isinstance(_id,str)
        
        id_loader = None        
        
        ## IF we have seen id before
        if _id in self.id_to_load_ind:
            loader_ind = self.id_to_load_ind[_id]
            id_loader = self.loaded_symbol_loaders[loader_ind]
        ## If this is a new symbol
        else:
            id_loader = TreeSymbolLoader(_id, self.pc)
        
        return id_loader
    
    
    def get_ids(self):
        return self.pc.get_api_ids()
        


########################
## STATIC DATA LOADER ##
########################

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
    
    def get_ids(self):
        return get_ids()
    
    @staticmethod
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





    




if __name__=='__main__':
    
    
    #################################
    ## PULL STATIC HISTORICAL DATA ##
    #################################
    
    VALID_INTERVALS = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
    
    interval_flag = '5m'
    
    db_start_date, db_end_date = (2021,1,28), (2021,2,1)
    db_start_Time, db_end_Time = Time.date_to_Time(*db_start_date), Time.date_to_Time(*db_end_date)
    
    ## UNCOMMENT TO UPDATE SHARPE RATIOS
    # pull_sharpe_ratios(start_Time=db_start_Time, end_Time=db_end_Time, interval_flag=interval_flag)
    
    ## UNCOMMENT TO 
    # num_symbols = 100
    # crypto_ids = get_best_stocks_from_CSV(SR_PATH, CSV_DEL, num_symbols)
    
    ## UNCOMMENT TO UPDATE HISTORICAL DATA
    # DataLoader.pull_data(start_Time=db_start_Time, end_Time=db_end_Time, interval_flag=interval_flag, bnc_ids=crypto_ids)
    
    # data_loader = DataLoader()
    
    ## GET AVAILABLE IDS FROM DRIVE
    # ids = data_loader.get_ids()
    # print(ids)

    
    
    ###################################
    ## PULL DYNAMMIC HISTORICAL DATA ##
    ###################################
    
    start_date, end_date = (2021,1,28,9,30), (2021,2,1,10,0)
    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    sample_symbol = 'BTCUSDT'
    
    tree_loader = TreeLoader()
    
    for datum in tree_loader[sample_symbol][start_Time:end_Time]:
        print(datum)
    
    
    
    
    
    
    
    
