""" Views"""

import sys
import pprint
import json
import logging
import os
import zipfile
import subprocess
import shutil
import tarfile
import datetime
import requests

# import django libs
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout

# import hbp modules

from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
import hbp_service_client
import hbp_service_client.storage_service.client as service_client
import hbp_service_client.storage_service.api as service_api_client
from hbp_service_client.document_service.service_locator import ServiceLocator
from hbp_service_client.document_service.client import Client
from hbp_service_client.document_service.requestor import DocNotFoundException, DocException

# import local tools
from tools import hpc_job_manager
from tools import wf_file_manager
from tools import resources

# import common tools library for the bspg project
sys.path.append(os.path.join(settings.BASE_DIR))
from ctools import manage_auth

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
accesslogger = logging.getLogger('hhnb_access.log')
accesslogger.addHandler(logging.FileHandler('/var/log/bspg/hhnb_access.log'))
accesslogger.setLevel(logging.DEBUG)


@login_required(login_url="/login/hbp/")
def home(request):
    """
    Serving home page for "hh neuron builder" application
    """
    
    ctx = request.GET.get('ctx', None)

    if not ctx:
        return render(request, 'efelg/hbp_redirect.html')
    else:
        exc = "tab_" + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        context = {"exc":exc, "ctx":str(ctx)}
        return render(request, 'hh_neuron_builder/home.html', context)

    # read context
    #if "context" not in request.session:
    #    context = request.GET.get('ctx', None)
    #else:
    #    context = request.session["context"]
    # if not ctx exit the application 
    #if not context:
    #    return render(request, 'efelg/hbp_redirect.html')
    #
    #exc = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    #request.session[exc] = {}

def initialize(request, exc = "", ctx = ""):

    request.session[exc] = {}

    my_url = settings.HBP_MY_USER_URL
    collab_context_url = settings.HBP_COLLAB_SERVICE_URL + "collab/context/"

    headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    request.session[exc]['headers'] = headers

    res = requests.get(my_url, headers = headers)
    collab_res = requests.get(collab_context_url + ctx, headers = headers)
        
    if res.status_code != 200 or collab_res.status_code != 200:
        manage_auth.Token.renewToken(request)
            
        headers = {'Authorization': \
            get_auth_header(request.user.social_auth.get())}
            
        res = requests.get(my_url, headers = headers)
        collab_res = requests.get(collab_context_url + ctx, \
            headers = headers)

    if res.status_code != 200 or collab_res.status_code != 200:
        return render(request, 'efelg/hbp_redirect.html')
        
    res_dict = res.json()

    if "username" not in request.session[exc]:
        username = res_dict['username']
        request.session[exc]['username'] = username
    if "userid" not in request.session[exc]:
        userid = res_dict['id']
        request.session[exc]['userid'] = userid
    if "ctx" not in request.session[exc]:
        request.session[exc]['ctx'] = ctx
    if "collab_id" not in request.session[exc]:
        collab_id = collab_res.json()['collab']['id']
        request.session[exc]['collab_id'] = collab_id
    
    # build directory names
    workflows_dir = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'workflows')
    scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'singlecellmodeling_structure.json')
    opt_model_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'optimizations')

    # create global variables in request.session
    request.session[exc]['singlecellmodeling_structure_path'] = scm_structure_path 
    request.session[exc]['optimization_model_path'] = opt_model_path
    request.session[exc]['workflows_dir'] = workflows_dir
    request.session[exc]['hhnb_storage_folder'] = "hhnb_workflows"
    request.session[exc]['opt_sub_flag_file'] = 'opt_sub_flag.txt'
    request.session[exc]['opt_sub_param_file'] = 'opt_sub_param.json'
    request.session[exc]['sim_run_flag_file'] = 'sim_run_flag.txt'
    request.session[exc]['wf_job_ids'] = 'wf_job_ids.json'

    accesslogger.info(resources.string_for_log('home', request))

    request.session.save()
    
    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")


