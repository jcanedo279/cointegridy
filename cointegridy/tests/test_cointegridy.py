import os


ROOT = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-2])
COINT_PATH = f'{ROOT}/cointegridy'


CLASSES_PATH = f'{COINT_PATH}/src/classes/'
UTILS_PATH = f'{COINT_PATH}/src/utils/'
SCRIPTS_PATH = f'{COINT_PATH}/scripts/'
EXAMPLES_PATH = f'{COINT_PATH}/examples/'

INVALID_FILENAMES = {'__pycache__', '.DS_Store'}

def test_cointegridy_compiles():
    for _dir in [CLASSES_PATH, UTILS_PATH, SCRIPTS_PATH, EXAMPLES_PATH]:
        for filename in os.listdir(_dir):
            if filename in INVALID_FILENAMES: continue
            source = None
            with open(_dir+filename, 'r') as s_reader:
                source = s_reader.read() + '\n'
            
            if not source: continue
            
            try:
                compile(source, _dir+filename, 'exec')
            except:
                assert False, f'class \'{filename[:-3]}\' contains un-interpretable code'
test_cointegridy_compiles()