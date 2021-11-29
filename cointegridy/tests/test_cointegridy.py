import os


ROOT = os.getcwd()
 
CLASSES_PATH = '/cointegridy/src/classes/'
UTILS_PATH = '/cointegridy/src/utils/'
SCRIPTS_PATH = '/cointegridy/scripts/'
EXAMPLES_PATH = '/cointegridy/examples/'

INVALID_FILENAMES = {'__pycache__', '.DS_Store'}


def test_cointegridy_compiles():
    
    for _dir in [CLASSES_PATH, UTILS_PATH, SCRIPTS_PATH, EXAMPLES_PATH]:

        for filename in os.listdir(ROOT+_dir):
            
            if filename in INVALID_FILENAMES: continue
            
            source = None
            with open(ROOT+_dir+filename, 'r') as s_reader:
                source = s_reader.read() + '\n'
            
            if not source: continue
            
            try:
                compile(source, ROOT+_dir+filename, 'exec')
            except:
                assert False, f'class \'{filename[:-3]}\' contains un-interpretable code'