def create_wf_folders(request, wf_type="new", exc="", ctx=""):
    """
    Create folders for current workflow
    """

    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session[exc]['workflows_dir']
    userid = request.session[exc]['userid']
    wf_id = time_info + '_' + userid

    request.session[exc]['time_info'] = time_info
    request.session[exc]['wf_id'] = wf_id

    if wf_type == "new":
        # delete keys if present in request.session
        request.session[exc].pop('gennum', None)
        request.session[exc].pop('offsize', None)
        request.session[exc].pop('nodenum', None)
        request.session[exc].pop('corenum', None)
        request.session[exc].pop('runtime', None)
        request.session[exc].pop('username_submit', None)
        request.session[exc].pop('password_submit', None)
        request.session[exc].pop('hpc_sys', None)
        request.session[exc].pop('username_fetch', None)
        request.session[exc].pop('password_fetch', None)
        request.session[exc].pop('hpc_sys_fetch', None)
        request.session[exc]['user_dir'] = os.path.join(workflows_dir, userid, wf_id)
        request.session[exc]['user_dir_data'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data')
        request.session[exc]['user_dir_data_feat'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data', 'features')
        request.session[exc]['user_dir_data_opt_set'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data', 'opt_settings')
        request.session[exc]['user_dir_data_opt_launch'] = os.path.join(\
                workflows_dir, userid, wf_id, 'data', 'opt_launch')
        request.session[exc]['user_dir_results'] = os.path.join(workflows_dir, \
                userid, wf_id, 'results')
        request.session[exc]['user_dir_results_opt'] = os.path.join(workflows_dir, \
                userid, wf_id, 'results', 'opt')
        request.session[exc]['user_dir_sim_run'] = os.path.join(workflows_dir,\
                userid, wf_id, 'sim')


        # create folders for global data and json files if not existing
        if not os.path.exists(request.session[exc]['user_dir_data_feat']):
	    os.makedirs(request.session[exc]['user_dir_data_feat'])
        if not os.path.exists(request.session[exc]['user_dir_data_opt_set']):
	    os.makedirs(request.session[exc]['user_dir_data_opt_set'])
        if not os.path.exists(request.session[exc]['user_dir_data_opt_launch']):
	    os.makedirs(request.session[exc]['user_dir_data_opt_launch'])
        if not os.path.exists(request.session[exc]['user_dir_results_opt']):
	    os.makedirs(request.session[exc]['user_dir_results_opt'])
        if not os.path.exists(request.session[exc]['user_dir_sim_run']):
	    os.makedirs(request.session[exc]['user_dir_sim_run'])

    if wf_type == "cloned":
        crr_user_dir = request.session[exc]['user_dir']
        new_user_dir = os.path.join(workflows_dir, userid, wf_id)

        # copy current user dir to the newly created workflow's dir
        shutil.copytree(os.path.join(crr_user_dir, 'data'), \
                os.path.join(new_user_dir, 'data'), symlinks=True)
                
        request.session[exc]['user_dir'] = new_user_dir
        
        #
        request.session[exc]['user_dir_data'] = os.path.join(new_user_dir,\
                'data')
        request.session[exc]['user_dir_data_feat'] = os.path.join(new_user_dir,\
                'data', 'features')
        request.session[exc]['user_dir_data_opt_set'] = os.path.join(new_user_dir, \
                'data', 'opt_settings')
        request.session[exc]['user_dir_data_opt_launch'] = os.path.join(new_user_dir,\
                'data', 'opt_launch')

        # remove old optimization launch folder and create a new one
        shutil.rmtree(request.session[exc]['user_dir_data_opt_launch'])
        os.makedirs(request.session[exc]['user_dir_data_opt_launch'])

        opt_pf = os.path.join(crr_user_dir, 'data', 'opt_launch', \
                request.session[exc]['opt_sub_param_file'])
        if os.path.exists(opt_pf):
            shutil.copy(opt_pf, request.session[exc]['user_dir_data_opt_launch'])

        # copy current user dir results folder  to the newly created workflow
        shutil.copytree(os.path.join(crr_user_dir, 'results'), \
                os.path.join(new_user_dir, 'results'), symlinks=True)

        request.session[exc]['user_dir_results'] = os.path.join(new_user_dir, \
                'results')
        request.session[exc]['user_dir_results_opt'] = os.path.join(new_user_dir, \
                'results', 'opt')

        # copy current user dir results folder  to the newly created workflow
        shutil.copytree(os.path.join(crr_user_dir, 'sim'), \
                os.path.join(new_user_dir, 'sim'), symlinks=True)

        request.session[exc]['user_dir_sim_run'] = os.path.join(workflows_dir, userid, wf_id, 'sim')
        
        sim_flag_file = os.path.join(request.session[exc]['user_dir_sim_run'], \
                request.session[exc]['sim_run_flag_file'])
        if os.path.exists(sim_flag_file):
            os.remove(sim_flag_file)

    request.session.save()

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")


def fetch_wf_from_storage(request, wfid="", exc="", ctx=""):
    '''
    Fetch previous workflows from current collab's storage
    '''

    time_info = wfid[:14]
    idx = wfid.find('_')

    userid_wf = wfid[idx+1:]
    userid = request.session[exc]['userid']
    workflows_dir = request.session[exc]['workflows_dir']
    
    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']

    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]

    request.session[exc]['time_info'] = time_info
    request.session[exc]['wf_id'] = wfid

    sc = service_client.Client.new(access_token)
    ac = service_api_client.ApiClient.new(access_token)
    
    # retrieve collab related projects
    project_dict = ac.list_projects(None, None, None, collab_id)
    project = project_dict['results']
    storage_root = ac.get_entity_path(project[0]['uuid'])
    
    # get current working directory
    current_working_dir = os.getcwd()

    storage_wf_list = []
    wf_storage_dir = str(os.path.join(storage_root, hhnb_storage_folder, username))
    wf_to_be_downloaded = str(os.path.join(wf_storage_dir, wfid))

    # backend user's workflow directories
    target_user_path = os.path.join(workflows_dir, userid)
    target_path = os.path.join(workflows_dir, userid, wfid)

    # target file
    target_file_path = os.path.join(workflows_dir, userid, wfid + '.zip')

    # create directories
    if not os.path.exists(target_user_path):
        os.makedirs(target_user_path)
    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    # download file from storage to backend
    sc.download_file(wf_to_be_downloaded + '.zip', target_file_path)

    # unzip wf file
    final_zip_name = os.path.join(target_user_path, wfid + '.zip')
    final_wf_dir = os.path.join(target_user_path, wfid)
    zip_ref = zipfile.ZipFile(final_zip_name, 'r')
    if os.path.exists(final_wf_dir):
        shutil.rmtree(final_wf_dir)
    zip_ref.extractall(target_user_path)
    zip_ref.close()
    os.remove(final_wf_dir + '.zip')

    # overwrite keys if present in request.session
    request.session[exc]['user_dir'] = target_path
    request.session[exc]['user_dir_data'] = os.path.join(target_path, 'data')
    request.session[exc]['user_dir_data_feat'] = os.path.join(target_path, 'data', 'features')
    request.session[exc]['user_dir_data_opt_set'] = os.path.join(target_path, 'data', 'opt_settings')
    request.session[exc]['user_dir_data_opt_launch'] = os.path.join(target_path, 'data', 'opt_launch')
    request.session[exc]['user_dir_results'] = os.path.join(target_path, 'results')
    request.session[exc]['user_dir_results_opt'] = os.path.join(target_path, 'results', 'opt')
    request.session[exc]['user_dir_sim_run'] = os.path.join(target_path, 'sim')

    user_dir_data_opt = request.session[exc]['user_dir_data_opt_set']
    for crr_f in os.listdir(user_dir_data_opt):
        if crr_f.endswith(".zip"):
            request.session[exc]['source_opt_name'] = os.path.splitext(crr_f)[0]
            request.session[exc]['source_opt_zip'] = \
                    os.path.join(user_dir_data_opt, crr_f)
            break


    # create folders for global data and json files if not existing
    if not os.path.exists(request.session[exc]['user_dir_data_feat']):
        os.makedirs(request.session[exc]['user_dir_data_feat'])
    if not os.path.exists(request.session[exc]['user_dir_data_opt_set']):
        os.makedirs(request.session[exc]['user_dir_data_opt_set'])
    if not os.path.exists(request.session[exc]['user_dir_data_opt_launch']):
        os.makedirs(request.session[exc]['user_dir_data_opt_launch'])
    if not os.path.exists(request.session[exc]['user_dir_results_opt']):
        os.makedirs(request.session[exc]['user_dir_results_opt'])
    if not os.path.exists(request.session[exc]['user_dir_sim_run']):
        os.makedirs(request.session[exc]['user_dir_sim_run'])

    request.session.save()

    return HttpResponse(json.dumps({"response":"OK"}), \
            content_type="application/json")



def embedded_efel_gui(request):
    """
    Serving page for rendering embedded efel gui page
    """

    accesslogger.info(resources.string_for_log('embedded_efel_gui', request))
    return render(request, 'hh_neuron_builder/embedded_efel_gui.html')


def workflow(request):
    """
    Serving page for rendering workflow page
    """

    return render(request, 'hh_neuron_builder/workflow.html')


def choose_opt_model(request):
    """
    Serving page for rendering choose optimization model page
    """

    accesslogger.info(resources.string_for_log('choose_opt_model', request))
    return render(request, 'hh_neuron_builder/choose_opt_model.html')


def get_model_list(request, exc="", ctx=""):
    """
    Serving api call to get list of optimization models
    """
    model_file = request.session[exc]["singlecellmodeling_structure_path"]
    with open(model_file) as json_file:
	model_file_dict = json.load(json_file)

    return HttpResponse(json.dumps(model_file_dict), content_type="application/json")


def copy_feature_files(request, featurefolder = "", exc = "", ctx = ""):
    response = {"expiration": False}
    if not os.path.exists(request.session[exc]["user_dir"]) or not \
            os.path.exists(os.path.join(os.sep,featurefolder)):
        response = {"expiration":True}
        return HttpResponse(json.dumps(response), content_type="application/json")

    response["folder"] = featurefolder
    shutil.copy(os.path.join(os.sep, featurefolder, 'features.json'), request.session[exc]['user_dir_data_feat'])
    shutil.copy(os.path.join(os.sep, featurefolder, 'protocols.json'), request.session[exc]['user_dir_data_feat'])


    return HttpResponse(json.dumps(response), content_type="application/json")

# fetch model from dataset
def fetch_opt_set_file(request, source_opt_name="", exc="", ctx=""):
    """
    Set optimization setting file
    """
    response = {"response": "OK", "message":""}

    opt_model_path = request.session[exc]['optimization_model_path']
    user_dir_data_opt = request.session[exc]['user_dir_data_opt_set']

    if not os.path.exists(user_dir_data_opt):
        response["response"] = "KO"
        response["message"] = "Folder does not exist anymore."
        return HttpResponse(json.dumps(response), content_type="application/json")

    shutil.rmtree(user_dir_data_opt)
    os.makedirs(user_dir_data_opt)
    request.session[exc]['source_opt_name'] = source_opt_name
    request.session[exc]['source_opt_zip'] = os.path.join(opt_model_path, source_opt_name, source_opt_name + '.zip')
    shutil.copy(request.session[exc]['source_opt_zip'], user_dir_data_opt)

    request.session.save()
    return HttpResponse("")


def run_optimization(request, exc="", ctx=""):
    """
    Run optimization on remote systems
    """

    # fetch information from the session variable
    username_submit = request.session[exc]['username_submit']
    password_submit = request.session[exc]['password_submit']
    core_num = request.session[exc]['corenum']
    node_num = request.session[exc]['nodenum']
    runtime = request.session[exc]['runtime']
    gennum = request.session[exc]['gennum']
    time_info = request.session[exc]['time_info']
    offsize = request.session[exc]['offsize']
    source_opt_name = request.session[exc]['source_opt_name']
    source_opt_zip = request.session[exc]['source_opt_zip']
    dest_dir = request.session[exc]['user_dir_data_opt_launch']
    user_dir_data_opt = request.session[exc]['user_dir_data_opt_set']
    hpc_sys = request.session[exc]['hpc_sys']
    source_feat = request.session[exc]['user_dir_data_feat']
    opt_res_dir = request.session[exc]['user_dir_results_opt']
    workflows_dir = request.session[exc]['workflows_dir']
    userid = request.session[exc]['userid']
    
    idx = source_opt_name.rfind('_')

    # build new optimization name
    opt_name = source_opt_name[:idx] + "_" + time_info
    zfName = os.path.join(dest_dir, opt_name + '.zip')
    fin_opt_folder = os.path.join(dest_dir, opt_name)

    if hpc_sys == "nsg":

	hpc_job_manager.Nsg.createzip(fin_opt_folder=fin_opt_folder, \
                source_opt_zip=source_opt_zip, opt_name=opt_name, \
                source_feat=source_feat, gennum=gennum, offsize=offsize, \
                zfName=zfName)

	resp = hpc_job_manager.Nsg.runNSG(username_submit=username_submit, \
                password_submit=password_submit, core_num=core_num, \
                node_num=node_num, runtime=runtime, zfName=zfName)

	if resp['status_code'] == 200:
            opt_sub_flag_file = os.path.join(dest_dir,\
                    request.session[exc]['opt_sub_flag_file'])

            with open(opt_sub_flag_file, 'w') as f:
                f.write("")
            f.close()
        
            wf_job_ids = request.session[exc]['wf_job_ids']
            wf_id = request.session[exc]['wf_id']
            ids_file = os.path.join(workflows_dir, userid, wf_job_ids)
            ids_dict = {"wf_id" : wf_id, "hpc_sys": hpc_sys}

            # update file containing 
            if os.path.exists(ids_file):
                with open(ids_file, "r") as fh:
                    all_id = json.load(fh)
            else:
                all_id = {}

            all_id[resp["jobname"]] = ids_dict
                
            with open(ids_file, "w") as fh:
                json.dump(all_id, fh)

    request.session.save()

    return HttpResponse(json.dumps(resp))


def model_loaded_flag(request, exc="", ctx=""):
    if 'res_file_name' in request.session[exc]:
	return HttpResponse(json.dumps(\
                {"response": request.session[exc]['res_file_name']}),\
                content_type="application/json")
    else:
	return HttpResponse(json.dumps({"response": "KO"}), \
                content_type="application/json")


def embedded_naas(request, exc="", ctx=""):
    """
    Render page with embedded "neuron as a service" app
    """

    accesslogger.info(resources.string_for_log('embedded_naas', request))
    dest_dir = request.session[exc]['user_dir_sim_run']
    sim_run_flag_file = os.path.join(dest_dir,\
            request.session[exc]['sim_run_flag_file'])
    with open(sim_run_flag_file, 'w') as f:
        f.write("")
    f.close()

    return render(request, 'hh_neuron_builder/embedded_naas.html')


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



def upload_to_naas(request, exc="", ctx=""):
    res_folder = request.session[exc]['user_dir_sim_run']
    res_folder_ls = os.listdir(res_folder) 
    abs_res_file = []
    for filename in res_folder_ls:
        if filename.endswith(".zip"):
            abs_res_file = os.path.join(res_folder, filename)
            break

    if not abs_res_file:
        return HttpResponse(json.dumps({"response": "KO", "message": "No \
        simulation .zip file is present"}), content_type="application/json")
    else:
        request.session[exc]['res_file_name'] = os.path.splitext(filename)[0]
        r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(abs_res_file, "rb")});
    
    request.session.save()

    return HttpResponse(json.dumps({"response": "OK", "message":"Model \
            correctly uploaded to naas"}), content_type="application/json")


