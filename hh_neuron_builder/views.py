from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
import pprint
import json
import os
import shutil
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
    workflows_dir = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'workflows')
    scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'singlecellmodeling_structure.json')
    opt_model_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'optimizations')

    # create global variables in request.session
    request.session['userid'] = userid
    request.session['username'] = username
    request.session['headers'] = headers
    request.session["singlecellmodeling_structure_path"] = scm_structure_path 
    request.session["optimization_model_path"] = opt_model_path
    request.session['workflows_dir'] = workflows_dir

    request.session.pop('gennum', None)
    request.session.pop('offsize', None)
    request.session.pop('nodenum', None)
    request.session.pop('corenum', None)
    request.session.pop('runtime', None)
    request.session.pop('username', None)
    request.session.pop('password', None)

    return render(request, 'hh_neuron_builder/home.html')


# create folders for current workflow
def create_wf_folders(request, wf_type="new"):
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session['workflows_dir']
    userid = request.session['userid']

    # user specific dir
    request.session['time_info'] = time_info
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

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")
    

# serving page for rendering embedded efel gui page
def embedded_efel_gui(request):
    return render(request, 'hh_neuron_builder/embedded_efel_gui.html')

# serving page for rendering workflow page
def workflow(request, wf="new"):
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
def copy_feature_files(request, featurefolder=""):
    shutil.copy(os.path.join(os.sep, featurefolder, 'features.json'), request.session['user_dir_data_feat'])
    shutil.copy(os.path.join(os.sep, featurefolder, 'protocols.json'), request.session['user_dir_data_feat'])
    return HttpResponse(json.dumps({"response":featurefolder}), content_type="application/json")

#
def fetch_opt_set_file(request, optimizationname=""):
    request.session['optimization_name'] = optimizationname
    opt_model_path = request.session['optimization_model_path']
    user_dir_data_opt = request.session['user_dir_data_opt']
    shutil.copy(os.path.join(opt_model_path, optimizationname, optimizationname + '.zip'), user_dir_data_opt)
    return HttpResponse("")


# run remote optimization
def run_optimization(request):
    username = request.session['username']
    password = request.session['password']
    core_num = request.session['corenum']
    node_num = request.session['nodenum']
    runtime = request.session['runtime']
    gennum = request.session['gennum']
    offsize = request.session['offsize']
    res_folder = request.session["result_folder"]
    optimization_name = request.session['optimization_name']
    utils_dir = os.path.join(settings.MEDIA_ROOT, '/hh_neuron_builder/workflows/utils/')
    opt_folder = os.path.join(request.session["optimization_model_path"], optimization_name)
    time_folder = request.session["wf_dir"]
    dest_folder = os.path.join(res_folder, time_folder, optimization_name)
    zfName = request.session['optimization_name'] + '.zip'
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
    if 'res_file_name' in request.session:
        return HttpResponse(json.dumps({"response": request.session['res_file_name']}), content_type="application/json")
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
    res_folder = request.session['user_dir_results_opt']
    res_folder_ls = os.listdir(res_folder) 
    request.session['res_file_name'] = os.path.splitext(res_folder_ls[0])[0]
    abs_res_file = os.path.join(res_folder, res_folder_ls[0])

    #optimization_model_path = request.session["optimization_model_path"]
    #optimizationname = request.session['optimization_name']
    #final_path = os.path.join(optimization_model_path, optimizationname, optimizationname + '.zip')
    #r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(final_path, "rb")});
    r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(abs_res_file, "rb")});
    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")

def submit_run_param(request):
    #selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST
    request.session['gennum'] = int(form_data['gen-max'])
    request.session['offsize'] = int(form_data['offspring'])
    request.session['nodenum'] = int(form_data['node-num']) 
    request.session['corenum'] = int(form_data['core-num'])  
    request.session['runtime'] = float(form_data['runtime'])
    request.session['username'] = form_data['username']
    request.session['password'] = form_data['password']

    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")

# check if conditions for performing steps are in present
def check_cond_exist(request):
    response = {"feat":False, "opt_files":False, "opt_set":False, "run_sim":False}
    data_feat = request.session['user_dir_data_feat']
    data_opt = request.session['user_dir_data_opt']
    result_opt = request.session['user_dir_results_opt']
    if not os.listdir(data_feat) == []:
        response['feat'] = True
    if not os.listdir(data_opt) == []:
        response['opt_files'] = True
    if not os.listdir(result_opt) == []:
        response['run_sim'] = True
    if ('gennum' and 'offsize' and 'nodenum' and 'corenum' and 'runtime' and 'username' and 'password') in request.session:
        response['opt_set'] = True
    return HttpResponse(json.dumps(response), content_type="application/json")

# upload .zip file for model upload
def upload_run_model(request):
    filename_list = request.FILES.getlist('opt-run-file')
    if not filename_list:
        return HttpResponse(json.dumps({"resp":False}), content_type="application/json") 

    firstfile = filename_list[0]
    filename = filename_list[0].name
    final_res_folder = request.session['user_dir_results_opt']
    if os.listdir(final_res_folder):
        shutil.rmtree(final_res_folder)
        os.makedirs(final_res_folder)
    final_res_file_name = os.path.join(final_res_folder, filename)
    final_res_file = open(final_res_file_name, 'w')
    if firstfile.multiple_chunks():
        for chunk in firstfile.chunks():
            final_res_file.write(chunk)
        final_res_file.close()
    else:
        final_res_file.write(firstfile.read())
        final_res_file.close()

    return HttpResponse(json.dumps({"resp":"response"}), content_type="application/json") 


# delete feature files
def delete_feature_files(request):
    feat_folder = request.session['user_dir_data_feat']
    shutil.rmtree(feat_folder)
    os.makedirs(feat_folder)
    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")
    

def delete_opt_files(request):
    opt_folder = request.session['user_dir_data_opt']
    shutil.rmtree(opt_folder)
    os.makedirs(opt_folder)
    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")
