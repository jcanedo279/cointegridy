import os
import sys
import subprocess

try:
    import setuptools
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'setuptools-scm==6.3.2'])
from setuptools import setup, find_packages
from setuptools.command.egg_info import egg_info

try:
    import termcolor
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'termcolor==1.1.0'])
from termcolor import cprint



ROOT = f'{os.path.dirname(os.path.abspath(__file__))}/'

if not os.path.exists(f'{ROOT}venv/') or (not 'venv' in sys.executable):
    cprint('Please create a venv and activate it before running this file', 'red')
    sys.exit()


class egg_info_parse(egg_info):
    """Includes license file into `.egg-info` folder."""

    def run(self):
        # don't duplicate license into `.egg-info` when building a distribution
        if not self.distribution.have_run.get('install', True):
            # `install` command is in progress, copy license
            self.mkpath(self.egg_info)
            self.copy_file('LICENSE.txt', self.egg_info)

        egg_info.run(self)

def parse_setup_requirements():
    req_path = f'{ROOT}misc/requirements.txt'
    reqs = []
    with open(req_path, 'r') as f_reader:
        for line in f_reader.readlines():
            if not '==' in line: continue
            _line = line[:-1] if line.endswith('\n') else line
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', _line])
            reqs.append(_line)
    return reqs

    



setup_config = {
    'name': 'cointegridy',
    
    'version': '0.0.1',
    
    'license': 'MIT',
    
    'author': 'Jorge Canedo, Thomas Cintra, David Pitt',
    
    'url': 'https://github.com/jcanedo279/cointegridy',
    
    'cmdclass': {'egg_info': egg_info_parse}, ## Include LICENSE.txt into package
    
    ## Barebone requirements for package contents
    'install_requires': parse_setup_requirements(),
    
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

