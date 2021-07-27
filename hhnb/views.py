""" Views"""

import sys
import traceback
import json
import logging
import os
import zipfile
import subprocess
import shutil
import tarfile
import datetime
import urllib
import uuid
import requests

from itertools import takewhile

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseBadRequest, HttpResponseForbidden

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from hbp_validation_framework import ModelCatalog
import ebrains_drive

from hhnb.tools import resources, hpc_job_manager, wf_file_manager

from mozilla_django_oidc.contrib.drf import get_oidc_backend

from deprecated import deprecated

# set logging up
#logging.basicConfig(stream=sys.stdout)
#àlogger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
#accesslogger = logging.getLogger('hhnb_access.log')
#accesslogger.addHandler(logging.FileHandler('hhnb_access.log'))
#accesslogger.setLevel(logging.DEBUG)


def home(request, exc=None, ctx=None):
    """
    Serving home page for "hh neuron builder" application
    """
    if not exc and exc not in request.session:
        exc = 'tab_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    if not ctx:
        ctx = uuid.uuid4()

    old_wf = request.session.get('old_wf', None)
    old_exc = request.session.get('old_exc', None)
    old_ctx = request.session.get('old_ctx', None)

    if old_wf:
        r0 = set_exc_tags(request, exc, ctx)
        r1 = initialize(request, exc, ctx)
        r2 = create_wf_folders(request, wf_type='restore', exc=exc, ctx=ctx) 
        
        request.session['old_wf'] = None
        request.session['old_exc'] = None
        request.session['old_ctx'] = None
        
        request.session.save()
        
        return render(request, 'hhnb/workflow.html', context={"exc": exc, "ctx": str(ctx)})

    context = {"exc": exc, "ctx": str(ctx)}
    return render(request, 'hhnb/home.html', context)


def set_exc_tags(request, exc="", ctx=""):
    print('set_exc_tags() called.')

    if exc in request.session and not request.session[exc].get('ctx', None):
        return HttpResponse(json.dumps({'response': 'KO', 'message': 'An error occurred while loading the application.<br><br>Please reload.'}), content_type='application/json')

    request.session[exc] = {'ctx': str(ctx)}
    request.session.save()


    #if exc in request.session:
    #    exc = ""
    #else:
    #    request.session[exc] = {}
    #    request.session[exc]['ctx'] = str(ctx)
    #    request.session.save()
    #if exc not in request.session:
    #    exc = ""
    #if exc == "" or "ctx" not in request.session[exc]:
    #    ctx = ""

    #if exc == "" or ctx == "":
    #    resp = {
    #        "response": "KO",
    #        "message": "An error occurred while loading the application.<br><br>Please reload."
    #    }
    #else:
    resp = {"response": "OK", "message": ""}

    return HttpResponse(json.dumps(resp), content_type="application/json")


def initialize(request, exc="", ctx=""):
    print('initialize() called.')
    if exc not in request.session.keys():
        return HttpResponse(json.dumps({"response": "KO",
                                        "message": "An error occured while loading the application.<br><br>Please reload."}),
                            content_type="application/json")

    # my_url = settings.HBP_MY_USER_URL
    # collab_context_url = settings.HBP_COLLAB_SERVICE_URL + "collab/context/"
    #
    # headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    # request.session[exc]['headers'] = headers
    #
    # res = requests.get(my_url, headers=headers)
    # collab_res = requests.get(collab_context_url + ctx, headers=headers)
    #
    # if res.status_code != 200 or collab_res.status_code != 200:
    #     manage_auth.Token.renewToken(request)
    #
    #     headers = {'Authorization': 'TOKEN'}  # get_auth_header(request.user.social_auth.get())}
    #
    #     res = requests.get(my_url, headers=headers)
    #     collab_res = requests.get(collab_context_url + ctx, headers=headers)
    #
    # if res.status_code != 200 or collab_res.status_code != 200:
    #     return render(request, 'efelg/hbp_redirect.html')
    #
    # res_dict = res.json()
    #
    if "username" not in request.session[exc]:
        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = 'anonymous'
        request.session[exc]['username'] = username
    # if "userid" not in request.session[exc]:
    #     userid = res_dict['id']
    #     request.session[exc]['userid'] = userid
    if "ctx" not in request.session[exc]:
        request.session[exc]['ctx'] = ctx
    # if "collab_id" not in request.session[exc]:
    #     collab_id = collab_res.json()['collab']['id']
    #     request.session[exc]['collab_id'] = collab_id

    # build directory names
    workflows_dir = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'workflows')
    # scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'singlecellmodeling_structure.json')
    # scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'hippocampus_models_py3.json')
    scm_structure_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'hippocampus_models_new.json')
    opt_model_path = os.path.join(settings.MEDIA_ROOT, 'hhnb', 'bsp_data_repository', 'optimizations')

    # create global variables in request.session
    request.session[exc]['singlecellmodeling_structure_path'] = scm_structure_path
    request.session[exc]['optimization_model_path'] = opt_model_path
    request.session[exc]['workflows_dir'] = workflows_dir
    request.session[exc]['hhnb_storage_folder'] = "hhnb_workflows"
    request.session[exc]['opt_sub_flag'] = False 
    request.session[exc]['opt_sub_param_file'] = 'opt_sub_param.json'
    request.session[exc]['sim_run_flag_file'] = 'sim_run_flag.txt'
    request.session[exc]['mod_clb_url'] = 'https://collab.humanbrainproject.eu/#/collab/79183/nav/535962?state=uuid%3D'
    request.session[exc]['wf_job_ids'] = 'wf_job_ids.json'
    request.session[exc]['mod_clb_id'] = '79183'
    request.session[exc]['mod_clb_user'] = 'test116'

    #accesslogger.info(resources.string_for_log('home', request))

    request.session.save()

    response = {"response": "OK", "message": ""}
    return HttpResponse(json.dumps(response), content_type="application/json")


def create_wf_folders(request, wf_type="new", exc="", ctx=""):
    """
    Create folders for current workflow
    """

    print('create_wf_folders() called.')

    if exc not in request.session.keys() or "workflows_dir" not in request.session[exc]:
        response = {"response": "KO", "message": "An error occurred while loading the application.<br><br>Please reload."}
        return HttpResponse(json.dumps(response), content_type="application/json")

    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    wf_id = time_info + '_' + username
    request.session[exc]['time_info'] = time_info
    request.session[exc]['wf_id'] = wf_id
    
    if wf_type == 'restore':
        old_wf = request.session.get('old_wf', None)
        if old_wf:
            shutil.copytree(old_wf, os.path.join(workflows_dir, username, wf_id))
            
            old_exc_dict = request.session[request.session['old_exc']]
            old_user_dir = old_exc_dict['user_dir']
            new_exc_dict = request.session[exc]
            new_user_dir = os.path.join(workflows_dir, username, wf_id)

            for k in old_exc_dict:
                if k not in new_exc_dict:    
                    if k == 'analysis_id':
                        if k not in new_exc_dict:
                            new_exc_dict.update({k: []})
                        for a in old_exc_dict[k]:
                            if type(a) == str:
                                a = a.replace(old_user_dir, new_user_dir)
                            new_exc_dict[k].append(a)
                    else:
                        if type(old_exc_dict[k]) == str:
                            v = old_exc_dict[k].replace(old_user_dir, new_user_dir)
                        else:
                            v = old_exc_dict[k]
                        new_exc_dict.update({k: v})  

            request.session.save()

            return HttpResponse(json.dumps({"response": "OK"}), content_type="application/json")
        
    if wf_type == "new":
        # delete keys if present in request.session
        request.session[exc].pop('from_hhf', None)
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
        request.session[exc].pop('source_opt_id', None)
        request.session[exc].pop('fetch_opt_uuid', None)
        request.session[exc]['user_dir'] = os.path.join(workflows_dir, username, wf_id)
        request.session[exc]['user_dir_data'] = os.path.join(workflows_dir, username, wf_id, 'data')
        request.session[exc]['user_dir_data_feat'] = os.path.join(workflows_dir, username, wf_id, 'data', 'features')
        request.session[exc]['user_dir_data_opt_set'] = os.path.join(workflows_dir, username, wf_id, 'data', 'opt_settings')
        request.session[exc]['user_dir_data_opt_launch'] = os.path.join(workflows_dir, username, wf_id, 'data', 'opt_launch')
        request.session[exc]['user_dir_results'] = os.path.join(workflows_dir, username, wf_id, 'results')
        request.session[exc]['user_dir_results_opt'] = os.path.join(workflows_dir, username, wf_id, 'results', 'opt')
        request.session[exc]['user_dir_sim_run'] = os.path.join(workflows_dir, username, wf_id, 'sim')
        request.session[exc]["analysis_id"] = []
        request.session[exc]['opt_sub_flag'] = False

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
        exc = "tab_" + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        crr_user_dir = request.session[exc]['user_dir']
        new_user_dir = os.path.join(workflows_dir, username, wf_id)

        # copy current user dir to the newly created workflow's dir
        shutil.copytree(os.path.join(crr_user_dir, 'data'), os.path.join(new_user_dir, 'data'), symlinks=True)

        request.session[exc]['user_dir'] = new_user_dir
        request.session[exc]['user_dir_data'] = os.path.join(new_user_dir, 'data')
        request.session[exc]['user_dir_data_feat'] = os.path.join(new_user_dir, 'data', 'features')
        request.session[exc]['user_dir_data_opt_set'] = os.path.join(new_user_dir, 'data', 'opt_settings')
        request.session[exc]['user_dir_data_opt_launch'] = os.path.join(new_user_dir, 'data', 'opt_launch')
        request.session[exc]["analysis_id"] = []

        # remove old optimization launch folder and create a new one
        shutil.rmtree(request.session[exc]['user_dir_data_opt_launch'])
        os.makedirs(request.session[exc]['user_dir_data_opt_launch'])

        opt_pf = os.path.join(crr_user_dir, 'data', 'opt_launch', request.session[exc]['opt_sub_param_file'])
        if os.path.exists(opt_pf):
            shutil.copy(opt_pf, request.session[exc]['user_dir_data_opt_launch'])

        # copy current user dir results folder  to the newly created workflow
        shutil.copytree(os.path.join(crr_user_dir, 'results'), os.path.join(new_user_dir, 'results'), symlinks=True)

        request.session[exc]['user_dir_results'] = os.path.join(new_user_dir, 'results')
        request.session[exc]['user_dir_results_opt'] = os.path.join(new_user_dir, 'results', 'opt')

        # copy current user dir results folder  to the newly created workflow
        shutil.copytree(os.path.join(crr_user_dir, 'sim'), os.path.join(new_user_dir, 'sim'), symlinks=True)

        request.session[exc]['user_dir_sim_run'] = os.path.join(workflows_dir, username, wf_id, 'sim')

        sim_flag_file = os.path.join(request.session[exc]['user_dir_sim_run'], request.session[exc]['sim_run_flag_file'])
        if os.path.exists(sim_flag_file):
            os.remove(sim_flag_file)

    request.session.save()

    return HttpResponse(json.dumps({"response": "OK"}), content_type="application/json")


@deprecated(reason='method unused with the new version')
def fetch_wf_from_storage(request, wfid="", exc="", ctx=""):
    """
    Fetch previous workflows from current collab's storage
    """

    time_info = wfid[:14]
    idx = wfid.find('_')

    userid_wf = wfid[idx + 1:]
    username = request.session[exc]['username']
    workflows_dir = request.session[exc]['workflows_dir']

    # retrieve access_token
    # TODO: get access token
    # access_token = get_access_token(request.user.social_auth.get())

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']

    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]

    request.session[exc]['time_info'] = time_info
    request.session[exc]['wf_id'] = wfid

    # TODO: replace with new API
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
            request.session[exc]['source_opt_zip'] = os.path.join(user_dir_data_opt, crr_f)
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

    return HttpResponse(json.dumps({"response": "OK"}), content_type="application/json")