def submit_run_param(request, exc="", ctx=""):
    """
    Save user's optimization parameters
    """

    #selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST

    # read data from form
    gennum = int(form_data['gen-max'])
    offsize = int(form_data['offspring'])
    nodenum = int(form_data['node-num']) 
    corenum = int(form_data['core-num'])  
    runtime = float(form_data['runtime'])
    hpc_sys = form_data['hpc_sys']

    # 
    request.session[exc]['gennum'] = gennum
    request.session[exc]['offsize'] = offsize 
    request.session[exc]['nodenum'] = nodenum
    request.session[exc]['corenum'] = corenum
    request.session[exc]['runtime'] = runtime
    request.session[exc]['hpc_sys'] = hpc_sys

    wf_id = request.session[exc]['wf_id']
    dest_dir = request.session[exc]['user_dir_data_opt_launch']

    # if chosen system is nsg
    if form_data['hpc_sys'] == 'nsg':
        resp_check_login = hpc_job_manager.Nsg.checkNsgLogin(username=form_data['username_submit'],
                password=form_data['password_submit'])

        # check credentials correctness
        if resp_check_login['response'] == 'OK':
            request.session[exc]['username_submit'] = form_data['username_submit']
            request.session[exc]['password_submit'] = form_data['password_submit']
            opt_sub_param_file = os.path.join(dest_dir, \
                    request.session[exc]["opt_sub_param_file"])

            wfid = request.session[exc]['wf_id']
            hpc_job_manager.OptSettings.print_opt_params(wf_id=wfid, \
                    gennum=str(gennum), offsize=str(offsize),
                    nodenum=str(nodenum), \
                    corenum=str(corenum), runtime=str(runtime), \
                    opt_sub_param_file=opt_sub_param_file, hpc_sys=hpc_sys)
            resp_dict = {'response':'OK', 'message':''}
        else:
            resp_dict = {'response':'KO', 'message':'Username and/or password \
                    are wrong'}
            request.session[exc].pop('username_submit', None)
            request.session[exc].pop('password_submit', None)

    request.session.save()

    return HttpResponse(json.dumps(resp_dict), content_type="application/json")


