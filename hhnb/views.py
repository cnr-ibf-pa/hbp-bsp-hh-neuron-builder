""" Views """

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from hh_neuron_builder.settings import MODEL_CATALOG_COLLAB_DIR, MODEL_CATALOG_COLLAB_URL, MODEL_CATALOG_CREDENTIALS, MODEL_CATALOG_FILTER, TMP_DIR

from hhnb.core.lib.exception.workflow_exception import AnalysisProcessError, MechanismsProcessError, WorkflowExists
from hhnb.core.lib.exception.model_exception import *
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
import logging

from hhnb.utils.misc import InvalidArchiveError, get_signed_archive, validate_archive, validate_json_file
logger = logging.getLogger(__name__)


LOG_ACTION = 'User: "{}"\t Action: {}'




def status(request):
    """ Returns the status of the service if is up. """
    return ResponseUtil.ok_json_response({'hh-neuron-builder-status': 1})


def session_refresh(request, exc):
    """ Refresh the user session to get a living user oidc_access_token. """
    logger.debug('refreshing session')
    if request.method == 'POST':
        refresh_url = request.POST.get('refresh_url')
        r = requests.get(url=refresh_url, verify=False)
        if r.status_code == 200:
            return ResponseUtil.ok_response('')
        
    return ResponseUtil.ko_response()


def generate_exc_code(request):
    """
    Generate an "exc" code to identify each user session. 
    The "exc" code is based on the current time.
    """
    exc = 'tab_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    logger.debug(f'generating exc code: {exc}')
    request.session[exc] = {}
    request.session.save()
    return exc


def get_workflow_and_user(request, exc):
    """
    Returns the workflow and the user of the session identified by
    the "exc" code.
    """
    hhnb_user = HhnbUser.get_user_from_request(request)
    workflow = Workflow.get_user_workflow_by_id(hhnb_user.get_sub(),
                                                request.session[exc]['workflow_id'])
    workflow.clean_tmp_dir()
    return workflow, hhnb_user


def index_docs(request):
    """ Render Guidebook main page. """
    return render(request, 'hhnb/docs/index.html')


def home_page(request):
    """ 
    By default the home page is redered, but if the "old_workflow_path"
    is found in the session stored keys, the old workflow is restored
    and the workflow page is rendered.
    """

    hhnb_user = HhnbUser.get_user_from_request(request)
    context = {}

    logger.info(LOG_ACTION.format(hhnb_user, 'access HOME page'))

    if 'old_workflow_path' in request.session.keys():
        workflow = Workflow.generate_user_workflow_from_path(hhnb_user.get_sub(),
                                                request.session['old_workflow_path'])
        exc = generate_exc_code(request)
        request.session[exc]['workflow_id'] = workflow.get_id()
        request.session.pop('old_workflow_path')
        request.session.save()
        context = {'exc': exc}
        logger.debug(f'workflow {workflow} restored for user: "{hhnb_user}"')

    return render(request, 'hhnb/home.html', context)


def workflow_page(request, exc):
    """
    Render the workflow page if everything is ok, otherwise the home page
    is rendered.
    """
    if not exc in request.session.keys():
        return home_page(request)
    
    _, hhnb_user = get_workflow_and_user(request, exc) 
    logger.info(LOG_ACTION.format(hhnb_user, 'access WORKFLOW page'))

    return render(request, 'hhnb/workflow.html', context={'exc': exc})


def initialize_workflow(request):
    """
    Initialize a new workflow for the current session and store its
    relative "exc" key.

    A WorkflowExists error will be raised if the new workflow tree
    is already preset in the file system, or a PermissionError
    will be raised if any else error occurred.
    """
    hhnb_user = HhnbUser.get_user_from_request(request)
    logger.debug(f'initializing workflow for "{hhnb_user}"')
    
    try:
        workflow = Workflow.generate_user_workflow(hhnb_user.get_sub())
        logger.debug(f'workflow {workflow} created for "{hhnb_user}"')
    except WorkflowExists as e:
        logger.error(e)
        return ResponseUtil.ko_response(497, str(e))
    except PermissionError as e:
        logger.critical(e)
        return ResponseUtil.ko_response(500, messages.CRITICAL_ERROR)

    exc = generate_exc_code(request)

    request.session[exc]['workflow_id'] = workflow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'exc': exc})


