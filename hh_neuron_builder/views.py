from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
import pprint
import json
import os
import shutil
from tools import hpc_job_manager
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

@login_required(login_url="/login/hbp/")
def home(request):
    """
    Serving home page for "hh neuron builder" application
    """

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
    request.session['singlecellmodeling_structure_path'] = scm_structure_path 
    request.session['optimization_model_path'] = opt_model_path
    request.session['workflows_dir'] = workflows_dir
    request.session['opt_flag'] = False

    # delete keys if present in request.session
    request.session.pop('gennum', None)
    request.session.pop('offsize', None)
    request.session.pop('nodenum', None)
    request.session.pop('corenum', None)
    request.session.pop('runtime', None)
    request.session.pop('username', None)
    request.session.pop('password', None)
    request.session.pop('hpc_sys', None)
    request.session.pop('username_fetch', None)
    request.session.pop('password_fetch', None)
    request.session.pop('hpc_sys_fetch', None)

    return render(request, 'hh_neuron_builder/home.html')


def create_wf_folders(request, wf_type="new"):
    """
    Create folders for current workflow
    """
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session['workflows_dir']
    userid = request.session['userid']

    # user specific dir
    request.session['time_info'] = time_info
    request.session['user_dir'] = os.path.join(workflows_dir, userid, time_info)
    request.session['user_dir_data'] = os.path.join(workflows_dir, userid, time_info, 'data')
    request.session['user_dir_data_feat'] = os.path.join(workflows_dir, userid, time_info, 'data', 'features')
    request.session['user_dir_data_opt_set'] = os.path.join(workflows_dir, userid, time_info, 'data', 'opt_settings')
    request.session['user_dir_data_opt_launch'] = os.path.join(workflows_dir, userid, time_info, 'data', 'opt_launch')
    request.session['user_dir_results'] = os.path.join(workflows_dir, userid, time_info, 'results')
    request.session['user_dir_results_opt'] = os.path.join(workflows_dir, userid, time_info, 'results', 'opt')

    # create folders for global data and json files if not existing
    if not os.path.exists(request.session['user_dir_data_feat']):
        os.makedirs(request.session['user_dir_data_feat'])
    if not os.path.exists(request.session['user_dir_data_opt_set']):
        os.makedirs(request.session['user_dir_data_opt_set'])
    if not os.path.exists(request.session['user_dir_data_opt_launch']):
        os.makedirs(request.session['user_dir_data_opt_launch'])
    if not os.path.exists(request.session['user_dir_results_opt']):
        os.makedirs(request.session['user_dir_results_opt'])

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")

    
def embedded_efel_gui(request):
    """
    Serving page for rendering embedded efel gui page
    """

    return render(request, 'hh_neuron_builder/embedded_efel_gui.html')


def workflow(request, wf="new"):
    """
    Serving page for rendering workflow page
    """

    return render(request, 'hh_neuron_builder/workflow.html')


def choose_opt_model(request):
    """
    Serving page for rendering choose optimization model page
    """

    return render(request, 'hh_neuron_builder/choose_opt_model.html')


def get_model_list(request):
    """
    Serving api call to get list of optimization models
    """
    model_file = request.session["singlecellmodeling_structure_path"]
    with open(model_file) as json_file:
        model_file_dict = json.load(json_file)

    return HttpResponse(json.dumps(model_file_dict), content_type="application/json")


def set_optimization_parameters(request):
    """
    Serving "set_optimization_parameters" page
    """

    return render(request, 'hh_neuron_builder/set_optimization_parameters.html')


def copy_feature_files(request, featurefolder = ""):
    shutil.copy(os.path.join(os.sep, featurefolder, 'features.json'), request.session['user_dir_data_feat'])
    shutil.copy(os.path.join(os.sep, featurefolder, 'protocols.json'), request.session['user_dir_data_feat'])

    return HttpResponse(json.dumps({"response":featurefolder}), content_type="application/json")


def fetch_opt_set_file(request, source_opt_name=""):
    """
    Set optimization setting file
    """

    opt_model_path = request.session['optimization_model_path']
    user_dir_data_opt = request.session['user_dir_data_opt_set']
    request.session['source_opt_name'] = source_opt_name
    request.session['source_opt_zip'] = os.path.join(opt_model_path, source_opt_name, source_opt_name + '.zip')
    shutil.copy(request.session['source_opt_zip'], user_dir_data_opt)

    return HttpResponse("")


