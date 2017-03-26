'''Views'''
import os
import urllib
from uuid import UUID
import sys, datetime, shutil, zipfile, pprint
import numpy, efel, neo
import matplotlib
matplotlib.use('Agg')
import requests
#requests.packages.urllib3.disable_warnings()
import json
import re
import logging
import bluepyextract as bpext

# import django libs
from django.http import JsonResponse
from django.shortcuts import render_to_response, render, redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.context import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# import local tools
from tools import manage_json
from tools import resources
from tools import manage_collab_storage

# if not in DEBUG mode
if not settings.DEBUG:
    from django.contrib.auth.decorators import login_required
    from django.contrib.auth import logout as auth_logout
    from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
    from bbp_client.oidc.client import BBPOIDCClient
    from bbp_client.document_service.client import Client as DocClient
    import bbp_client
    from bbp_client.client import *
    import bbp_services.client as bsc
else:
    def login_required(login_url=None):
        def decorator(f):
            return f
        return decorator

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
if not settings.DEBUG:
    accesslogger = logging.getLogger('efelg_access.log')
    accesslogger.addHandler(logging.FileHandler('/var/log/bspg/efelg_access.log'))
    accesslogger.setLevel(logging.DEBUG)


##### serve overview.html
@login_required(login_url='/login/hbp/')
@csrf_exempt
def overview(request):
    context = RequestContext(request, {'request':request, 'user':request.user})

    # if not in DEBUG mode check whether authentication token is valid
    if not settings.DEBUG:
        #
        context = request.GET.get('ctx')
        my_url = 'https://services.humanbrainproject.eu/idm/v1/api/user/me'
        headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
         
        res = requests.get(my_url, headers = headers)
        
        if res.status_code !=200:
            auth_logout(request)
            nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))
            return redirect('%s?next=%s' % (settings.LOGIN_URL, nextUrl))

        # get username from request
        username = request.user.username

        # get context and context uuid
        context_uuid = UUID(request.GET.get('ctx'))

        # get headers
        svc_url = settings.HBP_COLLAB_SERVICE_URL
        url = '%scollab/context/%s/' % (svc_url, context)
         
        # get collab_id
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            auth_logout(request)
            nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))
            return redirect('%s?next=%s' % (settings.LOGIN_URL, nextUrl))

        collab_id = res.json()['collab']['id']
        request.session['context'] = context
    else:
        username = 'test'
        headers = {}
        context = 'local'
        collab_id = -1

    # build data and json dir strings
    data_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data', 'efelg_rawdata')
    json_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'json_data')
    app_data_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data')  

    request.session['data_dir'] = data_dir
    request.session['json_dir'] = json_dir
    request.session['app_data_dir'] = app_data_dir
    # create folders for global data and json files if not existing
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    # save parameters in request.session
    request.session['username'] = username
    request.session['context'] = context
    request.session['headers'] = headers
    request.session['collab_id'] = collab_id
    request.session['authorized_data_list'] = []
    request.session["current_authorized_files"] = []

    # reading parameters from request.session
    username = request.session['username']
    context = request.session['context']
    
    # parameters for folder creation
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    # create global variables in request.session
    request.session['time_info'] = time_info

    # build local folder paths
    rel_result_folder = os.path.join('efel_gui', 'results')
    rel_uploaded_folder = os.path.join('efel_gui', 'uploaded')
    full_result_folder = os.path.join(settings.MEDIA_ROOT, 'efel_data', rel_result_folder)
    full_uploaded_folder = os.path.join(settings.MEDIA_ROOT, 'efel_data', rel_uploaded_folder)
    
    # build local folder complete paths
    rel_user_crr_results_folder = os.path.join(username, time_info)
    full_user_results_folder = os.path.join(full_result_folder, username)
    full_user_crr_results_folder = os.path.join(full_result_folder, rel_user_crr_results_folder)
    full_user_uploaded_folder = os.path.join(full_uploaded_folder, username)
    full_user_crr_res_res_folder = os.path.join(full_result_folder, username, time_info, 'u_res')
    full_user_crr_res_data_folder = os.path.join(full_result_folder, username, time_info, 'u_data')
    
    # build media relative result path
    media_rel_crr_user_res = os.path.join('media', 'efel_data', rel_result_folder, username, time_info, 'u_res')

    # storage relative path folder
    st_rel_user_results_folder = os.path.join(rel_result_folder, rel_user_crr_results_folder)
    st_rel_user_uploaded_folder = os.path.join(rel_uploaded_folder, username)
    
    # store paths in request.session
    request.session['media_rel_crr_user_res'] = media_rel_crr_user_res 
    request.session['st_rel_user_results_folder'] = st_rel_user_results_folder
    request.session['st_rel_user_uploaded_folder'] = st_rel_user_uploaded_folder
    request.session['full_user_crr_results_folder'] = full_user_crr_results_folder
    request.session['full_user_results_folder'] = full_user_results_folder
    request.session['full_user_crr_results_folder'] = full_user_crr_results_folder
    request.session['full_user_crr_res_res_folder'] = full_user_crr_res_res_folder
    request.session['full_user_crr_res_data_folder'] = full_user_crr_res_data_folder
    request.session['full_user_uploaded_folder'] = full_user_uploaded_folder
    
    # if not in DEBUG mode
    if not settings.DEBUG:
        accesslogger.info(resources.string_for_log('overview', request))

    # render to html 
    return render(request, 'efelg/overview.html')

    
