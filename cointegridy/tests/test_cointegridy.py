import os


ROOT = os.getcwd()
CLASSES_PATH = '/cointegridy/src/classes/'
UTILS_PATH = '/cointegridy/src/utils/'
SCRIPTS_PATH = '/cointegridy/scripts/'
EXAMPLES_PATH = '/cointegridy/examples/'

INVALID_FILENAMES = {'__pycache__'}


def test_cointegridy():
    
    for _dir in [CLASSES_PATH, UTILS_PATH, SCRIPTS_PATH, EXAMPLES_PATH]:

        for filename in os.listdir(ROOT+_dir):
            
            if filename in INVALID_FILENAMES: continue
            
            source = None
            with open(ROOT+_dir+filename, 'r') as s_reader:
                source = s_reader.read() + '\n'
            
            if not source: continue
            
            is_valid = True
            try:
                out = compile(source, ROOT+_dir+filename, 'exec')
            except:
                is_vaid = False
            
            assert is_valid, f'class \'{filename[:-3]}\' contains un-interpretable code'





# source = open(your_python_script_name, 'r').read() + '\n'
# compile(source, your_python_script_name, 'exec')