def submit_fetch_param(request, exc="", ctx=""):
    """
    Save user's optimization parameters
    """
    #selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST

    # if chosen system is nsg
    if form_data['hpc_sys_fetch'] == 'nsg':
        request.session[exc]['hpc_sys_fetch'] = form_data['hpc_sys_fetch']
        resp_check_login = \
        hpc_job_manager.Nsg.checkNsgLogin(username=form_data['username_fetch'],
                password=form_data['password_fetch'])

        # check credentials correctness
        if resp_check_login['response'] == 'OK':
            request.session[exc]['username_fetch'] = form_data['username_fetch']
            request.session[exc]['password_fetch'] = form_data['password_fetch']
        else:
            request.session[exc].pop('username_fetch', None)
            request.session[exc].pop('password_fetch', None)

    request.session.save()

    return HttpResponse(json.dumps(resp_check_login), content_type="application/json")

def check_cond_exist(request, exc="", ctx=""):
    """
    Check if conditions for performing steps are present.
    The function checks on current workflow folders whether files are present to go on with the workflow.
    The presence of simulation parameters are also checked.
    """

    # set responses dictionary
    response = { \
            "expiration": False,
            "feat": {"status": False, "message":"'features.json and/or \
                'protocols.json' NOT present"}, \
            "opt_files":{"status": False, "message":"Optimization files NOT \
                present"}, \
            "opt_set":{"status": False, "message":"Optimization parameters NOT \
                set"}, \
            "run_sim":{"status": False, "message":""}, \
            "opt_flag":{"status": False}, \
            "sim_flag":{"status": False}, \
            'opt_res': {"status": False}, \
            }

    if not os.path.exists(request.session[exc]['user_dir']):
        response = {"expiration":True}
        return HttpResponse(json.dumps(response), content_type="application/json")

    # retrieve folder paths 
    data_feat = request.session[exc]['user_dir_data_feat']
    data_opt = request.session[exc]['user_dir_data_opt_set']
    sim_dir = request.session[exc]['user_dir_sim_run']
    res_dir = request.session[exc]['user_dir_results']
    wf_id = request.session[exc]['wf_id']
    dest_dir = request.session[exc]['user_dir_data_opt_launch']
    
    # check if feature files exist
    if os.path.isfile(os.path.join(data_feat, "features.json")) and \
	    os.path.isfile(os.path.join(data_feat, "protocols.json")):
		response['feat']['status'] = True
		response['feat']['message'] = ""

    # check if optimization file exist
    if os.path.exists(data_opt) and not os.listdir(data_opt) == []:
	response['opt_files']['status'] = True

    # check if simulation files exist
    resp_sim = wf_file_manager.CheckConditions.checkSimFiles(sim_path=sim_dir)
    if resp_sim['response'] == "OK":
	response['run_sim']['status'] = True
        response['run_sim']['message'] = ''
    else:
	response['run_sim']['status'] = False
        response['run_sim']['message'] = resp_sim['message']

    # check if optimization results zip file exists
    for i in os.listdir(res_dir):
        if i.endswith('.zip'):
            response['opt_res']['status'] = True
            break

    # check if optimization has been submitted
    if os.path.exists(os.path.join(dest_dir, \
            request.session[exc]['opt_sub_flag_file'])):
	response['opt_flag']['status'] = True

    # check if simulation has been launched
    if os.path.exists(os.path.join(sim_dir, \
            request.session[exc]['sim_run_flag_file'])):
	response['sim_flag']['status'] = True

    # build dictionary with optimization submission parameters
    opt_sub_param_dict = {}
    opt_sub_param_file = os.path.join(request.session[exc]['user_dir_data_opt_launch'], \
        request.session[exc]['opt_sub_param_file'])
    # if parameter file exists, read values
    if os.path.exists(opt_sub_param_file):
        with open(opt_sub_param_file) as json_file:
	    opt_sub_param_dict = json.load(json_file)

        response['opt_set']['opt_sub_param_dict'] = opt_sub_param_dict

        rsk = request.session[exc].keys()
        rules = [
            'username_submit' in rsk,
            'password_submit' in rsk,
            ]

        if all(rules):
	    response['opt_set']['status'] = True 
	    response['opt_set']['message'] = ""
        else:
	    response['opt_set']['status'] = False
	    response['opt_set']['message'] = "Settings retrieved. Credentials NOT set"
    else:
        opt_sub_param_dict = hpc_job_manager.OptSettings.get_params_default()
	response['opt_set']['message'] = "Optimization parameters NOT set"
	response['opt_set']['status'] = False
        response['opt_set']['opt_sub_param_dict'] = opt_sub_param_dict
            
    request.session[exc]['gennum'] = opt_sub_param_dict['number_of_generations']
    request.session[exc]['offsize'] = opt_sub_param_dict['offspring_size']
    request.session[exc]['nodenum'] = opt_sub_param_dict['number_of_nodes']
    request.session[exc]['corenum'] = opt_sub_param_dict['number_of_cores']
    request.session[exc]['runtime'] = opt_sub_param_dict['runtime']
    request.session[exc]['hpc_sys'] = opt_sub_param_dict['hpc_sys']


    if request.session[exc]['wf_id']:
        response['wf_id'] = request.session[exc]['wf_id']

    request.session.save()

    return HttpResponse(json.dumps(response), content_type="application/json")