def embedded_efel_gui(request, exc='', ctx=''):
    """
    Serving page for rendering embedded efel gui page
    """

    #accesslogger.info(resources.string_for_log('embedded_efel_gui', request))
    context = {}
   
    if request.session[exc].get('hhf_etraces', None):
        context = {'hhf_etraces_dir': request.session[exc].get('hhf_etraces_dir', None), 'wfid': request.session[exc]['wf_id']}
    
    return render(request, 'hhnb/embedded_efel_gui.html', context)


def workflow(request, exc='', ctx=''):
    """
    Serving page for rendering workflow page
    """

    if exc and ctx: 
        context = {'exc': exc, 'ctx': str(ctx)}

        return render(request, 'hhnb/workflow.html', context)

    return render(request, 'hhnb/workflow.html')


def choose_opt_model(request):
    """
    Serving page for rendering choose optimization model page
    """

    #accesslogger.info(resources.string_for_log('choose_opt_model', request))
    # return render(request, 'hh_neuron_builder/choose_opt_model.html')
    return render(request, 'hhnb/choose_opt_model.html')


def get_model_list(request, exc="", ctx=""):
    model_file = request.session[exc]["singlecellmodeling_structure_path"]
    with open(model_file) as json_file:
        model_file_dict = json.load(json_file)

    return HttpResponse(json.dumps(model_file_dict), content_type="application/json")

def get_model_list2(request, exc="", ctx=""):
    """
    Serving api call to get list of optimization models
    """
    
    #model_file = request.session[exc]["singlecellmodeling_structure_path"]
    #with open(model_file) as json_file:
    #    model_file_dict = json.load(json_file)

    #return HttpResponse(json.dumps(model_file_dict), content_type="application/json")
    
    # Authenticate with token. To be change with permanent token
    
    mc_filter = settings.MODEL_CATALOG_FILTER

    mc = ModelCatalog(token=request.session['oidc_access_token'])
    
    models = mc.list_models()
    filtered_models = []
    
    fG = mc_filter['granule_models']
    fH = mc_filter['hippocampus_models']
    fP = mc_filter['purkinje_models']

    for m in models:
        if m['brain_region'] == fG['brain_region'] and m['cell_type'] == fG['cell_type'] and m['model_scope'] == fG['model_scope'] and m['species'] == fG['species'] and m['abstraction_level'] == fG['abstraction_level']:
                filtered_models.append(m)
                continue
        elif m['organization'] == fH['organization'] and m['model_scope'] == fH['model_scope'] and m['species'] == fH['species'] and m['collab_id'] == fH['collab_id']:
                filtered_models.append(m)
                continue
        elif m['brain_region'] == fP['brain_region'] and m['cell_type'] == fP['cell_type'] and m['model_scope'] == fP['model_scope'] and m['name'] == fP['name']:
                filtered_models.append(m)
    print(len(filtered_models))       
    if len(models) > 0:
        return JsonResponse(data={'models': json.dumps(filtered_models)}, status=200)
    return HttpResponse(status=404)


@csrf_exempt
def copy_feature_files(request, exc='', ctx=''):

    
    feature_folder = request.POST.get('folder', None)
    
    response = {"expiration": False}
   
    if not os.path.exists(request.session[exc]["user_dir"]) or not os.path.exists(feature_folder):
        print("efelg results folders not existing")
        response = {"expiration": True}
        return HttpResponse(json.dumps(response), content_type="application/json")

    print(os.listdir(feature_folder))
    for d in os.listdir(feature_folder):
        print(d)
        if os.path.isdir(os.path.join(feature_folder, d)):
            feature_folder = os.path.join(feature_folder, d)
            break

    print(os.listdir(feature_folder))
    if os.path.isfile(os.path.join(feature_folder, 'features.json')) and os.path.isfile(os.path.join(feature_folder, 'protocols.json')):
        if request.session[exc].get('from_hhf', None):
            dst_dir = os.path.join(request.session[exc]['hhf_dir'], 'config')
        else:
            dst_dir = request.session[exc]['user_dir_data_feat']

        shutil.copy2(os.path.join(feature_folder, 'features.json'), dst_dir)
        shutil.copy2(os.path.join(feature_folder, 'protocols.json'), dst_dir)
        response = {'resp': 'OK', 'message': 'features files copied'}

    else:
        response = {'resp': 'KO', 'message': 'features files not found'}

    # set hhf model key if features are fetched/uploaded after set files in HHF 
    if request.session[exc].get('hhf_model_key', None):
        hhf_apply_model_key(request, exc, ctx, request.session[exc]['hhf_model_key'])
    
    return HttpResponse(json.dumps(response), content_type="application/json")


# fetch model from dataset
def fetch_opt_set_file(request, source_opt_name="", source_opt_id="", exc="", ctx=""):
#def fetch_opt_set_file(request, source_opt_id='', exc='', ctx=''):
    """
    Set optimization setting file
    """
    
    print('fetch_opt_set_file() called.')

    if request.session[exc].get('from_hhf', None):
        for f in os.listdir(os.path.join(request.session[exc]['hhf_dir'], 'config')):
            if f == 'features.json' or f == 'protocols.json':
                shutil.copy(os.path.join(request.session[exc]['hhf_dir'], 'config', f), request.session[exc]['user_dir_data_feat']) 
        r = hhf_delete_all(request, exc, ctx)
    
    
    #source_opt_id = str(source_opt_id)
    response = {"response": "OK", "message": ""}

    # opt_model_path = request.session[exc]['optimization_model_path']
    user_dir_data_opt = request.session[exc]['user_dir_data_opt_set']

    if not os.path.exists(user_dir_data_opt):
        response.update({"response": "KO", "message": "Folder does not exist anymore."})
        return JsonResponse(response)

    print('setting up directories')

    shutil.rmtree(user_dir_data_opt)
    os.makedirs(user_dir_data_opt)

    model_file = request.session[exc]["singlecellmodeling_structure_path"]
    with open(model_file) as json_file:
        model_file_dict = json.load(json_file)

    request.session[exc]['source_opt_name'] = source_opt_name

    for k in model_file_dict:
        crr_k = str(list(k.keys())[0])
        if crr_k == source_opt_name:
            zip_url = k[crr_k]['meta']['zip_url']
            break

    #mc = ModelCatalog(token=request.session['oidc_access_token'])
    #model = mc.get_model(model_id=source_opt_id)
    #source_opt_name = model['name']

    # TODO: add version control on js
    #zip_url = ''
    #for instance in model['instances']:
    #    if instance['source']:
    #        zip_url = instance['source']
    #        break

    print('downloading the model')
    r = requests.get(zip_url)
    opt_zip_path = os.path.join(user_dir_data_opt, source_opt_name + '.zip')  
    with open(opt_zip_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=4096):
            f.write(chunk)
    print('finish')
    request.session[exc]['source_opt_zip'] = opt_zip_path
    request.session[exc]['source_opt_id'] = source_opt_id

    request.session.save()

    return JsonResponse(response)


def run_optimization(request, exc="", ctx=""):
    """
    Run optimization on remote systems
    """
    print(json.dumps(request.session[exc], indent=4))

    # fetch information from the session variable
    core_num = request.session[exc]['corenum']
    node_num = request.session[exc]['nodenum']
    runtime = request.session[exc]['runtime']
    gennum = request.session[exc]['gennum']
    time_info = request.session[exc]['time_info']
    offsize = request.session[exc]['offsize']
    hpc_sys = request.session[exc]['hpc_sys']

    workflows_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']

    if request.session[exc].get('from_hhf', None):
        from_hhf = True 
        source_opt_id = request.session[exc]['hhf_model_key']
        source_opt_name =  request.session[exc]['hhf_model_key']
        source_opt_zip = None
        
        dest_dir = os.path.join(request.session[exc]['user_dir'], 'hhf_opt')
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        opt_name = source_opt_name
    
        src_opt_dir = request.session[exc]['hhf_dir']
        zfName = request.session[exc]['hhf_model_key']

    else:
        from_hhf = False
        source_opt_id = request.session[exc]['source_opt_id']
        source_opt_name = request.session[exc]['source_opt_name']
        source_opt_zip = request.session[exc]['source_opt_zip']
        dest_dir = request.session[exc]['user_dir_data_opt_launch']
        user_dir_data_opt = request.session[exc]['user_dir_data_opt_set']
        source_feat = request.session[exc]['user_dir_data_feat']
        opt_res_dir = request.session[exc]['user_dir_results_opt']

        idx = source_opt_name.rfind('_')
        opt_name = source_opt_name[:idx] + "_" + time_info

        # build new optimization name
        fin_opt_folder = os.path.join(dest_dir, opt_name)
    
        zfName = os.path.join(dest_dir, opt_name + '.zip')
    
    wf_id = request.session[exc]['wf_id']

    if hpc_sys == "NSG":
        execname = "init.py"
        joblaunchname = ""

        username_submit = request.session[exc]['username_submit']
        password_submit = request.session[exc]['password_submit']

        if from_hhf:
            zfName = hpc_job_manager.OptFolderManager.create_hhf_zip(src_dir=src_opt_dir, dst_dir=dest_dir, gennum=gennum, offsize=offsize, zfName=zfName,
                                                            hpc=hpc_sys, execname='init.py')

        else:
            hpc_job_manager.OptFolderManager.createzip(fin_opt_folder=fin_opt_folder, source_opt_zip=source_opt_zip,
                                                       opt_name=opt_name, source_feat=source_feat, gennum=gennum,
                                                       offsize=offsize, zfName=zfName, hpc=hpc_sys, execname="init.py")

        resp = hpc_job_manager.Nsg.runNSG(username_submit=username_submit, password_submit=password_submit,
                                          core_num=core_num, node_num=node_num, runtime=runtime, zfName=zfName)

    elif hpc_sys == "DAINT-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}

        project_id = request.session[exc]['project']

        execname = "zipfolder.py"
        joblaunchname = "ipyparallel.sbatch"

        # retrieve access_token
        access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

        if from_hhf:
            zfName = hpc_job_manager.OptFolderManager.create_hhf_zip(src_dir=src_opt_dir, dst_dir=dest_dir, gennum=gennum, offsize=offsize, zfName=zfName,
                                                            hpc=hpc_sys, execname=execname, joblaunchname=joblaunchname)

        else:
            hpc_job_manager.OptFolderManager.createzip(fin_opt_folder=fin_opt_folder, source_opt_zip=source_opt_zip,
                                                       opt_name=opt_name, source_feat=source_feat, gennum=gennum,
                                                       offsize=offsize, zfName=zfName, hpc=hpc_sys, execname=execname,
                                                       joblaunchname=joblaunchname)

        # launch job on cscs-pizdaint
        resp = hpc_job_manager.Unicore.run_unicore_opt(hpc=hpc_sys, filename=zfName, joblaunchname=joblaunchname,
                                                       token=access_token, jobname=wf_id, core_num=core_num,
                                                       node_num=node_num, runtime=runtime, foldname=opt_name, project=project_id)

    elif hpc_sys == "SA-CSCS":
        PROXIES = {}
        execname = "zipfolder.py"
        joblaunchname = "ipyparallel.sbatch"

        # retrieve access_token
        access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

        if from_hhf:
            zfName = hpc_job_manager.OptFolderManager.create_hhf_zip(src_dir=src_opt_dir, dst_dir=dest_dir, gennum=gennum, offsize=offsize, zfName=zfName,
                                                            hpc=hpc_sys, execname=execname, joblaunchname=joblaunchname)
        else:
            hpc_job_manager.OptFolderManager.createzip(fin_opt_folder=fin_opt_folder, source_opt_zip=source_opt_zip,
                                                       opt_name=opt_name, source_feat=source_feat, gennum=gennum,
                                                       offsize=offsize, zfName=zfName, hpc=hpc_sys, execname=execname,
                                                       joblaunchname=joblaunchname)

        # launch job on cscs-pizdaint
        resp = hpc_job_manager.Unicore.run_unicore_opt(hpc=hpc_sys, filename=zfName, joblaunchname=joblaunchname,
                                                       token=access_token, jobname=wf_id, core_num=core_num,
                                                       node_num=node_num, runtime=runtime, foldname=opt_name)


        print(resp)
    if resp['response'] == "OK":
        crr_job_name = resp['jobname']

        request.session[exc]['opt_sub_flag'] = True

        wf_job_ids = request.session[exc]['wf_job_ids']
        ids_file = os.path.join(workflows_dir, username, wf_job_ids)
        ids_dict = {"wf_id": wf_id, "job_id": crr_job_name, "hpc_sys": hpc_sys, "time_info": time_info, "source_opt_id": source_opt_id}

        # update file containing
        if os.path.exists(ids_file):
            with open(ids_file, "r") as fh:
                all_id = json.load(fh)
        else:
            all_id = {}

        all_id[crr_job_name] = ids_dict

        with open(ids_file, "w") as fh:
            json.dump(all_id, fh)

    request.session.save()

    return HttpResponse(json.dumps(resp))