def store_workflow_in_session(request, exc):
    """
    Store the workflow root folder in the session.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)
    logger.debug('store workflow {workflow} in session')

    request.session['old_workflow_path'] =  workflow.get_workflow_path()
    request.session.save()

    return ResponseUtil.ok_response()


@csrf_exempt
def upload_workflow(request):
    """
    Allow to upload a zip file contains a whole workflow
    and continue to work with it. 
    """

    if request.method != 'POST':
        return ResponseUtil.method_not_allowed()
    
    wf = request.body
    filename = request.META['HTTP_CONTENT_DISPOSITION'].split('filename="')[1].split('"')[0]

    wf_zip = os.path.join(TMP_DIR, filename)
    with open(wf_zip, 'wb') as fd:
        fd.write(wf)

    try:
        valide_wf_zip = validate_archive(wf_zip)
    except InvalidArchiveError:
        return ResponseUtil.ko_json_response({'response': 'KO',
                                              'message': messages.INVALID_FILE.format(filename)})
    except InvalidSign:
        return ResponseUtil.ko_json_response({'response': 'KO',
                                              'message': messages.INVALID_SIGNATURE.format(filename)})

    exc = generate_exc_code(request)
    hhnb_user = HhnbUser.get_user_from_request(request)
    logger.info(LOG_ACTION.format(hhnb_user, 'uploading workflow'))

    try:
        workflow = Workflow.generate_user_workflow_from_zip(hhnb_user.get_sub(),
                                                            valide_wf_zip)
    except WorkflowExists as e:
        logger.error(e)
        return ResponseUtil.ko_json_response({'response': 'KO', 'message': str(e)})
    
    request.session[exc]['workflow_id'] = workflow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'response': 'OK', 'exc': exc})


def clone_workflow(request, exc):
    """
    Clone a workflow.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    old_workflow, hhnb_user = get_workflow_and_user(request, exc)
    new_worfklow = WorkflowUtil.clone_workflow(old_workflow)
    new_exc = generate_exc_code(request)

    logger.info(LOG_ACTION.format(
        hhnb_user, 'cloning old workflow %s to %s' % (old_workflow, new_worfklow))
    )

    request.session[new_exc]['workflow_id'] = new_worfklow.get_id()
    request.session.save()
    return ResponseUtil.ok_json_response({'exc': new_exc})


def download_workflow(request, exc):
    """
    Download the whole workflow after zipped and signed it.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
        
    zip_path = request.GET.get('zip_path')
    if zip_path:
        return ResponseUtil.file_response(zip_path)
    
    workflow, hhnb_user = get_workflow_and_user(request, exc)
    zip_path = WorkflowUtil.make_workflow_archive(workflow)
    signed_zip_path = get_signed_archive(zip_path)
    logger.info(LOG_ACTION.format(hhnb_user, 'downloading workflow %s' % workflow))
    
    return ResponseUtil.ok_json_response({'zip_path': signed_zip_path})


def get_workflow_properties(request, exc):
    """
    Returns the workflow properties using a JsonResponse object.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()    

    workflow, _ = get_workflow_and_user(request, exc)
    if request.session[exc].get('hhf_dict') and \
        not request.session[exc]['hhf_already_downloaded']:
        WorkflowUtil.download_from_hhf(workflow, request.session[exc]['hhf_dict'])
        request.session[exc]['hhf_already_downloaded'] = True
        request.session.save()

    props = workflow.get_properties()
    logger.debug(f'getting properties for {workflow}: {props}')

    # hhf flag needs to handle the modal dialog 
    hhf = True if 'hhf_dict' in request.session[exc].keys() else False
    props.update({'hhf_flag': hhf}) 
    logger.debug('enabling HHF flag on {workflow}')
    return ResponseUtil.ok_json_response(props)


