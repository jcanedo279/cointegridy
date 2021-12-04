import csv
import os
from datetime import datetime
from typing import Generator

import pandas as pd
import numpy as np
import requests
import shutil

from cointegridy.src.classes.cc_processor import Processor
from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.slicetree import SliceTree

from cointegridy.src.utils.stats import sharpe_ratio

TXT_DEL=' '
CSV_DEL=','


ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-3])
DATA_PATH = f'{ROOT}/data/'

DYNAMMIC_DATA_PATH = f'{DATA_PATH}dynammic_data'
HISOTICAL_DATA_PATH = f'{DATA_PATH}historical_data'
DATABASE_PATH = f'{DATA_PATH}database.csv'

METADATA_PATH = f'{DATA_PATH}_metadata.txt'
SR_PATH = f'{DATA_PATH}_sharpe_ratios.txt'


if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)
if not os.path.exists(DYNAMMIC_DATA_PATH):
    os.mkdir(DYNAMMIC_DATA_PATH)
if not os.path.exists(HISOTICAL_DATA_PATH):
    os.mkdir(HISOTICAL_DATA_PATH)


INT_TO_MULTIPLIER = Time.int_to_multiplier()
VALID_FLAGS, VALID_STEPS = Time.valid_flags(), Time.valid_steps()

DEFAULT_STEP = 5*INT_TO_MULTIPLIER['m'] ## The default amount to step
DEFAULT_NUM_STEPS = 499 ## Maximum number of steps (of step size) that a contiguous sequence can hold



###########################
## DYNAMMIC DATA LOADERS ##
###########################

class TreeSymbolLoader:
    """
        Acts as a wrapper to grab data timestamp data as a class item
    """
    
    def __init__(self, symbol, denom, processor):
        self.pc = processor
        self.symbol, self.denom = symbol.upper(), denom.upper()
        self.symbol_dir = f'{DYNAMMIC_DATA_PATH}/{self.symbol}'
        self.data_dir = f'{self.symbol_dir}/{self.denom}/'
        ## A mapping: slice [start:stop:step] -> filename
        self.slice_tree = SliceTree()

        ## If symbol does not have a data directory, create it
        if not os.path.exists(self.data_dir):
            if not os.path.exists(self.symbol_dir):
                os.mkdir(self.symbol_dir)
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
        running_max, seq_targ = start-1, start
        for filename, interval in self.slice_tree[start:stop:step]:
            
            if not filename: ## Stash this interval to put into memory later
                cached_missing.add(interval)
            
            _start,_stop,_step = interval
            interval_rep = filename if filename else f'{_start}_{_stop}_{_step}'

            cur_rep = f'{interval_rep}/'
            if not os.path.exists(self.data_dir + cur_rep):
                os.mkdir(self.data_dir+cur_rep)
            
            if filename: ## File exists
                for sub_dirname in sorted(os.listdir(self.data_dir+cur_rep)): ## TODO:: AT SOME POINT OPTIMIZE THIS SUB STRUCTURE
                    sub_dirname_P = sub_dirname[:-4] if sub_dirname.endswith('.csv') else sub_dirname
                    s_start,s_stop,s_step = [float(x) for x in sub_dirname_P.split('_')]
                    if running_max <= _stop:
                        for datum, running_max in self.pull_seq_from_loaded(cur_rep+sub_dirname, running_max):
                            if running_max==seq_targ:
                                yield datum
                                seq_targ += step
                    else: break
                running_max = seq_targ - step
            
            else: ## File does not exist
                c_start = _start
                while c_start+step*DEFAULT_NUM_STEPS < _stop:
                    for datum, running_max in self.pull_seq_from_bnc(c_start,c_start+step*DEFAULT_NUM_STEPS,running_max,interval_flag=i_flag):
                        yield datum
                    c_start += step*DEFAULT_NUM_STEPS
                if c_start <= _stop:
                    for datum, running_max in self.pull_seq_from_bnc(c_start,_stop,running_max,interval_flag=i_flag):
                        yield datum
                seq_targ = running_max + step
        
        ## Add cached_missing to local
        for c_start,c_stop,c_step in cached_missing:
            c_rep = f'{c_start}_{c_stop}_{c_step}'
            c_iflag = Time.valid_steps()[c_step]
            
            cache_start = c_start
            while cache_start+c_step*DEFAULT_NUM_STEPS<c_stop:
                _filename = f'{c_rep}/{cache_start}_{cache_start+c_step*DEFAULT_NUM_STEPS}_{c_step}.csv'
                with open(self.data_dir+_filename, 'w') as f_writer:
                    writer = csv.writer(f_writer)
                    for datum in self.pc.symbol_to_ohlc_seq(self.symbol, Time(utc_tmsp=float(cache_start)), Time(utc_tmsp=float(cache_start+c_step*DEFAULT_NUM_STEPS)), interval_flag=c_iflag, denom=self.denom):
                        writer.writerow(datum)
                cache_start += c_step*DEFAULT_NUM_STEPS
            if cache_start < c_stop:
                _filename = f'{c_rep}/{cache_start}_{c_stop}_{c_step}.csv'
                with open(self.data_dir+_filename, 'w') as f_writer:
                    writer = csv.writer(f_writer)
                    for datum in self.pc.symbol_to_ohlc_seq(self.symbol, Time(utc_tmsp=float(cache_start)), Time(utc_tmsp=c_stop), interval_flag=c_iflag, denom=self.denom):
                        writer.writerow(datum)
            
            self.slice_tree[c_start:c_stop:c_step] = c_rep
    
    def pull_seq_from_loaded(self, filename, running_max):
        with open(self.data_dir+filename, 'r') as f_reader:
            reader = csv.reader(f_reader)
            for line in reader:
                tmsp = float(line[0])
                if tmsp >= running_max:
                    yield (tmsp, float(line[1])), max(tmsp, running_max)
    
    def pull_seq_from_bnc(self, start_tmsp, stop_tmsp, running_max, interval_flag='5m'): ## ONLY GRAB WHAT YOU NEED TO HERE
        for datum in self.pc.symbol_to_ohlc_seq(self.symbol, Time(utc_tmsp=max(start_tmsp,running_max)), Time(utc_tmsp=stop_tmsp), interval_flag=interval_flag, denom=self.denom):
            ### datum = [tmsp, open, high, low, close, volume]
            tmsp = float(datum[0])
            if tmsp > running_max:
                yield [float(item) for item in datum], max(tmsp, running_max)



