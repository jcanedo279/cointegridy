import shutil
import os
import numpy as np

from cointegridy.src.classes.coin import Coin
from cointegridy.src.classes.Time import Time

def test_init():
    '''Test only the implementation of coin, without basket'''
    C1 = Coin('sample')
    x = list()

    C1.is_good()


def assert_good():



def test_metadata():
    
    TreeLoader.reset_metadata()
    
    ## TEST 1 ##
    
    metadata = TreeLoader.pull_metadata(active=False)
    
    symbol, denom = 'BTC', 'BUSD'
    assert symbol in metadata
    denoms = metadata[symbol]
    assert denom in denoms
    
    
    ## TEST 2 ##
    
    TreeLoader.push_metadata([symbol])
    
    active_metadata = TreeLoader.pull_metadata()
    
    symbol_other = 'ETC'
    
    assert symbol_other in metadata
    assert symbol_other not in active_metadata
    
    assert symbol in metadata
    denoms = metadata[symbol]
    assert denom in denoms


def test_filter_metadata():
    
    TreeLoader.reset_metadata()
    
    active_metadata = TreeLoader.pull_metadata()
    
    assert 'BTC' in active_metadata
    
    
    ## Filter coins by min volume
    
    start_date, end_date = (2018,1,1), (2018,1,20)
    filter_sT, filter_eT, filter_step = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date), '6h'
    
    comp_lt = lambda ref,ohlcv: ref<=ohlcv[5]
    
    f1 = Filter(1000, comp_lambda=comp_lt)
    
    filters = [f1]
    
    TreeLoader._filter(filters, filter_sT, filter_eT, interval_flag=filter_step)
    
    
    ## Test filter
    
    assert 'BTC' not in TreeLoader.pull_metadata()
    
    TreeLoader.push_metadata(active_metadata.keys())
    