def fetch_models(request, exc):
    """
    This API is used to fetch the model list from the model catalog
    or to download one of it.

    This can be used by passing a json object containing the "model" key.
    
    If the value is "all" (i.e. "{model: 'all'}"), then all the models are 
    fetched from the ModelCatalog and filtered using the 
    MODEL_CATALOG_FILTER imported from the settings project.
    Otherwise if the value is a model id (i.e "{model: 1}"), then the 
    model will be downloaded from the ModelCatalog and extracted into the
    current workflow.
    """

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    mc_filter = MODEL_CATALOG_FILTER['hippocampus_models']

    try:
        if MODEL_CATALOG_CREDENTIALS == ('username', 'password'):
            logger.debug('ModelCatalog username and password are not set')
            raise EnvironmentError(messages.MODEL_CATALOG_CREDENTIALS_NOT_FOUND)

        mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
        mc = ModelCatalog(username=mc_username, password=mc_password)

        if request.GET.get('model') == 'all':    
            models = mc.list_models(organization=mc_filter['organization'],
                                    model_scope=mc_filter['model_scope'],
                                    species=mc_filter['species'],
                                    collab_id=mc_filter['collab_id'])
            if len(models) > 0:
                logger.debug(f'{len(models)} models found')
                return ResponseUtil.ok_json_response({'models': models})
            logger.debug(f'no model founds in the ModelCatalog using the filter {mc_filter}')
            return ResponseUtil.ok_response(204, 'No content')
        else:
            workflow, hhnb_user = get_workflow_and_user(request, exc)
            requested_model = request.GET.get('model')
            logger.debug(f'requesting {requested_model} on ModelCatalog')
            model = mc.get_model(model_id=requested_model)
            if model:
                logger.debug(f'downloading model {model} from ModelCatalog')
                try:
                    model_path = mc.download_model_instance(
                        instance_id=model['instances'][-1]['id'],
                        local_directory=TMP_DIR, 
                        overwrite=False
                    )    
                    model_path = model_path.decode()
                    if not model_path:
                        logger.error(f'User: {hhnb_user} got error while fetching\
                                       model {model} from ModelCatalog on model_path: {model_path}')
                        return ResponseUtil.ko_response(messages.MODEL_CATALOG_NOT_AVAILABLE)
                except FileExistsError:
                    model_path = os.path.join(TMP_DIR, model['name'] + '.zip')
                workflow.load_model_zip(model_path)
                
                logger.info(LOG_ACTION.format(hhnb_user, 'downloaded model %s on %s' % (model, workflow)))

    except ResponseError as e:
        print(e)
        logger.error(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_NOT_AVAILABLE)
    except EnvironmentError as e:
        print(e)
        logger.error(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_INVALID_CREDENTIALS)

    # handle model 
    return ResponseUtil.ok_response()


