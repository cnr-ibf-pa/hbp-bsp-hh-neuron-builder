""" Views"""

import sys
import pprint
import json
import os
import zipfile
from subprocess import call
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

# import hbp/bbp modules
from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
from bbp_client.oidc.client import BBPOIDCClient
from bbp_client.document_service.client import Client as DocClient
import bbp_client
from bbp_client.client import *
import bbp_services.client as bsc

import hbp_service_client
import hbp_service_client.storage_service.client as service_client
import hbp_service_client.storage_service.api as service_api_client
from hbp_service_client.document_service.service_locator import ServiceLocator
from hbp_service_client.document_service.client import Client
from hbp_service_client.document_service.requestor import DocNotFoundException, DocException

# import local tools
from tools import hpc_job_manager
from tools import resources

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

    my_url = 'https://services.humanbrainproject.eu/idm/v1/api/user/me'
    hbp_collab_service_url = "https://services.humanbrainproject.eu/collab/v0/collab/context/"

    if "headers" not in request.session:
        headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
        request.session['headers'] = headers
    else:
        headers = request.session["headers"]

    res = requests.get(my_url, headers = headers)
    res_dict = res.json()

    if "username" not in request.session:
        username = res_dict['username']
        request.session['username'] = username
    if "userid" not in request.session:
        userid = res_dict['id']
        request.session['userid'] = userid
    if "context" not in request.session:
        context = request.GET.get('ctx')
        request.session['context'] = context
    if "collab_id" not in request.session:
        collab_res = requests.get(hbp_collab_service_url + context, headers = headers)
        collab_id = collab_res.json()['collab']['id']
        request.session['collab_id'] = collab_id
    
    # build directory names
    workflows_dir = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'workflows')
    scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'singlecellmodeling_structure.json')
    opt_model_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'optimizations')

    # create global variables in request.session
    request.session['singlecellmodeling_structure_path'] = scm_structure_path 
    request.session['optimization_model_path'] = opt_model_path
    request.session['workflows_dir'] = workflows_dir
    request.session['hhnb_storage_folder'] = "hhnb_workflows"
    request.session['opt_sub_flag_file'] = 'opt_sub_flag.txt'
    request.session['sim_run_flag_file'] = 'sim_run_flag.txt'

    accesslogger.info(resources.string_for_log('home', request))

    return render(request, 'hh_neuron_builder/home.html')