def model_loaded_flag(request, exc="", ctx=""):
    if 'res_file_name' in request.session[exc]:
        return HttpResponse(json.dumps({"response": request.session[exc]['res_file_name']}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({"response": "KO"}), content_type="application/json")


def embedded_naas(request, exc="", ctx=""):
    """
    Render page with embedded "neuron as a service" app
    """

    #accesslogger.info(resources.string_for_log('embedded_naas', request))
    dest_dir = request.session[exc]['user_dir_sim_run']
    sim_run_flag_file = os.path.join(dest_dir, request.session[exc]['sim_run_flag_file'])
    with open(sim_run_flag_file, 'w') as f:
        f.write("")
    f.close()

    return render(request, 'hhnb/embedded_naas.html')


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
        response = {"response": "KO", "message": "No simulation .zip file is present."}
    else:
        request.session[exc]['res_file_name'] = os.path.splitext(filename)[0]
        # r = requests.post("https://blue-naas-svc.humanbrainproject.eu/upload", files={"file": open(abs_res_file, "rb")})
        r = requests.post("https://blue-naas-svc-bsp-epfl.apps.hbp.eu/upload", files={"file": open(abs_res_file, "rb")}, verify=False)
        print(r.status_code, r.content)
        if r.status_code == 200:
            response = {'response': 'OK', 'message': 'Model correctly uploaded to naas.'}
        else:
            response = {'response': 'KO', 'message': 'Model uploading failed.<br>Try again later'}

    request.session.save()

    return JsonResponse(response)


def submit_run_param(request, exc="", ctx=""):
    """
    Save user's optimization parameters
    """

    # selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST
    print(form_data)

    # read data from form
    gennum = int(form_data['gen-max'])
    offsize = int(form_data['offspring'])
    nodenum = int(form_data['node-num'])
    corenum = int(form_data['core-num'])
    hpc_sys = form_data['hpc_sys']

    #
    request.session[exc]['gennum'] = gennum
    request.session[exc]['offsize'] = offsize
    request.session[exc]['nodenum'] = nodenum
    request.session[exc]['corenum'] = corenum
    request.session[exc]['hpc_sys'] = hpc_sys

    wf_id = request.session[exc]['wf_id']
    dest_dir = request.session[exc]['user_dir_data_opt_launch']
    username = request.session[exc]['username']

    project_id = None

    # if chosen system is nsg
    if hpc_sys == 'NSG':
        runtime = float(form_data['runtime'])
        resp_check_login = hpc_job_manager.Nsg.check_nsg_login(username=form_data['username_submit'],
                                                               password=form_data['password_submit'])

        # check credentials correctness
        if resp_check_login['response'] == 'OK':
            request.session[exc]['username_submit'] = form_data['username_submit']
            request.session[exc]['password_submit'] = form_data['password_submit']
            resp_dict = {'response': 'OK', 'message': ''}
        else:
            resp_dict = {'response': 'KO', 'message': 'Username and/or password are wrong'}
            request.session[exc].pop('username_submit', None)
            request.session[exc].pop('password_submit', None)

            return HttpResponse(json.dumps(resp_dict), content_type="application/json")

    elif hpc_sys == "DAINT-CSCS" or hpc_sys == "SA-CSCS":
        if hpc_sys == "DAINT-CSCS":
            project_id = form_data['project']
            request.session[exc]['project'] = project_id

        runtime = form_data['runtime']
        resp_dict = {'response': 'OK', 'message': 'Set Job title'}

    request.session[exc]['runtime'] = runtime
    opt_sub_param_file = os.path.join(dest_dir, request.session[exc]["opt_sub_param_file"])

    hpc_job_manager.OptSettings.print_opt_params(wf_id=wf_id, gennum=str(gennum), offsize=str(offsize),
                                                 nodenum=str(nodenum), corenum=str(corenum), runtime=str(runtime),
                                                 opt_sub_param_file=opt_sub_param_file, hpc_sys=hpc_sys, project=project_id)

    request.session.save()

    return HttpResponse(json.dumps(resp_dict), content_type="application/json")


def submit_fetch_param(request, exc="", ctx=""):
    """
    Save user's optimization parameters
    """
    # selected_traces_rest = request.POST.get('csrfmiddlewaretoken')
    form_data = request.POST
    hpc_sys = form_data["hpc_sys_fetch"]

    # if chosen system is nsg
    if hpc_sys == 'NSG':
        request.session[exc]['hpc_sys_fetch'] = form_data['hpc_sys_fetch']
        resp = hpc_job_manager.Nsg.check_nsg_login(username=form_data['username_fetch'],
                                                   password=form_data['password_fetch'])

        # check credentials correctness
        if resp['response'] == 'OK':
            request.session[exc]['username_fetch'] = form_data['username_fetch']
            request.session[exc]['password_fetch'] = form_data['password_fetch']
        else:
            request.session[exc].pop('username_fetch', None)
            request.session[exc].pop('password_fetch', None)
    elif hpc_sys == "DAINT-CSCS" or hpc_sys == "SA-CSCS":
        request.session[exc]['hpc_sys_fetch'] = form_data['hpc_sys_fetch']
        resp = {'response': 'OK', 'message': 'Job title correctly set'}

    request.session.save()

    return HttpResponse(json.dumps(resp), content_type="application/json")


def status(request):
    return HttpResponse(json.dumps({"hh-neuron-builder-status": 1}), content_type="application/json")


def check_cond_exist(request, exc="", ctx=""):

    """
    Check if conditions for performing steps are present.
    The function checks on current workflow folders whether files are present to go on with the workflow.
    The presence of simulation parameters are also checked.
    """

    if exc not in request.session or "user_dir" not in request.session[exc]:
        resp = {"response": "KO", "message": "An error occurred while loading the application.<br><br>Please go home and restart."}
        return HttpResponse(json.dumps(resp), content_type="application/json")

    # set responses dictionary
    response = {
        "expiration": False,
        "feat": {"status": False, "message": '"features.json" and "protocols.json" NOT present'},
        "opt_files": {"status": False, "message": "Optimization files NOT present"},
        "opt_set": {"status": False, "message": "Optimization parameters NOT set"},
        "run_sim": {"status": False, "message": ""},
        "opt_flag": {"status": False},
        "sim_flag": {"status": False},
        # 'opt_res': {"status": False},
        "opt_res_files": {"status": False},

        "from_hhf": {"status": request.session[exc].get('from_hhf', False)}
    }

    if not os.path.exists(request.session[exc]['user_dir']):
        response = {"expiration": True}
        return HttpResponse(json.dumps(response), content_type="application/json")

    # retrieve folder paths
    if request.session[exc].get('from_hhf', None):
        data_feat = os.path.join(request.session[exc]['hhf_dir'], 'config')
    else:
        data_feat = request.session[exc]['user_dir_data_feat']
    data_opt = request.session[exc]['user_dir_data_opt_set']
    sim_dir = request.session[exc]['user_dir_sim_run']
    res_dir = request.session[exc]['user_dir_results']
    wf_id = request.session[exc]['wf_id']
    dest_dir = request.session[exc]['user_dir_data_opt_launch']

    etraces_files = request.session[exc].get('hhf_etraces', None)
    
    features_file = False
    protocols_file = False
    if os.path.isfile(os.path.join(data_feat, 'features.json')):
        features_file = True
    if os.path.isfile(os.path.join(data_feat, "protocols.json")):
        protocols_file = True
    if features_file and protocols_file:
        response['feat']['status'] = True
        response['feat']['message'] = ""
    elif features_file and not protocols_file:
        response['feat']['status'] = False
        response['feat']['message'] = '"protocols.json" NOT present'
    elif protocols_file and not features_file:
        response['feat']['status'] = False
        response['feat']['message'] = '"features.json" NOT present'

    # check if feature files exist
    elif etraces_files:
        response['feat']['status'] = 'hhf_etraces'
        response['feat']['message'] = 'Extract features from fetched files'

    # check if optimization file exist
    if request.session[exc].get('from_hhf', None):
        hhf_dir = request.session[exc]['hhf_dir']
        morph_file = False
        mechanisms_file = False
        morph_dict = False
        params_dict = False
        config_dir = os.path.join(hhf_dir, 'config')
        morph_dir = os.path.join(hhf_dir, 'morphology')
        mechanisms_dir = os.path.join(hhf_dir, 'mechanisms')
        if os.path.exists(config_dir):
            if os.path.isfile(os.path.join(config_dir, 'morph.json')):
                morph_dict = True
            if os.path.isfile(os.path.join(config_dir, 'parameters.json')):
                params_dict = True
        if os.path.exists(morph_dir):
            if len(os.listdir(morph_dir)) == 1:
                morph_file = True
        if os.path.exists(mechanisms_dir):
            if len(os.listdir(mechanisms_dir)) > 0:
                mechanisms_file = True
        
        if morph_file and mechanisms_file and morph_dict and params_dict:
            response['opt_files']['status'] = True
        else:
            response['opt_files']['status'] = False
            response['opt_files']['message'] = ''
            if not morph_file:
                response['opt_files']['message'] += 'Morphology file NOT present<br>'
            if not mechanisms_file:
                response['opt_files']['message'] += 'Mechanisms files NOT present<br>'
            if not morph_dict:
                response['opt_files']['message'] += '"morph.json" NOT present<br>'
            if not params_dict:
                response['opt_files']['message'] += '"parameters.json" NOT present<br>'
    
    elif os.path.exists(data_opt) and not os.listdir(data_opt) == []:
        response['opt_files']['status'] = True

    # check if simulation files exist
    resp_sim = wf_file_manager.CheckConditions.check_sim_files(sim_path=sim_dir)
    if resp_sim['response'] == "OK":
        response['run_sim']['status'] = True
        response['run_sim']['message'] = ''
    else:
        response['run_sim']['status'] = False
        response['run_sim']['message'] = resp_sim['message']

    # check if ANY optimization results zip file exists
    try:
        for i in os.listdir(res_dir):
            if i.endswith('_opt_res.zip'):
                response['opt_res_files']['status'] = True
                break
    except FileNotFoundError:
        return HttpResponse(content=json.dumps({'response': 'KO', 'message': 'Content empty'}))

    # check if optimization has been submitted
    if request.session[exc].get('from_hhf', None) and os.path.exists(os.path.join(request.session[exc]['user_dir'], 'hhf_opt')):
        for f in os.listdir(os.path.join(request.session[exc]['user_dir'], 'hhf_opt')):
            if f.endswith('.zip'):
                response['opt_flag']['status'] = True
    #elif os.path.exists(os.path.join(dest_dir, request.session[exc]['opt_sub_flag_file'])):
    #    response['opt_flag']['status'] = True
    else:
        response['opt_flag']['status'] = request.session[exc]['opt_sub_flag']

    # check if simulation has been launched
    if os.path.exists(os.path.join(sim_dir, request.session[exc]['sim_run_flag_file'])):
        response['sim_flag']['status'] = True

    # build dictionary with optimization submission parameters
    opt_sub_param_dict = {}
    opt_sub_param_file = os.path.join(request.session[exc]['user_dir_data_opt_launch'], request.session[exc]['opt_sub_param_file'])
    # if parameter file exists, read values
    if os.path.exists(opt_sub_param_file):
        with open(opt_sub_param_file) as json_file:
            opt_sub_param_dict = json.load(json_file)
        response['opt_set']['opt_sub_param_dict'] = opt_sub_param_dict

        rsk = request.session[exc].keys()
        hpc = request.session[exc].get("hpc_sys", "NO-HPC-SELECTED")
        if hpc == 'NO-HPC-SELECTED':
            try:
                hpc = opt_sub_param_dict['hpc_sys']
            except KeyError:
                hpc = 'NO-HPC-SELECTED'
        
        if hpc == "NSG":
            rules = [
                'username_submit' in rsk,
                'password_submit' in rsk,
            ]
        
        elif hpc == "DAINT-CSCS" or hpc == "SA-CSCS":
            if hpc == "DAINT-CSCS":
                request.session[exc]['project'] = opt_sub_param_dict['project']
            rules = [True]
        else:
            rules = [False]
        
        if all(rules):
            response['opt_set']['status'] = True
            response['opt_set']['message'] = ""
        else:
            response['opt_set']['status'] = False
            response['opt_set']['message'] = "Settings retrieved. Credentials NOT set"
            if hpc == 'NO-HPC-SELECTED':
                response['opt_set']['message'] = 'No HPC selected'
    
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
def delete_files(request, file_type="", exc="", ctx=""):
    if file_type == "feat":
        
        if request.session[exc].get('from_hhf', None):
            os.remove(os.path.join(request.session[exc]['hhf_dir'], 'config', 'features.json'))
            os.remove(os.path.join(request.session[exc]['hhf_dir'], 'config', 'protocols.json'))
            return HttpResponse(json.dumps({"resp": True}), content_type="application/json")
            
        folder = request.session[exc]['user_dir_data_feat']
    elif file_type == "optset":
        folder = request.session[exc]['user_dir_data_opt_set']
    elif file_type == "modsim":
        folder = request.session[exc]['user_dir_sim_run']

    shutil.rmtree(folder)
    os.makedirs(folder)

    return HttpResponse(json.dumps({"resp": True}), content_type="application/json")


def upload_feat_files(request, exc='', ctx=''):
    response = upload_files(request, 'feat', exc, ctx)
    # set hhf model key if features are fetched/uploaded after set files in HHF 
    if request.session[exc].get('hhf_model_key', None):
        hhf_apply_model_key(request, exc, ctx, request.session[exc]['hhf_model_key'])
    return response


def upload_optset_files(request, exc='', ctx=''):
    return upload_files(request, 'optset', exc, ctx)


def upload_modsim_files(request, exc='', ctx=''):
    return upload_files(request, 'modsim', exc, ctx)


def upload_files(request, filetype='', exc='', ctx=''):
    filename_list = request.FILES.getlist('formFile')

    if filetype == "feat":
        for f in filename_list:
            if f.name != 'features.json' and f.name != 'protocols.json':
                return JsonResponse(data={'response': 'KO', 'message': 'Wrong file uploaded.<br>Please upload "features.json" and/or "protocols.json" file only.'})
        if request.session[exc].get('from_hhf', None):
            final_res_folder = os.path.join(request.session[exc]['hhf_dir'], 'config')
        else:
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
        return HttpResponse(json.dumps({"response": False}), content_type="application/json")

    for k in filename_list:
        filename = k.name
        if not filename.endswith(ext):
            continue
        final_res_file = os.path.join(final_res_folder, filename)
        final_file = open(final_res_file, 'wb')
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
        
        check_resp = wf_file_manager.CheckConditions.check_uploaded_model(file_path=final_res_file, folder_path=final_res_folder)
        if check_resp["response"] == "KO":
            shutil.rmtree(final_res_folder)
            os.mkdir(final_res_folder)
            return HttpResponse(json.dumps(check_resp), content_type="application/json")

        request.session[exc]['source_opt_id'] = ""
        request.session.save()

    elif filetype == "modsim":
        user_dir_sim_run = request.session[exc]['user_dir_sim_run']

        # unzip uploaded model file
        z = zipfile.ZipFile(final_res_file, 'r')
        try:
            z.extractall(path=user_dir_sim_run)
        except Exception as e:
            msg = "Unable to unzip the uploaded file. Check file integrity"
            for k in filename_list:
                os.remove(os.path.join(final_res_folder, k.name))
            return HttpResponse(json.dumps({"response": "KO", "message": msg}), content_type="application/json")
        request.session['fetch_opt_uuid'] = ""

    request.session.save()
    return HttpResponse(json.dumps({"response": "OK", "message": ""}), content_type="application/json")


def get_job_list2(request, hpc, exc='', ctx=''):
    print('get_job_list2() called.')
    request.session[exc]['hpc_sys_fetch'] = hpc;
    print(request.session[exc]['hpc_sys_fetch'])

    if hpc == "NSG":
        username_fetch = request.session[exc]['username_fetch']
        password_fetch = request.session[exc]['password_fetch']

        resp = hpc_job_manager.Nsg.fetch_job_list(username_fetch=username_fetch, password_fetch=password_fetch)
        print(resp)

    elif hpc == 'DAINT-CSCS' or hpc == 'SA-CSCS':
        access_token = 'Bearer ' + request.session['oidc_access_token']
        resp = hpc_job_manager.Unicore.fetch_job_list2(hpc, access_token)

    print(resp)
    request.session[exc]['hpc_fetch_job_list'] = resp
    request.session.save()

    return JsonResponse(data=json.dumps(resp), status=200, safe=False)


def get_job_list(request, exc="", ctx=""):
    """
    """
    print("get_job_list() called.")
    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch']

    # read job id file
    opt_res_dir = request.session[exc]['user_dir_results_opt']
    workflows_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    wf_job_ids = request.session[exc]['wf_job_ids']
    wf_id = request.session[exc]['wf_id']
    ids_file = os.path.join(workflows_dir, username, wf_job_ids)
    if os.path.exists(ids_file):
        with open(ids_file, "r") as fh:
            all_id = json.load(fh)
    else:
        all_id = {}

    if hpc_sys_fetch == "NSG":
        username_fetch = request.session[exc]['username_fetch']
        password_fetch = request.session[exc]['password_fetch']

        resp = hpc_job_manager.Nsg.fetch_job_list(username_fetch=username_fetch, password_fetch=password_fetch)

    if hpc_sys_fetch == "DAINT-CSCS" or hpc_sys_fetch == "SA-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}

        # TODO: update with new API [RESOLVED]
        # access_token = get_access_token(request.user.social_auth.get())
        access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

        resp = hpc_job_manager.Unicore.fetch_job_list(hpc_sys_fetch, access_token)  # , proxies=PROXIES)

    # fetch workflow ids for all fetched jobs and add to response
    # for key in resp:
    #     if key in all_id:
    #         resp[key]["wf"] = all_id[key]
    #     else:
    #         resp[key]["wf"] = {"wf_id": "No workflow id associated", "hpc_sys": hpc_sys_fetch}

    request.session[exc]['hpc_fetch_job_list'] = resp
    
    request.session.save()

    return HttpResponse(json.dumps(resp), content_type="application/json")


def get_job_details2(request, jobid='', exc='', ctx=''):
    jobid = str(jobid)
    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch']

    try:
        # if job has to be fetched from NSG
        if hpc_sys_fetch == 'NSG':
            username_fetch = request.session[exc]['username_fetch']
            password_fetch = request.session[exc]['password_fetch']

            resp = hpc_job_manager.Nsg.fetch_job_details(job_id=jobid, username_fetch=username_fetch, password_fetch=password_fetch)

        elif hpc_sys_fetch == 'DAINT-CSCS' or hpc_sys_fetch == 'SA-CSCS':
            fetch_job_list = request.session[exc]["hpc_fetch_job_list"]
            job_url = fetch_job_list[jobid]["url"]
            access_token = request.session.get('oidc_access_token')
            resp = hpc_job_manager.Unicore.fetch_job_details(hpc=hpc_sys_fetch, job_url=job_url, job_id=jobid, token="Bearer " + access_token)

    except RuntimeError:
        return JsonResponse(data=json.dumps({'resp': 'KO', 'message': 'RuntimeError on get_job_details2()'}), status=200, safe=False)
        
    return JsonResponse(data=json.dumps(resp), status=200, safe=False)


def get_job_details(request, jobid="", exc="", ctx=""):
    """
    """
    jobid = str(jobid)

    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch']

    # if job has to be fetched from NSG
    if hpc_sys_fetch == "NSG":
        username_fetch = request.session[exc]['username_fetch']
        password_fetch = request.session[exc]['password_fetch']

        resp = hpc_job_manager.Nsg.fetch_job_details(job_id=jobid, username_fetch=username_fetch, password_fetch=password_fetch)

        # if job has to be fetched from DAINT-CSCS
    elif hpc_sys_fetch == "DAINT-CSCS" or hpc_sys_fetch == "SA-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}
        fetch_job_list = request.session[exc]["hpc_fetch_job_list"]
        job_url = fetch_job_list[jobid]["url"]
        # access_token = get_access_token(request.user.social_auth.get())
        access_token = request.session.get('oidc_access_token')
        resp = hpc_job_manager.Unicore.fetch_job_details(hpc=hpc_sys_fetch, job_url=job_url, job_id=jobid,
                                                         token="Bearer " + access_token)  # , proxies=PROXIES)
        print(json.dumps(resp, indent=4))
        request.session.save()

    return HttpResponse(json.dumps(resp), content_type="application/json")


def download_job(request, job_id="", exc="", ctx=""):
    """
    """
    job_id = str(job_id)

    opt_res_dir = request.session[exc]['user_dir_results_opt']
    wf_id = request.session[exc]['wf_id']
    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch']
    fetch_job_list = request.session[exc]["hpc_fetch_job_list"]

    #
    if not os.path.exists(opt_res_dir):
        return HttpResponse(json.dumps({"response": "KO", "message": "The workflow session has expired." +
                                        "<br> Please start a new workflow or fetch a previous one."}),
                            content_type="application/json")
        # remove folder with current zip file
    if os.listdir(opt_res_dir):
        shutil.rmtree(opt_res_dir)
        os.makedirs(opt_res_dir)
    if hpc_sys_fetch == "NSG":
        username_fetch = request.session[exc]['username_fetch']
        password_fetch = request.session[exc]['password_fetch']

        resp_job_details = hpc_job_manager.Nsg.fetch_job_details(job_id=job_id, username_fetch=username_fetch,
                                                                 password_fetch=password_fetch)
        job_res_url = resp_job_details['job_res_url']

        resp = hpc_job_manager.Nsg.fetch_job_results(job_res_url, username_fetch=username_fetch,
                                                     password_fetch=password_fetch, opt_res_dir=opt_res_dir, wf_id=wf_id)

    elif hpc_sys_fetch == "DAINT-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}
        job_url = fetch_job_list[job_id]["url"]

        # retrieve access_token
        # TODO: update with new API [RESOLVED]
        # access_token = get_access_token(request.user.social_auth.get())
        access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

        resp = hpc_job_manager.Unicore.fetch_job_results(hpc=hpc_sys_fetch, job_url=job_url, dest_dir=opt_res_dir, token=access_token)  # , proxies=PROXIES, wf_id=wf_id)

    elif hpc_sys_fetch == "SA-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}
        job_url = fetch_job_list[job_id]["url"]

        # TODO: update with new API [RESOLVED]
        # access_token = get_access_token(request.user.social_auth.get())
        access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

        resp = hpc_job_manager.Unicore.fetch_job_results(hpc=hpc_sys_fetch, job_url=str(job_url), dest_dir=opt_res_dir, token=access_token)  # , proxies=PROXIES, wf_id=wf_id)

    print(resp)
    return HttpResponse(json.dumps(resp), content_type="application/json")


def run_analysis(request, exc="", ctx=""):
    print('run_analysis() called.')

    msg = ""
    opt_res_folder = request.session[exc]['user_dir_results_opt']

    hpc_sys_fetch = request.session[exc]['hpc_sys_fetch']

    print(hpc_sys_fetch, opt_res_folder, sep='\n')

    # set output file name
    if hpc_sys_fetch == "NSG":
        opt_res_file = "output.tar.gz"
    elif hpc_sys_fetch == "DAINT-CSCS" or hpc_sys_fetch == "SA-CSCS":
        opt_res_file = "output.zip"

    output_fetched_file = os.path.join(opt_res_folder, opt_res_file)
    print(output_fetched_file)

    if not os.path.exists(output_fetched_file):
        msg = "No output file was generated in the optimization process. Check your optimization settings."
        return HttpResponse(json.dumps({"response": "KO", "message": msg}), content_type="application/json")

    if hpc_sys_fetch == "NSG":
        tar = tarfile.open(os.path.join(opt_res_folder, "output.tar.gz"))
        tar.extractall(path=opt_res_folder)
        tar.close()

        analysis_file_list = []
        for (dirpath, dirnames, filenames) in os.walk(opt_res_folder):
            for filename in filenames:
                if filename == "analysis.py":
                    analysis_file_list.append(os.path.join(dirpath, filename))

        if len(analysis_file_list) != 1:
            msg = "No (or multiple) analysis.py file(s) found. Check the .zip file submitted for the optimization."
            resp = {"Status": "ERROR", "response": "KO", "message": msg}
            return HttpResponse(json.dumps(resp), content_type="application/json")
        else:
            full_file_path = analysis_file_list[0]
            file_path = os.path.split(full_file_path)[0]
            up_folder = os.path.split(file_path)[0]

            # modify analysis.py file
            #f = open(full_file_path, 'r')

            #lines = f.readlines()
            #lines[228] = '    traces=[]\n'
            #lines[238] = '        traces.append(response.keys()[0])\n'
            #lines[242] = '\n    stimord={} \n    for i in range(len(traces)): \n        stimord[i]=float(traces[i][traces[i].find(\'_\')+1:traces[i].find(\'.soma\')]) \n    import operator \n    sorted_stimord = sorted(stimord.items(), key=operator.itemgetter(1)) \n    traces2=[] \n    for i in range(len(sorted_stimord)): \n        traces2.append(traces[sorted_stimord[i][0]]) \n    traces=traces2 \n'
            #lines[243] = '    plot_multiple_responses([responses], cp_filename, fig=model_fig, traces=traces)\n'
            #lines[366] = "def plot_multiple_responses(responses, cp_filename, fig, traces):\n"
            #lines[369] = "\n"
            #lines[370] = "\n"
            #lines[371] = "\n"  # n is the line number you want to edit; subtract 1 as indexing of list starts from 0
            #f.close()
            
            #f = open(full_file_path, 'w')
            #f.writelines(lines)
            #f.close()

            # modify evaluator.py if present
            if not os.path.exists(os.path.join(file_path, 'evaluator.py')):
                msg = "No evaluator.py file found. Check the .zip file submitted for the optimization."
                resp = {"Status": "ERROR", "response": "KO", "message": msg}
                return HttpResponse(json.dumps(resp), content_type="application/json")
            else:
                f = open(os.path.join(file_path, 'evaluator.py'), 'r')  # pass an appropriate path of the required file
                lines = f.readlines()
                lines[167] = '    #print param_names\n'
                f.close()
                f = open(os.path.join(file_path, 'evaluator.py'), 'w')  # pass an appropriate path of the required file
                f.writelines(lines)
                f.close()

            if up_folder not in sys.path:
                sys.path.append(up_folder)

            # import model
            fig_folder = os.path.join(up_folder, 'figures')

            if os.path.exists(fig_folder):
                shutil.rmtree(fig_folder)
            os.makedirs(fig_folder)

            checkpoints_folder = os.path.join(up_folder, 'checkpoints')

            try:
                if 'checkpoint.pkl' not in os.listdir(checkpoints_folder):
                    for files in os.listdir(checkpoints_folder):
                        if files.endswith('pkl'):
                            shutil.copy(os.path.join(checkpoints_folder, files), os.path.join(checkpoints_folder, 'checkpoint.pkl'))
                            os.remove(os.path.join(up_folder, 'checkpoints', files))

                f = open(os.path.join(up_folder, 'opt_neuron.py'), 'r')
                lines = f.readlines()

                # TODO: optimization
                new_line = ["import matplotlib \n"]
                new_line.append("matplotlib.use('Agg') \n")
                for i in lines:
                    new_line.append(i)
                f.close()
                f = open(os.path.join(up_folder, 'opt_neuron.py'), 'w')
                f.writelines(new_line)
                f.close()

                subprocess.call('. /usr/local/hhnb-dev/venv3/bin/activate; cd ' + up_folder + '; /usr/local/hhnb-dev/venv3/bin/nrnivmodl mechanisms', shell=True)

                r_0_fold = os.path.join(up_folder, 'r_0')
                if os.path.isdir(r_0_fold):
                    shutil.rmtree(r_0_fold)
                os.mkdir(r_0_fold)

                subprocess.call('. /usr/local/hhnb-dev/venv3/bin/activate; cd ' + up_folder + '; python opt_neuron.py --analyse --checkpoint ./checkpoints', shell=True)

            except Exception as e:
                msg = traceback.format_exception(*sys.exc_info())
                return HttpResponse(json.dumps({"response": "KO", "message": msg}), content_type="application/json")

    elif hpc_sys_fetch == "DAINT-CSCS" or hpc_sys_fetch == "SA-CSCS":
        #PROXIES = settings.PROXIES
        PROXIES = {}
        try:
            resp = hpc_job_manager.OptResultManager.create_analysis_files(opt_res_folder, opt_res_file)
            up_folder = resp["up_folder"]
            print(up_folder)
            tempresp = subprocess.call('. /usr/local/hhnb-dev/venv3/bin/activate; cd ' + up_folder + '; nrnivmodl mechanisms; python opt_neuron.py --analyse --checkpoint ./checkpoints > /dev/null 2>&1', shell=True)
            print(tempresp)
        except Exception as e:
            msg = traceback.format_exception(*sys.exc_info())
            resp = {"response": "KO", "msg": "An error occurred while analysis results. Check your files."}
            return HttpResponse(json.dumps(resp), content_type="application/json")

    resp = {"response": "OK", "message": msg}
    request.session["opt_res_mod_folder"] = up_folder
    request.session.save()

    return HttpResponse(json.dumps(resp), content_type="application/json")


def zip_sim(request, job_id="", exc="", ctx=""):
    user_dir_res_opt = request.session[exc]['user_dir_results_opt']
    user_dir_sim_run = request.session[exc]['user_dir_sim_run']
    opt_res_mod_folder = request.session.get("opt_res_mod_folder", "")

    resp_opt_res = \
        wf_file_manager.CheckConditions.check_sim_folders(folder_path=opt_res_mod_folder)
    if resp_opt_res["response"] == "KO":
        return HttpResponse(json.dumps({"response": "KO", "message": resp_opt_res["message"]}), content_type="application/json")

    opt_logs_folder = 'opt_logs'

    # create simulation folder
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

    if len(mec_folder_path) != 1 or len(config_folder_path) != 1:
        return HttpResponse(json.dumps({"response": "KO",
                                        "message": "Optimization result folder is not consistent. Check your data."}),
                            content_type="application/json")

    if os.path.split(mec_folder_path[0])[0] != os.path.split(config_folder_path[0])[0]:
        return HttpResponse(json.dumps({"response": "KO",
                                        "message": "Optimization result folder is not consistent. Check your data."}),
                            content_type="application/json")

    else:
        crr_opt_folder = opt_res_mod_folder
        checkpoint_folder = os.path.join(crr_opt_folder, "checkpoints")
        crr_opt_name = os.path.split(crr_opt_folder)[1]
        sim_mod_folder = os.path.join(user_dir_sim_run, crr_opt_name)
        os.makedirs(sim_mod_folder)
        user_opt_logs = os.path.join(user_dir_sim_run, crr_opt_name, opt_logs_folder)
        os.makedirs(user_opt_logs)

        log_files = ["STDERR", "stderr.txt", "STDOUT", "stdout.txt", "_JOBINFO.TXT", "nsgdebug",
                     "scheduler.conf", "scheduler_stderr.txt", "scheduler_stdout.txt", "epilog"]
        for root, dirs, files in os.walk(user_dir_res_opt):
            if root.endswith("mechanisms") or root.endswith("morphology") or root.endswith("checkpoints"):
                crr_folder = os.path.split(root)[1]
                dst = os.path.join(sim_mod_folder, crr_folder)
                shutil.copytree(root, dst, symlinks=True)

            for crr_f in log_files:
                if crr_f in files:
                    shutil.copyfile(os.path.join(root, crr_f), os.path.join(user_opt_logs, crr_f))

    for filename in os.listdir(os.path.join(sim_mod_folder, 'checkpoints')):
        if filename.endswith(".hoc"):
        # if filename.endswith('.pkl'):
            os.rename(os.path.join(sim_mod_folder, "checkpoints", filename), os.path.join(sim_mod_folder, "checkpoints", "cell.hoc"))

    current_working_dir = os.getcwd()

    zipname = crr_opt_name + '.zip'

    final_zip_name = os.path.join(user_dir_sim_run, zipname)
    foo = zipfile.ZipFile(final_zip_name, 'w', zipfile.ZIP_DEFLATED)

    crr_dir_opt = os.path.join(user_dir_sim_run, crr_opt_name)
    for root, dirs, files in os.walk(user_dir_sim_run):
        if root == os.path.join(crr_dir_opt, 'morphology') or \
                root == os.path.join(crr_dir_opt, 'checkpoints') or \
                root == os.path.join(crr_dir_opt, 'mechanisms') or \
                root == os.path.join(crr_dir_opt, opt_logs_folder):
            for f in files:
                final_zip_fname = os.path.join(root, f)
                foo.write(final_zip_fname,
                        final_zip_fname.replace(user_dir_sim_run, '', 1))

    foo.close()

    wf_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    wf_job_ids = request.session[exc]['wf_job_ids']

    # open file containing job info for current user
    job_ids_file = os.path.join(wf_dir, username, wf_job_ids)
    with open(job_ids_file, 'r') as f:
        user_job_ids = json.load(f)
    f.close()
    if job_id in user_job_ids and "source_opt_id" in user_job_ids[job_id]:
        fetch_opt_uuid = user_job_ids[job_id]["source_opt_id"]
    else:
        fetch_opt_uuid = ""

    request.session[exc]['fetch_opt_uuid'] = fetch_opt_uuid
    request.session.save()

    return HttpResponse(json.dumps({"response": "OK"}), content_type="application/json")


def download_zip(request, file_type="", exc="", ctx=""):
    """
    download files to local machine
    """
    
    user_dir = request.session[exc]['user_dir']
    tmp_dir = os.path.join(user_dir, 'tmp')

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)

    if file_type == 'feat':
        if request.session[exc].get('from_hhf', None):
            src_dir = os.path.join(request.session[exc]['hhf_dir'], 'config')
        else:
            src_dir = request.session[exc]['user_dir_data_feat']
        zipname = os.path.join(tmp_dir, 'features.zip')
        z = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        z.write(os.path.join(src_dir, 'features.json'), 'features.json')
        z.write(os.path.join(src_dir, 'protocols.json'), 'protocols.json')
        z.close()
        return FileResponse(open(zipname, 'rb'), as_attachment=True)

    elif file_type == 'optset':
        src_dir = request.session[exc]['user_dir_data_opt_set']
    elif file_type == 'modsim':
        src_dir = request.session[exc]['user_dir_sim_run']
    elif file_type == 'optres':
        src_dir = request.session[exc]['user_dir_results'] 
        
    for f in os.listdir(src_dir):
        if f.endswith('.zip'):
            # shutil.copy2(os.path.join(src_dir, f), os.path.join(tmp_dir, f))
            return FileResponse(open(os.path.join(src_dir, f), 'rb'), as_attachment=True)

    return HttpResponseBadRequest()

    # if file_type == "feat":
    #     if request.session[exc].get('from_hhf', None):
    #         fetch_folder = os.path.join(request.session[exc]['hhf_dir'], 'config')
    #     else:
    #         fetch_folder = request.session[exc]['user_dir_data_feat']
    #     zipname = os.path.join(fetch_folder, "features.zip")
    #     foo = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    #     foo.write(os.path.join(fetch_folder, "features.json"), "features.json")
    #     foo.write(os.path.join(fetch_folder, "protocols.json"), "protocols.json")
    #     foo.close()
    # elif file_type == "optset":
    #     fetch_folder = request.session[exc]['user_dir_data_opt_set']
    # elif file_type == "modsim":
    #     fetch_folder = request.session[exc]['user_dir_sim_run']
    # elif file_type == "optres":
    #     fetch_folder = request.session[exc]['user_dir_results']

    # zip_file_list = []

    # # create a list with all .zip files in folder, but use only the first one
    # for i in os.listdir(fetch_folder):
    #     if i.endswith(".zip"):
    #         zip_file_list.append(i)

    # crr_file = zip_file_list[0]
    # full_file_path = os.path.join(fetch_folder, crr_file)
    # crr_file_full = open(full_file_path, "rb")
    # response = HttpResponse(crr_file_full, content_type="application/zip")

    # request.session.save()

    # response['Content-Disposition'] = 'attachment; filename="%s"' % crr_file

    # return response


