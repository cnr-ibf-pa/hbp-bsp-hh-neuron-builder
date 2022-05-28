
# General error messages
CRITICAL_ERROR = '<b>Critical Error !</b><br><br>Please contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a> if the problem persists.'
MODEL_CATALOG_CREDENTIALS_NOT_FOUND = '<b>Error !</b><br><br>Invalid Model Catalog credentials. Set them in your configuraztion file under "/hh_neuron_builder/conf".'
GENERAL_ERROR = '<b>Error !<b>'

#  Model Catalog error messages
MODEL_CATALOG_INVALID_CREDENTIALS = '<b>Error !</b><br><br>Invalid Model Catalog credentials.<br><br>Please, contanct the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a>.'
MODEL_CATALOG_NOT_AVAILABLE = 'The Model Catalog is temporarily not available.<br>Please, try again later.'


# Files error messsages
NO_FILE_UPLOADED = 'No file was uploaded.'
NO_MORE_THEN = 'You can upload only {}.'
WRONG_UPLAODED_FILE = 'The uploaded file/s is wrong.'
ONLY_ACCEPTED_FILE = 'You can upload only a {} file.'
INVALID_FILE = '<b>Invalid file !</b><br><br>Upload a correct {} archive.'
INVALID_SIGNATURE = '<b>Invalid signature !</b><br><br>Uploaded {} archive is corrupted or was modified.'
MARLFORMED_FILE = '<b>Error !</b><br><br>Malformed {} file.'
NO_FILE_TO_DOWNLOAD = 'No file selected to download.' 
NO_FILE_TO_DELETE = 'No file to delete.'
FILE_NOT_FOUND_ERROR = '<b>Error !</b><br><br>File not found.'


# Authentication messages
AUTHENTICATION_INVALID_CREDENTIALS = 'Invalid credentials.'
NOT_AUTHENTICATED = 'User is not authenticated.'
USER_LOGIN_ERROR = 'Unable to logged in the user.'


# HPC error messages
NO_HPC_SELECTED = 'No HPC was selected.'
NO_JOB_SELECTED = 'No job was selected.'
JOB_FETCH_ERROR = '<b>Error !</b><br><br>Some error occurred while fetching jobs on {}.<br>Please contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a> if the problem persists.'
JOB_RESULTS_FETCH_ERRROR = '<b>Error !</b><br><br>Error while fetching job results.'
JOB_SUBMITTED = 'Job submitted on {}.'
JOB_EXPIRED = 'Job {} has expired and no file is present'
HPC_NOT_AVAILABLE = '<b>{}</b> system not available at this moment.<br>Please, try again later...<br><br>If the problem persists contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a>.'


# Analysis error messages
ANALYSIS_ERROR = '<b>Error !</b><br><br>Something went wrong while the analysis process was running.<br>Please contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a> if the problem persists.'
MECHANISMS_PROCESS_ERROR = '<b>Error !</b><br><br>Something went wrong while mechanisms file were building.<br>Please, take a look on the files and if the problem persists contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a>.'
ANALYSIS_PROCESS_ERROR = '<b>Error !</b><br><br>Analysis process was stopped due to the following error:<br><br><i>{}</i><br><br>If the problem persists contact the <a href="https://ebrains.eu/support" target="_blank">EBRAINS support</a>.'
BLUE_NAAS_NOT_AVAILABLE = 'The BlueNaas is temporarily not available.<br>Please, try again later.'


MODEL_SUCCESSFULLY_REGISTERED = '<b>Congratulation, the model was successfully registered in the Model Catalog !</b><br><br>Model\'s info and metadata can be shown <a href="{}" target="_blank">here</a>.<br><br>Once the page is opened in a new tab, if a welcome message is displayed instead of the model instance, please click on the "Authorize" button if requested.<br><br>Leave the current tab open in case you need to recollect the model url.'
MODEL_ALREADY_EXISTS = 'Model already exists on the Model Catalog.'


SIGNATURE_README_DESCRIPTION = \
"""
The "signature" file provides the ".zip" file sign generated from the Hodgikin-Huxley NeuronBuilder.
This signature is unique and is generated using the ".zip" file readed bitwise. 
If you want to upload a previously downloaded ".zip" file, you must provide the original "signature.txt" otherwise the file will be rejected.
"""
