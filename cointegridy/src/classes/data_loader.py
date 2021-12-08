import csv
import os
from typing import Generator, Iterable

import pandas as pd
import numpy as np
import shutil

from cointegridy.src.classes.processor import Processor
from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.slicetree import SliceTree


################
## FILTRATION ##
################

PROCESSOR = Processor(exchange_id='binanceus')

LT_OHLC = lambda ref,ohlcv:ref<=ohlcv[5]
    
class Filter:
    """[Filter helper class defines a filter that acts on a coin and]
    
    Args:
        ref (comparable): some comparable value
        comp_lamda (lambda): a lambda expression between two comparables
        
        __call__(other) (function(comparable)) -> bool: a function (ref com_lampda other) -> bool
    """
    
    def __init__(self, ref, comp_lambda=LT_OHLC):
        self.ref, self.comp_lambda = ref, comp_lambda
    
    def __call__(self, ohlcv):
        return self.comp_lambda(self.ref, ohlcv)


##################
## DATA PARSING ##
##################

TXT_DEL=' '
TXT_SUB_DEL = '&'
CSV_DEL=','


ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-3])
DATA_PATH = f'{ROOT}/data/'

DYNAMMIC_DATA_PATH = f'{DATA_PATH}dynammic_data'

if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)
if not os.path.exists(DYNAMMIC_DATA_PATH):
    os.mkdir(DYNAMMIC_DATA_PATH)



METADATA_PATH = f'{DATA_PATH}_metadata.txt'
ACTIVE_METADATA_PATH = f'{DATA_PATH}_active_metadata.txt'

if not os.path.exists(METADATA_PATH):
    pc = PROCESSOR
    with open(METADATA_PATH, 'w') as f_writer:
        for symbol,denoms in pc.get_api_metadata().items():
            print(f'{symbol}{TXT_SUB_DEL}{list(denoms)}\n')
            f_writer.write(f'{symbol}{TXT_SUB_DEL}{list(denoms)}\n')
if not os.path.exists(ACTIVE_METADATA_PATH):
    shutil.copy(METADATA_PATH, ACTIVE_METADATA_PATH)


INT_TO_MULTIPLIER = Time.int_to_multiplier()
VALID_FLAGS, VALID_STEPS = Time.valid_flags(), Time.valid_steps()

DEFAULT_STEP = 5*INT_TO_MULTIPLIER['m'] ## The default amount to step
DEFAULT_NUM_STEPS = 499 ## Maximum number of steps (of step size) that a contiguous sequence can hold


DEFAULT_MODE = 'gen'


###########################
## DYNAMMIC DATA LOADERS ##
###########################