##### serve select_features
@csrf_exempt
def select_features(request):
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    feature_names = efel.getFeatureNames()
    selected_traces_rest = request.POST.get('data')
    selected_traces_rest_json = json.loads(selected_traces_rest)
    request.session['selected_traces_rest_json'] = selected_traces_rest_json

    # if not in DEBUG mode
    if not settings.DEBUG:
        accesslogger.info(resources.string_for_log('select_features', request, page_spec_string = selected_traces_rest))
    
    return render(request, 'efelg/select_features.html')


# build .json files containing data and metadata
@login_required(login_url='/login/hbp')
def generate_json_data(request):
    data_dir = request.session['data_dir']
    json_dir = request.session['json_dir']
    all_files = os.listdir(data_dir)
    files_authorization = {}

    for name in all_files:
        if name.endswith('.abf'):
            fname = os.path.splitext(name)[0]
            metadata_file = os.path.join(data_dir, fname + '_metadata.json')
            if not os.path.isfile(metadata_file):
                continue
            else:
                outfilename = '____'.join(manage_json.get_cell_info(metadata_file)) + '.json'
                outfilepath = os.path.join(json_dir, outfilename)
                crr_file_auth_collab = manage_json.extract_authorized_collab(metadata_file)
                if outfilepath not in files_authorization:
                    #files_authorization[outfilepath] = crr_file_auth_collab
                    files_authorization[outfilename] = crr_file_auth_collab

                # if the .json file has not been created
                if not os.path.isfile(outfilepath):
                    data = manage_json.gen_data_struct(os.path.join(data_dir,name), metadata_file)
                    with open(outfilepath, 'w') as f:
                        json.dump(data, f)
    #
    app_data_dir = request.session['app_data_dir']
    file_auth_fullpath = os.path.join(app_data_dir, "files_authorization.json")
    with open(file_auth_fullpath, 'w') as fa:
        json.dump(files_authorization, fa)

    return HttpResponse("")


#####
@login_required(login_url='/login/hbp')
def show_traces(request):
    return render_to_response('efelg/show_traces.html')


##### retrieve the list of .json files to be displayed for trace selection
@login_required(login_url='/login/hbp')
def get_list(request):
    
    # final list of authorized files
    allfiles = []

    #retrieve data from session variables
    json_dir = request.session['json_dir']
    
    # extract the list of the collabs the current user belongs to
    my_collabs_url = "https://services.humanbrainproject.eu/collab/v0/mycollabs/"
    crr_auth_data_list = resources.user_collab_list(my_collabs_url, request.user.social_auth.get()) 

    # retrieve the file containing the authorizations for each data file
    app_data_dir = request.session['app_data_dir']
    file_auth_fullpath = os.path.join(app_data_dir, "files_authorization.json")
    with open(file_auth_fullpath) as f:
        files_auth = json.load(f)

    # for 
    for i in os.listdir(json_dir):
        crr_file_path = os.path.join(json_dir, i)
        logger.info(i)
        #if crr_file_path in files_auth:
        logger.info(files_auth.keys())
        if i in files_auth:
            #crr_file_auth = files_auth[crr_file_path]
            crr_file_auth = files_auth[i]
            logger.info(crr_file_auth)
            if any(j in crr_file_auth for j in crr_auth_data_list) or crr_file_auth[0]=="all":
                allfiles.append(i[:-5])

    request.session["current_authorized_files"] = allfiles 

    return HttpResponse(json.dumps(allfiles), content_type="application/json")