@deprecated(reason='method dismissed with Ebrains')
# handle file upload to storage collab
def save_wf_to_storage(request, exc="", ctx=""):
    # retrieve access_token
    # TODO: update with new API [RESOLVED]
    # access_token = get_access_token(request.user.social_auth.get())
    access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']
    user_crr_wf_dir = request.session[exc]['user_dir']
    wf_id = request.session[exc]['wf_id']
    wf_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]

    # TODO: update with new API [RESOLVED]
    # access_token = get_access_token(request.user.social_auth.get())
    access_token = 'Bearer ' + request.session['oidc_access_token']  # get access token with new method

    # TODO: update with new API
    sc = service_client.Client.new(access_token)
    ac = service_api_client.ApiClient.new(access_token)

    # retrieve collab related projects
    project_dict = ac.list_projects(None, None, None, collab_id)
    project = project_dict['results']
    storage_root = ac.get_entity_path(project[0]['uuid'])

    # create zip file with the entire workflow
    user_wf_path = os.path.join(wf_dir, username)
    zipname = wf_id + '.zip'
    zipname_full = os.path.join(user_wf_path, zipname)
    if os.path.exists(zipname_full):
        os.remove(zipname_full)

    foo = zipfile.ZipFile(zipname_full, 'w', zipfile.ZIP_DEFLATED)

    # for root, dirs, files in os.walk(os.path.join('.', wf_id)):
    for root, dirs, files in os.walk(os.path.join(user_wf_path, wf_id)):
        for d in dirs:
            if not os.listdir(os.path.join(root, d)):
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

    sc.upload_file(zipname_full, str(crr_zip_storage_path), "application/zip")
    return HttpResponse(json.dumps({"response": "OK", "message": ""}), content_type="application/json")


