# hbp-bsp-hh-neuron-builder

This project contains the Hodgkin-Huxley Neuron Builder web application integrated in the Human Brain Project - Brain Simulation Platform.

The Web App allows to go through the entire pipeline of a single neuronal cell building: 1) feature extraction; 2) cell optimization; 3) simulation.

The project is implemented via the Django framework and consists of two applications:
  - efelg: to extract electrophysiological features from recorded and/or simulated traces
  - hh-neuron-builder: to go through the neuron builder pipeline. This app integrates efelg in the feature extraction step
  


## How to run it locally

To run the Hodgkin-Huxley Neuron Builder locally, you need to set up a python3 virtual environment,
 install the all requirements that you can find on the "requirements.txt" file, create an OIDC Connect Client to provide
 the authentication with the Ebrains platform and lastly run the server.


#### Ubuntu/Linux:

---

Create the virtual environment:

`virtualenv -p /usb/bin/python3 venv`

Activate it:

`source venv/bin/activate` 

And then install the all requirements:

`pip install -r requirements.txt`


Once you have set up all of prerequisite you need to create the OIDC Connect Client provided by the Ebrains platform.
To do that you can follow the Ebrains guide [here](https://wiki.ebrains.eu/bin/view/Collabs/collaboratory-community-apps/Community%20App%20Developer%20Guide/)
or run the python script _"dev_tool/create_hhnb_dev_client.py"_.

**N.B. You need an account on the Ebrains platform and ensure you have access to the developer token as described on the guide.**

The last thing to do, when you have got your client, is to export the ***"secret"*** and ***"clientId"*** value inside your virtual
environment by append these lines on your _venv/bin/activate_ script. 



    # ADDING OIDC CLIENT_ID AND CLIENT_SECRET
    OIDC_RP_CLIENT_ID=hhnb-client-example
    OIDC_RP_CLIENT_SECRET=fe7e...
    
    export OIDC_RP_CLIENT_ID
    export OIDC_RP_CLIENT_SECRET

**N.B. Make sure to add the right values inside the environment without the quotes.**
    
---

When everything is done just run the server with this command:

`python manage.py runsslserver`

open your browser and go to https://127.0.0.1:8000/hh-neuron-builder to start the application.