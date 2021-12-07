import shutil
import os

from cointegridy.src.classes.data_loader import TreeLoader, Filter
from cointegridy.src.classes.Time import Time



def test_data_loader_sensibility_depth():
    
    samp_symbol, samp_denom = 'BTC', 'USD'
    
    ## Dismount data
    TreeLoader.clear()
    
    ## Dismounted querry -> Mount
    assert_data_load(samp_symbol, samp_denom)
    ## Mounted querry
    assert_data_load(samp_symbol, samp_denom)


def assert_data_load(samp_symbol, samp_denom):

    samp_data = {
        (samp_symbol,samp_denom): [
            ((2021,1,28), (2021,2,1), '6h', 'v1'),
            ((2020,12,16), (2020,12,23), '12h', 'v2'),
            ((2021,1,29), (2021,2,1), '4h', 'v3'),
            ((2020,11,19), (2020,11,22), '6h', 'v4'),
            ((2020,11,29),  (2020,12,1), '8h', 'v5'),
            ((2020,12,1), (2020,12,3), '4h', 'v6')
        ]
    }

    tree_loader = TreeLoader(data=samp_data)
    
    
    
    samp_querries = {
        ((2020,12,28), (2021,1,1), '12h'),
        ((2021,1,1), (2021,11,1), '6h'),
        ((2021,11,1), (2021,11,2), '1h'),
    }
    
    for samp_sd,samp_ed,samp_iflag in samp_querries:
        
        ## QUERRYING
        querry_sT, querry_eT = Time.date_to_Time(*samp_sd), Time.date_to_Time(*samp_ed)
    
        data = list( tree_loader[samp_symbol:samp_denom][querry_sT:querry_eT:Time.parse_interval_flag(samp_iflag)] )
        
        ## VERIFY QUERRY
        assert data[0][0] == querry_sT.get_psx_tmsp()
        
        for datum_ind in range(len(data)-1):
            datum, next_datum = data[datum_ind], data[datum_ind+1]
            assert datum[0]+Time.parse_interval_flag(samp_iflag) == next_datum[0]
        
        ## Not exactly sure about this yet
        # assert data[-1][0] == querry_eT.get_psx_tmsp()


def test_metadata():
    
    cached_metadata = TreeLoader.pull_metadata()
    
    ## TEST 1 ##
    
    metadata = TreeLoader.pull_metadata(active=False)
    
    symbol, denom = 'BTC', 'USD'
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
    
    TreeLoader.push_metadata(cached_metadata)


def test_filter_metadata():
    
    cached_metadata = TreeLoader.pull_metadata()
    
    dataloader = TreeLoader()
    
    TreeLoader.reset_metadata()
    
    assert 'BTC' in cached_metadata
    
    
    ## Filter coins by min volume
    
    start_date, end_date = (2018,1,1), (2018,1,20)
    filter_sT, filter_eT, filter_step = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date), '6h'
    
    comp_lt = lambda ref,ohlcv: ref<=ohlcv[5]
    
    f1 = Filter(0.1, comp_lambda=comp_lt)
    
    filters = [f1]
    
    TreeLoader._filter(filters, filter_sT, filter_eT, interval_flag=filter_step)
    
    
    ## Test filter
    
    assert 'BTC' not in TreeLoader.pull_metadata()
    
    TreeLoader.push_metadata(cached_metadata.keys())
    