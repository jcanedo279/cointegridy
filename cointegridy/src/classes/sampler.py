
import os

from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.data_loader import TreeLoader


ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-3])
DATA_PATH = f'{ROOT}/data/'

METADATA_PATH = f'{DATA_PATH}/_metadata.txt'
ACTIVE_METADATA_PATH = f'{DATA_PATH}/_active_metadata.txt'



##################
## COIN FILTERS ##
##################

__FILTER_ = lambda x: bool(x)





###################
## COINS SAMPLER ##
###################

SAMPLE_TIME = Time(utc_tmsp= ( Time.utcnow()-6000 ) ) ## Since one hour ago

class sampler:
    
    def __init__(self, filtration_start=SAMPLE_TIME, filtration_end=Time()):
        self.filtration_start, self.filtration_end = filtration_start, filtration_end
        
        self.active_filters = {}
        
        self.dataloader = TreeLoader(mode='df')
        self.symbols_to_denoms = TreeLoader.get_api_symbols_to_denoms()
    
    def set_filtration_window(self, filtration_start=SAMPLE_TIME, filtration_end=Time()):
        assert isinstance(filtration_start,Time), isinstance(filtration_end,Time)
        self.filtration_start, self.filtration_end = filtration_start, filtration_end

    def _filter(self, filtration_interval='30m'):
        assert filtration_interval in Time.valid_flags
        
    