def upload_features(request, exc):
    """
    Allow to upload the features and/or protocols and write 
    it/them to the current workflow.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc) 
    logger.info(LOG_ACTION.format(hhnb_user, 'uploading features in %s' % workflow))

    # get features from NFE
    folder = request.POST.get('folder')
    if folder:
        try:
            for d in os.listdir(folder):
                if os.path.splitext(d)[1] == '':
                    workflow.copy_features(os.path.join(folder, d, 'features.json'))
                    workflow.copy_features(os.path.join(folder, d, 'protocols.json'))
        except FileNotFoundError as e:
            logger.error(e)
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
    """
    Allow to upload a model zip if the zip file is not corrupted 
    and the its signature is valid.
    """
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
    logger.info(LOG_ACTION.format(user, 'uploading model to %s' % workflow))

    for uploaded_file in uploaded_files: 
        uploaded_file_path = os.path.join(workflow.get_tmp_dir(), uploaded_file.name)
        with open(uploaded_file_path, 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    try:
        zip_path = validate_archive(uploaded_file_path)
    except InvalidSign:
        return ResponseUtil.ko_response(messages.INVALID_SIGNATURE.format('model'))
    except InvalidArchiveError:
        return ResponseUtil.ko_response(messages.INVALID_FILE.format('model'))

    try:
        workflow.load_model_zip(zip_path)
    except FileNotFoundError as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format('"model.zip"'))

    return ResponseUtil.ok_response()


# TODO: optimize this function 
def upload_analysis(request, exc):
    """
    Allow to upload the analysis zip to run the simulation in the frontend, 
    or the results job zip file can be uploaded and then the analysis process
    will be executed over the uploaded results files once the uploaded zip 
    is validated.  
    """
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
    logger.info(LOG_ACTION.format(user, 'uploading analysis to %s' % workflow))

    for uploaded_file in uploaded_files: 
        uploaded_file_path = os.path.join(workflow.get_tmp_dir(), 
                                          uploaded_file.name)
        with open(uploaded_file_path, 'wb') as fd:
            if uploaded_file.multiple_chunks(chunk_size=4096):
                for chunk in uploaded_file.chunks(chunk_size=4096):
                    fd.write(chunk)
            else:
                fd.write(uploaded_file.read())

    try:
        analysis_zip = validate_archive(uploaded_file_path)
    except InvalidSign:
        return ResponseUtil.ko_response(messages.INVALID_SIGNATURE.format(f'"{uploaded_file.name}"'))
    except InvalidArchiveError:
        return ResponseUtil.ko_response(messages.INVALID_FILE.format(f'"{uploaded_file.name}"'))
    try:        
        shutil.unpack_archive(analysis_zip, workflow.get_tmp_dir())
        
        try:
            os.remove(os.path.join(workflow.get_tmp_dir(), os.path.split(analysis_zip)[1]))
        except FileNotFoundError:
            # go haed if file is not found
            pass

        tmp_dir_list = os.listdir(workflow.get_tmp_dir())
        if len(tmp_dir_list) > 1:            
            # if uploaded zip has more then one file it means that it is a job results zip
            for f in tmp_dir_list:
                shutil.move(os.path.join(workflow.get_tmp_dir(), f),
                            workflow.get_results_dir())
            # and then run the analisys
            return run_analysis(request, exc)

        else:
            # otherwise check if it has the required folders to run the simulation 
            unzip_dir_path = os.path.join(workflow.get_tmp_dir(), tmp_dir_list[0])
            simulation_folder_list = ['mechanisms', 'morphology', 'checkpoints']
            if all([folder in os.listdir(unzip_dir_path) for folder in simulation_folder_list]):
                shutil.move(unzip_dir_path, workflow.get_analysis_dir())
        
        return ResponseUtil.ok_response('')

    except Exception as e:
        print(e)
        logger.error(e)

    return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format(f'"{uploaded_file.name}"'))


def upload_files(request, exc):
    """
    Allow to upload some model's file and to write it in the
    model used by the current workflow.

    The accepted files are one of the following type: 
    morphology, mechanisms, features, protocols and parameters.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')

    workflow, user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(user, 'uploading file to %s' % workflow))

    folder = request.POST.get('folder')
    uploaded_file = request.FILES.get('file')

    # store the uploaded file
    full_path = os.path.join(workflow.get_model_dir(), folder, uploaded_file.name)
    with open(full_path, 'wb') as fd:
        if uploaded_file.multiple_chunks(chunk_size=4096):
            for chunk in uploaded_file.chunks(chunk_size=4096):
                fd.write(chunk)
        else:
            fd.write(uploaded_file.read())

    try:
        if folder == 'morphology/':
            workflow.get_model().set_morphology(full_path)
            with open(os.path.join(workflow.get_model_dir(), 'config', 'morph.json'), 'w') as fd:
                json.dump(workflow.get_model().get_morphology().get_config(), fd)

        elif folder == 'mechanisms/':
            if not uploaded_file.name.endswith('.mod'):
                return ResponseUtil.ko_response('Mechanisms must be "<b>.mod</b>" file.')

        elif folder == 'config/':
            if not uploaded_file.name in ['features.json', 'protocols.json', 'parameters.json']:
                os.remove(full_path)
                return ResponseUtil.ko_response(
                    'Config file must be one of the fallowing files:<br>\
                    "<b>protocols.json</b>", "<b>features.json</b>", <b>"parameters.json</b>"'
                )    
            validate_json_file(full_path)
    
    except InvalidMorphologyFile as e:
        os.remove(full_path)
        return ResponseUtil.ko_response('<b>File Format Error</b><br><br>' + str(e))
    
    except json.decoder.JSONDecodeError as e:
        os.remove(full_path)    
        return ResponseUtil.ko_response('<b>JSON Decode Error:</b><br><br>' + str(e) + '.')

    return ResponseUtil.ok_response('')