# delete feature files
def delete_files(request, filetype="", exc="", ctx=""):
    if filetype == "feat":
        folder = request.session[exc]['user_dir_data_feat']
    elif filetype == "optset":
        folder = request.session[exc]['user_dir_data_opt_set']
    elif filetype == "modsim":
        folder = request.session[exc]['user_dir_sim_run']

    shutil.rmtree(folder)
    os.makedirs(folder)

    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")


def upload_files(request, filetype = "", exc = "", ctx = ""):
    filename_list = request.FILES.getlist('opt-res-file')

    if filetype == "feat":
	final_res_folder = request.session[exc]['user_dir_data_feat']
	ext = '.json'

    elif filetype == "optset":
	final_res_folder = request.session[exc]['user_dir_data_opt_set']

	# remove folder with current zip file
	if os.listdir(final_res_folder):
	    shutil.rmtree(final_res_folder)
	    os.makedirs(final_res_folder)
	ext = '.zip'

    elif filetype == "modsim":
	final_res_folder = request.session[exc]['user_dir_sim_run']

	# remove folder with current zip file
	if os.listdir(final_res_folder):
	    shutil.rmtree(final_res_folder)
	    os.makedirs(final_res_folder)
	ext = '.zip'

    if not filename_list:
	return HttpResponse(json.dumps({"resp":False}), content_type="application/json") 


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

    if filetype == "optset":
        request.session[exc]['source_opt_name'] = os.path.splitext(filename)[0]
        request.session[exc]['source_opt_zip'] = final_res_file 
        print(request.session[exc]['source_opt_zip'])
        print(request.session[exc]['source_opt_name'])
    elif filetype == "modsim":
        user_dir_sim_run = request.session[exc]['user_dir_sim_run']

        # unzip uploaded model file 
        z = zipfile.ZipFile(final_res_file, 'r')
        try:
            z.extractall(path = user_dir_sim_run)
        except Exception as e:
            msg = "Unable to unzip the uploaded file. Check file integrity"
            return HttpResponse(json.dumps({"response":"KO", "message":msg}), content_type="application/json") 

    request.session.save()
    
    return HttpResponse(json.dumps({"response":"OK", "message":""}), content_type="application/json") 


