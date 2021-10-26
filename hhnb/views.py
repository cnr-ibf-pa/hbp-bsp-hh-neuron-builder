""" Views """

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from hbp_validation_framework import ModelCatalog, ResponseError
from hh_neuron_builder.settings import MODEL_CATALOG_CREDENTIALS, MODEL_CATALOG_FILTER, TMP_DIR
from hhnb.core.lib.exception.workflow_exception import WorkflowExists

from hhnb.core.response import ResponseUtil
from hhnb.core.workflow import Workflow, WorkflowUtil
from hhnb.core.user import * 

from hhnb.tools import hpc_job_manager
import requests
import datetime
import os
import json
import shutil
import ebrains_drive
import base64

from hhnb.utils.misc import Cypher


def status(request):
    return ResponseUtil.ok_json_response({'hh-neuron-builder-status': 1})


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


def home(request):
    return render(request, 'hhnb/home.html')


def workflow(request, exc):
    if not exc in request.session.keys():
        return home(request)

    return render(request, 'hhnb/workflow.html', context={'exc': exc})


def initialize_workflow(request):
    print('intializing workflow')
    hhnb_user = HhnbUser.get_user_from_request(request)

    try:
        workflow = Workflow.generate_user_workflow(hhnb_user.get_username())
    except WorkflowExists as e:
        return ResponseUtil.ko_response(500, str(e))

    exc = generate_exc_code(request)

    request.session[exc]['workflow_id'] = workflow.get_id()
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

    return ResponseUtil.ok_json_response(workflow.get_properties())


def fetch_models(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    mc_filter = MODEL_CATALOG_FILTER['hippocampus_models']

    if MODEL_CATALOG_CREDENTIALS == ('username', 'password'):
        raise Exception('Invalid ModelCatalog credentials.\
                         Set them into your configuration \
                         file under\ "hh_neuron_builder/conf/"')

    try:
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
                        return ResponseUtil.ko_response('ModelCatalog temporarily not accessible')
                except FileExistsError:
                    model_path = os.path.join(TMP_DIR, model['name'] + '.zip')
                workflow, _ = get_workflow_and_user(request, exc)
                workflow.load_model_zip(model_path)

    # except NameError:
        # return ResponseUtil.ko_response('Credentials not founds !')
    except ResponseError as e:
        print(e)
        return ResponseUtil.ko_response('ModelCatalog termporarily not accessible')

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

    workflow, _ = get_workflow_and_user(request, exc)

    for uploaded_file in uploaded_files: 
        with open(os.path.join(workflow.get_tmp_dir(), uploaded_file.name), 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    try:
        workflow.load_model_zip(os.path.join(workflow.get_tmp_dir(), uploaded_file.name))
    except FileNotFoundError as e:
        return ResponseUtil.ko_response('Invalid model archive')

    return ResponseUtil.ok_response()


def upload_analysis(request, exc=None):
    pass


def upload_files(request, exc):
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')

    workflow, _ = get_workflow_and_user(request, exc)

    file_content = request.body
    file_path = request.META['HTTP_CONTENT_DISPOSITION'].split('filename="')[1].split('"')[0]

    WorkflowUtil.write_file_content(workflow, file_path, file_content)
    return ResponseUtil.ok_response()


def download_files(request, exc):
    print(request.GET)

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, _ = get_workflow_and_user(request, exc)
    WorkflowUtil.set_model_key(workflow)

    pack = request.GET.get('pack')
    file_list = request.GET.get('file_list')

    if pack:
        if pack == 'features':
            zip_file = WorkflowUtil.make_features_archive(workflow)
        elif pack == 'model':
            zip_file = WorkflowUtil.make_model_archive(workflow)
        elif pack == 'analysis':
            zip_file = WorkflowUtil.make_analysis_archive(workflow)
    elif file_list:
        path_list = json.loads(file_list).get('path')
        files = [os.path.join(workflow.get_model_dir(), f) for f in path_list]
        zip_file = WorkflowUtil.make_archive(workflow, 'files.zip', 'files', files)

    if zip_file:
        return ResponseUtil.file_response(zip_file)
    return ResponseUtil.ko_response('No files selected to download')


def delete_files(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    file_list = json.loads(request.body).get('file_list')

    if file_list and len(file_list) <= 0:
        return ResponseUtil.ok_response('Any file to delete')
    
    workflow, _ = get_workflow_and_user(request, exc)
    
    for f in file_list:
        try:
            workflow.remove_file(f)
        except FileNotFoundError as e:
            return ResponseUtil.ko_json_response(str(e))
    
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
            nsg_user = NsgUser(username=optimization_settings['username_submit'],
                               password=optimization_settings['password_submit'])
            if not nsg_user.validate_credentials():
                return ResponseUtil.ko_response('Invalid credentials')

            plain_username = optimization_settings['username_submit']
            plain_password = optimization_settings['password_submit']
            cipher_username = Cypher.encrypt(plain_username)
            cipher_password = Cypher.encrypt(plain_password)

            optimization_settings.update({'username_submit': cipher_username,
                                          'password_submit': cipher_password})

        workflow.set_optimization_settings(optimization_settings)
        return ResponseUtil.ok_json_response()
    else:
        return ResponseUtil.method_not_allowed()


def run_optimization(request, exc):
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    opt_model_dir = WorkflowUtil.make_optimization_model(workflow)
    opt_zip_path = os.path.join(workflow.get_tmp_dir(), os.path.split(opt_model_dir)[1])
    shutil.make_archive(opt_zip_path, 'zip', os.path.split(opt_model_dir)[0])

    # hpc = workflow.get_optimization_settings()['hpc']
    # if hpc == 'NSG':
    #     optimization_settings = workflow.get_optimization_settings()
    #     plain_username = Cypher.decrypt(optimization_settings['username_submit'])
    #     plain_password = Cypher.decrypt(optimization_settings['password_submit'])


    # return ResponseUtil.ok_response()

    return ResponseUtil.ko_response('Some errors occurred on job submission')


def fetch_jobs(request, exc):
    pass


def download_job_results(request, exc, job_id):
    pass


def get_job_results(request, exc, job_id):
    pass


def run_analysis(request, exc):
    pass


def get_user_avatar(request):
    url = 'https://wiki.ebrains.eu/bin/download/XWiki/' + request.user.username \
        + '/avatar.png?width=36&height=36&keepAspectRatio=true'
    r = requests.get(url, verify=False)
    return ResponseUtil.raw_response(content=r.content,
                                     content_type='image/png;',
                                     charset='UTF-8')


def hhf_comm(request):
    
    hhf_comm = json.loads(request.GET.get('hhf_dict')).get('HHF-Comm')
    if not hhf_comm:
        # if hhf_dict is not found redirect to home 
        return home(request)
    
    print('initializing')
    r = initialize_workflow(request)
    exc = json.loads(r.content)['exc']

    request.session[exc]['hhf_dict'] = hhf_comm
    request.session[exc]['hhf_already_downloaded'] = False
    request.session.save()
    # return workflow(request, exc)
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