def download_files(request, exc):
    """
    This download API can works in two different ways depending
    on wich parameter is passed through the GET request. 

    If the key "pack" is found in the GET request, then an archive zip 
    will be downloaded depends on what the relative value is. The accepted
    "pack" values are:
    "model": that allows to download the whole model in the workflow,
    "results": that allows to dowload the all results of a downloaded job,
    "analysis": that allows to download the files that are required by the
                blue naas to run the simulation.
    
    Otherwise the key "file_list" can be used to download a list of files 
    instead of a whole package.
    """

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, user = get_workflow_and_user(request, exc)
    WorkflowUtil.set_model_key(workflow)

    pack = request.GET.get('pack')
    file_list = request.GET.get('file_list')

    if pack:
        logger.info(LOG_ACTION.format(user, 'downloading %s from %s' % (pack, workflow)))
        if pack == 'features':
            arch_file = WorkflowUtil.make_features_archive(workflow)
            return ResponseUtil.file_response(arch_file)
        
        elif pack == 'model':
            arch_file = WorkflowUtil.make_model_archive(workflow)
        elif pack == 'results':
            arch_file = WorkflowUtil.make_results_archive(workflow)
        elif pack == 'analysis':
            arch_file = WorkflowUtil.make_analysis_archive(workflow)

        return ResponseUtil.file_response(get_signed_archive(arch_file))

    elif file_list:
        logger.info(LOG_ACTION.format(user, 'download %s from %s' % (file_list, workflow)))
        path_list = json.loads(file_list).get('path')

        files = [os.path.join(workflow.get_model_dir(), f) for f in path_list]
        arch_name = workflow.get_id() + '_model_files.zip'
        
        try:
            arch_file = WorkflowUtil.make_archive(workflow, arch_name, 'files', files)
        except PermissionError as e:
            logger.error(e)
            return ResponseUtil.ko_response(messages.CRITICAL_ERROR)
        except FileNotFoundError as e:
            logger.error(e)
            return ResponseUtil.ko_response(str(e))

        return ResponseUtil.file_response(arch_file)
    
    return ResponseUtil.ko_response(messages.NO_FILE_TO_DOWNLOAD)


def delete_files(request, exc):
    """
    Allows to delete a list of files from the current workflow.
    """
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    file_list = json.loads(request.body).get('file_list')

    if file_list and len(file_list) <= 0:
        return ResponseUtil.ok_response(messages.NO_FILE_TO_DELETE)
    
    workflow, user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(user, 'deleting %s from %s' % (file_list, workflow)))

    for f in file_list:
        try:
            workflow.remove_file(f)
        except PermissionError as e:
            logger.error(e)
            return ResponseUtil.ko_response(messages.CRITICAL_ERROR)
    
    return ResponseUtil.ok_json_response()