#####
@login_required(login_url='/login/hbp')
def get_data(request, cellname=""):
    json_dir = request.session['json_dir']
    full_user_uploaded_folder = request.session['full_user_uploaded_folder']
    current_authorized_files = request.session["current_authorized_files"]

    if cellname not in current_authorized_files:
        return HttpResponse("")
    
    if os.path.isfile(os.path.join(json_dir, cellname) + '.json'):
        cellname_path = os.path.join(json_dir, cellname) + '.json'
        
    elif os.path.isfile(os.path.join(full_user_uploaded_folder, cellname) + '.json'):
        cellname_path = os.path.join(full_user_uploaded_folder, cellname) + '.json'

    with open(cellname_path) as f:
        content = f.read()
    
    return HttpResponse(json.dumps(content), content_type="application/json")


#####
@login_required(login_url='/login/hbp')
@csrf_exempt
def extract_features(request):
    data_dir = request.session['data_dir']
    json_dir = request.session['json_dir']
    selected_traces_rest_json = request.session['selected_traces_rest_json'] 
    allfeaturesnames = efel.getFeatureNames()
    
    crr_user_folder = request.session['time_info'] 
    full_crr_result_folder = request.session['full_user_crr_res_res_folder']
    full_crr_uploaded_folder = request.session['full_user_uploaded_folder']
    full_crr_data_folder = request.session['full_user_crr_res_data_folder']
    full_crr_user_folder = request.session['full_user_crr_results_folder']
    
    check_features = request.POST.getlist('crr_feature_check_features')
    request.session['selected_features'] = check_features 
    cell_dict = {}
    selected_traces_rest = []
    
    for k in selected_traces_rest_json:
        #crr_vcorr = selected_traces_rest_json[k]['vcorr']
        crr_file_rest_name = k + '.json'
        crr_name_split = k.split('____')
        crr_cell_name = crr_name_split[5]
        crr_sample_name = crr_name_split[6]
        crr_key = crr_name_split[0] + '____' + crr_name_split[1] + '____' + crr_name_split[2] + '____' + crr_name_split[3] + '____' + crr_name_split[4] +  '____' + crr_name_split[5]
        if os.path.isfile(os.path.join(json_dir, crr_file_rest_name)):
            crr_json_file = os.path.join(json_dir, crr_file_rest_name)
        elif os.path.isfile(os.path.join(full_crr_uploaded_folder, crr_file_rest_name)):
            crr_json_file = os.path.join(full_crr_uploaded_folder, crr_file_rest_name)
        else:
            continue

        with open(crr_json_file) as f:
            crr_file_dict_read = f.read()

        crr_file_dict = json.loads(crr_file_dict_read)
        crr_file_all_stim = crr_file_dict['traces'].keys()
        crr_file_sel_stim = selected_traces_rest_json[k]['stim']
        
        #
        if crr_key in cell_dict:
            cell_dict[crr_key]['stim'].append(crr_file_sel_stim)
            cell_dict[crr_key]['files'].append(k)
            #cell_dict[crr_key]['vcorr'].append(float(crr_vcorr))
        else:
            cell_dict[crr_key] = {}
            cell_dict[crr_key]['stim'] = [crr_file_sel_stim]
            cell_dict[crr_key]['files'] = [k]
            cell_dict[crr_key]['cell_name'] = crr_cell_name
            cell_dict[crr_key]['all_stim'] = crr_file_all_stim
            #cell_dict[crr_key]['vcorr'] = [float(crr_vcorr)]
    
    target = []
    final_cell_dict = {}  
    final_exclude = []
    for key in cell_dict:
        crr_el = cell_dict[key]
        #v_corr = crr_el['vcorr']
        v_corr = 0
        for c_stim_el in crr_el['stim']:
            [target.append(float(i)) for i in c_stim_el if float(i) not in target]
        exc_stim_lists = [list(set(crr_el['all_stim']) - set(sublist)) for sublist in crr_el['stim']]
        crr_exc = []
        for crr_list in exc_stim_lists:
            crr_stim_val = [float(i) for i in crr_list]
            crr_exc.append(crr_stim_val)
        final_cell_dict[cell_dict[key]['cell_name']] = {'v_corr':v_corr, 'ljp':0, 'experiments':{'step': {'location':'soma', 'files': [str(i) for i in crr_el['files']]}}, 'etype':'etype', 'exclude':crr_exc}

    # build configuration dictionary
    config = {}
    config['features'] = {'step':[str(i) for i in check_features]}
    config['path'] = json_dir + os.sep
    config['format'] = 'ibf_json'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {'relative': False, 'tolerance': 0.02, 'target': target, 'delay': 500, 'nanmean': False}

    extractor = bpext.Extractor(full_crr_result_folder, config)
    extractor.create_dataset()
    extractor.plt_traces()
    extractor.extract_features()
    extractor.mean_features()
    extractor.plt_features()
    extractor.feature_config_cells()
    extractor.feature_config_all()

    crr_result_folder = request.session['time_info']
    output_path = os.path.join(full_crr_user_folder, crr_user_folder + '_results.zip')
    request.session['result_file_zip'] = output_path
    request.session['result_file_zip_name'] = crr_user_folder + '_results.zip'
    parent_folder = os.path.dirname(full_crr_result_folder)
    contents = os.walk(full_crr_result_folder)
    try:
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(parent_folder + os.sep, '')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(parent_folder + os.sep, '')
                zip_file.write(absolute_path, relative_path)
    except IOError as message:
        print(message)
        sys.exit(1)
    except OSError as message:
        print(message)
        sys.exit(1)
    except zip_file.BadZipfile as message:
        print(message)
        sys.exit(1)
    finally:
        zip_file.close()

    accesslogger.info(resources.string_for_log('extract_features', request, page_spec_string = '___'.join(check_features)))
    return render(request, 'efelg/extract_features.html') 


