import csv
import os
from datetime import datetime
from typing import Generator

from slicetree import SliceTree
from intervaltree import IntervalTree

import pandas as pd
import numpy as np
import requests

from bin.classes.processor import Processor

# Custom imports
# from .time import Time
from bin.classes.Time import Time
from bin.utils.stats import sharpe_ratio




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

VALID_FLAGS = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']

STEP_TO_FLAG = {Time.parse_interval_flag(flag):flag for flag in VALID_FLAGS}


DEFAULT_STEP = 5*INT_TO_MULTIPLIER['m'] ## The amount to step
DEFAULT_NUM_STEPS = 499 ## Maximum number of steps


def get_ids():
    with open(METADATA_PATH, "r") as f_reader:
        return f_reader.read().split(TXT_DEL)


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
        ## A mapping: slice [start:stop:step] -> filename
        self.slice_tree = SliceTree()

        ## If id does not have a data directory, create it
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        
        for dirname in os.listdir(self.data_dir):
            dirname_P = dirname[:-4] if dirname.endswith('csv') else dirname
            start,stop,step = dirname_P.split('_')
            start,stop,step = float(start),float(stop), float(step)
            self.slice_tree[start:stop:step] = dirname_P
    
    
    def __getitem__(self, _slice: slice) -> Generator:
        
        assert isinstance(_slice, slice)
        start,stop,step = _slice.start,_slice.stop,_slice.step
        if isinstance(step, str):
            step = Time.parse_interval_flag(step)
        if isinstance(start, Time):
            start = start.get_psx_tmsp()
        if isinstance(stop, Time):
            stop = stop.get_psx_tmsp()
        
        step = DEFAULT_STEP if not step else step
        i_flag = Time.valid_steps()[step]
        
        ## Yield results from local and bnc
        cached_missing = set()
        running_max = start-1
        for filename, interval in self.slice_tree.overlap_querry(slice(start,stop,step)):
            if not filename: ## Stash this interval to put into memory later
                cached_missing.add(interval)
            
            _start,_stop,_step = interval
            interval_rep = filename if filename else f'{_start}_{_stop}_{_step}'

            cur_rep = f'{interval_rep}/'
            if not os.path.exists(self.data_dir + cur_rep):
                os.mkdir(self.data_dir+cur_rep)
            
            if filename: ## File exists
                for sub_dirname in os.listdir(self.data_dir+cur_rep):
                    sub_dirname_P = sub_dirname[:-4] if sub_dirname.endswith('.csv') else sub_dirname
                    s_start,s_stop,s_step = [float(x) for x in sub_dirname_P.split('_')]
                    if running_max < s_stop:
                        for datum, running_max in self.pull_seq_from_loaded(cur_rep+sub_dirname, running_max):
                            yield datum
                    else:
                        break
            
            else: ## File does not exist
                c_start = _start
                while c_start+step*DEFAULT_NUM_STEPS < _stop:
                    for datum, running_max in self.pull_seq_from_bnc(c_start,c_start+step*DEFAULT_NUM_STEPS,running_max,interval_flag=i_flag):
                        yield datum
                    c_start += step*DEFAULT_NUM_STEPS
                if c_start < _stop:
                    for datum, running_max in self.pull_seq_from_bnc(c_start,_stop,running_max,interval_flag=i_flag):
                        yield datum
        
        ## Add cached_missing to local
        for c_start,c_stop,c_step in cached_missing:
            c_rep = f'{c_start}_{c_stop}_{c_step}'
            c_iflag = Time.valid_steps()[c_step]
            
            cache_start = c_start
            while cache_start+c_step*DEFAULT_NUM_STEPS<c_stop:
                _filename = f'{c_rep}/{cache_start}_{cache_start+c_step*DEFAULT_NUM_STEPS}_{c_step}.csv'
                with open(self.data_dir+_filename, 'w') as f_writer:
                    writer = csv.writer(f_writer)
                    for datum in self.pc.id_to_ohlc_seq(self.id, Time(utc_tmsp=float(cache_start)), Time(utc_tmsp=float(cache_start+c_step*DEFAULT_NUM_STEPS)), interval_flag=c_iflag):
                        writer.writerow([float(datum['open_tmsp']), float(datum['open'])])
                cache_start += c_step*DEFAULT_NUM_STEPS
            if cache_start < c_stop:
                _filename = f'{c_rep}/{cache_start}_{c_stop}_{c_step}.csv'
                with open(self.data_dir+_filename, 'w') as f_writer:
                    writer = csv.writer(f_writer)
                    for datum in self.pc.id_to_ohlc_seq(self.id, Time(utc_tmsp=float(cache_start)), Time(utc_tmsp=c_stop), interval_flag=c_iflag):
                        writer.writerow([float(datum['open_tmsp']), float(datum['open'])])
            
            self.slice_tree[c_start:c_stop:c_step] = c_rep
    
    
    
    def pull_seq_from_loaded(self, filename, running_max):
        with open(self.data_dir+filename, 'r') as f_reader:
            reader = csv.reader(f_reader)
            for line in reader:
                tmsp = float(line[0])
                if tmsp > running_max:
                    yield (tmsp, float(line[1])), max(tmsp, running_max)
    
    
    def pull_seq_from_bnc(self, start_tmsp, stop_tmsp, running_max, interval_flag='5m'): ## ONLY GRAB WHAT YOU NEED TO HERE
        for datum in self.pc.id_to_ohlc_seq(self.id, Time(utc_tmsp=max(start_tmsp,running_max)), Time(utc_tmsp=stop_tmsp), interval_flag=interval_flag):
            tmsp, value = float(datum['open_tmsp']), float(datum['open'])
            if tmsp > running_max:
                yield (tmsp, value), max(tmsp, running_max)
        