def optimization_settings(request, exc=None):
    """
    The GET method allows to fetch the json object containing the
    workflow optimization settings.

    The POST method allows to write the optimization settings for
    the current workflow.
    If the NSG credentials are passed, they are checked if work before
    to store them in the current session instead of store them 
    in the optimization settings file.

    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, hhnb_user = get_workflow_and_user(request, exc)
    
    if request.method == 'GET':
        logger.info(LOG_ACTION.format(hhnb_user, 'get optimization settings from %s' % workflow))
        settings = {'settings': {}, 'service-account': {}}
        
        # fetch service account hpc and projects
        settings.update(json.loads(get_service_account_content(request).content))

        try:
            settings['settings'].update(workflow.get_optimization_settings())
            return ResponseUtil.ok_json_response(settings)
        except FileNotFoundError as e:
            return ResponseUtil.ok_json_response(settings)

    elif request.method == 'POST':
        logger.info(LOG_ACTION.format(hhnb_user, 'set optimization settings from %s' % workflow))
        optimization_settings = json.loads(request.body)

        if optimization_settings['hpc'] == 'NSG':
            nsg_username = optimization_settings.get('username_submit')
            nsg_password = optimization_settings.get('password_submit')

            if nsg_username and nsg_password:
                nsg_user = NsgUser(nsg_username, nsg_password)
                
                # override nsg credentials 
                if not nsg_user.validate_credentials():
                    optimization_settings.update({
                        'username_submit': False,
                        'password_submit': False
                    })
                else:
                    optimization_settings.update({
                        'username_submit': True,
                        'password_submit': True
                    })
                    request.session['nsg_username'] = nsg_username
                    request.session['nsg_password'] = nsg_password
                    request.session.save()
                        
        workflow.set_optimization_settings(optimization_settings)

        if optimization_settings['hpc'] == 'NSG':
            if not optimization_settings['username_submit'] and not optimization_settings['password_submit']:
                return ResponseUtil.ko_response(messages.AUTHENTICATION_INVALID_CREDENTIALS)

        return ResponseUtil.ok_json_response()

    else:
        return ResponseUtil.method_not_allowed()


def run_optimization(request, exc):
    """
    Execute the optimization by submitting the job to the HPC system
    according to the stored optimization settings of the current 
    workflow.
    """
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(hhnb_user, 'run optimization of %s' % workflow))
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

    try:
        response = JobHandler.submit_job(hhnb_user, zip_file, optimization_settings)
    except JobHandler.HPCException as e:
        return ResponseUtil.ko_response(str(e))
    if response.status_code == 200:
        workflow.set_optimization_settings(optimization_settings, job_submitted_flag=True)
    return response


def reoptimize_model(request, exc):
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    data = request.POST.dict()

    user = HhnbUser.get_user_from_request(request)
    try:
        response = JobHandler.reoptimize_model(data, user)
    except:
        return ResponseUtil.ko_response("<b>Something went wrong !</b>")

    return response


def fetch_jobs(request, exc):
    """
    Fetch all the jobs from the selected HPC system passed through
    the GET request data.
    """
    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    hpc = request.GET.get('hpc')
    sa_hpc = request.GET.get('saHPC')
    sa_project = request.GET.get('saProject')

    if not hpc:
        return ResponseUtil.ko_response(messages.NO_HPC_SELECTED)

    _, hhnb_user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(hhnb_user, 'fetch all %s jobs' % hpc))

    try:
        data = JobHandler.fetch_jobs_list(hpc, hhnb_user, sa_hpc, sa_project)
        return ResponseUtil.ok_json_response(data)
    except JobHandler.ServiceAccountException as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.JOB_FETCH_ERROR.format('SERVICE ACCOUNT'))
    except JobHandler.UnicoreClientException as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.JOB_FETCH_ERROR.format('DAINT-CSCS'))
    except JobHandler.HPCException as e:
        logger.error(e)
        return ResponseUtil.ko_response(str(f'<b>{e}</b>'))

    except Exception as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.CRITICAL_ERROR)


def fetch_job_results(request, exc):
    """
    Download all the results files of the job id, from the HPC system
    to the current workflow.
    """

    if exc not in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    job_id = request.GET.get('job_id')
    hpc = request.GET.get('hpc')
    sa_hpc = request.GET.get('saHPC')
    sa_project = request.GET.get('saProject')

    if not hpc:
        return ResponseUtil.ko_response(messages.NO_HPC_SELECTED)
    if not job_id:
        return ResponseUtil.ko_response(messages.NO_JOB_SELECTED)

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(
        hhnb_user, 'download result for job: %s in %s' % (job_id, workflow)
    ))

    try:
        file_list = JobHandler.fetch_job_files(hpc, job_id, hhnb_user, sa_hpc, sa_project)
        WorkflowUtil.download_job_result_files(workflow, file_list)

        return ResponseUtil.ok_response()

    except JobHandler.JobsFilesNotFound as e:
        logger.error(e)
        return ResponseUtil.ko_response(str(e))

    except Exception as e:
        logger.error(e)

    return ResponseUtil.ko_response(messages.JOB_RESULTS_FETCH_ERRROR)


def run_analysis(request, exc):
    """
    Execute the analysis process for the results job present in the
    current workflow.
    """

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(hhnb_user, 'run analysis on %s' % workflow))

    try:
        for f in os.listdir(workflow.get_results_dir()):
            if 'output' in f:
                job_output = os.path.join(workflow.get_results_dir(), f)
        WorkflowUtil.run_analysis(workflow, job_output)
        return ResponseUtil.ok_response('')

    except MechanismsProcessError as e:
        logger.error(e)
        workflow.clean_analysis_dir()
        return ResponseUtil.ko_response(498, messages.MECHANISMS_PROCESS_ERROR)
    
    except AnalysisProcessError as e:
        logger.error(e)
        workflow.clean_analysis_dir()
        return ResponseUtil.ko_response(499, messages.ANALYSIS_PROCESS_ERROR.format(e))
    
    except FileNotFoundError as e:
        logger.error(e)
        workflow.clean_analysis_dir()
        return ResponseUtil.ko_response(404, str(e))       
     
    except Exception as e:
        logger.error(e)
        workflow.clean_analysis_dir()
    return ResponseUtil.ko_response(messages.ANALYSIS_ERROR)


def upload_to_naas(request, exc):
    """
    Upload the zip files containing all the required files to run the
    simulation in the blue naas application and if everything works
    without errors, it returns the link of the relative simulation.
    """

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, hhnb_user = get_workflow_and_user(request, exc)
    logger.info(LOG_ACTION.format(
        hhnb_user, 'uploading analysis of %s to naas' % workflow
    ))
    try:
        naas_archive = WorkflowUtil.make_naas_archive(workflow)
        naas_model = os.path.split(naas_archive)[1].split('.zip')[0]
    except Exception as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.ANALYSIS_ERROR)
    
    uploaded_naas_model = request.session[exc].get('naas_model')
    if uploaded_naas_model and uploaded_naas_model == naas_model: 
        return ResponseUtil.ok_response(naas_model)
    
    try:
        r = requests.post(url='https://blue-naas-svc-bsp-epfl.apps.hbp.eu/upload',
                          files={'file': open(naas_archive, 'rb')}, verify=False)
        if r.status_code == 200:
            request.session[exc]['naas_model'] = naas_model
            request.session.save()
            return ResponseUtil.ok_response(naas_model)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return ResponseUtil.ko_response(500, messages.BLUE_NAAS_NOT_AVAILABLE)

    return ResponseUtil.ko_response(r.status_code, r.content)


def get_model_catalog_attribute_options(request):
    """
    Returns the attribute options list required by the ModelCatalog.
    """
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')
    mc_username, mc_password = MODEL_CATALOG_CREDENTIALS
    try:
        mc = ModelCatalog(username=mc_username, password=mc_password)
        options = mc.get_attribute_options()
        return ResponseUtil.ok_json_response(options)
    except Exception as e:
        logger.error('get_model_catalog_attriute_options(): %s' % e)
        return ResponseUtil.ko_response(messages.GENERAL_ERROR)


def register_model(request, exc):
    """
    Store a new model in the ModelCatalog by setting all the required
    parameters and returns its relative link to the ModelCatalog.
    """
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

    logger.info(LOG_ACTION.format(
        hhnb_user, 'register model %s of %s' % (model_zip_name, workflow)
    ))

    try:
        if MODEL_CATALOG_CREDENTIALS == ('username', 'password'):
            logger.error('Invalid ModelCatalog credentials')
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

        model_path_on_mc = 'https://model-catalog.brainsimulation.eu/'\
                         + '#model_id.{}'.format(registered_model['id'])
        
        return ResponseUtil.ok_response(messages.MODEL_SUCCESSFULLY_REGISTERED.format(model_path_on_mc))

    except EbrainsDriveClientError as e:
        code = e.code
        message = e.message
        logger.error(e)
        return ResponseUtil.ko_response(code, message)

    except FileExistsError as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.MODEL_ALREADY_EXISTS)

    except EnvironmentError as e:
        logger.error(e)
        return ResponseUtil.ko_response(messages.MODEL_CATALOG_INVALID_CREDENTIALS)

    except Exception as e:
        logger.error(e)
        uploaded_model.delete()
        return ResponseUtil.ko_response(f'<b>Error !</b><br><br>{str(e)}')

    return ResponseUtil.ko_response(messages.GENERAL_ERROR)


def get_user_avatar(request):
    """
    Returns the user avatar image.
    """
    logger.debug('get_user_avatar() called')
    hhnb_user = HhnbUser.get_user_from_request(request)
    return ResponseUtil.raw_response(content=hhnb_user.get_user_avatar(),
                                     content_type='image/png',
                                     charset='UTF-8')


def get_user_page(request):
    """
    Redirect to the Ebrains user page.
    """
    hhnb_user = HhnbUser.get_user_from_request(request)
    return redirect(hhnb_user.get_ebrains_user().get_user_page())


def get_authentication(request):
    """
    Returns 200 if the stored NSG credential are valid or 400 if not.
    """
    logger.debug('get_authentication() called')
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
    """
    Loads the json that comes from the HippocampusHub, download all the
    files in it and then initialize a new workflow with all these files.
    """
    hhf_comm = json.loads(request.GET.get('hhf_dict')).get('HHF-Comm')
    logger.debug('got dictionary from HHF')
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
    """
    Returns the folder where the eTraces, from the HippocampusHub,
    have been downloaded.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')
    workflow, _ = get_workflow_and_user(request, exc)
    return ResponseUtil.ok_json_response({'hhf_etraces_dir': workflow.get_etraces_dir()})