def get_nsg_job_list(request, exc="", ctx=""):
    """
    """
    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
	username_fetch = request.session[exc]['username_fetch']
	password_fetch = request.session[exc]['password_fetch']
	opt_res_dir = request.session[exc]['user_dir_results_opt']

	resp = hpc_job_manager.Nsg.fetch_job_list(username_fetch=username_fetch, \
                password_fetch=password_fetch)

        # read job id file
        workflows_dir = request.session[exc]['workflows_dir']
        userid = request.session[exc]['userid']
        wf_job_ids = request.session[exc]['wf_job_ids']
        wf_id = request.session[exc]['wf_id']

        ids_file = os.path.join(workflows_dir, userid, wf_job_ids)

        if os.path.exists(ids_file):
            with open(ids_file, "r") as fh:
                all_id = json.load(fh)
        else:
            all_id = {}

        # fetch workflow ids for all fetched jobs and add to response
        for key in resp:
            if key in all_id:
                resp[key]["wf"] = all_id[key]
            else:
                resp[key]["wf"] = {"wf_id": "No workflow id associated", \
                        "hpc_sys":"unknown"}

    request.session.save()

    return HttpResponse(json.dumps(resp), content_type="application/json") 


def get_nsg_job_details(request, jobid="", exc="", ctx=""):
    """
    """
    #return HttpResponse(json.dumps({"job_id": jobid, "job_date_submitted":"2017-07-24T16:40:21-07:00", "job_stage":"COMPLETED"}), content_type="application/json") 

    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
	username_fetch = request.session[exc]['username_fetch']
	password_fetch = request.session[exc]['password_fetch']

	resp = hpc_job_manager.Nsg.fetch_job_details( \
                job_id = jobid, username_fetch=username_fetch, \
                password_fetch=password_fetch) 


    return HttpResponse(json.dumps(resp), content_type="application/json") 


def download_job(request, job_id="", exc="", ctx=""): 
    """
    """

    opt_res_dir = request.session[exc]['user_dir_results_opt']
    if not os.path.exists(opt_res_dir):
        return HttpResponse(json.dumps({"response":"KO", \
            "message": "The workflow folder does not exist anymore. \
            <br> Please start a new workflow or fetch a previous one."}), \
            content_type="application/json") 

    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
	username_fetch = request.session[exc]['username_fetch']
	password_fetch = request.session[exc]['password_fetch']
        wf_id = request.session[exc]['wf_id']

	# remove folder with current zip file
	if os.listdir(opt_res_dir):
	    shutil.rmtree(opt_res_dir)
	    os.makedirs(opt_res_dir)

	resp_job_details = hpc_job_manager.Nsg.fetch_job_details( \
                job_id = job_id, username_fetch=username_fetch, \
                password_fetch=password_fetch) 
	job_res_url = resp_job_details['job_res_url']

	resp = hpc_job_manager.Nsg.fetch_job_results(job_res_url, \
                username_fetch=username_fetch, \
                password_fetch=password_fetch, opt_res_dir=opt_res_dir, \
                wf_id=wf_id)

    return HttpResponse(json.dumps(resp), content_type="application/json") 