#####
@login_required(login_url='/login/hbp')
def download_zip(request):
    # if not in DEBUG mode
    if not settings.DEBUG:
        accesslogger.info(resources.string_for_log('download_zip', request))
    result_file_zip = request.session['result_file_zip']
    result_file_zip_name = request.session['result_file_zip_name']
    zip_file = open(result_file_zip, 'rb')
    response = HttpResponse(zip_file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % result_file_zip_name
    return response


#####
@login_required(login_url='/login/hbp')
def features_dict(request):
    '''Render the feature dictionary containing all feature names, grouped by feature type'''
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return HttpResponse(json.dumps(features_dict))


#####
@login_required(login_url='/login/hbp')
def _reverse_url(view_name, context_uuid):
    """generate an URL for a view including the ctx query param"""
    return '%s?ctx=%s' % (reverse(view_name), context_uuid)


#####
@login_required(login_url='/login/hbp')
def features_json(request):
    full_user_crr_res_res_folder = request.session['full_user_crr_res_res_folder']
    with open(os.path.join(full_user_crr_res_res_folder, 'features.json')) as json_file:
        features_json = json.load(json_file) 
    return HttpResponse(json.dumps(features_json))


#####
@login_required(login_url='/login/hbp')
def features_json_path(request):
    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'features.json')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, full_feature_json_file)}))


#####
@login_required(login_url='/login/hbp')
def protocols_json_path(request):
    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'protocols.json')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, full_feature_json_file)}))


#####
@login_required(login_url='/login/hbp')
def features_pdf_path(request):
    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'features_step.pdf')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, full_feature_json_file)}))