def run_optimization(request):
    """
    Run optimization on remote systems
    """
    
    # fetch information from the session variable
    username = request.session['username']
    password = request.session['password']
    core_num = request.session['corenum']
    node_num = request.session['nodenum']
    runtime = request.session['runtime']
    gennum = request.session['gennum']
    time_info = request.session['time_info']
    offsize = request.session['offsize']
    source_opt_name = request.session['source_opt_name']
    dest_dir = request.session['user_dir_data_opt_launch']
    user_dir_data_opt = request.session['user_dir_data_opt_set']
    source_opt_zip = request.session['source_opt_zip']
    hpc_sys = request.session['hpc_sys']
    source_feat = request.session['user_dir_data_feat']
    opt_res_dir = request.session['user_dir_results_opt']

    # build new optimization name
    idx = source_opt_name.rfind('_')
    opt_name = source_opt_name[:idx] + "_" + time_info

    if hpc_sys == "nsg":
        nsg_obj = hpc_job_manager.Nsg(username=username, password=password, core_num=core_num, node_num=node_num, \
                runtime=runtime, gennum=gennum, offsize=offsize, dest_dir=dest_dir, source_opt_zip=source_opt_zip, opt_name=opt_name, \
                source_feat=source_feat, opt_res_dir=opt_res_dir)
        nsg_obj.createzip()
        resp = nsg_obj.runNSG()
        if resp['status_code'] == 200:
            request.session['opt_flag'] = True
        else:
            request.session['opt_flag'] = False

    
    return HttpResponse(json.dumps(resp))



def model_loaded_flag(request):
    if 'res_file_name' in request.session:
        return HttpResponse(json.dumps({"response": request.session['res_file_name']}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")


def embedded_naas(request):
    """
    Render page with embedded "neuron as a service" app
    """

    return render(request, 'hh_neuron_builder/embedded_naas.html')


def set_optimization_parameters_fetch(request):
    """
    Render page for optimization parameter fetch
    """

    return render(request, 'hh_neuron_builder/set_optimization_parameters_fetch.html')


def get_local_optimization_list(request):
    """
    Get the list of locally stored optimizations
    """
    opt_list = os.listdir("/app/media/hh_neuron_builder/bsp_data_repository/optimizations/")
    final_local_opt_list = {}
    for i in opt_list:
        if "README" in i:
            continue
        final_local_opt_list[i] = i
    return HttpResponse(json.dumps(final_local_opt_list), content_type="application/json")



def upload_to_naas(request):
    res_folder = request.session['user_dir_results_opt']
    res_folder_ls = os.listdir(res_folder) 
    request.session['res_file_name'] = os.path.splitext(res_folder_ls[0])[0]
    abs_res_file = os.path.join(res_folder, res_folder_ls[0])

    #optimization_model_path = request.session["optimization_model_path"]
    #source_opt_name = request.session['source_opt_name']
    #final_path = os.path.join(optimization_model_path, source_opt_name, source_opt_name + '.zip')
    #r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(final_path, "rb")});
    r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(abs_res_file, "rb")});
    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")


def submit_run_param(request):
    """
    Save user's optimization parameters
    """
    #selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST
    request.session['gennum'] = int(form_data['gen-max'])
    request.session['offsize'] = int(form_data['offspring'])
    request.session['nodenum'] = int(form_data['node-num']) 
    request.session['corenum'] = int(form_data['core-num'])  
    request.session['runtime'] = float(form_data['runtime'])
    request.session['username'] = form_data['username']
    request.session['password'] = form_data['password']
    request.session['hpc_sys'] = form_data['hpc_sys']

    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")


def submit_fetch_param(request):
    """
    Save user's optimization parameters
    """
    #selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST
    request.session['username_fetch'] = form_data['username_fetch']
    request.session['password_fetch'] = form_data['password_fetch']
    request.session['hpc_sys_fetch'] = form_data['hpc_sys_fetch']

    return HttpResponse(json.dumps({"response": "nothing"}), content_type="application/json")