@deprecated(reason='method dismissed with Ebrains')
def wf_storage_list(request, exc="", ctx=""):
    # TODO: update with new API [RESOLVED]
    # retrieve access_token
    # access_token = get_access_token(request.user.social_auth.get())
    access_token = request.session['oidc_access_token']

    # retrieve data from request.session
    collab_id = request.session[exc]['collab_id']

    hhnb_storage_folder = request.session[exc]['hhnb_storage_folder']
    username = request.session[exc]["username"]

    context = request.session[exc]['ctx']

    # TODO: update with new API [RESOLVED]
    # access_token = get_access_token(request.user.social_auth.get())
    access_token = request.session['oidc_access_token']

    # TODO: update with new API
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

    return HttpResponse(json.dumps({"list": storage_list}), content_type="application/json")


@deprecated(reason='method dismissed with Ebrains')
def get_user_clb_permissions(request, exc="", ctx=""):
    return JsonResponse(data={'response': 'OK'})

    collab_url = "https://services.humanbrainproject.eu/collab/v0/collab/context/" + ctx + "/permissions/"

    # get user header token

    # TODO: update with new API
    headers = {'Authorization': "TOKEN"}  # get_auth_header(request.user.social_auth.get())}

    resp = requests.get(collab_url, headers=headers)
    if resp.json()["UPDATE"]:
        response = "OK"
    else:
        response = "KO"

    return HttpResponse(json.dumps({"response": response}), content_type="application/json")