#####
@login_required(login_url='/login/hbp')
@csrf_exempt
def upload_files(request):
    """
    Upload file to local folder
    """
    full_user_uploaded_folder = request.session['full_user_uploaded_folder']
    if not os.path.exists(full_user_uploaded_folder):
        os.makedirs(full_user_uploaded_folder)
    
    user_files = request.FILES.getlist('user_files')

    # list of modified names of uploaded files
    name_abf_list = []
    
    # list of uploaded json file names
    name_json_list = []
    
    # list of uploaded files full paths
    names_full_path = []

    data_name_dict = {"all_json_names" : []}
    
    #for every files to be uploaded, save them on local folders:
    for k in user_files:
        if not k.name.endswith('.abf'):
            continue
        crr_file_name = k.name
        crr_file_name = re.sub('-', '_', k.name)
        crr_local_filename = os.path.join(full_user_uploaded_folder, crr_file_name)

        # if file exists delete and recreate it
        if os.path.isfile(crr_local_filename):
            os.remove(crr_local_filename)
        final_file = open(crr_local_filename, 'w')
        
        # save chunks or entire file based on dimensions
        if k.multiple_chunks():
            for chunk in k.chunks():
                final_file.write(chunk)
            final_file.close()
        else:
            final_file.write(k.read())
            final_file.close()

        # 
        if resources.check_file_validity(crr_local_filename):
            name_abf_list.append(crr_file_name) 
            names_full_path.append(crr_local_filename)
        else:
            os.remove(crr_local_filename)
            

    #  
    all_authorized_files = request.session["current_authorized_files"]
    for name in names_full_path:
        outfilename = '____'.join(manage_json.get_cell_info(name, upload_flag = True)) + '.json'
        outfilepath = os.path.join(full_user_uploaded_folder, outfilename)

        data = manage_json.gen_data_struct(name, "",  upload_flag = True)
        if os.path.isfile(outfilepath):
            os.remove(outfilepath)        
        with open(outfilepath, 'w') as f:
            json.dump(data, f)
        if outfilename[:-5] not in data_name_dict['all_json_names']:
            data_name_dict['all_json_names'].append(outfilename[:-5])
            all_authorized_files.append(outfilename[:-5])
    
    request.session["current_authorized_files"] = all_authorized_files

    accesslogger.info(resources.string_for_log('upload_files', request, page_spec_string = str(len(names_full_path))))

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json") 


@login_required(login_url='/login/hbp')
def get_directory_structure(request):
    """ 
    Creates a nested dictionary that represents the folder structure of rootdir
    """
    # if not in DEBUG mode
    if not settings.DEBUG:
        accesslogger.info(resources.string_for_log('get_directory_structure', request))
    rootdir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data')
    media_dir_dict = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1 
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    with open(os.path.join(settings.BASE_DIR, 'static', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return HttpResponse(json.dumps(features_dict))




########### handle file upload to storage collab
def upload_zip_file_to_storage(request):

    # if not in DEBUG mode, save files in the collab storage
    if not settings.DEBUG:
        access_token = get_access_token(request.user.social_auth.get())
        # retrieve data from request.session
        headers = request.session['headers']
        collab_id = request.session['collab_id']

        st_rel_user_results_folder = request.session['st_rel_user_results_folder']
        st_rel_user_uploaded_folder = request.session['st_rel_user_uploaded_folder']
        storage_root = request.session['storage_root']
        access_token = request.session['access_token']
        crr_user_folder = request.session['time_info'] 
        output_path = request.session['result_file_zip']
        context = request.session['context']

	services = bsc.get_services()
    
    	# get clients from bbp python packages
    	oidc_client = BBPOIDCClient.bearer_auth(services['oidc_service']['prod']['url'], access_token)
    	bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    	doc_client = DocClient(services['document_service']['prod']['url'], oidc_client)


        context = request.session['context']
        auth_logout(request)
        nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))
        #return redirect('%s?next=%s' % (settings.LOGIN_URL, nextUrl))



        # extract project from collab_id
        project = doc_client.get_project_by_collab_id(collab_id)
        
        # extract collab storage root path
        storage_root = doc_client.get_path_by_id(project["_uuid"])
        crr_collab_storage_folder = os.path.join(storage_root, st_rel_user_results_folder)
        if not doc_client.exists(crr_collab_storage_folder):
            doc_client.makedirs(crr_collab_storage_folder)

        # final zip collab storage path
        zip_collab_storage_path = os.path.join(crr_collab_storage_folder, crr_user_folder + '_results.zip')

        # bypassing uploading data to collab storage
        if not doc_client.exists(zip_collab_storage_path):
            doc_client.upload_file(output_path, zip_collab_storage_path) 

    # render to html page
    return HttpResponse("") 
