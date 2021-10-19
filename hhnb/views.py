""" Views """

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from hbp_validation_framework import ModelCatalog, ResponseError
from hh_neuron_builder.settings import MODEL_CATALOG_FILTER, TMP_DIR
from hhnb.core.lib.exception.workflow_exception import WorkflowExists

from hhnb.core.response import ResponseUtil
from hhnb.core.workflow import Workflow, WorkflowUtil
from hhnb.core.user import * 

from hhnb.tools import hpc_job_manager

import requests
import datetime
import os
import json
import ebrains_drive


def status(request):
    return ResponseUtil.ok_json_response({'hh-neuron-builder-status': 1})


def generate_exc_code(request):
    exc = 'tab_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    request.session[exc] = {}
    request.session.save()
    return exc

def store_workflow_id_in_session(request, exc, workflow_id):
    request.session.save()


def get_workflow(request, exc):
    hhnb_user = HhnbUser.get_user_from_request(request)
    workflow = Workflow.get_user_workflow_by_id(hhnb_user.get_username(),
                                                request.session[exc]['workflow_id'])
    return workflow


def home(request):
    return render(request, 'hhnb/home.html')


def workflow(request, exc=None):
    if not exc in request.session.keys():
        return home(request)

    return render(request, 'hhnb/workflow.html', context={'exc': exc})


def initialize_workflow(request):

    hhnb_user = HhnbUser.get_user_from_request(request)

    try:
        workflow = Workflow.generate_user_workflow(hhnb_user.get_username())
    except WorkflowExists as e:
        return ResponseUtil.ko_response(500, str(e))

    exc = generate_exc_code(request)
    request.session[exc]['workflow_id'] = workflow.get_workflow_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'exc': exc})


@csrf_exempt
def upload_workflow(request):

    if request.method != 'POST':
        return ResponseUtil.method_not_allowed()
    
    wf = request.body
    filename = request.META['HTTP_CONTENT_DISPOSITION'].split('filename="')[1].split('"')[0]

    with open(os.path.join(TMP_DIR, filename), 'wb') as fd:
        fd.write(wf)
    
    exc = generate_exc_code(request)
    hhnb_user = HhnbUser.get_user_from_request(request)
    try:
        workflow = Workflow.generate_user_workflow_from_zip(hhnb_user.get_username(),
                                                            os.path.join(TMP_DIR, filename))
    except WorkflowExists as e:
        return ResponseUtil.ko_json_response({'response': 'KO', 'message': str(e)})
    request.session[exc]['workflow_id'] = workflow.get_workflow_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'response': 'OK', 'exc': exc})