def get_data_model_catalog(request, exc="", ctx=""):
    mc_clb_user = request.session[exc]["mod_clb_user"]

    # refresh collab user token from permanent refresh token
    # storage_user_token = resources.get_token_from_refresh_token(mc_clb_user)
    storage_user_token = request.session['oidc_access_token']

    fetch_opt_uuid = request.session[exc].pop('fetch_opt_uuid', None)

    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    username = request.session[exc]['username']

    model_name = "hhnb_" + time_info + "_" + username

    # headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    headers = {'Authorization': "Bearer " + storage_user_token}
    vf_url = "https://validation-v1.brainsimulation.eu/authorizedcollabparameterrest/?format=json&python_client=true"
    res = requests.get(vf_url, verify=False)
    default_values = res.json()
    data = {"default_values": default_values}
    print('=========== DEFAULT ============', default_values)
    print(fetch_opt_uuid)
    if not fetch_opt_uuid:
        data.update({
            "name": model_name,
            "response": "KO",
            "base_model": ""
        })

        return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        # retrieve access_token
        # access_token = get_access_token(request.user.social_auth.get())
        mc = ModelCatalog(token=storage_user_token)

        # retrieve UUID of chosen optimized model
        try:
            base_model_data = mc.get_model(model_id=fetch_opt_uuid)
            data.update({
                "fetched_values": base_model_data,
                "response": "OK",
                "base_model": base_model_data["name"]
            })
        except:
            data.update({
                "response": "KO",
                "base_model": ""
            })

        data["name"] = model_name
        return HttpResponse(json.dumps(data), content_type="application/json")


