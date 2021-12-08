
import os
import shutil

from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.data_loader import TreeLoader


#############################
## SAVED METADATA TO CACHE ##
#############################

ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-2])
METADATA_PATH = f'{ROOT}/data/_metadata.txt'
ACTIVE_METADATA_PATH = f'{ROOT}/data/_active_metadata.txt'
CACHED_METADATA_PATH = f'{ROOT}/data/_cached_metadata.txt'

if not os.path.exists(METADATA_PATH):
    TreeLoader.reset_metadata(active=False)
if not os.path.exists(ACTIVE_METADATA_PATH):
    TreeLoader.reset_metadata(active=True)

shutil.copy(ACTIVE_METADATA_PATH, CACHED_METADATA_PATH)


################################
## Reset metadata for testing ##
################################
TreeLoader.reset_metadata()