def modify_analysis_py(request, exc="", ctx=""):
    msg = ""
    opt_res_folder = request.session[exc]['user_dir_results_opt']
    output_fetched_file = os.path.join(opt_res_folder, "output.tar.gz")

    if not os.path.exists(output_fetched_file):
        msg = "No ouptut file was generated in the optimization process. \
                Check your optimization settings."    
        return HttpResponse(json.dumps({"response":"KO", "message": msg}), content_type="application/json")

    tar = tarfile.open(os.path.join(opt_res_folder, "output.tar.gz"))
    tar.extractall(path=opt_res_folder)
    tar.close()

    analysis_file_list = []
    for (dirpath, dirnames, filenames) in os.walk(opt_res_folder):
	for filename in filenames:
	    if filename == "analysis.py":
		analysis_file_list.append(os.path.join(dirpath,filename))

    if len(analysis_file_list) != 1:
        msg = "No (or multiple) analysis.py file(s) found. \
                Check the .zip file submitted for the optimization."
        resp = {"Status":"ERROR", "response":"KO", "message": msg}
	return HttpResponse(json.dumps(resp), content_type="application/json") 
    else:
	full_file_path = analysis_file_list[0]
	file_path = os.path.split(full_file_path)[0]
	up_folder = os.path.split(file_path)[0]

	# modify analysis.py file
	f = open(full_file_path, 'r')

	lines = f.readlines()
	lines[228]='    traces=[]\n'
	lines[238]='        traces.append(response.keys()[0])\n'
	lines[242]='\n    stimord={} \n    for i in range(len(traces)): \n        stimord[i]=float(traces[i][traces[i].find(\'_\')+1:traces[i].find(\'.soma\')]) \n    import operator \n    sorted_stimord = sorted(stimord.items(), key=operator.itemgetter(1)) \n    traces2=[] \n    for i in range(len(sorted_stimord)): \n        traces2.append(traces[sorted_stimord[i][0]]) \n    traces=traces2 \n'
        lines[243]='    plot_multiple_responses([responses], cp_filename, fig=model_fig, traces=traces)\n'
	#lines[243]='    plot_multiple_responses([responses], fig=model_fig, traces=traces)\n'
	#lines[366]="def plot_multiple_responses(responses, fig, traces):\n"
        lines[366]="def plot_multiple_responses(responses, cp_filename, fig, traces):\n"
	lines[369] = "\n"
	lines[370] = "\n"
	lines[371] = "\n"# n is the line number you want to edit; subtract 1 as indexing of list starts from 0
	f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.

	f = open(full_file_path, 'w')
	f.writelines(lines)
	f.close()

        # modify evaluator.py if present
        if not os.path.exists(os.path.join(file_path, 'evaluator.py')):
            msg = "No evaluator.py file found. \
                Check the .zip file submitted for the optimization."
            resp = {"Status":"ERROR", "response":"KO", "message": msg}
            return HttpResponse(json.dumps(resp), \
                    content_type="application/json") 
        else:
	    f = open(os.path.join(file_path, 'evaluator.py'), 'r')    # pass an appropriate path of the required file
	    lines = f.readlines()
	    lines[167]='    #print param_names\n'
	    f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.
	    f = open(os.path.join(file_path, 'evaluator.py'), 'w')    # pass an appropriate path of the required file
	    f.writelines(lines)
	    f.close()

        if up_folder not in sys.path:
            sys.path.append(up_folder)

        import model
	fig_folder = os.path.join(up_folder, 'figures')

	if os.path.exists(fig_folder):
	    shutil.rmtree(fig_folder)
	os.makedirs(fig_folder)

	checkpoints_folder = os.path.join(up_folder, 'checkpoints')

        try:
	    if 'checkpoint.pkl' not in os.listdir(checkpoints_folder):
	        for files in os.listdir(checkpoints_folder):
		    if files.endswith('pkl'):
		        shutil.copy(os.path.join(checkpoints_folder, files), \
			        os.path.join(checkpoints_folder, 'checkpoint.pkl'))
                        os.remove(os.path.join(up_folder, 'checkpoints', files))
                    # else:
                    #    if files.endswith('.hoc'):
                    #        os.remove(os.path.join(up_folder, 'checkpoints', files))

            f = open(os.path.join(up_folder, 'opt_neuron.py'), 'r')
            lines = f.readlines()

            new_line = ["import matplotlib \n"]
            new_line.append("matplotlib.use('Agg') \n")
            for i in lines:
                new_line.append(i)
            f.close()
            f = open(os.path.join(up_folder, 'opt_neuron.py'), 'w')
            f.writelines(new_line)
            f.close()

            subprocess.call(". /web/bspg/venvbspg/bin/activate; cd " \
                    + up_folder + "; nrnivmodl mechanisms", shell=True)

            r_0_fold = os.path.join(up_folder, 'r_0')
            if os.path.isdir(r_0_fold) == True:
                shutil.rmtree(r_0_fold)
            os.mkdir(r_0_fold)
            subprocess.call(". /web/bspg/venvbspg/bin/activate; cd " \
                    + up_folder + "; python opt_neuron.py --analyse --checkpoint \
                    ./checkpoints > /dev/null 2>&1", shell=True)

            # symlink to be removed
            symlink_path = os.path.join(up_folder, "x86_64", "*.inc")
            try:
                os.remove(symlink_path)
            except:
                pass

        except Exception as e:
            msg = traceback.format_exception(*sys.exc_info())

            return HttpResponse(json.dumps({"response":"KO", "message":msg}), content_type="application/json")

    
    return HttpResponse(json.dumps({"response":"OK", "message":msg}), content_type="application/json")


def zip_sim(request, exc="", ctx=""):
    user_dir_res_opt = request.session[exc]['user_dir_results_opt']
    user_dir_sim_run = request.session[exc]['user_dir_sim_run']

    opt_logs_folder = 'opt_logs'

    # folder named as the optimization
    if os.path.exists(user_dir_sim_run):
        shutil.rmtree(user_dir_sim_run)

    os.makedirs(user_dir_sim_run)
        
    # extract the name of the model folder
    mec_folder_path = []
    config_folder_path = []

    for root, dirs, files in os.walk(user_dir_res_opt):
        if (root.endswith("mechanisms")):
            mec_folder_path.append(root)
        elif (root.endswith("config")):
            config_folder_path.append(root)

    if len(mec_folder_path) != 1 or len(config_folder_path) !=1:
        return HttpResponse(json.dumps({"response":"ERROR", "message":"Optimization result folder is not consistent. Check your data."}), content_type="application/json")
    
    if os.path.split(mec_folder_path[0])[0] != os.path.split(config_folder_path[0])[0]:
        return HttpResponse(json.dumps({"response":"ERROR", "message":"Optimization result folder is not consistent. Check your data."}), content_type="application/json")

    else:
        crr_opt_folder = os.path.split(mec_folder_path[0])[0]
        crr_opt_name = os.path.split(crr_opt_folder)[1]
        sim_mod_folder = os.path.join(user_dir_sim_run, crr_opt_name)
        os.makedirs(sim_mod_folder)
        user_opt_logs = os.path.join(user_dir_sim_run, crr_opt_name, opt_logs_folder)
        os.makedirs(user_opt_logs)

        log_files = ["STDERR", "stderr.txt", "STDOUT", "stdout.txt", \
                        "_JOBINFO.TXT", "nsgdebug", "scheduler.conf", \
                        "scheduler_stderr.txt", "scheduler_stdout.txt", \
                        "epilog"]
        for root, dirs, files in os.walk(user_dir_res_opt):
            if (root.endswith("mechanisms") or root.endswith("morphology") or \
                    root.endswith("checkpoints")):
                crr_folder = os.path.split(root)[1]
                dst = os.path.join(sim_mod_folder, crr_folder)
                shutil.copytree(root,dst, symlinks=True)

            for crr_f in log_files:
                if crr_f in files:
                    shutil.copyfile(os.path.join(root, crr_f), \
                            os.path.join(user_opt_logs, crr_f))
    

    for filename in os.listdir(os.path.join(sim_mod_folder, 'checkpoints')):
        if filename.endswith(".hoc"):
            os.rename(os.path.join(sim_mod_folder, "checkpoints", filename), \
                    os.path.join(sim_mod_folder, "checkpoints", "cell.hoc"))

    current_working_dir = os.getcwd()

    zipname = crr_opt_name + '.zip'

    final_zip_name = os.path.join(user_dir_sim_run, zipname)
    foo = zipfile.ZipFile(final_zip_name, 'w', zipfile.ZIP_DEFLATED)

    crr_dir_opt = os.path.join(user_dir_sim_run, crr_opt_name)
    for root, dirs, files in os.walk(user_dir_sim_run):
        if (root == os.path.join(crr_dir_opt, 'morphology')) or \
        (root == os.path.join(crr_dir_opt, 'checkpoints')) or \
        (root == os.path.join(crr_dir_opt, 'mechanisms')) or \
        (root == os.path.join(crr_dir_opt, opt_logs_folder)):
            for f in files:
                final_zip_fname = os.path.join(root, f)
                foo.write(final_zip_fname, \
                        final_zip_fname.replace(user_dir_sim_run, '', 1))

    foo.close()

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")
    