def register_model_catalog(request, reg_collab="", exc="", ctx=""):
    # get data from form
    form_data = request.POST

    if form_data["modelSuffix"] and form_data["modelSuffix"][0] != '-' and form_data["modelSuffix"][0] != '_':
        mod_name = form_data["modelName"] + '_' + form_data["modelSuffix"]
    else:
        mod_name = form_data["modelName"] + form_data["modelSuffix"]

    # retrieve model full path
    sim_dir = request.session[exc]['user_dir_sim_run']

    full_file_path = ""
    for i in os.listdir(sim_dir):
        if i.endswith(".zip"):
            full_file_path = os.path.join(sim_dir, i)
            break

    if full_file_path == "":
        return HttpResponse(json.dumps({"response": "KO", "message": "No sim model is present"}), content_type="application/json")

    mc_dir = sim_dir + "_mc"
    dest_file = os.path.join(mc_dir, i)
    if os.path.exists(sim_dir + "_mc"):
        shutil.rmtree(mc_dir, ignore_errors=True)
    os.makedirs(mc_dir)

    shutil.copyfile(full_file_path, dest_file)

    # unzip model file in mc folder
    final_wf_dir = os.path.splitext(dest_file)[0]
    mc_mod_name = os.path.splitext(i)[0]
    zip_ref = zipfile.ZipFile(dest_file, 'r')
    if os.path.exists(final_wf_dir):
        shutil.rmtree(final_wf_dir)
    zip_ref.extractall(mc_dir)
    zip_ref.close()

    # remove zip file
    os.remove(dest_file)

    # rename destination folder
    final_folder = os.path.join(mc_dir, mod_name)
    orig_folder = os.path.join(mc_dir, mc_mod_name)
    os.rename(orig_folder, final_folder)

    # zip final folder with mc name
    mc_zip_name_full = final_folder + '.zip'
    mc_zip_name = mod_name + ".zip"
    foo = zipfile.ZipFile(mc_zip_name_full, 'w', zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(final_folder):
        for d in dirs:
            if not os.listdir(os.path.join(root, d)):
                crr_zip_filename = os.path.join(root, d)
                crr_arcname = crr_zip_filename.replace(mc_dir, '', 1)
                foo.write(os.path.join(root, d), crr_arcname)
        for f in files:
            crr_zip_ffilename = os.path.join(root, f)
            crr_farcname = crr_zip_ffilename.replace(mc_dir, '', 1)
            foo.write(os.path.join(root, f), crr_farcname)
    foo.close()

    # retrieve info
    mc_clb_id = request.session[exc]["mod_clb_id"]
    mc_clb_user = request.session[exc]["mod_clb_user"]
    mc_clb_url = request.session[exc]['mod_clb_url']

    clb_user_token = request.session['oidc_access_token']

    # create model catalog instance and add to Collab if not present
    mc = ModelCatalog(token=clb_user_token)
    print('============== TOKEN =================')
    print(mc.auth.token)
    print(mc.token)
    client = ebrains_drive.connect(token=mc.auth.token)
    repo = client.repos.get_repo_by_url("https://wiki.ebrains.eu/bin/view/Collabs/hhnb-registeredmodels/")
    seafdir = repo.get_dir('/hhnb_wf_model')
    mc_zip_uploaded = seafdir.upload_local_file(mc_zip_name_full)

    reg_mod_url = 'https://drive.ebrains.eu/lib/' + repo.id + '/file/hhnb_wf_model/' + mc_zip_name + '?dl=1'
    print(reg_mod_url)
    print('============== FORM DATA ==================', form_data)
    auth_family_name = form_data["authorLastName"]
    auth_given_name = form_data["authorFirstName"]
    organization = form_data["modelOrganization"]
    cell_type = form_data["modelCellType"]
    model_scope = form_data["modelScope"]
    abstraction_level = form_data["modelAbstraction"]
    brain_region = form_data["modelBrainRegion"]
    species = form_data["modelSpecies"]
    own_family_name = form_data["ownerLastName"]
    own_given_name = form_data["ownerFirstName"]
    license = form_data["modelLicense"]
    description = form_data["modelDescription"]
    private = form_data["modelPrivate"]
    if private == "true":
        private_flag = True
    else:
        private_flag = False

    model = mc.register_model(collab_id="hhnb-registeredmodels",
                              name=mod_name,
                              author={"family_name": auth_family_name, "given_name": auth_given_name},
                              organization=organization,
                              private=private_flag,
                              species=species,
                              brain_region=brain_region,
                              cell_type=cell_type,
                              model_scope=model_scope,
                              abstraction_level=abstraction_level,
                              owner={"family_name": own_family_name, "given_name": own_given_name},
                              description=description,
                              instances=[{
                                  "version": "1.0",
                                  "source": reg_mod_url,
                                  "license": license,
                              }])
    model_path_on_catalog = "https://model-catalog.brainsimulation.eu/#model_id.{}".format(model["id"])
    print('==================URL=================', model_path_on_catalog)
    edit_message = "\
            The model was successfully registered in the Model Catalog.<br>\
            Model's info and metadata can be shown \
            <a href='" + model_path_on_catalog + "' target='_blank'>here</a>.<br><br>\
            Once the page will be opened in a new tab, if a welcome message is displayed \
            instead of the model instance, please click on the Model Catalog \
            item in the left menu in order to reload the page; click on the 'Authorize' button if requested.<br><br>\
            Leave the current tab open in case you need to recollect the model url."

    return HttpResponse(json.dumps({"response": "OK", "message": edit_message, "reg_mod_url": model_path_on_catalog}),
                        content_type="application/json")


# tmp dir workflow
def workflow_upload(request, exc='', ctx=''):
    print('upload_workflow endpoint.')
    if request.method == 'POST':
        wf = request.body
        filename = request.META['HTTP_CONTENT_DISPOSITION'].split('filename="')[1].split('"')[0]

        workflows_dir = request.session[exc]['workflows_dir']

        if not request.user.is_authenticated:
            username = 'anonymouse'
        else:
            username = request.user.username
        if not os.path.exists(os.path.join(workflows_dir, username)):
            os.mkdir(os.path.join(workflows_dir, username))

        crr_wf_folder = os.path.join(workflows_dir, username, filename.split('_')[0] + '_' + username)
        if os.path.exists(crr_wf_folder):
            shutil.rmtree(crr_wf_folder)
        os.mkdir(crr_wf_folder)
        
        # overwrite wf_id
        request.session[exc]['wf_id'] = crr_wf_folder.split('/')[-1]
        
        with open(os.path.join(crr_wf_folder, filename), 'wb') as fd:
            fd.write(wf)
        with open(os.path.join(crr_wf_folder, filename), 'rb') as fd:
            zip_file = zipfile.ZipFile(fd)
            zip_file.extractall(path=crr_wf_folder)
        os.remove(os.path.join(crr_wf_folder, filename))

        crr_session_dict = request.session[exc]

        try:
            with open(os.path.join(crr_wf_folder, 'wf_session_dict.json'), 'r') as fd:
                uploaded_session_dict = json.load(fd)
        except FileNotFoundError:
            resp = {'response': 'KO', 'message': 'Uploaded old workflow'}
            return HttpResponse(content=json.dumps(resp), content_type='application/json', status=200)

        old_user_dir = uploaded_session_dict['user_dir']

        for k in uploaded_session_dict.keys():
            if k not in crr_session_dict:    
                if k == 'analysis_id':
                    if k not in crr_session_dict:
                        crr_session_dict.update({k: []})
                    for a in uploaded_session_dict[k]:
                        if type(a) == str:
                            a = a.replace(old_user_dir, crr_wf_folder)
                        crr_session_dict[k].append(a)
                else:
                    if type(uploaded_session_dict[k]) == str:
                        v = uploaded_session_dict[k].replace(old_user_dir, crr_wf_folder)
                    else:
                        v = uploaded_session_dict[k]
                    crr_session_dict.update({k: v})
        
        os.remove(os.path.join(crr_wf_folder, 'wf_session_dict.json'))

        r = check_cond_exist(request, exc, str(crr_session_dict['ctx']))
        rj = json.loads(r.content)

        try:
            if rj['response'] == 'KO':
                resp = {'response': 'KO', 'message': 'Uploaded broken workflow'}
        except KeyError:
            if rj['expiration']:
                resp = {'response': 'KO', 'message': 'Uploaded broken or empty workflow'}
            else:
                resp = {'response': 'OK'}

        request.session.save()
        if resp['response'] == 'KO':
            return HttpResponse(content=json.dumps(resp), content_type='application/json', status=200)
        return HttpResponse(content=json.dumps(resp), content_type='application/json', status=200)

    return HttpResponse(content=json.dumps({'response': 'KO', 'message': 'Error'}), content_type='application/json', status=200)


def workflow_download(request, exc='', ctx=''):
    print('================ SESSION ==================')
    print(json.dumps(request.session[exc]))

    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    # retrieve data from request.session
    wf_id = request.session[exc]['wf_id']
    user_dir = request.session[exc]['user_dir']

    wf_session_dict = request.session.get(exc, 'None')
    print(wf_session_dict)
    if wf_session_dict:
        with open(os.path.join(user_dir, 'wf_session_dict.json'), 'w') as fd:
            json.dump(wf_session_dict, fd, indent=4)

    tmp_wf_dir = os.path.join(tmp_dir, wf_id)
    if os.path.exists(tmp_wf_dir):
        shutil.rmtree(tmp_wf_dir)
    os.mkdir(tmp_wf_dir)    

    shutil.make_archive(tmp_wf_dir , 'zip', user_dir)

    return FileResponse(open(os.path.join(tmp_dir, wf_id + '.zip'), 'rb'), as_attachment=True)


def simulation_result_download(request, exc='', ctx=''):
    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    # retrieve the file from the current working directory
    wf_dir = request.session[exc]['workflows_dir']
    user_id = request.user.username
    wf_id = request.session[exc]['wf_id']
    result_dir = os.path.abspath(os.path.join(wf_dir, user_id, wf_id, 'sim'))

    for f in os.listdir(result_dir):
        if f.endswith('.zip'):
            print(os.path.join(result_dir, f))
            return FileResponse(open(os.path.join(result_dir, f), 'rb'), as_attachment=True)

    return HttpResponse(content=b'File not found', status=404)


def get_user_avatar(request):
    r = requests.get('https://wiki.ebrains.eu/bin/download/XWiki/' + request.user.username + '/avatar.png?width=36&height=36&keepAspectRatio=true', verify=False)
    return HttpResponse(content_type='image/png;', charset='UTF-8', content=r.content)


def get_user_page(request):
    return redirect('https://wiki.ebrains.eu/bin/view/Identity/#/users/' + request.user.username)


def clone_workflow(request, exc='', ctx=''):

    if exc not in request.session.keys() or "workflows_dir" not in request.session[exc]:
        response = {"response": "KO", "message": "An error occurred while loading the application.<br><br>Please reload."}
        return HttpResponse(json.dumps(response), content_type="application/json")

    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    workflows_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    new_wf_id = time_info + '_' + username

    crr_user_dir = request.session[exc]['user_dir']
    new_user_dir = os.path.join(workflows_dir, username, new_wf_id)

    # copy current user dir to the newly created workflow's dir
    shutil.copytree(os.path.join(crr_user_dir, 'data'), os.path.join(new_user_dir, 'data'), symlinks=True)

    # cloning request.session[exc] in request.session[new_exc]
    new_exc = "tab_" + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    new_ctx = str(uuid.uuid4())

    request.session[new_exc] = request.session[exc].copy()
    request.session[new_exc].update({
        'ctx': new_ctx,
        'time_info': time_info,
        'wf_id': new_wf_id,
        'user_dir': new_user_dir,
        'user_dir_data': os.path.join(new_user_dir, 'data'),
        'user_dir_data_feat': os.path.join(new_user_dir, 'data', 'features'),
        'user_dir_data_opt_set': os.path.join(new_user_dir, 'data', 'opt_settings'),
        'user_dir_data_opt_launch': os.path.join(new_user_dir, 'data', 'opt_launch'),
        "analysis_id": []
    })

    # remove old optimization launch folder and create a new one
    shutil.rmtree(request.session[exc]['user_dir_data_opt_launch'])
    os.makedirs(request.session[exc]['user_dir_data_opt_launch'])

    opt_pf = os.path.join(crr_user_dir, 'data', 'opt_launch', request.session[exc]['opt_sub_param_file'])
    if os.path.exists(opt_pf):
        shutil.copy(opt_pf, request.session[exc]['user_dir_data_opt_launch'])

    # copy current user dir results folder to the newly created workflow
    shutil.copytree(os.path.join(crr_user_dir, 'results'), os.path.join(new_user_dir, 'results'), symlinks=True)

    request.session[new_exc]['user_dir_results'] = os.path.join(new_user_dir, 'results')
    request.session[new_exc]['user_dir_results_opt'] = os.path.join(new_user_dir, 'results', 'opt')

    # copy current user dir results folder to the newly created workflow
    shutil.copytree(os.path.join(crr_user_dir, 'sim'), os.path.join(new_user_dir, 'sim'), symlinks=True)

    request.session[new_exc]['user_dir_sim_run'] = os.path.join(workflows_dir, username, new_wf_id, 'sim')

    request.session[new_exc]['opt_sub_flag'] = False

    sim_flag_file = os.path.join(request.session[exc]['user_dir_sim_run'], request.session[exc]['sim_run_flag_file'])
    if os.path.exists(sim_flag_file):
        os.remove(sim_flag_file)

    request.session.save()
    return JsonResponse(data={'exc': new_exc, 'ctx': new_ctx}, status=200)


def open_cloned_workflow(request, exc='', ctx=''):
    context = {"exc": exc, "ctx": str(ctx)}
    return render(request, 'hhnb/home.html', context)


# @login_required()
def get_authentication(request):
    print('get_authentication() called.')
    if request.user.is_authenticated:
        return HttpResponse(status=200)
    return HttpResponse(status=401)


@csrf_exempt
def check_nsg_login(request, exc='', ctx=''):
    data = request.POST
    print(json.dumps(data, indent=4))
    
    print((data['username']).encode('utf-16'))
    print((data['password']).encode('utf-16'))

    request.session[exc]['username_fetch'] = data['username']
    request.session[exc]['password_fetch'] = data['password']
    request.session.save()

    resp = hpc_job_manager.Nsg.check_nsg_login(username=data['username'], password=data['password'])

    if resp['response'] == 'OK':
        return JsonResponse(status=200, data=json.dumps(resp), safe=False)
    return JsonResponse(status=403, data=json.dumps(resp), safe=False)


def store_workflow_in_session(request, exc='', ctx=''):
    print('STORE WORKFLOW')
    
    old_wf = request.session.get('old_wf', None)
    old_exc = request.session.get('old_exc', None)
    old_ctx = request.session.get('old_ctx', None)

    wf_dir = request.session[exc]['workflows_dir']
    username = request.session[exc]['username']
    wf_id = request.session[exc]['wf_id']

    request.session['old_wf'] = os.path.join(wf_dir, username, wf_id)
    request.session['old_exc'] = exc
    request.session['old_ctx'] = str(ctx)
    
    request.session.save()

    return HttpResponse(status=200)


def hhf_comm(request, exc='', ctx=''):
    print('hhf-comm called()')
         
    hhf_dict = json.loads(request.GET.get('hhf_dict', None))
    print(json.dumps(hhf_dict, indent=4))

    if hhf_dict:

        # create exc and ctx tag
        exc = 'tab_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        ctx = uuid.uuid4()
         
        r0 = set_exc_tags(request, exc, ctx)
        r1 = initialize(request, exc, ctx)
        r2 = create_wf_folders(request, wf_type='new', exc=exc, ctx=ctx) 

        hhf_dir = os.path.join(request.session[exc]['user_dir'], 'hhf')
        hhf_model_key = 'K_' + request.session[exc]['wf_id']

        if os.path.exists(hhf_dir):
            shutil.rmtree(hhf_dir)
        os.mkdir(hhf_dir)

        # load template
        if os.path.exists(os.path.join(request.session[exc]['user_dir'], 'hhf')):
            shutil.rmtree(os.path.join(request.session[exc]['user_dir'], 'hhf'))
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, 'hhnb', 'hhf_template', 'hhf'), os.path.join(request.session[exc]['user_dir'], 'hhf'))
        

        morp = hhf_dict['HHF-Comm'].get('morphology', None)
        mod = hhf_dict['HHF-Comm'].get('modFiles', None)
        etraces = hhf_dict['HHF-Comm'].get('electrophysiologies', None)


        if morp:
            morp_dir = os.path.join(hhf_dir, 'morphology')
            if not os.path.exists(morp_dir):
                os.mkdir(morp_dir)
            
            # downloading morphology 
            r = requests.get(morp['url'], verify=False)
            with open(os.path.join(morp_dir, morp['name']), 'wb') as fd:
                for chunk in r.iter_content():
                    fd.write(chunk)
            
            # writing morph.json
            morp_dict = {hhf_model_key: morp['name']}
            with open(os.path.join(hhf_dir, 'config', 'morph.json'), 'w') as fd:
                json.dump(morp_dict, fd)
        
        if mod:
            mod_dir = os.path.join(hhf_dir, 'mechanisms')
            if not os.path.exists(mod_dir):
                os.mkdir(mod_dir)

            # downloading mods files
            for m in mod:
                r = requests.get(m['url'], verify=False)
                with open(os.path.join(mod_dir, m['name']), 'wb') as fd:
                    for chunk in r.iter_content():
                        fd.write(chunk)

        hhf_etraces = False
        if etraces:
            # add etraces on user_tmp dir
            etraces_dir = os.path.join(request.session[exc]['user_dir'], 'tmp', 'etraces')
            if not os.path.exists(etraces_dir):
                os.makedirs(etraces_dir)

            # downloading etraces files
            for e in etraces:
                r = requests.get(e['url'], verify=False)
                with open(os.path.join(etraces_dir, e['name'] + '.abf'), 'wb') as fd:
                    for chunk in r.iter_content():
                        fd.write(chunk)
                if e.get('metadata', None):
                    r = requests.get(e['metadata'], verify=False)
                    with open(os.path.join(etraces_dir, e['name'] + '_metadata.json'), 'wb') as fd:
                        for chunk in r.iter_content():
                            fd.write(chunk)

            hhf_etraces = True
            request.session[exc]['hhf_etraces_dir'] = etraces_dir

        request.session[exc]['from_hhf'] = True
        request.session[exc]['hhf_dir'] = hhf_dir
        request.session[exc]['hhf_etraces'] = hhf_etraces
        request.session[exc]['hhf_model_key'] = hhf_model_key
        request.session.save()

        # apply model key after 
        hhf_apply_model_key(request, exc, ctx, hhf_model_key)
        
        if etraces and not mod and not morp:
            r = hhf_delete_all(request, exc, ctx)


        return render(request, 'hhnb/workflow.html', context={"exc": exc, "ctx": str(ctx)})

    return home(request)