def create_wf_folders(request, wf_type="new"):
    """
    Create folders for current workflow
    """
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session['workflows_dir']
    userid = request.session['userid']
    wf_id = time_info + '_' + userid

    request.session['time_info'] = time_info
    request.session['wf_id'] = wf_id

    if wf_type == "new":
        # delete keys if present in request.session
        request.session.pop('gennum', None)
        request.session.pop('offsize', None)
        request.session.pop('nodenum', None)
        request.session.pop('corenum', None)
        request.session.pop('runtime', None)
        request.session.pop('username_submit', None)
        request.session.pop('password_submit', None)
        request.session.pop('hpc_sys', None)
        request.session.pop('username_fetch', None)
        request.session.pop('password_fetch', None)
        request.session.pop('hpc_sys_fetch', None)
        request.session['user_dir'] = os.path.join(workflows_dir, userid, wf_id)
        request.session['user_dir_data'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data')
        request.session['user_dir_data_feat'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data', 'features')
        request.session['user_dir_data_opt_set'] = os.path.join(workflows_dir, \
                userid, wf_id, 'data', 'opt_settings')
        request.session['user_dir_data_opt_launch'] = os.path.join(\
                workflows_dir, userid, wf_id, 'data', 'opt_launch')
        request.session['user_dir_results'] = os.path.join(workflows_dir, \
                userid, wf_id, 'results')
        request.session['user_dir_results_opt'] = os.path.join(workflows_dir, \
                userid, wf_id, 'results', 'opt')
        request.session['user_dir_sim_run'] = os.path.join(workflows_dir,\
                userid, wf_id, 'sim')


        # create folders for global data and json files if not existing
        if not os.path.exists(request.session['user_dir_data_feat']):
	    os.makedirs(request.session['user_dir_data_feat'])
        if not os.path.exists(request.session['user_dir_data_opt_set']):
	    os.makedirs(request.session['user_dir_data_opt_set'])
        if not os.path.exists(request.session['user_dir_data_opt_launch']):
	    os.makedirs(request.session['user_dir_data_opt_launch'])
        if not os.path.exists(request.session['user_dir_results_opt']):
	    os.makedirs(request.session['user_dir_results_opt'])
        if not os.path.exists(request.session['user_dir_sim_run']):
	    os.makedirs(request.session['user_dir_sim_run'])

    if wf_type == "cloned":
        crr_user_dir = request.session['user_dir']
        new_user_dir = os.path.join(workflows_dir, userid, wf_id)

        request.session['user_dir'] = os.path.join(workflows_dir, userid, wf_id)

        # copy current user dir to the newly created workflow's dir
        shutil.copytree(os.path.join(crr_user_dir, 'data'), \
                os.path.join(new_user_dir, 'data'))
                
        request.session['user_dir'] = new_user_dir
        
        #
        request.session['user_dir_data'] = os.path.join(new_user_dir,\
                'data')
        request.session['user_dir_data_feat'] = os.path.join(new_user_dir,\
                'data', 'features')
        request.session['user_dir_data_opt_set'] = os.path.join(new_user_dir, \
                'data', 'opt_settings')
        request.session['user_dir_data_opt_launch'] = os.path.join(new_user_dir,\
                'data', 'opt_launch')

        # remove old optimization launch folder and create a new one
        shutil.rmtree(request.session['user_dir_data_opt_launch'])
        os.makedirs(request.session['user_dir_data_opt_launch'])

        # create folders
        request.session['user_dir_results'] = os.path.join(new_user_dir, \
                'results')
        request.session['user_dir_results_opt'] = os.path.join(new_user_dir, \
                'results', 'opt')
        if not os.path.isdir(request.session['user_dir_results']):
            os.makedirs(request.session['user_dir_results'])
        if not os.path.isdir(request.session['user_dir_results_opt']):
            os.makedirs(request.session['user_dir_results_opt'])
        
        request.session['user_dir_sim_run'] = os.path.join(workflows_dir, userid, wf_id, 'sim')

        if not os.path.isdir(request.session['user_dir_sim_run']):
            os.makedirs(request.session['user_dir_sim_run'])

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")


def fetch_wf_from_storage(request, wfid=""):
    '''
    Fetch previous workflows from current collab's storage
    '''

    time_info = wfid[:14]
    idx = wfid.find('_')

    userid_wf = wfid[idx+1:]
    userid = request.session['userid']
    workflows_dir = request.session['workflows_dir']
    
    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session['collab_id']

    hhnb_storage_folder = request.session['hhnb_storage_folder']
    username = request.session["username"]

    context = request.session['context']

    request.session['time_info'] = time_info
    request.session['wf_id'] = wfid

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
    os.chdir(target_user_path)
    zip_ref = zipfile.ZipFile(wfid + '.zip', 'r')
    if os.path.exists(wfid):
        shutil.rmtree(wfid)
    zip_ref.extractall('.')
    zip_ref.close()
    os.remove(wfid + '.zip')
    os.chdir(current_working_dir)

    # delete keys if present in request.session
    request.session.pop('gennum', None)
    request.session.pop('offsize', None)
    request.session.pop('nodenum', None)
    request.session.pop('corenum', None)
    request.session.pop('runtime', None)
    request.session.pop('username_submit', None)
    request.session.pop('password_submit', None)
    request.session.pop('hpc_sys', None)
    request.session.pop('username_fetch', None)
    request.session.pop('password_fetch', None)
    request.session.pop('hpc_sys_fetch', None)
    request.session['user_dir'] = target_path
    request.session['user_dir_data'] = os.path.join(target_path, 'data')
    request.session['user_dir_data_feat'] = os.path.join(target_path, 'data', 'features')
    request.session['user_dir_data_opt_set'] = os.path.join(target_path, 'data', 'opt_settings')
    request.session['user_dir_data_opt_launch'] = os.path.join(target_path, 'data', 'opt_launch')
    request.session['user_dir_results'] = os.path.join(target_path, 'results')
    request.session['user_dir_results_opt'] = os.path.join(target_path, 'results', 'opt')
    request.session['user_dir_sim_run'] = os.path.join(target_path, 'sim')

        # create folders for global data and json files if not existing
    if not os.path.exists(request.session['user_dir_data_feat']):
        os.makedirs(request.session['user_dir_data_feat'])
    if not os.path.exists(request.session['user_dir_data_opt_set']):
        os.makedirs(request.session['user_dir_data_opt_set'])
    if not os.path.exists(request.session['user_dir_data_opt_launch']):
        os.makedirs(request.session['user_dir_data_opt_launch'])
    if not os.path.exists(request.session['user_dir_results_opt']):
        os.makedirs(request.session['user_dir_results_opt'])
    if not os.path.exists(request.session['user_dir_sim_run']):
        os.makedirs(request.session['user_dir_sim_run'])

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")



def embedded_efel_gui(request):
    """
    Serving page for rendering embedded efel gui page
    """

    accesslogger.info(resources.string_for_log('embedded_efel_gui', request))
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

    accesslogger.info(resources.string_for_log('choose_opt_model', request))
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
    shutil.rmtree(user_dir_data_opt)
    os.makedirs(user_dir_data_opt)
    request.session['source_opt_name'] = source_opt_name
    request.session['source_opt_zip'] = os.path.join(opt_model_path, source_opt_name, source_opt_name + '.zip')
    shutil.copy(request.session['source_opt_zip'], user_dir_data_opt)

    return HttpResponse("")


def run_optimization(request):
    """
    Run optimization on remote systems
    """

    # fetch information from the session variable
    username_submit = request.session['username_submit']
    password_submit = request.session['password_submit']
    core_num = request.session['corenum']
    node_num = request.session['nodenum']
    runtime = request.session['runtime']
    gennum = request.session['gennum']
    time_info = request.session['time_info']
    offsize = request.session['offsize']
    source_opt_name = request.session['source_opt_name']
    source_opt_zip = request.session['source_opt_zip']
    dest_dir = request.session['user_dir_data_opt_launch']
    user_dir_data_opt = request.session['user_dir_data_opt_set']
    hpc_sys = request.session['hpc_sys']
    source_feat = request.session['user_dir_data_feat']
    opt_res_dir = request.session['user_dir_results_opt']

    # build new optimization name
    idx = source_opt_name.rfind('_')
    opt_name = source_opt_name[:idx] + "_" + time_info

    if hpc_sys == "nsg":
	nsg_obj = hpc_job_manager.Nsg(username_submit=username_submit,
                password_submit=password_submit, core_num=core_num, \
                node_num=node_num, runtime=runtime, gennum=gennum, \
                offsize=offsize, dest_dir=dest_dir, \
                source_opt_zip=source_opt_zip, opt_name=opt_name, \
		source_feat=source_feat, opt_res_dir=opt_res_dir)
	nsg_obj.createzip()
	resp = nsg_obj.runNSG()
	if resp['status_code'] == 200:
            opt_sub_flag_file = os.path.join(dest_dir,\
                    request.session['opt_sub_flag_file'])
            with open(opt_sub_flag_file, 'w') as f:
                f.write("")
            f.close()

    return HttpResponse(json.dumps(resp))


def model_loaded_flag(request):
    if 'res_file_name' in request.session:
	return HttpResponse(json.dumps({"response": request.session['res_file_name']}), content_type="application/json")
    else:
	return HttpResponse(json.dumps({"response": "ERROR"}), content_type="application/json")


def embedded_naas(request):
    """
    Render page with embedded "neuron as a service" app
    """

    accesslogger.info(resources.string_for_log('embedded_naas', request))
    #request.session['sim_flag'] = True
    dest_dir = request.session['user_dir_data_opt_launch']
    sim_run_flag_file = os.path.join(dest_dir,\
            request.session['sim_run_flag_file'])
    with open(sim_run_flag_file, 'w') as f:
        f.write("")
    f.close()

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
    res_folder = request.session['user_dir_sim_run']
    res_folder_ls = os.listdir(res_folder) 
    for filename in res_folder_ls:
        if filename.endswith(".zip"):
            abs_res_file = os.path.join(res_folder, filename)
    request.session['res_file_name'] = os.path.splitext(filename)[0]

    #optimization_model_path = request.session["optimization_model_path"]
    #source_opt_name = request.session['source_opt_name']
    #final_path = os.path.join(optimization_model_path, source_opt_name, source_opt_name + '.zip')
    #r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(final_path, "rb")});
    r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(abs_res_file, "rb")});
    
    return HttpResponse(json.dumps({"response": "ERROR"}), content_type="application/json")


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
    request.session['hpc_sys'] = form_data['hpc_sys']

    if form_data['hpc_sys'] == 'nsg':
	nsg_obj = hpc_job_manager.Nsg() 
        resp_check_login = nsg_obj.checkNsgLogin(form_data['username_submit'],
                form_data['password_submit'])
        if resp_check_login['response'] == 'OK':
            request.session['username_submit'] = form_data['username_submit']
            request.session['password_submit'] = form_data['password_submit']
            resp_dict = {'response':'OK', 'message':''}
        else:
            resp_dict = {'response':'KO', 'message':'Bad credentials inserted'}

    return HttpResponse(json.dumps(resp_dict), content_type="application/json")


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

    response = {"feat":False, "opt_files":False, "opt_set":False, \
            "run_sim":False, "opt_flag":False, "sim_flag":False}
    data_feat = request.session['user_dir_data_feat']
    data_opt = request.session['user_dir_data_opt_set']
    sim_zip = request.session['user_dir_sim_run']
    if os.path.isfile(os.path.join(data_feat, "features.json")) and \
	    os.path.isfile(os.path.join(data_feat, "protocols.json")):
		response['feat'] = True
    if os.path.exists(data_opt) and not os.listdir(data_opt) == []:
	response['opt_files'] = True
    if os.path.exists(sim_zip) and not os.listdir(sim_zip) == []:
	response['run_sim'] = True
    if ('gennum' and 'offsize' and 'nodenum' and 'corenum' and 'runtime' and \
            'username_submit' and 'password_submit' and 'hpc_sys') in request.session:
	response['opt_set'] = True

    dest_dir = request.session['user_dir_data_opt_launch']

    if os.path.exists(os.path.join(dest_dir, \
            request.session['opt_sub_flag_file'])):
	response['opt_flag'] = True

    if os.path.exists(os.path.join(dest_dir, \
            request.session['sim_run_flag_file'])):
	response['sim_flag'] = True
    if request.session['wf_id']:
        response['wf_id'] = request.session['wf_id']


    return HttpResponse(json.dumps(response), content_type="application/json")