class TreeSymbolLoader:
    """
        Acts as a wrapper to grab symbol timestamp data as a class item
    """
    
    def __init__(self, symbol, denom, mode=DEFAULT_MODE):
        self.mode = mode
        self.pc = PROCESSOR
        self.symbol, self.denom = symbol.upper(), denom.upper()
        self.symbol_dir = f'{DYNAMMIC_DATA_PATH}/{self.symbol}'
        self.data_dir = f'{self.symbol_dir}/{self.denom}/'
        ## A mapping: slice [start:stop:step] -> filename
        self.slice_tree = SliceTree()

        ## If symbol does not have a data directory, create it
        if not os.path.exists(self.data_dir):
            self.create_dir()
        
        for dirname in os.listdir(self.data_dir):
            dirname_P = dirname[:-4] if dirname.endswith('csv') else dirname
            start,stop,step = dirname_P.split('_')
            start,stop,step = float(start),float(stop), float(step)
            self.slice_tree[start:stop:step] = dirname_P
    
    
    def __getitem__(self, _slice:slice):
        
        if not os.path.exists(self.data_dir):
            self.create_dir()
        
        if self.mode == 'gen':
            yield from self.gen_data(_slice)
        elif self.mode == 'df':
            df = pd.DataFrame(data=[row for row in self.gen_data(_slice)], columns=['tmsp', 'open', 'high', 'low', 'close', 'volume'])
            df.set_index('tmsp')
            return df
    
    def gen_data(self, _slice:slice):
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
                    if s_stop < _start: continue
                    for datum in self.pull_seq_from_loaded(cur_rep+sub_dirname):
                        if float(datum[0]) >= _start:
                            yield datum
            
            else: ## File does not exist
                c_start = _start
                while c_start+step*DEFAULT_NUM_STEPS < _stop:
                    for datum in self.pull_seq_from_bnc(c_start,c_start+step*DEFAULT_NUM_STEPS,interval_flag=i_flag):
                        yield datum
                    c_start += step*DEFAULT_NUM_STEPS
                if c_start < _stop:
                    for datum in self.pull_seq_from_bnc(c_start,_stop,interval_flag=i_flag):
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
    
    
    def pull_seq_from_loaded(self, filename):
        with open(self.data_dir+filename, 'r') as f_reader:
            reader = csv.reader(f_reader)
            for line in reader:
                yield [float(item) for item in line]
    
    def pull_seq_from_bnc(self, start_tmsp, stop_tmsp, interval_flag='5m'): ## ONLY GRAB WHAT YOU NEED TO HERE
        for datum in PROCESSOR.symbol_to_ohlc_seq(self.symbol, Time(utc_tmsp=start_tmsp), Time(utc_tmsp=stop_tmsp), denom=self.denom, interval_flag=interval_flag):
            ### datum = [tmsp, open, high, low, close, volume]
            yield [float(item) for item in datum]
    
    def create_dir(self):
        if not os.path.exists(self.data_dir):
            if not os.path.exists(self.symbol_dir):
                os.mkdir(self.symbol_dir)
            os.mkdir(self.data_dir)
    
    def clear(self, all_denoms=False):
        rm_path = f'{DYNAMMIC_DATA_PATH}/{self.symbol}/' if all_denoms else f'{DYNAMMIC_DATA_PATH}/{self.symbol}/{self.denom}/'
        if all_denoms:
            shutil.rmtree(rm_path)
        else:
            shutil.rmtree(rm_path)
        self.slice_tree = SliceTree()



