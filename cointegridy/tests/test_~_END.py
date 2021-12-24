
import os
import shutil

from cointegridy.src.classes.data_loader import TreeLoader


###########################
## RESET ACTIVE METADATA ##
###########################

def test_end():
    
    ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-2])
    ACTIVE_METADATA_PATH = f'{ROOT}/data/_active_metadata.txt'
    CACHED_METADATA_PATH = f'{ROOT}/data/_cached_metadata.txt'

    # with open(CACHED_METADATA_PATH, 'r') as f_reader:
    #     lines = f_reader.readlines()
    #     for line in lines:
    #         print(lines)

    shutil.copy(CACHED_METADATA_PATH, ACTIVE_METADATA_PATH)
    # print(f'{CACHED_METADATA_PATH} {ACTIVE_METADATA_PATH}')
    # sys.exit()
    