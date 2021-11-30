
<h1 align="center">Cointegridy</h1>

![Epic Logo](./misc/img/Cointegridy_logo.png)
<style type="text/css">
    img {
        width: 400px;
        display: block;
        margin: 0 auto;
    }
</style>


Cointegridy Package Usage
-------------------------

 * **package installation:** `pip install -e .`
   
   Running this command from the root of the workspace will install the cointegridy package. The flag `-e` makes sure the cointegridy package is editable so we don't hae to re-install the package.
    
    <br />

* **package testing:** `python setup.py test [--addopts <pathFromCWDToTestFileName>.py::<test_method>]`

    Running this command from anywhere in the workspace will instruct python to run all tests in the `cointegridy/src/tests/` directory. In order to make a test it must be placed inside the tests directory and named `test_<testFileName>.py` and must have test methods of the format `test_<testName>()`. Additionally the test file does not need to have a main method so it is not recommended.

    Running this command with the optional `--addopts <pathFromCWDToTestFileName>.py` will specify a test file to run. Running this command with the optional `--addopts <pathFromCWDToTestFileName>.py::<test_method>` will limit the test to a specific method.






