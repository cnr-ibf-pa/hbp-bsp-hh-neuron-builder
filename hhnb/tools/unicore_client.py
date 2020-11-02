"""
Helper methods for using UNICORE's REST API

For a full API reference and examples, have a look at
https://sourceforge.net/p/unicore/wiki/REST_API
https://sourceforge.net/p/unicore/wiki/REST_API_Examples

Author: Bernd Schuller
Modified by: Luca Leonardo Bologna

"""
import requests
import json
import time
import os


def get_sites():
    """
    Get info about the known sites in the HPC Platform.
    """
    sites = {}
    sites['JUQUEEN'] = {'name': 'JUQUEEN (JSC)', 'id': 'JUQUEEN', 'url': "https://hbp-unic.fz-juelich.de:7112/HBP_JUQUEEN/rest/core"}
    sites['JURECA'] = {'name': 'JURECA (JSC)', 'id': 'JURECA', 'url': "https://hbp-unic.fz-juelich.de:7112/HBP_JURECA/rest/core"}
    sites['VIZ_CSCS'] = {'name': 'VIZ (CSCS)', 'id': 'VIS', 'url': "https://contra.cscs.ch:8080/VIS-CSCS/rest/core"}
    sites['BGQ_CSCS'] = {'name': 'BGQ (CSCS)', 'id': 'BGQ', 'url': "https://contra.cscs.ch:8080/BGQ-CSCS/rest/core"}
    sites['MARE_NOSTRUM'] = {'name': 'Mare Nostrum (BSC)', 'id': 'MN', 'url': "https://unicore-hbp.bsc.es:8080/BSC-MareNostrum/rest/core"}
    sites['PICO'] = {'name': 'PICO (CINECA)', 'id': 'PICO', 'url': "https://grid.hpc.cineca.it:9111/CINECA-PICO/rest/core"}
    sites['GALILEO'] = {'name': 'GALILEO (CINECA)', 'id': 'GALILEO', 'url': "https://grid.hpc.cineca.it:9111/CINECA-GALILEO/rest/core"}
    sites['FERMI'] = {'name': 'FERMI (CINECA)', 'id': 'FERMI', 'url': "https://grid.hpc.cineca.it:9111/CINECA-FERMI/rest/core"}
    sites['KIT'] = {'name': 'Cloud storage (KIT)', 'id': 'S3-KIT', 'url': "https://unicore.data.kit.edu:8080/HBP-KIT/rest/core"}
    sites['DAINT-CSCS'] = {'name': 'PIZDAINT (CSCS)', 'url': 'https://unicoregw.cscs.ch:8080/DAINT-CSCS/rest/core', 'id': 'CSCS'}
    sites['SA-CSCS'] = {'name': 'SERVICE ACCOUNT PIZDAINT (CSCS)', 'url': 'https://bspsa.cineca.it', 'id': 'SA-CSCS'}
    return sites


def get_site(name):
    return get_sites().get(name, None)


def get_properties(resource, headers={}, proxies={}):
    """
    Get JSON properties of a resource.
    """
    my_headers = headers.copy()
    my_headers['Accept'] = "application/json"
    r = requests.get(resource, headers=my_headers, verify=False, proxies=proxies)
    if r.status_code != 200:
        raise RuntimeError("Error getting properties: %s" % r.status_code)
    else:
        return r.json()

    
def get_working_directory(job, headers={}, properties=None, proxies={}):
    """
    Returns the URL of the working directory resource of a job.
    """
    if properties is None:
        properties = get_properties(job,headers, proxies=proxies)
    return properties['_links']['workingDirectory']['href']


def invoke_action(resource, action, headers, data={}, proxies={}):
    my_headers = headers.copy()
    my_headers['Content-Type'] = "application/json"
    action_url = get_properties(resource, headers, proxies=proxies)['_links']['action:'+action]['href']
    r = requests.post(action_url, data=json.dumps(data), headers=my_headers, verify=False, proxies=proxies)
    if r.status_code != 200:
        raise RuntimeError("Error invoking action: %s" % r.status_code)
    return r.json()


def upload(destination, file_desc, headers, proxies={}):
    my_headers = headers.copy()
    my_headers['Content-Type'] = "application/octet-stream"
    name = file_desc['To']
    data = file_desc['Data']
    # TODO file_desc could refer to local file
    r = requests.put(destination+"/"+name, data=data, headers=my_headers, verify=False, proxies=proxies)
    if r.status_code != 204:
        raise RuntimeError("Error uploading data: %s" % r.status_code)


def submit(url, job, headers, inputs=[], proxies={}):
    """
    Submits a job to the given URL, which can be the ".../jobs" URL or a ".../sites/site_name/" URL.
    If inputs is not empty, the listed input data files are uploaded to the job's working directory,
    and a "start" command is sent to the job.
    """
    my_headers = headers.copy()
    my_headers['Content-Type'] = "application/json"

    if len(inputs) > 0:
        # make sure UNICORE does not start the job before we have uploaded data
        job['haveClientStageIn'] = 'true'
    
    if proxies:
        os.environ["no_proxy"] = ""
    r = requests.post(url, data=json.dumps(job), headers=my_headers, verify=False, proxies=proxies)
    print(r.status_code, r.text)
    if r.status_code != 201:
        raise RuntimeError("Error submitting job: %s" % r.status_code)
    else:
        job_url = r.headers['Location']

    #  upload input data and explicitely start job
    if len(inputs) > 0:
        working_directory = get_working_directory(job_url, headers)
        for i in inputs:
            upload(working_directory+"/files", i, headers)
        invoke_action(job_url, "start", headers)
    
    return job_url

    
def is_running(job, headers={}, proxies={}):
    """
    Check status for a job.
    """
    properties = get_properties(job, headers, proxies=proxies)
    status = properties['status']
    return ("SUCCESSFUL" != status) and ("FAILED" != status)


def wait_for_completion(job, headers={}, refresh_function=None, refresh_interval=360):
    """
    Wait until job is done if refresh_function is not none, it will be called
    to refresh the "Authorization" header refresh_interval is in seconds.
    """
    sleep_interval = 10
    do_refresh = refresh_function is not None
    # refresh every N iterations
    refresh = int(1 + refresh_interval / sleep_interval)
    count = 0
    while is_running(job, headers):
        time.sleep(sleep_interval)
        count += 1
        if do_refresh and count == refresh:
            headers['Authorization'] = refresh_function()
            count = 0


def file_exists(wd, name, headers, proxies={}):
    """
    Check if a file with the given name exists:
    if yes, return its URL;
    if no, return None
    """
    files_url = get_properties(wd, headers, proxies=proxies)['_links']['files']['href']
    children = get_properties(files_url, headers, proxies=proxies)['children']
    return name in children or "/" + name in children


def get_file_content(file_url, headers, check_size_limit=True, MAX_SIZE=30240000, proxies={}):
    """
    Download binary file data.
    """
    if check_size_limit:
        size = get_properties(file_url, headers, proxies=proxies)['size']
        if size > MAX_SIZE:
            raise RuntimeError("File size too large!")
    my_headers = headers.copy()
    my_headers['Accept'] = "application/octet-stream"
    r = requests.get(file_url, headers=my_headers, verify=False, proxies=proxies)
    if r.status_code != 200:
        raise RuntimeError("Error getting file data: %s" % r.status_code)
    else:
        return r.content


def list_files(dir_url, auth, path="/", proxies={}):
    return get_properties(dir_url+"/files"+path, auth, proxies=proxies)['children']


def get_oidc_auth(token=None):
    """
    Returns HTTP headers containing OIDC bearer token.
    """
    return {'Authorization': token}