def hhf_list_files_new(request, exc):
    """
    Returns a list of the all model files inside the workflow.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    
    workflow, _ = get_workflow_and_user(request, exc)
    model_files = WorkflowUtil.list_model_files(workflow)
    return ResponseUtil.ok_json_response(model_files)


# TODO: the functions below will be deprecated, use the above one
def hhf_list_files(request, exc):
    """
    Returns a list of the all model files inside the workflow.
    This API is deprecated, please use "hhf_list_files_new()".
    """
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
    """
    Returns a json with the content of the all files contained in the folder.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, user = get_workflow_and_user(request, exc)
    if not os.path.join(workflow.get_model_dir(), folder):
        return ResponseUtil.ko_response()

    folder = folder.split('Folder')[0]
    hhf_files_content = {}

    file_path = os.path.join(workflow.get_model_dir(), folder)
    for f in os.listdir(file_path):
        with open(os.path.join(file_path, f), 'r') as fd:
            if f.endswith('.json'):
                try:
                    jj = json.load(fd)
                    hhf_files_content[f] = json.dumps(jj, indent=8)
                except json.decoder.JSONDecodeError as e:
                    logger.warning(LOG_ACTION.format(user, 'JSON Decode error on file: "%s".' % os.path.join(file_path, f)))
                    fd.seek(0)
                    hhf_files_content[f] = fd.read()
            else:
                hhf_files_content[f] = fd.read()

    return ResponseUtil.ok_json_response(hhf_files_content)


