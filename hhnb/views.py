""" Views """

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from hh_neuron_builder.settings import MODEL_CATALOG_COLLAB_DIR, MODEL_CATALOG_COLLAB_URL, MODEL_CATALOG_CREDENTIALS, MODEL_CATALOG_FILTER, TMP_DIR

from hhnb.core.lib.exception.workflow_exception import WorkflowExists
from hhnb.core.response import ResponseUtil
from hhnb.core.workflow import Workflow, WorkflowUtil
from hhnb.core.user import * 
from hhnb.core.security import *
from hhnb.core.job_handler import *

from hhnb.utils import messages 

from hbp_validation_framework import ModelCatalog, ResponseError

from ebrains_drive.exceptions import ClientHttpError as EbrainsDriveClientError
import ebrains_drive

import requests
import datetime
import os
import json
import shutil


def status(request):
    return ResponseUtil.ok_json_response({'hh-neuron-builder-status': 1})

def session_refresh(request, exc):
    if request.method == 'POST':
        refresh_url = request.POST.get('refresh_url')
        r = requests.get(url=refresh_url, verify=False)
        if r.status_code == 200:
            return ResponseUtil.ok_response('')
        
    return ResponseUtil.ko_response()


def generate_exc_code(request):
    exc = 'tab_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    request.session[exc] = {}
    request.session.save()
    return exc


def get_workflow_and_user(request, exc):
    hhnb_user = HhnbUser.get_user_from_request(request)
    workflow = Workflow.get_user_workflow_by_id(hhnb_user.get_username(),
                                                request.session[exc]['workflow_id'])
    workflow.clean_tmp_dir()
    return workflow, hhnb_user


def home_page(request):

    hhnb_user = HhnbUser.get_user_from_request(request)

    context = {}

    if 'old_workflow_path' in request.session.keys():
        workflow = Workflow.generate_user_workflow_from_path(hhnb_user.get_username(),
                                                request.session['old_workflow_path'])
        exc = generate_exc_code(request)
        request.session[exc]['workflow_id'] = workflow.get_id()
        request.session.pop('old_workflow_path')
        request.session.save()
        context = {'exc': exc}

    return render(request, 'hhnb/home.html', context)


def workflow_page(request, exc):
    if not exc in request.session.keys():
        return home_page(request)

    return render(request, 'hhnb/workflow.html', context={'exc': exc})


def initialize_workflow(request):
    print('intializing workflow')
    hhnb_user = HhnbUser.get_user_from_request(request)

    try:
        workflow = Workflow.generate_user_workflow(hhnb_user.get_username())
    except WorkflowExists as e:
        return ResponseUtil.ko_response(500, str(e))
    except PermissionError as e:
        print(e)
        return ResponseUtil.ko_response(500, messages.CRITICAL_ERROR)

    exc = generate_exc_code(request)

    request.session[exc]['workflow_id'] = workflow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'exc': exc})


def store_workflow_in_session(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)

    request.session['old_workflow_path'] =  workflow.get_workflow_path()
    request.session.save()

    return ResponseUtil.ok_response()


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
    
    request.session[exc]['workflow_id'] = workflow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'response': 'OK', 'exc': exc})


def clone_workflow(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    old_workflow, _ = get_workflow_and_user(request, exc)
    new_worfklow = WorkflowUtil.clone_workflow(old_workflow)
    new_exc = generate_exc_code(request)

    request.session[new_exc]['workflow_id'] = new_worfklow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'exc': new_exc})