def check_cond_exist(request):
    """
    Check if conditions for performing steps are present.
    The function checks on current workflow folders whether files are present to go on with the workflow.
    The presence of simulation parameters are also checked.
    """

    response = {"feat":False, "opt_files":False, "opt_set":False, "run_sim":False, "opt_flag":False}
    data_feat = request.session['user_dir_data_feat']
    data_opt = request.session['user_dir_data_opt_set']
    result_opt = request.session['user_dir_results_opt']
    if os.path.isfile(os.path.join(data_feat, "features.json")) and \
        os.path.isfile(os.path.join(data_feat, "protocols.json")):
        response['feat'] = True
    if not os.listdir(data_opt) == []:
        response['opt_files'] = True
    if not os.listdir(result_opt) == []:
        response['run_sim'] = True
    if ('gennum' and 'offsize' and 'nodenum' and 'corenum' and 'runtime' and 'username' and 'password') in request.session:
        response['opt_set'] = True
    if request.session['opt_flag']:
        response['opt_flag'] = True
   

    return HttpResponse(json.dumps(response), content_type="application/json")



# delete feature files
def delete_feature_files(request):
    feat_folder = request.session['user_dir_data_feat']
    shutil.rmtree(feat_folder)
    os.makedirs(feat_folder)
    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")
    

def delete_opt_files(request):
    opt_folder = request.session['user_dir_data_opt_set']
    shutil.rmtree(opt_folder)
    os.makedirs(opt_folder)
    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")

def launch_optimization(request):
    pass


def upload_files(request, filetype = ""):
    filename_list = request.FILES.getlist('opt-res-file')

    if filetype == "feat":
        final_res_folder = request.session['user_dir_data_feat']
        ext = '.json'

    elif filetype == "optset":
        final_res_folder = request.session['user_dir_data_opt_set']
        ext = '.zip'

    elif filetype == "optrun":
        final_res_folder = request.session['user_dir_results_opt']
        ext = '.zip'

    if not filename_list:
        return HttpResponse(json.dumps({"resp":False}), content_type="application/json") 

    #if os.listdir(final_res_folder):
    #    shutil.rmtree(final_res_folder)
    #    os.makedirs(final_res_folder)

    for k in filename_list:
        filename = k.name
        if not filename.endswith(ext):
            continue
        final_res_file = os.path.join(final_res_folder, filename)
        final_file = open(final_res_file, 'w')
        if k.multiple_chunks():
            for chunk in k.chunks():
                final_file.write(chunk)
            final_file.close()
        else:
            final_file.write(k.read())
            final_file.close()

    return HttpResponse(json.dumps({"resp":"Success"}), content_type="application/json") 



def get_nsg_job_list(request):
    return HttpResponse(json.dumps({"safa":"fff", "sadfsadfadasdfaasdfasdf":"fff"}), content_type="application/json") 
    hpc_sys_fetch = request.session['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
        username_fetch = request.session['username_fetch']
        password_fetch = request.session['password_fetch']
        opt_res_dir = request.session['user_dir_results_opt']

        nsg_obj = hpc_job_manager.Nsg(username_fetch=username_fetch, password_fetch=password_fetch, \
               opt_res_dir=opt_res_dir) 

        resp = nsg_obj.fetch_job_list()

    return HttpResponse(json.dumps(resp), content_type="application/json") 

def get_nsg_job_details(request, jobid=""):
    return HttpResponse(json.dumps({"job_id": jobid, "job_date_submitted":"2017-07-24T16:40:21-07:00", "job_stage":"COMPLETED"}), content_type="application/json") 

    hpc_sys_fetch = request.session['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
        username_fetch = request.session['username_fetch']
        password_fetch = request.session['password_fetch']
        opt_res_dir = request.session['user_dir_results_opt']

        nsg_obj = hpc_job_manager.Nsg(username_fetch=username_fetch, password_fetch=password_fetch, \
               opt_res_dir=opt_res_dir) 

        resp = nsg_obj.fetch_job_details(jobid)
    pprint.pprint(resp)
    return HttpResponse(json.dumps(resp), content_type="application/json") 