# delete feature files
def delete_files(request, filetype=""):
    if filetype == "feat":
        folder = request.session['user_dir_data_feat']
    elif filetype == "optset":
        folder = request.session['user_dir_data_opt_set']
    elif filetype == "modsim":
        folder = request.session['user_dir_sim_run']

    shutil.rmtree(folder)
    os.makedirs(folder)

    return HttpResponse(json.dumps({"resp":True}), content_type="application/json")


def upload_files(request, filetype = ""):
    filename_list = request.FILES.getlist('opt-res-file')

    if filetype == "feat":
	final_res_folder = request.session['user_dir_data_feat']
	ext = '.json'

    elif filetype == "optset":
	final_res_folder = request.session['user_dir_data_opt_set']

	# remove folder with current zip file
	if os.listdir(final_res_folder):
	    shutil.rmtree(final_res_folder)
	    os.makedirs(final_res_folder)

	ext = '.zip'

    elif filetype == "modsim":
	final_res_folder = request.session['user_dir_sim_run']

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
        request.session['source_opt_name'] = os.path.splitext(filename)[0]
        request.session['source_opt_zip'] = final_res_file 
    
    return HttpResponse(json.dumps({"resp":"Success"}), content_type="application/json") 


def get_nsg_job_list(request):
    #return HttpResponse(json.dumps({"safa":"fff", "sadfsadfadasdfaasdfasdf":"fff"}), content_type="application/json") 
    """
    """
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
    """
    """
    #return HttpResponse(json.dumps({"job_id": jobid, "job_date_submitted":"2017-07-24T16:40:21-07:00", "job_stage":"COMPLETED"}), content_type="application/json") 

    hpc_sys_fetch = request.session['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
	username_fetch = request.session['username_fetch']
	password_fetch = request.session['password_fetch']

	nsg_obj = hpc_job_manager.Nsg(username_fetch=username_fetch, password_fetch=password_fetch) 

	resp = nsg_obj.fetch_job_details(jobid)
    return HttpResponse(json.dumps(resp), content_type="application/json") 


def download_job(request, job_id=""): 
    """
    """

    hpc_sys_fetch = request.session['hpc_sys_fetch'] 
    if hpc_sys_fetch == "nsg":
	username_fetch = request.session['username_fetch']
	password_fetch = request.session['password_fetch']
	opt_res_dir = request.session['user_dir_results_opt']

	# remove folder with current zip file
	if os.listdir(opt_res_dir):
	    shutil.rmtree(opt_res_dir)
	    os.makedirs(opt_res_dir)

	nsg_obj = hpc_job_manager.Nsg(username_fetch=username_fetch, password_fetch=password_fetch, \
		opt_res_dir=opt_res_dir) 

	resp_job_details = nsg_obj.fetch_job_details(job_id)
	job_res_url = resp_job_details['job_res_url']
	resp = nsg_obj.fetch_job_results(job_res_url)

    return HttpResponse(json.dumps(resp), content_type="application/json") 


def modify_analysis_py(request):
    opt_res_folder = request.session['user_dir_results_opt']
    output_fetched_file = os.path.join(opt_res_folder, "output.tar.gz")

    if not os.path.exists(output_fetched_file):
        return HttpResponse(json.dumps({"response":"KO", "message":"No output \
            file downloaded"}), content_type="application/json")

    tar = tarfile.open(os.path.join(opt_res_folder, "output.tar.gz"))
    tar.extractall(path=opt_res_folder)
    tar.close()

    analysis_file_list = []
    for (dirpath, dirnames, filenames) in os.walk(opt_res_folder):
	for filename in filenames:
	    if filename == "analysis.py":
		analysis_file_list.append(os.path.join(dirpath,filename))

    if len(analysis_file_list) != 1:
	resp = {"Status":"ERROR", "Message":"No (or multiple) analysis.py file(s) found"}
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
	lines[243]='    plot_multiple_responses([responses], fig=model_fig, traces=traces)\n'
	lines[366]="def plot_multiple_responses(responses, fig, traces):\n"
	lines[369] = "\n"
	lines[370] = "\n"
	lines[371] = "\n"# n is the line number you want to edit; subtract 1 as indexing of list starts from 0
	f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.

	f = open(full_file_path, 'w')
	f.writelines(lines)
	f.close()

	f = open(os.path.join(file_path, 'evaluator.py'), 'r')    # pass an appropriate path of the required file
	lines = f.readlines()
	lines[167]='    #print param_names\n'
	f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.


	f = open(os.path.join(file_path, 'evaluator.py'), 'w')    # pass an appropriate path of the required file
	f.writelines(lines)
	f.close()
        current_working_dir = os.getcwd()
        os.chdir(up_folder)

        import model
	fig_folder = os.path.join(up_folder, 'figures')

	if os.path.exists(fig_folder):
	    shutil.rmtree(fig_folder)
	os.makedirs(fig_folder)

	checkpoints_folder = os.path.join(up_folder, 'checkpoints')
	if 'checkpoint.pkl' not in os.listdir(checkpoints_folder):
	    for files in os.listdir(checkpoints_folder):
		if files.endswith('pkl'):
		    shutil.copy(os.path.join(checkpoints_folder, files), \
			    os.path.join(checkpoints_folder, 'checkpoint.pkl'))
                    os.remove(os.path.join(up_folder, 'checkpoints', files))
                else:
                    if files.endswith('.hoc'):
                        os.remove(os.path.join(up_folder, 'checkpoints', files))

        f = open('opt_neuron.py', 'r')
        lines = f.readlines()

        new_line = ["import matplotlib \n"]
        new_line.append("matplotlib.use('Agg') \n")
        for i in lines:
            new_line.append(i)

        f.close()

        f = open('opt_neuron.py', 'w')
        f.writelines(new_line)
        f.close()

        os.system(". /web/bspg/venvbspg/bin/activate; nrnivmodl mechanisms")

        if os.path.isdir('r_0')==True:
            shutil.rmtree('r_0')
        os.mkdir('r_0')
        os.system(". /web/bspg/venvbspg/bin/activate; python opt_neuron.py --analyse --checkpoint ./checkpoints/checkpoint.pkl > /dev/null 2>&1")

        os.chdir(current_working_dir)

    
    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")


def zip_sim(request):
    user_dir_res_opt = request.session['user_dir_results_opt']
    user_dir_sim_run = request.session['user_dir_sim_run']

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
        for root, dirs, files in os.walk(user_dir_res_opt):
            if (root.endswith("mechanisms") or root.endswith("morphology") or \
                    root.endswith("checkpoints")):
                crr_folder = os.path.split(root)[1]
                dst = os.path.join(sim_mod_folder, crr_folder)
                shutil.copytree(root,dst)
    

    for filename in os.listdir(os.path.join(sim_mod_folder, 'checkpoints')):
        if filename.endswith(".hoc"):
            os.rename(os.path.join(sim_mod_folder, "checkpoints", filename), \
                    os.path.join(sim_mod_folder, "checkpoints", "cell.hoc"))

    current_working_dir = os.getcwd()
    os.chdir(user_dir_sim_run)           
    zipname = crr_opt_name + '.zip'

    foo = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)

    crr_dir_opt = os.path.join('.', crr_opt_name)
    for root, dirs, files in os.walk('.'):
        if (root == os.path.join(crr_dir_opt, 'morphology')) or \
        (root == os.path.join(crr_dir_opt, 'checkpoints')) or \
        (root == os.path.join(crr_dir_opt, 'mechanisms')):
            for f in files:
                foo.write(os.path.join(root, f))

    foo.close()

    os.chdir(current_working_dir)

    return HttpResponse(json.dumps({"response":"OK"}), content_type="application/json")
    