def download_workflow(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
        
    zip_path = request.GET.get('zip_path')
    if zip_path:
        return ResponseUtil.file_response(zip_path)
    
    workflow, _ = get_workflow_and_user(request, exc)
    zip_path = WorkflowUtil.make_workflow_archive(workflow)
    
    return ResponseUtil.ok_json_response({'zip_path': zip_path})


def get_workflow_properties(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()    

    workflow, _ = get_workflow_and_user(request, exc)
    if request.session[exc].get('hhf_dict') and \
        not request.session[exc]['hhf_already_downloaded']:
        WorkflowUtil.download_from_hhf(workflow, request.session[exc]['hhf_dict'])
        request.session[exc]['hhf_already_downloaded'] = True
        request.session.save()

    props = workflow.get_properties()

    # hhf flag needs to handle the modal dialog 
    hhf = True if 'hhf_dict' in request.session[exc].keys() else False
    props.update({'hhf_flag': hhf}) 
    return ResponseUtil.ok_json_response(props)


def fetch_models(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    mc_filter = MODEL_CATALOG_FILTER['hippocampus_models']

    try:
        if MODEL_CATALOG_CREDENTIALS == ('username', 'password'):
            raise EnvironmentError(messages.MODEL_CATALOG_CREDENTIALS_NOT_FOUND)

        mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
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
                    model_path = model_path.decode()
                    if not model_path:
                        return ResponseUtil.ko_response(messages.MODEL_CATALOG_NOT_AVAILABLE)
                except FileExistsError:
                    model_path = os.path.join(TMP_DIR, model['name'] + '.zip')
                workflow, _ = get_workflow_and_user(request, exc)
                workflow.load_model_zip(model_path)
                
    except ResponseError as e:
        print(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_NOT_AVAILABLE)
    except EnvironmentError as e:
        print(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_INVALID_CREDENTIALS)

    # handle model 
    return ResponseUtil.ok_response()


def upload_features(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc) 

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
        return ResponseUtil.ok_response(messages.NO_FILE_UPLOADED)
    if len(uploaded_files) > 2:
            return ResponseUtil.ko_response(messages.NO_MORE_THEN.format('2 files'))
    
    for uploaded_file in uploaded_files:
        if uploaded_file.name != 'features.json' and uploaded_file.name != 'protocols.json':
            return ResponseUtil.ko_response(messages.WRONG_UPLAODED_FILE)
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
        return ResponseUtil.ok_response(messages.NO_FILE_UPLOADED)
    if len(uploaded_files) != 1:
        return ResponseUtil.ko_response(messages.ONLY_ACCEPTED_FILE.format('"model.zip"'))

    workflow, user = get_workflow_and_user(request, exc)

    for uploaded_file in uploaded_files: 
        uploaded_file_path = os.path.join(workflow.get_tmp_dir(), uploaded_file.name)
        with open(uploaded_file_path, 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    # check signature
    tmp_dir = os.path.join(TMP_DIR, user.get_username() + '_' + workflow.get_id())
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    shutil.unpack_archive(uploaded_file_path, tmp_dir)
    
    zip_content_list = [uploaded_file.name, 'signature.txt', 'README.txt']
    # if os.listdir(tmp_dir) != [uploaded_file.name, 'signature.txt', 'README.txt']:
    if not all([f in zip_content_list for f in os.listdir(tmp_dir)]):
        return ResponseUtil.ko_response(messages.INVALID_FILE.format('model'))
    try:
        with open(os.path.join(tmp_dir, uploaded_file.name), 'rb') as arch_fd:
            with open(os.path.join(tmp_dir, 'signature.txt'), 'r') as sign_fd:
                Sign.verify_data_sign(sign_fd.read(), arch_fd.read())
    except InvalidSign:
        return ResponseUtil.ko_response(messages.INVALID_SIGNATURE.format('model'))
 
    try:
        workflow.load_model_zip(os.path.join(tmp_dir, uploaded_file.name))
    except FileNotFoundError as e:
        print(e)
        return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format('"model.zip"'))

    return ResponseUtil.ok_response()


# TODO: fix this function 
def upload_analysis(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST') 
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    uploaded_files = request.FILES.getlist('formFile')
    if len(uploaded_files) == 0:
        return ResponseUtil.ok_response(messages.NO_FILE_UPLOADED)
    if len(uploaded_files) != 1:
        return ResponseUtil.ko_response(messages.NO_MORE_THEN.format('a ".zip" file'))

    workflow, user = get_workflow_and_user(request, exc)

    for uploaded_file in uploaded_files: 
        uploaded_file_path = os.path.join(workflow.get_tmp_dir(), 
                                          uploaded_file.name)
        with open(uploaded_file_path, 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    # check signature
    tmp_dir = os.path.join(TMP_DIR, user.get_username() + '_' + workflow.get_id())
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    shutil.unpack_archive(uploaded_file_path, tmp_dir)

    if os.listdir(tmp_dir) == [uploaded_file.name.split('.')[0]]:
        unzip_dir_path = os.path.join(tmp_dir, uploaded_file.name.split('.')[0])
        if all([True if dir in os.listdir(unzip_dir_path) else False\
                for dir in ['mechanisms', 'morphology', 'checkpoints']]):
            shutil.move(unzip_dir_path, workflow.get_analysis_dir())
            return ResponseUtil.ok_response('')

    zip_content_list = [uploaded_file.name, 'signature.txt', 'README.txt']
    # if os.listdir(tmp_dir) != [uploaded_file.name, 'signature.txt', 'README.txt']:
    if not all([f in zip_content_list for f in os.listdir(tmp_dir)]):
        return ResponseUtil.ko_response(messages.INVALID_FILE.format('analysis'))
    try:
        with open(os.path.join(tmp_dir, uploaded_file.name), 'rb') as arch_fd:
            with open(os.path.join(tmp_dir, 'signature.txt'), 'r') as sign_fd:
                Sign.verify_data_sign(sign_fd.read(), arch_fd.read())
    except InvalidSign:
        return ResponseUtil.ko_response(messages.INVALID_SIGNATURE.format('analysis'))

    try:
        shutil.unpack_archive(os.path.join(tmp_dir, uploaded_file.name),
                              workflow.get_tmp_dir())
        tmp_dir_list = os.listdir(workflow.get_tmp_dir())
        tmp_dir_list.remove(uploaded_file.name) # remove zip file from list
        if len(tmp_dir_list) == 1:
            unzip_dir_path = os.path.join(workflow.get_tmp_dir(), tmp_dir_list[0])
            if all([True if dir in os.listdir(unzip_dir_path) else False\
                    for dir in ['mechanisms', 'morphology', 'checkpoints']]):
                shutil.move(unzip_dir_path, workflow.get_analysis_dir())
        else:
            for f in tmp_dir_list:
               shutil.move(os.path.join(workflow.get_tmp_dir(), f),
                          workflow.get_results_dir())
            # run analisys
            return run_analysis(request, exc)
        
        return ResponseUtil.ok_response('')

    except Exception as e:
        print(str(e))

    return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format('"analysis.zip"'))


def upload_files(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')

    workflow, _ = get_workflow_and_user(request, exc)

    folder = request.POST.get('folder')
    uploaded_file = request.FILES.get('file')
    print(uploaded_file.name)

    if folder == 'morphology/':
        if not uploaded_file.endswith('.asc'):
            return ResponseUtil.ko_response('Morphology must be "<b>.asc</b>" file.')
    elif folder == 'mechanisms/':
        if not uploaded_file.endswith('.mod'):
            return ResponseUtil.ko_response('Mechanisms must be "<b>.mod</b>" file.')
    elif folder == 'config/':
        if not uploaded_file.name in ['features.json', 'protocols.json', 'parameters.json']:
            return ResponseUtil.ko_response(
                'Config file must be one of the fallowing files:<br>\
                "<b>protocols.json</b>", "<b>features.json</b>", <b>"parameters.json</b>"'
            )
 
    full_path = os.path.join(workflow.get_model_dir(), folder, uploaded_file.name)
    with open(full_path, 'wb') as fd:
        if uploaded_file.multiple_chunks(chunk_size=4096):
            for chunk in uploaded_file.chunks(chunk_size=4096):
                fd.write(chunk)
        else:
            fd.write(uploaded_file.read())

    return ResponseUtil.ok_response('')


def download_files(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, user = get_workflow_and_user(request, exc)
    WorkflowUtil.set_model_key(workflow)

    pack = request.GET.get('pack')
    file_list = request.GET.get('file_list')

    if pack:
        if pack == 'features':
            arch_file = WorkflowUtil.make_features_archive(workflow)
            return ResponseUtil.file_response(arch_file)
        elif pack == 'model':
            arch_file = WorkflowUtil.make_model_archive(workflow)
        elif pack == 'results':
            arch_file = WorkflowUtil.make_results_archive(workflow)
        elif pack == 'analysis':
            arch_file = WorkflowUtil.make_analysis_archive(workflow)
    elif file_list:
        path_list = json.loads(file_list).get('path')

        # TODO: add Permission control

        files = [os.path.join(workflow.get_model_dir(), f) for f in path_list]
        arch_name = workflow.get_id() + '_model_files.zip'
        arch_file = WorkflowUtil.make_archive(workflow, arch_name, 'files', files)

    if arch_file:

        tmp_dir = os.path.join(TMP_DIR, user.get_username() + '_' + workflow.get_id())
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)

        root_dir, zip_name = os.path.split(arch_file)
        arch_sign = os.path.join(root_dir, 'signature.txt')
        with open(arch_sign, 'w') as sign_fd:
            with open(arch_file, 'rb') as arch_fd:
                sign_fd.write(Sign.get_data_sign(arch_fd.read()))
        
        arch_readme = os.path.join(root_dir, 'README.txt')
        with open(arch_readme, 'w') as readme_fd:
            readme_fd.write(messages.SIGNATURE_README_DESCRIPTION)
        
        final_zip_file = shutil.make_archive(
            base_name=os.path.join(tmp_dir, zip_name.split('.zip')[0]),
            format='zip',
            root_dir=root_dir
        )  
        return ResponseUtil.file_response(final_zip_file)
    
    return ResponseUtil.ko_response(messages.NO_FILE_TO_DOWNLOAD)


def delete_files(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    file_list = json.loads(request.body).get('file_list')

    if file_list and len(file_list) <= 0:
        return ResponseUtil.ok_response(messages.NO_FILE_TO_DELETE)
    
    workflow, _ = get_workflow_and_user(request, exc)
    
    for f in file_list:
        try:
            workflow.remove_file(f)
        except PermissionError:
            return ResponseUtil.ko_response(messages.CRITICAL_ERROR)
    
    return ResponseUtil.ok_json_response()


def optimization_settings(request, exc=None):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, _ = get_workflow_and_user(request, exc)
    if request.method == 'GET':
        try:
            return ResponseUtil.ok_json_response(workflow.get_optimization_settings())
        except FileNotFoundError:
            return ResponseUtil.ok_json_response({})
    elif request.method == 'POST':
        optimization_settings = json.loads(request.body)
        if optimization_settings['hpc'] == 'NSG':
            nsg_username = optimization_settings.get('username_submit')
            nsg_password = optimization_settings.get('password_submit')

            if nsg_username and nsg_password:
                nsg_user = NsgUser(nsg_username, nsg_password)
                if not nsg_user.validate_credentials():
                    return ResponseUtil.ko_response(messages.AUTHENTICATION_INVALID_CREDENTIALS)

                request.session['nsg_username'] = nsg_username
                request.session['nsg_password'] = nsg_password
                request.session.save()

        workflow.set_optimization_settings(optimization_settings)
        return ResponseUtil.ok_json_response()
    else:
        return ResponseUtil.method_not_allowed()


def run_optimization(request, exc):
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    opt_model_dir = WorkflowUtil.make_optimization_model(workflow)
    zip_dst_dir = os.path.join(workflow.get_tmp_dir(), 
                               os.path.split(opt_model_dir)[1])
    zip_file = shutil.make_archive(base_name=zip_dst_dir,
                                   format='zip',
                                   root_dir=os.path.split(opt_model_dir)[0])

    optimization_settings = workflow.get_optimization_settings()

    optimization_settings.update({
        'nsg_username': request.session.get('nsg_username'),
        'nsg_password': request.session.get('nsg_password'),
    })

    response = JobHandler.submit_job(hhnb_user, zip_file, optimization_settings)
    if response.status_code == 200:
        workflow.set_optimization_settings(optimization_settings, job_submitted_flag=True)
    return response


def fetch_jobs(request, exc):
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    hpc = request.GET.get('hpc')
    if not hpc:
        return ResponseUtil.ko_response(messages.NO_HPC_SELECTED)

    _, hhnb_user = get_workflow_and_user(request, exc)

    try:
        data = JobHandler.fetch_jobs_list(hpc, hhnb_user)
        return ResponseUtil.ok_json_response(data)
    except JobHandler.ServiceAccountException as e:
        print(e)
        return ResponseUtil.ko_response(messages.JOB_FETCH_ERROR.format('SERVICE ACCOUNT'))
    except JobHandler.UnicoreClientException as e:
        print(e)
        return ResponseUtil.ko_response(messages.JOB_FETCH_ERROR.format('DAINT-CSCS'))
    except JobHandler.HPCException as e:
        print(e)
        return ResponseUtil.ko_response(str(f'<b>{e}</b>'))

    except Exception as e:
        print(e)
        return ResponseUtil.ko_response(messages.CRITICAL_ERROR)


def fetch_job_results(request, exc):
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    hpc = request.GET.get('hpc')
    job_id = request.GET.get('job_id')

    if not hpc:
        return ResponseUtil.ko_response(messages.NO_HPC_SELECTED)
    if not job_id:
        return ResponseUtil.ko_response(messages.NO_JOB_SELECTED)

    workflow, hhnb_user = get_workflow_and_user(request, exc)

    try:
        file_list = JobHandler.fetch_job_files(hpc, job_id, hhnb_user)
        WorkflowUtil.download_job_result_files(workflow, file_list)

        return ResponseUtil.ok_response()

    except JobHandler.JobsFilesNotFound as e:
        return ResponseUtil.ko_response(str(e))

    except Exception as e:
        print(e)

    return ResponseUtil.ko_response(messages.JOB_RESULTS_FETCH_ERRROR)


def run_analysis(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)

    try:
        for f in os.listdir(workflow.get_results_dir()):
            print(f)
            if f.split('.')[0] == 'output':
                job_output = os.path.join(workflow.get_results_dir(), f)

        WorkflowUtil.run_analysis(workflow, job_output)
        return ResponseUtil.ok_response('')

    except FileNotFoundError as e:
        return ResponseUtil.ko_response(404, str(e))       
     
    except Exception as e:
        print(e)
    return ResponseUtil.ko_response(messages.ANALYSIS_ERROR)


def upload_to_naas(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)

    naas_model = request.session[exc].get('naas_model')
    print(naas_model)
    if naas_model:
        return ResponseUtil.ok_response(naas_model)

    try:
        naas_archive = WorkflowUtil.make_naas_archive(workflow)
    except Exception as e:
        print(e)
        return ResponseUtil.ko_response(messages.ANALYSIS_ERROR)

    try:
        r = requests.post(url='https://blue-naas-svc-bsp-epfl.apps.hbp.eu/upload',
                          files={'file': open(naas_archive, 'rb')}, verify=False)
        if r.status_code == 200:
            model_link = os.path.split(naas_archive)[1].split('.zip')[0]
            request.session[exc]['naas_model'] = 'already_uploaded'
            request.session.save()
            return ResponseUtil.ok_response(model_link)
    except requests.exceptions.ConnectionError as e:
        print(e)
        return ResponseUtil.ko_response(500, messages.BLUE_NAAS_NOT_AVAILABLE)

    return ResponseUtil.ko_response(r.status_code, r.content)


def get_model_data(request, exc):
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, hhnb_user = get_workflow_and_user(request, exc)

    # STILL USING THE DEFAULT CREDENTIAL


def get_model_catalog_attribute_options(request):
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')
    mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
    try:
        mc = ModelCatalog(username=mc_username, password=mc_password)
        options = mc.get_attribute_options()
        return ResponseUtil.ok_json_response(options)
    except Exception as e:
        print(e)
        return ResponseUtil.ko_response(messages.GENERAL_ERROR)


def register_model(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    form_data = request.POST

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    
    if not workflow.get_properties()['analysis']:
        return ResponseUtil.ko_response('No model detected')

    model_zip = WorkflowUtil.make_analysis_archive(workflow)
    model_zip_path, old_model_zip_name = os.path.split(model_zip)
    model_zip_name = old_model_zip_name.split('_analysis.zip')[0] \
                   + form_data.get('modelSuffix', '') + '.zip'
    os.rename(src=model_zip, dst=os.path.join(model_zip_path, model_zip_name))
    model_zip = os.path.join(model_zip_path, model_zip_name)

    try:
        if MODEL_CATALOG_CREDENTIALS == ('username', 'password'):
            raise EnvironmentError(messages.MODEL_CATALOG_INVALID_CREDENTIALS)

        mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
        mc = ModelCatalog(username=mc_username, password=mc_password)

        client = ebrains_drive.connect(username=mc_username, password=mc_password)
        repo = client.repos.get_repo_by_url(MODEL_CATALOG_COLLAB_URL)
        seafdir = repo.get_dir('/' + MODEL_CATALOG_COLLAB_DIR)
        uploaded_model = seafdir.upload_local_file(model_zip)

        reg_mod_url = f'https://wiki.ebrains.eu/lib/{ repo.id }/file/'\
                    + f'{ MODEL_CATALOG_COLLAB_DIR }/{ model_zip_name }?dl=1'

        auth_family_name = form_data.get('authorLastName')
        auth_given_name = form_data.get('authorFirstName')
        organization = form_data.get('modelOrganization')
        cell_type = form_data.get('modelCellType')
        model_scope = form_data.get('modelScope')
        abstraction_level = form_data.get('modelAbstraction')
        brain_region = form_data.get('modelBrainRegion')
        species = form_data.get('modelSpecies')
        own_family_name = form_data.get('ownerLastName')
        own_given_name = form_data.get('ownerFirstName')
        license = form_data.get('modelLicense')
        description = form_data.get('modelDescription')
        private_flag = True if form_data.get('modelPrivate') == 'true' else False     

        registered_model = mc.register_model(
            collab_id='hhnb-registeredmodels',
            name=model_zip_name.split('.')[0],
            author={'family_name': auth_family_name, 'given_name': auth_given_name},
            organization=organization,
            private=private_flag,
            species=species,
            brain_region=brain_region,
            cell_type=cell_type,
            model_scope=model_scope,
            abstraction_level=abstraction_level,
            owner={'family_name': own_family_name, 'given_name': own_given_name},
            description=description,
            instances=[{
                'version': '1.0',
                'source': reg_mod_url,
                'license': license,
            }]
        )
        print(registered_model)
        import pprint
        pprint.pprint(registered_model)

        model_path_on_mc = 'https://model-catalog.brainsimulation.eu/'\
                         + '#model_id.{}'.format(registered_model['id'])
        
        return ResponseUtil.ok_response(messages.MODEL_SUCCESSFULLY_REGISTERED.format(model_path_on_mc))

    except EbrainsDriveClientError as e:
        code = e.code
        message = e.message
        return ResponseUtil.ko_response(code, message)

    except FileExistsError as e:
        print(e)
        return ResponseUtil.ko_response(messages.MODEL_ALREADY_EXISTS)

    except EnvironmentError as e:
        print(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_INVALID_CREDENTIALS)

    except Exception as e:
        uploaded_model.delete()
        print(e)
        return ResponseUtil.ko_response(f'<b>Error !</b><br><br>{str(e)}')

    return ResponseUtil.ko_response(messages.GENERAL_ERROR)


def get_user_avatar(request):
    url = 'https://wiki.ebrains.eu/bin/download/XWiki/' + request.user.username \
        + '/avatar.png?width=36&height=36&keepAspectRatio=true'
    r = requests.get(url, verify=False)
    return ResponseUtil.raw_response(content=r.content,
                                     content_type='image/png;',
                                     charset='UTF-8')


def get_user_page(request):
    return redirect('https://wiki.ebrains.eu/bin/view/Identity/#/users/' + request.user.username)


def get_authentication(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return ResponseUtil.ok_response()
    elif request.method == 'POST':
        request.session['nsg_username'] = request.POST.get('username')
        request.session['nsg_password'] = request.POST.get('password')
        
        hhnb_user = HhnbUser.get_user_from_request(request)

        if hhnb_user.validate_nsg_login():
            return ResponseUtil.ok_response()
    return ResponseUtil.ko_response(messages.NOT_AUTHENTICATED)


def hhf_comm(request):
    
    hhf_comm = json.loads(request.GET.get('hhf_dict')).get('HHF-Comm')
    if not hhf_comm:
        # if hhf_dict is not found redirect to home 
        return home_page(request)
    
    r = initialize_workflow(request)
    exc = json.loads(r.content)['exc']

    request.session[exc]['hhf_dict'] = hhf_comm
    request.session[exc]['hhf_already_downloaded'] = False
    request.session.save()
    #
    return render(request, 'hhnb/hhf_comm.html', context={'exc': exc})


def hhf_etraces_dir(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')
    workflow, _ = get_workflow_and_user(request, exc)
    return ResponseUtil.ok_json_response({'hhf_etraces_dir': workflow.get_etraces_dir()})


def hhf_list_files_new(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, _ = get_workflow_and_user(request, exc)
    model_files = WorkflowUtil.list_model_files(workflow)
    print(json.dumps(model_files, indent=4))
    return ResponseUtil.ok_json_response(model_files)


# TODO: the functions below will be deprecated
def hhf_list_files(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)
    hhf_dir = workflow.get_model_dir()
    
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
    
    return ResponseUtil.ok_json_response(hhf_file_list)


def hhf_get_files_content(request, folder, exc):

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)
    if not os.path.join(workflow.get_model_dir(), folder):
        return ResponseUtil.ko_response()

    folder = folder.split('Folder')[0]
    hhf_files_content = {}

    for f in os.listdir(os.path.join(workflow.get_model_dir(), folder)):
        print(os.path.join(workflow.get_model_dir(), folder, f))
        with open(os.path.join(workflow.get_model_dir(), folder, f), 'r') as fd:
            if f.endswith('.json'):
                jj = json.load(fd)
                hhf_files_content[f] = json.dumps(jj, indent=8)
            else:
                    hhf_files_content[f] = fd.read()
    
    return ResponseUtil.ok_json_response(hhf_files_content)


def hhf_get_model_key(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, _ = get_workflow_and_user(request, exc)
    return ResponseUtil.ok_json_response({'model_key': workflow.get_model().get_key()})


def hhf_apply_model_key(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, _ = get_workflow_and_user(request, exc)
    WorkflowUtil.set_model_key(workflow, key=request.POST.get('model_key'))
    return ResponseUtil.ok_response()


@csrf_exempt
def hhf_save_config_file(request, folder, config_file, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, _ = get_workflow_and_user(request, exc)

    try:
        file_content = json.loads(request.POST.get(config_file))
        file_path = os.path.join(workflow.get_model_dir(), 
                                 folder.split('Folder')[0],
                                 config_file)
        with open(file_path, 'w') as fd:
            json.dump(file_content, fd, indent=4)
        return ResponseUtil.ok_response('')
    except json.JSONDecodeError:
        print('Malformed json')
        return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format(config_file + '.json')) 
    except FileNotFoundError:
        print('File not found')
        return ResponseUtil.ko_response(404, messages.CRITICAL_ERROR)
    except Exception as e:
        print(str(e))
        return ResponseUtil.ko_response(400, messages.GENERAL_ERROR)
