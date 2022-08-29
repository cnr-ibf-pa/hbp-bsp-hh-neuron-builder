# Automatic testing



## Introduction

These scripts have been implemented to test automatically the **Hodgkin-Huxley Neuron Builder** and the **NeuroFeatureExtractor** web applications.

These scripts simulate the whole workflow for both applications and if something not works, then the tests ends with an error.

The tests are based to the external tool [Cypress](https://www.cypress.io/) and it is required to run them.
In addition, another useful python script was also implemented to run the automatic tests in a simple way with the support of the parallelism to test the reliability of the server where the web applications were hosted.
If a multiple test is run, the output will show the number of successful and failed tests.


---

## Usage

To run the automatic scripts the [Cypress](https://www.cypress.io/) tool is required.
To install it locally run this command:

`npm install cypress`

the command above assumes that *nodejs* is already installed in the system.

Once [Cypress](https://www.cypress.io/) is installed in the system the scripts can be launched directly using cypress:

```
cypress open -p NFE_Cypress/ 
cypress open -p HHNB_Cypress/
```

to launch a single test or alternatively the python script can be used as follow:

```
python3 ./run_cypress_in_parallel_session.py -p NFE_Cypress/
python3 ./run_cypress_in_parallel_session.py -p HHNB_Cypress/
```

or multiple tests by adding the `-t` option followed by the number of tests that want to launch:

```
python3 ./run_cypress_in_parallel_session.py -p NFE_Cypress/ -t 8
python3 ./run_cypress_in_parallel_session.py -p HHNB_Cypress/ -t 8
```

## Issues

*   If _cypress_ is not available in the global path and it is not found by the python script, the option `-c` can be used by specifying the absolute path of the _cypress_ binary.


*   If a multiple test seems looped or stucked then try to run it using the flag `--enable-browser` that enable the _cypress_ browser view during the tests.

*   The _HHNB_Cypress_ test requires the _EBRAINS authetication session id_ to be executed without errors.
This can be done by followin these steps:
    
    1. Go to https://hbp-bsp-hhnb.cineca.it
    2. Click on the login icon in the top right corner
    3. Insert the credentials on the Ebrains login form
    4. Once you are logged in open the web developer tools and got to the storage tab
    5. Under _Cookies_ select the page
    6. Copy the value of the _sessionid_ item
    7. Open the _HHNB_Cypress/_ forlder.
    8. Open the _cypress.env.json_
    9. Paste the _sessionid_ values (copied in step 6) in the `"sessionid"` field, save and close
    10. Launch the script
    11. Redo if the _sessionid_ code expires 



