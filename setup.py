
import os
import sys
import subprocess


MIN_PYTHON_VERSION = (3,6,0)
SETUPTOOLS_VERSION = 'setuptools-scm==6.3.2'

ROOT = f'{os.path.dirname(os.path.abspath(__file__))}/'

VENV_ACTIVATE = f'{ROOT}venv/bin/activate'
VENV_EXECUTABLE = f'{ROOT}venv/bin/python'
VENV_PIP = f'{ROOT}venv/bin/pip'

LOC_BASH = f'{ROOT}bin/bash'


##########################
## CHECK PYTHON VERSION ##
if sys.version_info < MIN_PYTHON_VERSION:
    print(f"Must be using Python >= {MIN_PYTHON_VERSION}")
    sys.exit(1)


SETUP_MODE = ''
if 'test' in sys.argv: SETUP_MODE = 'test'


#####################
## LOAD SETUPTOOLS ##
try:
    import setuptools
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', SETUPTOOLS_VERSION])
from setuptools import setup, find_packages
from setuptools.command.egg_info import egg_info


###############
## MAKE VENV ##
if not os.path.exists(f'{ROOT}venv/'):
    print('Please create a venv and activate it before running this file')
    print('Creating a local venv')
    subprocess.check_call([sys.executable, '-m', 'venv', './venv'])

###################
## ACTIVATE VENV ##
if not 'venv' in sys.executable:
    print("No 'venv' detected... Re-loading Cointegridy from 'venv'...")
    subprocess.call([VENV_EXECUTABLE, __file__] + sys.argv[1:])
    sys.exit(0)


class egg_info_parse(egg_info):
    """Includes license file into `.egg-info` folder."""

    def run(self):
        # don't duplicate license into `.egg-info` when building a distribution
        if not self.distribution.have_run.get('install', True):
            # `install` command is in progress, copy license
            self.mkpath(self.egg_info)
            self.copy_file('LICENSE.txt', self.egg_info)

        egg_info.run(self)


###############################
## LOAD MINIMUM REQUIREMENTS ##
def parse_setup_requirements():
    req_path = f'{ROOT}env/requirements.txt'
    reqs = []
    with open(req_path, 'r') as f_reader:
        for line in f_reader.readlines():
            if not '==' in line: continue
            _line = line[:-1] if line.endswith('\n') else line
            if SETUP_MODE!='test':
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', _line])
            reqs.append(_line)
    return reqs

    
PARSED_REQUIREMENTS = [] if SETUP_MODE=='test' else parse_setup_requirements()


setup_config = {
    'name': 'cointegridy',
    
    'version': '0.0.1',
    
    'license': 'MIT',
    
    'author': 'Jorge Canedo, Thomas Cintra, David Pitt',
    
    'url': 'https://github.com/jcanedo279/cointegridy',
    
    'cmdclass': {'egg_info': egg_info_parse}, ## Include LICENSE.txt into package
    
    ## Barebone requirements for package contents
    'install_requires': PARSED_REQUIREMENTS,
    
    'setup_requires': ('pytest-runner', 'flake8',),
    
    'test_suite': 'tests',
    
    'tests_require': ('pytest',),
    
    'classifiers': [
        "Programming Language :: Python :: 3.7-3.9",
        "License :: MIT License",
        "Operating System :: LINUX + OS",
    ],
}



if __name__ == '__main__': ## Important to ensure tests only run once
    setup( **setup_config )
    