def download_zip(request, filetype="", exc="", ctx=""):
    """
    download files to local machine
    """
    current_working_dir = os.getcwd()
    if filetype == "feat":
        fetch_folder = request.session[exc]['user_dir_data_feat']
        zipname = os.path.join(fetch_folder, "features.zip")
        foo = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        foo.write(os.path.join(fetch_folder, "features.json"), "features.json")
        foo.write(os.path.join(fetch_folder, "protocols.json"), "protocols.json")
        foo.close()
    elif filetype == "optset":
        fetch_folder = request.session[exc]['user_dir_data_opt_set']
    elif filetype == "modsim":
        fetch_folder = request.session[exc]['user_dir_sim_run']
    elif filetype == "optres":
        fetch_folder = request.session[exc]['user_dir_results']

    zip_file_list = []

    # create a list with all .zip files in folder, but use only the first one
    for i in os.listdir(fetch_folder):
        if i.endswith(".zip"):
            zip_file_list.append(i)

    crr_file = zip_file_list[0]
    full_file_path = os.path.join(fetch_folder, crr_file)
    crr_file_full = open(full_file_path, "r")
    response = HttpResponse(crr_file_full, content_type="application/zip")

    request.session.save()

    response['Content-Disposition'] = 'attachment; filename="%s"' % crr_file

    return response


########### handle file upload to storage collab
def save_wf_to_storage(request, exc="", ctx=""):

    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']
    user_crr_wf_dir = request.session[exc]['user_dir']
    wf_id = request.session[exc]['wf_id']
    wf_dir = request.session[exc]['workflows_dir']
    userid = request.session[exc]['userid']
    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]
    
    access_token = get_access_token(request.user.social_auth.get())

    sc = service_client.Client.new(access_token)
    ac = service_api_client.ApiClient.new(access_token)
    
    # retrieve collab related projects
    project_dict = ac.list_projects(None, None, None, collab_id)
    project = project_dict['results']
    storage_root = ac.get_entity_path(project[0]['uuid'])
    
    # create zip file with the entire workflow
    user_wf_path = os.path.join(wf_dir, userid)
    zipname = wf_id + '.zip'
    zipname_full = os.path.join(user_wf_path, zipname)
    if os.path.exists(zipname_full):
        os.remove(zipname_full)

    foo = zipfile.ZipFile(zipname_full, 'w', zipfile.ZIP_DEFLATED)

    #for root, dirs, files in os.walk(os.path.join('.', wf_id)):
    for root, dirs, files in os.walk(os.path.join(user_wf_path, wf_id)):
        for d in dirs:
            if os.listdir(os.path.join(root,d)) == []:
                crr_zip_filename = os.path.join(root, d)
                crr_arcname = crr_zip_filename.replace(user_wf_path, '', 1)
                foo.write(os.path.join(root, d), crr_arcname)
        for f in files:
            crr_zip_ffilename = os.path.join(root, f)
            crr_farcname = crr_zip_ffilename.replace(user_wf_path, '', 1)
            foo.write(os.path.join(root, f), crr_farcname)
    foo.close()
    
    # create user's folder if it does not exist
    hhnb_full_storage_path = os.path.join(storage_root, hhnb_storage_folder)
    user_storage_path = os.path.join(hhnb_full_storage_path, username)
    crr_zip_storage_path = os.path.join(user_storage_path, zipname) 

    if not sc.exists(str(hhnb_full_storage_path)):
        sc.mkdir(str(hhnb_full_storage_path))
    if not sc.exists(str(user_storage_path)):
        sc.mkdir(str(user_storage_path))
    if sc.exists(str(crr_zip_storage_path)):
        sc.delete(str(crr_zip_storage_path))

    sc.upload_file(zipname_full, str(crr_zip_storage_path), \
        "application/zip")

    return HttpResponse(json.dumps({"response":"OK", "message":""}), content_type="application/json")


def wf_storage_list(request, exc="", ctx=""):

    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']

    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]

    context = request.session[exc]['ctx']
    
    access_token = get_access_token(request.user.social_auth.get())

    sc = service_client.Client.new(access_token)
    ac = service_api_client.ApiClient.new(access_token)
    
    # retrieve collab related projects
    project_dict = ac.list_projects(None, None, None, collab_id)
    project = project_dict['results']
    storage_root = ac.get_entity_path(project[0]['uuid'])
    
    storage_wf_list = []
    wf_storage_dir = str(os.path.join(storage_root, hhnb_storage_folder, username))
    if not sc.exists(wf_storage_dir):
        storage_list = []
    else:
        storage_list = sc.list(wf_storage_dir)

    return HttpResponse(json.dumps({"list":storage_list}), content_type="application/json")

