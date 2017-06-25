from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
import pprint
import json
import os
from tools import manage_nsg 
import datetime
import requests

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
from bbp_client.oidc.client import BBPOIDCClient
from bbp_client.document_service.client import Client as DocClient
import bbp_client
from bbp_client.client import *
import bbp_services.client as bsc

# Serving home page for "hh neuron builder appliation"
@login_required(login_url="/login/hbp/")
def home(request):

    my_url = 'https://services.humanbrainproject.eu/idm/v1/api/user/me'
    headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    res = requests.get(my_url, headers = headers)
    res_dict = res.json()
    username = res_dict['username']
    userid = res_dict['id']
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'workflows')
    scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'singlecellmodeling_structure.json')
    opt_model_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'optimizations')

    # create global variables in request.session
    request.session['userid'] = userid
    request.session['username'] = username
    request.session['headers'] = headers
    request.session["singlecellmodeling_structure_path"] = scm_structure_path 
    request.session["optimization_model_path"] = opt_model_path
    request.session['time_info'] = time_info
    request.session['workflows_dir'] = workflows_dir
    


    # user specific dir
    request.session['user_dir'] = os.path.join(workflows_dir, userid, time_info)
    request.session['user_dir_data'] = os.path.join(workflows_dir, userid, time_info, 'data')
    request.session['user_dir_data_feat'] = os.path.join(workflows_dir, userid, time_info, 'data', 'features')
    request.session['user_dir_data_opt'] = os.path.join(workflows_dir, userid, time_info, 'data', 'opt_settings')
    request.session['user_dir_results'] = os.path.join(workflows_dir, userid, time_info, 'results')
    request.session['user_dir_results_opt'] = os.path.join(workflows_dir, userid, time_info, 'results', 'opt')


    # create folders for global data and json files if not existing
    if not os.path.exists(request.session['user_dir_data_feat']):
        os.makedirs(request.session['user_dir_data_feat'])
    if not os.path.exists(request.session['user_dir_data_opt']):
        os.makedirs(request.session['user_dir_data_opt'])
    if not os.path.exists(request.session['user_dir_results_opt']):
        os.makedirs(request.session['user_dir_results_opt'])

    return render(request, 'hh_neuron_builder/home.html')

# serving page for rendering embedded efel gui page
def embedded_efel_gui(request):
    return render(request, 'hh_neuron_builder/embedded_efel_gui.html')

# serving page for rendering workflow page
def workflow(request):
    return render(request, 'hh_neuron_builder/workflow.html')

# serving page for rendering choose optimization model page
def choose_opt_model(request):
    return render(request, 'hh_neuron_builder/choose_opt_model.html')

# serving api call to get list of optimization models
def get_model_list(request):
    model_file = request.session["singlecellmodeling_structure_path"]
    with open(model_file) as json_file:
        model_file_dict = json.load(json_file)
    return HttpResponse(json.dumps(model_file_dict), content_type="application/json")

# serving "set_optimization_parameters" page
def set_optimization_parameters(request):
    return render(request, 'hh_neuron_builder/set_optimization_parameters.html')

# 
def set_feature_folder(request, featurefolder=""):
    feat_path = os.path.split(featurefolder)[0]
    request.session['efel_feature_folder'] = feat_path
    print(request.session['efel_feature_folder'])
    print(request.session['efel_feature_folder'])
    print(request.session['efel_feature_folder'])
    print(request.session['efel_feature_folder'])
    #return HttpResponse(request.session['featurefolder'])
    return HttpResponse("")

def set_optimization_name(request, optimizationname=""):
    request.session['optimization_name'] = optimizationname
    #return HttpResponse(request.session['featurefolder'])
    print(request.session['optimization_name'])
    return HttpResponse("")

# set generation number
def set_gen_num(request, gennum=""):
    print(gennum)
    request.session['gennum'] = float(gennum)
    return HttpResponse("")

# set offspring size
def set_off_size(request, offsize=""):
    print(offsize)
    request.session['offsize'] = float(offsize)
    return HttpResponse("")

# set node number
def set_node_num(request, nodenum=""):
    print(nodenum)
    request.session['nodenum'] = float(nodenum)
    return HttpResponse("")

# set core number
def set_core_num(request, corenum=""):
    print(corenum)
    request.session['corenum'] = float(corenum) 
    return HttpResponse("")

# set run time
def set_run_time(request, runtime=""):
    print(runtime)
    request.session['runtime'] = float(runtime)
    return HttpResponse("")

# set username
def set_username(request, username):
    print(username)
    request.session['username'] = username
    return HttpResponse("")

# set password
def set_password(request, password):
    print(password)
    request.session['password'] = password
    return HttpResponse("")

# run remote optimization
def run_optimization(request):
    username = request.session['username']
    password = request.session['password']
    core_num = request.session['corenum']
    node_num = request.session['nodenum']
    runtime = request.session['runtime']
    res_folder = request.session["result_folder"]
    optimization_name = request.session['optimization_name']
    gennum = request.session['gennum']
    utils_dir = "/app/media/hh_neuron_builder/workflows/utils/"
    opt_folder = os.path.join(request.session["optimization_model_path"], optimization_name)
    time_folder = request.session["wf_dir"]
    dest_folder = os.path.join(res_folder, time_folder, optimization_name)
    zfName = request.session['optimization_name'] + '.zip'
    offsize = request.session['offsize']
    manage_nsg.copy_orig_opt_folder(opt_folder, dest_folder)    

    feature_folder = request.session['feature_folder']
    dest_dir_feat = os.path.join(dest_folder, optimization_name, 'config')
    manage_nsg.replace_feat_files(feature_folder, dest_dir_feat)
    manage_nsg.createzip(dest_folder, utils_dir, gennum, offsize, optimization_name)


    job_sub_resp = manage_nsg.runNSG(username, password, core_num, node_num, runtime, zfName, dest_folder)
    pprint.pprint(job_sub_resp)

    return HttpResponse(job_sub_resp)   
# createzip(foldernameOPTstring, utils_dir, gennum, offsize, _):

# def runNSG(username, password, core_num, node_num, runtime, zfName):

def model_loaded_flag(request):
    if 'optimization_name' in request.session:
        return HttpResponse(json.dumps({"response": request.session['optimization_name']}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")

 


# render page with embedded "neuron as a service" app
def embedded_naas(request):
    return render(request, 'hh_neuron_builder/embedded_naas.html')


# 
def set_optimization_parameters_fetch(request):
    return render(request, 'hh_neuron_builder/set_optimization_parameters_fetch.html')

# get local optimization file list
def get_local_optimization_list(request):
    opt_list = os.listdir("/app/media/hh_neuron_builder/bsp_data_repository/optimizations/")
    final_local_opt_list = {}
    for i in opt_list:
        if "README" in i:
            continue
        final_local_opt_list[i] = i
    return HttpResponse(json.dumps(final_local_opt_list), content_type="application/json")

# get nsg job list
def get_nsg_job_list(request):
    KEY = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
    URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
    headers = {'cipres-appkey' : KEY}
    r = requests.get(URL+"/job/"+CRA_USER+"/" + "NGBW-JOB-BLUEPYOPT_TG-2D269B47A942465EB2E5BC5E999E277D", auth=(CRA_USER, PASSWORD), headers=headers)
    return HttpResponse("")

def upload_to_naas(request):
    optimization_model_path = request.session["optimization_model_path"]
    optimizationname = request.session['optimization_name']
    final_path = os.path.join(optimization_model_path, optimizationname, optimizationname + '.zip')
    r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(final_path, "rb")});
    print(file_path)
    print("uploading to naas")
    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")

