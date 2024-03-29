
<h1 align="center">Cointegridy</h1>

<div align="center">
    <img width="400" src="./misc/img/Cointegridy_logo.png" alt="Insert Epic Logo">
</div>

<br />


Cointegridy Package Usage
-------------------------

 * **package installation:** `pip install -e .`
   
   Running this command from the root of the workspace will install the cointegridy package. The flag `-e` makes sure the cointegridy package is editable so we don't have to re-install the package.
   
   In general you want to: clone, pip install -e ., activate your venv, run the tests, cut a new branch and start developing.

* **package testing:** `python setup.py test [--addopts <pathFromCWDToTestFileName>.py::<test_method>]`

    Running this command from anywhere in the workspace will instruct python to run all tests in the `cointegridy/src/tests/` directory. In order to make a test it must be placed inside the tests directory and named `test_<testFileName>.py` and must have test methods of the format `test_<testName>()`. Additionally the test file does not need to have a main method so it is not recommended.

    Running this command with the optional `--addopts <pathFromCWDToTestFileName>.py` will specify a test file to run. Running this command with the optional `--addopts <pathFromCWDToTestFileName>.py::<test_method>` will limit the test to a specific method.

<br />


API Keys
-------------------------
You will need to update env directory with a new .env file specifying your Binance and Alpha Vantage keys. This file must be downloaded separately.


Cointegridy Virtual Environment Usage
-------------------------

 * The Cointegridy Virtual Environment should be automatically created upon package installation. This package's virtual envrionment is located in `./venv/`.
   
   This virtual environment is activated via the commant `source <path_to_venv>/bin/activate`

<br />


Cointegridy Project Structure
-----------------------------

```
cointegridy
├─ .gitignore
├─ LICENSE.txt
├─ README.md
├─ cointegridy
│  ├─ dev
│  │  ├─ dhpitt_dev
│  │  │  └─ cointegration_dp.ipynb
│  │  ├─ jcanedo_dev
│  │  │  ├─ cryptos_bnc.txt
│  │  │  └─ processor_testor.ipynb
│  │  └─ tcintra_dev
│  │     ├─ processing.ipynb
│  │     └─ processing.py
│  ├─ examples
│  │  ├─ driver_data_loader.py
│  │  ├─ driver_processor.py
│  │  └─ driver_slicetree.py
│  ├─ scripts
│  │  ├─ cointegration.ipynb
│  │  ├─ oracle.ipynb
│  │  └─ stationarity_tests.ipynb
│  ├─ src
│  │  ├─ classes
│  │  │  ├─ Time.py
│  │  │  ├─ backtest.py
│  │  │  ├─ basket.py
│  │  │  ├─ coin.py
│  │  │  ├─ data_loader.py
│  │  │  ├─ exceptions.py
│  │  │  ├─ oracle.py
│  │  │  ├─ portfolio.py
│  │  │  ├─ processor.py
│  │  │  ├─ slicetree.py
│  │  │  └─ trader.py
│  │  └─ utils
│  │     ├─ stats.py
│  │     └─ transforms.py
│  └─ tests
│     ├─ test_Time.py
│     ├─ test_cointegridy.py
│     ├─ test_data_loader.py
│     └─ test_slicetree.py
├─ data
│  ├─ .gitkeep
│  ├─ _metadata.txt
│  └─ dynammic_data
│     └── .gitkeep
├─ misc
│  ├─ img
│  │  ├─ Cointegridy_logo.ai
│  │  ├─ Cointegridy_logo.png
│  │  └─ Cointegridy_logo_small.jpg
│  └─ requirements.txt
├─ setup.cfg
├─ setup.py
└─ workspace.code-workspace
```