class TreeLoader:
    
    def __init__(self, data={}):
        self.pc = Processor()
        self.asset_to_load_ind, self.loaded_loaders = {}, []
        
        if not os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'w') as f_writer:
                for symbol in self.pc.get_api_symbols():
                    f_writer.write(symbol+'\n')

        for (symbol,denom), symb_data in data.items():
            loader = TreeSymbolLoader(symbol, denom, self.pc)
            self.asset_to_load_ind[(symbol,denom)] = len(self.loaded_loaders)
            for start_date, end_date, step_flag, value in symb_data:
                start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
                for _ in loader[start_Time:end_Time:Time.parse_interval_flag(step_flag)]:
                    pass
            self.loaded_loaders.append(loader)
    
    
    def __getitem__(self, asset) -> TreeSymbolLoader:
        assert isinstance(asset,str) or isinstance(asset,slice)
        symbol,denom = asset.split('/') if isinstance(asset,str) else asset.start,asset.stop
        
        loader = None        
        
        if (symbol,denom) in self.asset_to_load_ind: ## If we have seen symbol before
            loader_ind = self.asset_to_load_ind[(symbol,denom)]
            loader = self.loaded_loaders[loader_ind]
        else: ## If this is a new symbol
            loader = TreeSymbolLoader(symbol, denom, self.pc)
        return loader

    
    def clear_loaded(self):
        self.asset_to_load_ind, self.loaded_loaders = {}, []
        
        INVALID_FILENAMES = {'.gitkeep'}
        for filename in os.listdir(DYNAMMIC_DATA_PATH):
            if filename in INVALID_FILENAMES: continue
            shutil.rmtree(f'{DYNAMMIC_DATA_PATH}/{filename}')
    
    
    @staticmethod
    def pull_symbols():
        with open(METADATA_PATH, 'r') as f_reader:
            for line in f_reader.readlines():
                _line = line[:-1] if line.endswith('\n') else line
                yield _line
    
    @staticmethod
    def push_symbols(new_symbols):
        with open(METADATA_PATH, 'w') as f_writer:
            for symbol in new_symbols:
                f_writer.write(symbol+'\n')



    
