
import os
import shutil

from cointegridy.src.classes.data_loader import TreeLoader


###########################
## RESET ACTIVE METADATA ##
###########################

ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-2])
ACTIVE_METADATA_PATH = f'{ROOT}/data/_active_metadata.txt'
CACHED_METADATA_PATH = f'{ROOT}/data/_cached_metadata.txt'

shutil.copy(CACHED_METADATA_PATH, ACTIVE_METADATA_PATH)
