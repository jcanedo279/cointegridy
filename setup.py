from setuptools import setup, find_packages
from setuptools.command.egg_info import egg_info



class egg_info_parse(egg_info):
    """Includes license file into `.egg-info` folder."""

    def run(self):
        # don't duplicate license into `.egg-info` when building a distribution
        if not self.distribution.have_run.get('install', True):
            # `install` command is in progress, copy license
            self.mkpath(self.egg_info)
            self.copy_file('LICENSE.txt', self.egg_info)

        egg_info.run(self)




setup_config = {
    'name': 'cointegridy',
    
    'version': '0.0.1',
    
    'license': 'MIT',
    
    'author': 'Jorge Canedo, Thomas Cintra, David Pitt',
    
    'url': 'https://github.com/jcanedo279/cointegridy',
    
    'cmdclass': {'egg_info': egg_info_parse}, ## Include LICENSE.txt into package
    
    # 'packages': 'setup.my_test_suite', ## TODO:: Apparently dangerous, look into endpoints
    
    ## Barebone requirements for package contents
    'install_requires': (
        ## CLASSES ##
        ## backtest
        'pandas==1.3.4',
        'numpy==1.21.4',
        'sklearn==0.0',
        'statsmodels==0.13.1',
        ## processor
        'requests==2.26.0',
        'matplotlib==3.5.0',
        'python-dotenv==0.19.2',
        # slicetree
        'treelib==1.6.1',
        ## Time
        'pytz==2021.3',
        ## SCRIPTS ##
        'hurst==0.0.5',
        'pycoingecko==2.2.0',
    ),
    
    'extras_require': { ## TODO:: Requirements for a specific version
        'cli': ( ## pip install -e .[cli]
            'ipykernel==6.5.1',
            'ipython==7.29.0',
        ),
    },
    
    'setup_requires': ('pytest-runner', 'flake8',),
    
    'test_suite': 'tests',
    
    'tests_require': ('pytest',),
    
    'classifiers': [
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: LINUX + OS",
    ],
}



if __name__ == '__main__': ## Important to ensure tests only run once
    setup( **setup_config )