def download_zip(request, filetype=""):
    """
    download files
    """
    current_working_dir = os.getcwd()
    if filetype == "feat":
        fetch_folder = request.session['user_dir_data_feat']
        os.chdir(fetch_folder)
        zipname = os.path.join(fetch_folder, "features.zip")
        foo = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        foo.write("features.json")
        foo.write("protocols.json")
        foo.close()
    elif filetype == "optset":
        fetch_folder = request.session['user_dir_data_opt_set']
    elif filetype == "modsim":
        fetch_folder = request.session['user_dir_sim_run']

    zip_file_list = []
    for i in os.listdir(fetch_folder):
        if i.endswith(".zip"):
            zip_file_list.append(i)
    crr_file = zip_file_list[0]
    full_file_path = os.path.join(fetch_folder, crr_file)
    crr_file_full = open(full_file_path, "r")
    response = HttpResponse(crr_file_full, content_type="application/zip")

    response['Content-Disposition'] = 'attachment; filename="%s"' % crr_file
    os.chdir(current_working_dir)

    return response


########### handle file upload to storage collab
def save_wf_to_storage(request):

    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session['collab_id']
    user_crr_wf_dir = request.session['user_dir']
    wf_id = request.session['wf_id']
    hhnb_storage_folder = request.session['hhnb_storage_folder']
    username = request.session["username"]

    context = request.session['context']
    
    access_token = get_access_token(request.user.social_auth.get())

    sc = service_client.Client.new(access_token)
    ac = service_api_client.ApiClient.new(access_token)
    
    # retrieve collab related projects
    project_dict = ac.list_projects(None, None, None, collab_id)
    project = project_dict['results']
    storage_root = ac.get_entity_path(project[0]['uuid'])
    
    # get current working directory
    current_working_dir = os.getcwd()

    # create zip file with the entire workflow
    os.chdir(os.path.join(user_crr_wf_dir, '..'))
    zipname = wf_id + '.zip'
    if os.path.exists(zipname):
        os.remove(zipname)

    foo = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(os.path.join('.', wf_id)):
        for d in dirs:
            if os.listdir(os.path.join(root,d)) == []:
                foo.write(os.path.join(root, d))
        for f in files:
            foo.write(os.path.join(root, f))
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

    sc.upload_file(zipname, str(crr_zip_storage_path), \
        "application/zip")
    os.chdir(current_working_dir)

    return HttpResponse(json.dumps({"response":"OK", "message":""}), content_type="application/json")


def get_context(request):
    """
    Get the context used to call the application
    """
    context = request.session['context']

    return HttpResponse(json.dumps({"context":context}), content_type="application/json")


def wf_storage_list(request):

    # retrieve access_token
    access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session['collab_id']

    hhnb_storage_folder = request.session['hhnb_storage_folder']
    username = request.session["username"]

    context = request.session['context']
    
    access_token = get_access_token(request.user.social_auth.get())

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
    if not sc.exists(wf_storage_dir):
        storage_list = []
    else:
        storage_list = sc.list(wf_storage_dir)

    os.chdir(current_working_dir)

    return HttpResponse(json.dumps({"list":storage_list}), content_type="application/json")