def clone_workflow(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    old_workflow = get_workflow(request, exc)
    new_worfklow = WorkflowUtil.clone_workflow(old_workflow)

    new_exc = generate_exc_code(request)
    request.session[new_exc]['workflow_id'] = new_worfklow.get_workflow_id()
    request.session.save()

    return ResponseUtil.ok_json_response({'exc': new_exc})


def download_workflow(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    zip_path = request.GET.get('zip_path')
    if zip_path:
        return ResponseUtil.file_response(zip_path)
    workflow = get_workflow(request, exc)
    zip_path = WorkflowUtil.make_workflow_archive(workflow)
    return ResponseUtil.ok_json_response({'zip_path': zip_path})


def get_workflow_properties(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()    
    workflow = get_workflow(request, exc)
    return ResponseUtil.ok_json_response(workflow.get_properties())


def fetch_models(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    mc_filter = MODEL_CATALOG_FILTER['hippocampus_models']

    # try:
    # mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
    mc_username = 'lbologna001'
    mc_password = 'Us*ZdV%CHP-Q[2ghX)Jv2[t{T!gp9Uck'
    mc = ModelCatalog(username=mc_username, password=mc_password)

    if request.GET.get('model') == 'all':    
        models = mc.list_models(organization=mc_filter['organization'],
                                model_scope=mc_filter['model_scope'],
                                species=mc_filter['species'],
                                collab_id=mc_filter['collab_id'])
        if len(models) > 0:
            return ResponseUtil.ok_json_response({'models': models})
        return ResponseUtil.ok_response(204, 'No content')
    else:
        model = mc.get_model(model_id=request.GET.get('model'))
        if model:
            try:
                model_path = mc.download_model_instance(instance_id=model['instances'][-1]['id'],
                                                    local_directory=TMP_DIR, overwrite=False)    
                if not model_path:
                    return ResponseUtil.ko_response('ModelCatalog temporarily not accessible')
            except FileExistsError:
                model_path = os.path.join(TMP_DIR, model['name'] + '.zip')
            workflow = get_workflow(request, exc)
            workflow.load_model_zip(model_path.decode())

    # except NameError:
        # return ResponseUtil.ko_response('Credentials not founds !')
    # except ResponseError:
        # return ResponseUtil.ko_response('ModelCatalog termporarily not accessible')

    # handle model 
    return ResponseUtil.ok_response()
    



def upload_features(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow = get_workflow(request, exc) 

    # get features from NFE
    folder = request.POST.get('folder')
    if folder:
        try:
            for d in os.listdir(folder):
                if os.path.splitext(d)[1] == '':
                    workflow.copy_features(os.path.join(folder, d, 'features.json'))
                    workflow.copy_features(os.path.join(folder, d, 'protocols.json'))
        except FileNotFoundError as e:
            return ResponseUtil.ko_response(str(e))
        return ResponseUtil.ok_response()
    
    # get uploaded features 
    uploaded_files = request.FILES.getlist('formFile')
    if len(uploaded_files) == 0:
        return ResponseUtil.ok_response('No files uploaded')
    if len(uploaded_files) > 2:
            return ResponseUtil.ko_response('Cannot upload more then 2 files')
    
    for uploaded_file in uploaded_files:
        if uploaded_file.name != 'features.json' and uploaded_file.name != 'protocols.json':
            return ResponseUtil.ko_response('Wrong files uploaded')
        if uploaded_file.name == 'features.json':
            workflow.write_features(uploaded_file)
        elif uploaded_file.name == 'protocols.json':
            workflow.write_protocols(uploaded_file)
    
    return ResponseUtil.ok_response()


def upload_model(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST') 
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    uploaded_files = request.FILES.getlist('formFile')
    if len(uploaded_files) == 0:
        return ResponseUtil.ok_response('No files uploaded')
    if len(uploaded_files) != 1:
        return ResponseUtil.ko_response('Must upload only "model.zip" file.')

    workflow = get_workflow(request, exc)
    print(workflow)

    for uploaded_file in uploaded_files: 
        with open(os.path.join(workflow.get_tmp_dir(), uploaded_file.name), 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    workflow.load_model_zip(os.path.join(workflow.get_tmp_dir(), uploaded_file.name))

    return ResponseUtil.ok_response()


def upload_analysis(request, exc=None):
    pass


def upload_files(request, exc):
    pass


def download_files(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow = get_workflow(request, exc)

    if 'pack' in request.GET.keys():
        if request.GET['pack'] == 'features':
            zip_file = WorkflowUtil.make_features_archive(workflow)
        elif request.GET['pack'] == 'model':
            zip_file = WorkflowUtil.make_model_archive(workflow)
        elif request.GET['pack'] == 'analysis':
            zip_file = WorkflowUtil.make_analysis_archive(workflow)
        return ResponseUtil.file_response(zip_file)
        
    if 'list' in request.GET.keys():
        pass

    return ResponseUtil.ko_response('No files selected to download')


def delete_files(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    file_list = json.loads(request.body).get('file_list')

    if file_list and len(file_list) <= 0:
        return ResponseUtil.ok_response('Any file to delete')
    
    workflow = get_workflow(request, exc)
    
    for f in file_list:
        try:
            workflow.remove_file(f)
        except FileNotFoundError as e:
            return ResponseUtil.ko_json_response(str(e))
    
    return ResponseUtil.ok_json_response()


def optimization_settings(request, exc=None):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow = get_workflow(request, exc)
    if request.method == 'GET':
        try:
            return ResponseUtil.ok_json_response(workflow.get_optimization_settings())
        except FileNotFoundError:
            return ResponseUtil.ok_json_response({})
    elif request.method == 'POST':
        optimization_settings = json.loads(request.body)
        workflow.set_optimization_settings(optimization_settings)
        return ResponseUtil.ok_json_response()
    else:
        return ResponseUtil.method_not_allowed()


def run_optimization(request, exc):
    pass


def fetch_jobs(request, exc):
    pass


def download_job_results(request, exc, job_id):
    pass


def get_job_results(request, exc, job_id):
    pass


def run_analysis(request, exc):
    pass



    