class TreeLoader:
    
    def __init__(self):
        self.pc = Processor('bnc')
        self.id_to_load_ind = {}
        self.loaded_symbol_loaders = []
    
    def __getitem__(self, _id: str ) -> TreeSymbolLoader:
        assert isinstance(_id,str)
        id_loader = None        
        
        if _id in self.id_to_load_ind: ## If we have seen id before
            loader_ind = self.id_to_load_ind[_id]
            id_loader = self.loaded_symbol_loaders[loader_ind]
        else: ## If this is a new symbol
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
    def pull_data(start_Time=Time.date_to_Time(2021,1,1), end_Time=Time.date_to_Time(2021,11,1), interval_flag='1d', bnc_ids=None):
        """
            1 day ~ 289 5 minute intervals   -->   1 year ~ 105,485 lines
            
            20 lines ~ 6.3 MB   -->   105,485 lines ~ 34 GB
            
            1 day ~ 5 minutes to compute   -->   11 months ~ 27.5 hrs to compute
        """
        
        interval = Time.parse_interval_flag(interval_flag)
        
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
    
    db_start_date, db_end_date = (2021,1,28), (2021,4,1)
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
    
    sample_symbol = 'BTCUSDT'
    
    
    date_intervals = [
        ((2021,1,28), (2021,2,1), '6h', 'v1'),
        ((2020,12,16), (2020,12,23), '12h', 'v2'),
        ((2021,1,29), (2021,2,1), '4h', 'v3'),
        ((2020,11,19), (2020,11,22), '6h', 'v4'),
        ((2020,11,29),  (2020,12,1), '8h', 'v5'),
        ((2020,12,1), (2020,12,3), '4h', 'v6')
    ]

    tree_loader = TreeLoader()


    
    for start_date, end_date, step_flag, value in date_intervals:
        start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
        ## UNCOMMENT TO PUSH DATES
        for item in tree_loader[sample_symbol][start_Time:end_Time:Time.parse_interval_flag(step_flag)]:
            # print(item)
            pass
    
    print(tree_loader[sample_symbol].slice_tree)




    
    ## QUERRYING
    querry_interval_flag = '6h'
    querry_sT, querry_eT = Time.date_to_Time(*(2021,1,1)), Time.date_to_Time(*(2021,11,1))
    
    data = list( tree_loader[sample_symbol][querry_sT:querry_eT:Time.parse_interval_flag(querry_interval_flag)] )
    
    ## VERIFY QUERRY
    # data = list(data)
    print('QUERRYING: ', querry_sT.get_psx_tmsp(), querry_eT.get_psx_tmsp())
    
    for datum in data:
        print(datum)
    print('-'*20)
    
    for datum_ind in range(len(data)-1):
        datum, next_datum = data[datum_ind], data[datum_ind+1]
        if datum[0]+Time.parse_interval_flag(querry_interval_flag) != next_datum[0]:
            print(datum, next_datum)
    
    
    # print(tree_loader[sample_symbol].slice_tree)
    
    
    