def hhf_get_model_key(request, exc):
    """
    Returns the model global key of the current workflow.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, _ = get_workflow_and_user(request, exc)
    return ResponseUtil.ok_json_response({'model_key': workflow.get_model().get_key()})


def hhf_apply_model_key(request, exc):
    """
    Overwrite the model global key for the current workflow.
    """
    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()
    workflow, _ = get_workflow_and_user(request, exc)
    WorkflowUtil.set_model_key(workflow, key=request.POST.get('model_key'))
    return ResponseUtil.ok_response()


@csrf_exempt
def hhf_save_config_file(request, folder, config_file, exc):
    """
    Save the content of the "config_file" by overwriting it.
    """
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
        
        # automatically add empty distributions field in parameters.json
        if file_path.endswith('parameters.json'):
            fd = open(file_path, 'r')
            jj = json.load(fd)
            fd.close()

            # check if there is only the wf_id key
            if len(jj.keys()) == 1:
                main_key = list(jj.keys())[0]
                jj = jj[main_key]

            # check for distributions key and add an empty field if there isn't
            if not 'distributions' in jj.keys():
                jj.update({'distributions': {}})

            fd = open(file_path, 'w')
            json.dump({main_key: jj} if main_key else jj, fd)
            fd.close()

        return ResponseUtil.ok_response('')
    except json.JSONDecodeError:
        return ResponseUtil.ko_response(messages.MARLFORMED_FILE.format(config_file)) 
    except FileNotFoundError:
        return ResponseUtil.ko_response(404, messages.CRITICAL_ERROR)
    except Exception as e:
        print(str(e))
        return ResponseUtil.ko_response(400, messages.GENERAL_ERROR)


def hhf_load_parameters_template(request, exc):
    if request.method != 'POST':
        return ResponseUtil.method_not_allowed('POST')

    if not exc in request.session.keys():
        return ResponseUtil.no_exc_code_response()

    workflow, _ = get_workflow_and_user(request, exc)
    
    parameters_type = request.POST.get('type')
    if not parameters_type in ['pyramidal', 'interneuron']:
        return ResponseUtil.ko_response(f"Parameters type {parameters_type} unknown")

    WorkflowUtil.load_parameters_template(workflow, parameters_type)
    return ResponseUtil.ok_response()


def get_service_account_content(request):
    if request.method != 'GET':
        return ResponseUtil.method_not_allowed('GET')

    SERVICE_ACCOUNT_ROOT_URL = 'https://bspsa.cineca.it/'
    APP_CONTEXT_TAG = 'hhnb'

    sa_content = {'service-account': {}}

    try:
        r0 = requests.get(SERVICE_ACCOUNT_ROOT_URL + 'hpc/', timeout=30)
        r1 = requests.get(SERVICE_ACCOUNT_ROOT_URL + 'projects/', timeout=30)
        if r0.status_code == 200 and r1.status_code == 200:
            for hpc in r0.json():
                h = hpc['id']
                projects = []
                for p in r1.json():
                    if p['hpc'] == h and APP_CONTEXT_TAG in p['name']:
                        projects.append(p['name'])
                sa_content['service-account'].update({h: projects})
        
    except requests.RequestException as e:
        logger.error('Service-Account connection error: "%s".' % str(e))
        sa_content = {'service-account': False}

    return ResponseUtil.ok_json_response(sa_content, True)