def hhf_get_files(request, exc, ctx):

    hhf_dir = request.session[exc]['hhf_dir']

    hhf_file_list = {'morphology': [], 'mechanisms': [], 'config': [], 'model': [], 'parameters.json': '', 'opt_neuron.py': ''}
    
    # get morphology
    if os.path.exists(os.path.join(hhf_dir, 'morphology')):
        for m in os.listdir(os.path.join(hhf_dir, 'morphology')):
            hhf_file_list['morphology'].append(m)
    
    # list mechanisms files
    if os.path.exists(os.path.join(hhf_dir, 'mechanisms')):
        for m in os.listdir(os.path.join(hhf_dir, 'mechanisms')):
            hhf_file_list['mechanisms'].append(m)

    # list config files
    if os.path.exists(os.path.join(hhf_dir, 'config')):
        for c in os.listdir(os.path.join(hhf_dir, 'config')):
            hhf_file_list['config'].append(c)
            # if c == 'parameters.json':
                # with open(os.path.join(hhf_dir, 'config', 'parameters.json'), 'r') as fd:
                    # jj = json.load(fd)
                    # hhf_file_list['parameters.json'] = json.dumps(jj, indent='\t')

    # list model files
    if os.path.exists(os.path.join(hhf_dir, 'model')):
        for m in os.listdir(os.path.join(hhf_dir, 'model')):
            hhf_file_list['model'].append(m)

    if os.path.exists(os.path.join(hhf_dir, 'opt_neuron.py')):
        with open(os.path.join(hhf_dir, 'opt_neuron.py'), 'r') as fd:
            hhf_file_list['opt_neuron.py'] = fd.read()
    
    return HttpResponse(content=json.dumps(hhf_file_list), content_type='application/json', status=200)


def hhf_get_files_content(request, folder, exc, ctx):

    hhf_dir = request.session[exc]['hhf_dir']
    folder = folder.split('Folder')[0]
    hhf_files_content = {}

    if not os.path.exists(os.path.join(hhf_dir, folder)):
        return HttpResponseBadRequest()

    for f in os.listdir(os.path.join(hhf_dir, folder)):
        with open(os.path.join(hhf_dir, folder, f), 'r') as fd:
            if f.endswith('.json'):
                jj = json.load(fd)
                hhf_files_content[f] = json.dumps(jj, indent=8)
            else:
                hhf_files_content[f] = fd.read()
    
    return JsonResponse(json.dumps(hhf_files_content), safe=False)


def hhf_download_files(request, folder, exc, ctx):
    try:
        file_ids = json.loads(request.GET.get('file_list', None))
        hhf_dir = request.session[exc]['hhf_dir']
        user_dir = request.session[exc]['user_dir']

        src_dir = os.path.join(hhf_dir, folder.split('Folder')[0])

        if len(file_ids['id']) > 1:
            # build zip archive
            tmp_dir = os.path.join(user_dir, 'tmp')
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            os.mkdir(tmp_dir)

            for f in file_ids['id']:
                shutil.copy2(os.path.join(src_dir, f), os.path.join(tmp_dir, f))

            shutil.make_archive(os.path.join(user_dir, 'files'), 'zip', tmp_dir)

            return FileResponse(open(os.path.join(user_dir, 'files.zip'), 'rb'), as_attachment=True)

        elif len(file_ids['id']) == 1:
            return FileResponse(open(os.path.join(src_dir, file_ids['id'][0]), 'rb'), as_attachment=True)

        else:
            return HttpResponseBadRequest()

    except json.JSONDecodeError:
        return HttpResponseBadRequest(content='file_dict Not present')


def hhf_download_parameters(request, exc, ctx):
    hhf_dir = request.session[exc]['hhf_dir']
    return FileResponse(open(os.path.join(hhf_dir, 'config', 'parameters.json'), 'rb'), as_attachment=True)


def hhf_download_optneuron(request, exc, ctx):
    hhf_dir = request.session[exc]['hhf_dir']
    return FileResponse(open(os.path.join(hhf_dir, 'opt_neuron.py'), 'rb'), as_attachment=True)


@csrf_exempt
def hhf_save_config_file(request, config_file, exc, ctx):
    try:
        file_content = json.loads(request.POST.get(config_file, None))
        hhf_dir = request.session[exc]['hhf_dir']
        with open(os.path.join(hhf_dir, 'config', config_file), 'w') as fd:
            json.dump(file_content, fd, indent=4)

        return HttpResponse(content=json.dumps({'resp': 'OK', 'message': config_file + ' saved correctly'}))
    
    except json.JSONDecodeError:
        return HttpResponseBadRequest(content=json.dumps({'resp': 'KO', 'message': 'Malformed "' + config_file + '" file!<br>File not saved.'}))


@csrf_exempt
def hhf_upload_files(request, folder, exc, ctx):

    if folder != 'morphologyFolder' and folder != 'mechanismsFolder' and folder != 'configFolder':
        return HttpResponseForbidden()

    if request.method == 'POST':
        file_content = request.body
        filename = request.META['HTTP_CONTENT_DISPOSITION'].split('filename="')[1].split('"')[0]

        hhf_dir = request.session[exc]['hhf_dir']

        if folder == 'configFolder':
            if filename == 'morph.json':
                return HttpResponse(json.dumps({'response': 'KO', 'message': 'Upload rejected.<br><br>The "morph.json" file will be generated automatically<br>once the morphology file will be uploaded.'}))
            try:
                jj = json.loads(file_content.decode())
                k = list(jj.keys())[0]
                filename_json = {request.session[exc]['hhf_model_key']: jj[k]}
                with open(os.path.join(hhf_dir, 'config', filename), 'w') as fd:
                    json.dump(filename_json, fd, indent=4)
            except json.JSONDecodeError:
                if os.path.exists(os.path.join(hhf_dir, 'config', filename)):
                    os.remove(os.path.join(hhf_dir, 'config', filename))
                return HttpResponseBadRequest(content=json.dumps({'message': 'Wrong file type. Accept only ".json" format.<br><br>Uploaded file deleted !'}))
            
            return HttpResponse(content=json.dumps({'response': 'OK', 'message': 'File uploaded successfully'}), status=200)

        dst_dir = os.path.join(hhf_dir, folder.split('Folder')[0])

        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)

        if folder == 'morphologyFolder':
            if not filename.endswith('.asc'):
                return HttpResponse(content=json.dumps({'response': 'KO', 'message': 'File "%s" rejected.<br>Moprholy file must be in ".asc" format.' % filename}))
        elif folder == 'mechanismsFolder':
            if not filename.endswith('.mod'):
                return HttpResponse(content=json.dumps({'response': 'KO', 'message': 'File "%s" rejected.<br>Mechanisms file must be in ".mod" format.' % filename}))

        with open(os.path.join(dst_dir, filename), 'wb') as fd:
            fd.write(file_content)

        if folder == 'morphologyFolder':
            morp_dict = {request.session[exc]['hhf_model_key']: filename}
            with open(os.path.join(hhf_dir, 'config', 'morph.json'), 'w') as fd:
                json.dump(morp_dict, fd)

        return HttpResponse(content=json.dumps({'response': 'OK', 'message': 'File uploaded successfully'}), status=200)

    return HttpResponseBadRequest(content=json.dumps({'response': 'KO', 'message': 'Some errors occured while uploading files'}))


def hhf_delete_files(request, folder, exc, ctx):

    try:
        file_ids = json.loads(request.GET.get('file_list', None))
        
        hhf_dir = request.session[exc]['hhf_dir']
        folder = folder.split('Folder')[0]

        if folder == 'morphology':
            os.remove(os.path.join(hhf_dir, folder, f))
            os.remove(os.path.join(hhf_dir, 'config', 'morph.json'))
        else:
            for f in file_ids['id']:
                os.remove(os.path.join(hhf_dir, folder, f))

        return HttpResponse(status=200)

    except json.JSONDecodeError:
        return HttpResponseBadRequest(content='Bad json')


def hhf_apply_model_key(request, exc, ctx, model_key):
    print('apply_model_key() called.')

    if model_key == 'workflow_id':
        model_key = request.session[exc]['wf_id']
    request.session[exc]['hhf_model_key'] = model_key

    hhf_dir = request.session[exc]['hhf_dir']

    config_files = [
        os.path.join(hhf_dir, 'config', 'parameters.json'),
        os.path.join(hhf_dir, 'config', 'features.json'),
        os.path.join(hhf_dir, 'config', 'protocols.json'),
        os.path.join(hhf_dir, 'config', 'morph.json'),
    ]

    jj_new = {model_key: ''}
    for f in config_files:
        if os.path.exists(f):
            # overwriting first json file key if different
            with open(f, 'r') as fd:
                jj_old = json.load(fd)
                k = list(jj_old.keys())[0]
                if k != model_key:
                    jj_new.update({model_key: jj_old[k]})
                else:
                    continue
            with open(f, 'w') as fd:
                json.dump(jj_new, fd, indent=4)

    # overwriting model line on opt_neuron.py
    if os.path.exists(os.path.join(hhf_dir, 'opt_neuron.py')):
        with open(os.path.join(hhf_dir, 'opt_neuron.py'), 'r') as fd:
            lines = fd.readlines()
        for l in lines:
            if l.startswith('evaluator = model.evaluator.create'):
                x = l.split("'")
                y = x[0] + "'" + model_key + "'" + x[2]
                z = lines.index(l)
                lines[z] = y

        with open(os.path.join(hhf_dir, 'opt_neuron.py'), 'w') as fd:
            fd.writelines(lines)

    request.session.save()
    return HttpResponse(status=200)


def hhf_get_model_key(request, exc, ctx):
    model_key = request.session[exc].get('hhf_model_key', None) 
    if model_key:
        return HttpResponse(content=json.dumps({'model_key': model_key}), status=200)
    return HttpResponse(status=204)


def hhf_delete_all(request, exc, ctx):
    
    # find all hhf session keys and if exists maintain hhf_etraces_dir references
    # and copy features.json and protocolos.json files on the standard worflow
    kk = []
    for k in request.session[exc].keys():
        if 'hhf' in k and (k != 'hhf_etraces' and k != 'hhf_etraces_dir'):
            kk.append(k)
        for f in os.listdir(os.path.join(request.session[exc]['hhf_dir'], 'config')):
            if f == 'features.json' or f == 'protocols.json':
                shutil.copy(os.path.join(request.session[exc]['hhf_dir'], 'config', f), request.session[exc]['user_dir_data_feat']) 
    
    # delete all folders
    hhf_dir = request.session[exc].get('hhf_dir', None)
    if hhf_dir and os.path.exists(hhf_dir):
        shutil.rmtree(hhf_dir)

    # remove all hhf session keys
    for k in kk:
        request.session[exc].pop(k)
    request.session.save()
    return HttpResponse(status=204)


def hhf_download_all(request, exc, ctx):
    hhf_dir = request.session[exc].get('hhf_dir', None)
    if hhf_dir:
        tmp_dir = os.path.join(request.session[exc]['user_dir'], 'tmp')
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        hhf_zip = os.path.join(tmp_dir, 'hhf_folder')
        shutil.make_archive(hhf_zip, 'zip', hhf_dir)
        return FileResponse(open(hhf_zip + '.zip', 'rb'), as_attachment=True)
    return HttpResponse(status=204)