class TreeLoader:
    
    def __init__(self, data={}, mode=DEFAULT_MODE):
        self.mode = mode
        
        self.pc = PROCESSOR
        self.asset_to_load_ind, self.loaded_loaders = {}, []
        
        self.symbol_to_denoms = TreeLoader.pull_metadata()
        
        for (symbol,denom), symb_data in data.items():
            if denom not in self.symbol_to_denoms[symbol]: continue ## We do not have this symbol->denom in our _metadata
            loader = TreeSymbolLoader(symbol, denom, mode=self.mode)
            self.asset_to_load_ind[(symbol,denom)] = len(self.loaded_loaders)
            for start_date, end_date, step_flag, value in symb_data:
                start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
                for _ in loader[start_Time:end_Time:Time.parse_interval_flag(step_flag)]:
                    pass
            self.loaded_loaders.append(loader)
        
    
    def __getitem__(self, asset) -> TreeSymbolLoader:
        assert isinstance(asset,str) or isinstance(asset,slice)
        str_asset = None
        if isinstance(asset,str):
            str_asset = asset.split('/') if '/' in asset else asset
        symbol,denom = str_asset if isinstance(asset,str) else asset.start,asset.stop
        if not denom in self.symbol_to_denoms[symbol]: return
        
        loader = None
        if (symbol,denom) in self.asset_to_load_ind: ## If we have seen symbol before
            loader_ind = self.asset_to_load_ind[(symbol,denom)]
            loader = self.loaded_loaders[loader_ind]
        else: ## If this is a new symbol
            loader = TreeSymbolLoader(symbol, denom, mode=self.mode)
        loader.mode = self.mode
        return loader

    
    def change_mode(self, mode=None):
        if mode:
            self.mode = mode
        else:
            self.mode = 'gen' if self.mode=='df' else 'df'
    
    
    def clear_loaded(self):
        self.asset_to_load_ind, self.loaded_loaders = {}, []
        
        INVALID_FILENAMES = {'.gitkeep'}
        for filename in os.listdir(DYNAMMIC_DATA_PATH):
            if filename in INVALID_FILENAMES: continue
            shutil.rmtree(f'{DYNAMMIC_DATA_PATH}/{filename}')
    
    
    ##########
    ## UTIL ##
    ##########
    
    @staticmethod
    def clear():
        IGNORED_FILENAMES = {'.gitkeep'}
        for filename in os.listdir(DYNAMMIC_DATA_PATH):
            if filename in IGNORED_FILENAMES: continue
            rm_path = f'{DYNAMMIC_DATA_PATH}/{filename}/'
            shutil.rmtree(rm_path)
            # os.rmdir(rm_path)
    
    
    ###############
    ## PROCESSOR ##
    ###############
    
    def get_api_tickers(self):
        return PROCESSOR.get_api_tickers()
    
    def get_api_metadata(self):
        return PROCESSOR.get_api_metadata()
    
    
    ##############
    ## METADATA ##
    ##############
    
    @staticmethod
    def _filter(filters:list, start_Time:Time, end_Time:Time, interval_flag:str='6h'):
        """Filter the active metadata symbols by the filter functions in filters

        Args:
            filters (list): A list of filters that
        
        Returns:
            a symbol to denoms dict 
        """
        
        assert isinstance(interval_flag,str)
        
        filters = [_filter for _filter in filters if isinstance(_filter,Filter)]
        if not filters: return {}
        
        ## (symbol,denoms)
        running_symbol_to_denoms, active_symbol_to_denoms = {}, TreeLoader.pull_metadata()
        
        for symbol,denoms in active_symbol_to_denoms.items():
            denom = list(denoms)[0]
            if not f'{symbol}/{denom}' in PROCESSOR.exchange.symbols: continue
            for ohlcv in PROCESSOR.symbol_to_ohlc_seq(symbol, start_Time, end_Time, denom=denom, interval_flag=interval_flag):
                is_filtered = True
                for _filter in filters:
                    if not _filter(ohlcv):
                        is_filtered = False
                        break
                if is_filtered: running_symbol_to_denoms[symbol]=denom
                        
        TreeLoader.push_metadata(running_symbol_to_denoms.keys())
    
    
    @staticmethod
    def reset_metadata(active=True):
        """[Resets the metadata files (symbols), if active -> reset active_metadata from metadata, if not active -> reset metadata from processor]
        """
        if active:
            if not os.path.exists(METADATA_PATH):
                TreeLoader.reset_metadata(active=False)
            shutil.copy(METADATA_PATH, ACTIVE_METADATA_PATH)
        else:
            with open(METADATA_PATH, 'w') as f_writer:
                for symbol,denoms in PROCESSOR.get_api_metadata.items():
                    f_writer.write(f'{symbol}{TXT_SUB_DEL}{list(denoms)}\n')
    
    @staticmethod
    def pull_metadata(active=True):
        symbol_to_denoms = {}
        metadata_path = ACTIVE_METADATA_PATH if active else METADATA_PATH
        with open(metadata_path, 'r') as f_reader:
            for line in f_reader.readlines():
                _line = line[:-1] if line.endswith('\n') else line
                symbol, denoms = _line.split(TXT_SUB_DEL)
                _denoms = {denom.strip().strip("\'") for denom in denoms.strip('[]').split(CSV_DEL)}
                symbol_to_denoms[symbol] = _denoms
        return symbol_to_denoms
    
    @staticmethod
    def push_metadata(new_symbols:Iterable, active=True):
        new_symbols_set = set(new_symbols)
        metadata_path = ACTIVE_METADATA_PATH if active else METADATA_PATH
        
        metadata_reader = []
        with open(metadata_path, 'r') as f_reader:
            metadata_reader = f_reader.readlines()
        
        with open(metadata_path, 'w') as f_writer:
            for line in metadata_reader:
                if line.split(TXT_SUB_DEL)[0] in new_symbols_set:
                    f_writer.write(line)

