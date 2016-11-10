'''Views'''

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, render, redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django import forms
from django.http import HttpResponse
#from django.core.context_processors import csrf
from uuid import UUID
from markdown import markdown
import os, time, sys, datetime,bleach, shutil, zipfile, zlib
from math import trunc
import numpy, efel, neo
import matplotlib
matplotlib.use('Agg')
import requests
requests.packages.urllib3.disable_warnings()
import json
import re
from . import manage_json
from . import manage_collab_storage

sys.path.append(os.path.join(settings.BASE_DIR, 'BluePyExtract'))
from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
from bbp_client.oidc.client import BBPOIDCClient
from bbp_client.document_service.client import Client as DocClient
import bbp_client
from bbp_client.client import *
import bbp_services.client as bsc
import bluepyextract as bpext
import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def ibf(request):
    return redirect("http://joomla.pa.ibf.cnr.it")

@login_required(login_url='/login/hbp')
@csrf_exempt
def overview(request):
    #request.session.flush()
    logger.info('username ' + request.user.username)
    data_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'app_data')
    json_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'json_data')
    
    request.session['data_dir'] = data_dir
    request.session['json_dir'] = json_dir

    # create folder for global data and json files if not existing
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    # get username from request
    username = request.user.username

    # get context and context uuid
    context_uuid = UUID(request.GET.get('ctx'))
    context = request.GET.get('ctx')
    logger.info("request")
    #logger.info(get_auth_header(request.user.social_auth.get()))
    # get headers
    svc_url = settings.HBP_COLLAB_SERVICE_URL
    url = '%scollab/context/%s/' % (svc_url, context)
    headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    logger.info(headers)
    
    # get collab_id
    res = requests.get(url, headers=headers)
    collab_id = res.json()['collab']['id']

    # save parameters in request.session
    request.session['username'] = username
    request.session['context'] = context
    request.session['headers'] = headers
    request.session['collab_id'] = collab_id
    # render to html 
    return render(request, 'efelg/overview.html')

    
@csrf_exempt
def select_features(request):
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    selected_traces = request.POST.getlist('check_traces')
    request.session['selected_traces'] = selected_traces
    feature_names = efel.getFeatureNames()
    selected_traces_rest = request.POST.get('data')
    selected_traces_rest_json = json.loads(selected_traces_rest)
    request.session['selected_traces_rest_json'] = selected_traces_rest_json
    
    return render(request, 'efelg/select_features.html', {'feature_names': feature_names, 'features_dict': features_dict})


@login_required(login_url='/login/hbp')
@csrf_exempt
def upload_files_page(request):
    return render(request, 'upload_files_page.html')

@login_required(login_url='/login/hbp')
def select_files_tree(request):
    data_dir = request.session['data_dir']
    json_dir = request.session['json_dir']
    for root, dirs, files in os.walk(data_dir):
        for name in files:
            if name.endswith('.abf'):
                infilepath = os.path.join(root, name)
                outfilename = '_'.join(manage_json.getCellInfo(infilepath)) + '.json'
                outfilepath = os.path.join(json_dir, outfilename)
                
                if not os.path.isfile(outfilepath):
                    data = manage_json.genDataStruct(infilepath)

                    with open(outfilepath, 'w') as f:
                        json.dump(data, f)
    return HttpResponse("")

@login_required(login_url='/login/hbp')
def show_traces(request):
    return render_to_response('efelg/show_traces.html')



@login_required(login_url='/login/hbp')
def get_list(request):
    json_dir = request.session['json_dir']
    allfiles = [f[:-5] for f in os.listdir(json_dir) if f.endswith('.json')]
    
    return HttpResponse(json.dumps(allfiles), content_type="application/json")

@login_required(login_url='/login/hbp')
def get_data(request, cellname=""):
    json_dir = request.session['json_dir']
    full_user_uploaded_folder = request.session['full_user_uploaded_folder']
    

    if os.path.isfile(os.path.join(json_dir, cellname) + '.json'):
        cellname_path = os.path.join(json_dir, cellname) + '.json'
    #elif os.path.isfile(os.path.join(full_crr_uploaded_folder, cellname) + '.json'):
    #    cellname_path = os.path.join(full_crr_uploaded_folder, cellname) + '.json'
    elif os.path.isfile(os.path.join(full_user_uploaded_folder, cellname) + '.json'):
        cellname_path = os.path.join(full_user_uploaded_folder, cellname) + '.json'

    with open(cellname_path) as f:
        content = f.read()
    
    return HttpResponse(json.dumps(content), content_type="application/json")

# handle select_traces template
@login_required(login_url='/login/hbp')
def select_traces(request):
    temp = []
    all_trace_dict = {}
    all_trace_plt = {}
    etype = request.session.get('etype')
    all_post = request.POST.getlist('check_files')
    all_name_list = request.session.get('all_name_list', False)
    data_dir = request.session.get('data_dir', False)
    for crr_file in all_post:
        all_stim = []
        crr_file_full = join(data_dir, crr_file)
        crr_etype = [i for i in etype if crr_file_full.find(i)]
        if not os.path.isfile(crr_file_full):
            continue
        r = neo.io.AxonIO(crr_file_full)
        bl = r.read_block(lazy = False, cascade = True)
        all_trace_dict[crr_file] = []

        # extract current amplitudes from files
        for i_seg, seg in enumerate(bl.segments):
            voltage = numpy.array(seg.analogsignals[0]).astype(numpy.float64)
            current = numpy.array(seg.analogsignals[1]).astype(numpy.float64)
            dt = 1./int(seg.analogsignals[0].sampling_rate) * 1e3
            t = numpy.arange(len(voltage)) * dt
            # when does voltage change
            c_changes = numpy.where( abs(numpy.gradient(current, 1.)) > 0.0 )[0]
            # detect on and off of current
            c_changes2 = numpy.where( abs(numpy.gradient(c_changes, 1.)) > 10.0 )[0]
            ion = c_changes[c_changes2[0]]
            ioff = c_changes[-1]
            ton = ion * dt
            toff = ioff * dt
            # estimate hyperpolarization current
            hypamp = numpy.mean( current[0:ion] )
            # 10% distance to measure step current
            iborder = int((ioff-ion)*0.1)
            # depolarization amplitude
            amp = numpy.mean( current[ion+iborder:ioff-iborder] )
            #
            amp_round = numpy.around(amp, decimals=3)
            #
            amp_form = "{0:.2f}".format(amp_round)
            # extract current amplitude from file - end
            all_trace_dict[crr_file].append(amp_form)
            #
            all_trace_plt[crr_file+'_'+amp_form] = []
            all_trace_plt[crr_file+'_'+amp_form].append(voltage.tolist())
    #
    request.session['all_trace_dict'] = all_trace_dict
    # create dictionary for all cell type
    all_trace_plt = json.dumps(all_trace_plt)
    return render_to_response('select_traces.html', {'all_trace_dict': all_trace_dict, 'all_trace_plt': all_trace_plt, 'temp_var': all_post})

@login_required(login_url='/login/hbp')
@csrf_exempt
def extract_features_rest(request):
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
    etype = request.session['etype']
    request.session['selected_features'] = check_features 
    cell_dict = {}
    selected_traces_rest = []
    
    for k in selected_traces_rest_json:
        crr_file_rest_name = k + '.json'
        crr_name_split = k.split('_')
        crr_cell_name = crr_name_split[5]
        crr_sample_name = crr_name_split[6]
        crr_key = crr_name_split[0] + '_' + crr_name_split[1] + '_' + crr_name_split[2] + '_' + crr_name_split[3] + '_' + crr_name_split[4] +  '_' + crr_name_split[5]
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
        crr_file_sel_stim = selected_traces_rest_json[k]
        crr_abf_file_path = crr_file_dict['abfpath']
        logger.info('crr_abf_file_path')
        logger.info(crr_abf_file_path)
        crr_abf_name_ext = os.path.basename(crr_abf_file_path)

        crr_cell_data_folder = os.path.join(full_crr_data_folder, crr_cell_name)
        if not os.path.exists(crr_cell_data_folder):
            os.makedirs(crr_cell_data_folder)
        if not os.path.isfile(os.path.join(crr_cell_data_folder, crr_abf_name_ext)):
            shutil.copy(crr_abf_file_path, crr_cell_data_folder)

        if crr_key in cell_dict:
            cell_dict[crr_key]['stim'].append(crr_file_sel_stim)
            cell_dict[crr_key]['files'].append(crr_sample_name)
        else:
            cell_dict[crr_key] = {}
            cell_dict[crr_key]['stim'] = [crr_file_sel_stim]
            cell_dict[crr_key]['files'] = [crr_sample_name]
            cell_dict[crr_key]['cell_name'] = crr_cell_name
            cell_dict[crr_key]['all_stim'] = crr_file_all_stim
   
    final_cell_dict = {}  
    for key in cell_dict:
        crr_el = cell_dict[key]
        all_ch_stim = [item for sublist in crr_el['stim'] for item in sublist]
        crr_diff_stim = list(set(crr_el['all_stim']) - set(all_ch_stim))
        crr_exc = [float(i) for i in crr_diff_stim]
        final_cell_dict[cell_dict[key]['cell_name']] = {'v_corr':False, 'ljp':0, 'experiments':{'step': {'location':'soma', 'files': [str(i) for i in crr_el['files']]}}, 'etype':'etype', 'exclude':list(set(crr_exc))}
        
    # build configuration dictionary
    config = {}
    config['features'] = {'step':[str(i) for i in check_features]}
    config['path'] = full_crr_data_folder
    config['format'] = 'axon'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {'relative': False, 'tolerance': 0.02, 'target': [-1.0, -0.8, -0.6, -0.4, -0.2, 0.2, 0.4, 0.6, 0.8, 1.0], 'delay': 500, 'nanmean': False}

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
            # Include all subfolders, including empty ones.
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

    # save files in the collab storage
    st_rel_user_results_folder = request.session['st_rel_user_results_folder']
    st_rel_user_uploaded_folder = request.session['st_rel_user_uploaded_folder']
    storage_root = request.session['storage_root']
    access_token = request.session['access_token']
    doc_client = manage_collab_storage.create_doc_client(access_token)
    crr_collab_storage_folder = os.path.join(storage_root, st_rel_user_results_folder)
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    logger.info("starting manipulating collab storage")
    if not doc_client.exists(crr_collab_storage_folder):
        doc_client.makedirs(crr_collab_storage_folder)
    # final zip collab storage path
    zip_collab_storage_path = os.path.join(crr_collab_storage_folder, crr_user_folder + '_results.zip')
    if not doc_client.exists(zip_collab_storage_path):
        doc_client.upload_file(output_path, zip_collab_storage_path) 
    #doc_client.mkdir(os.path.join(storage_root, 'temptestfolder'))
    #shutil.copy(os.path.join(full_crr_result_folder, 'features_step.pdf'), os.path.join(settings.BASE_DIR, 'static'))
    #shutil.copy(os.path.join(full_crr_result_folder, 'protocols.json'), os.path.join(settings.BASE_DIR, 'static'))
    #shutil.copy(os.path.join(full_crr_result_folder, 'features.json'), os.path.join(settings.BASE_DIR, 'static'))
    return render(request, 'efelg/extract_features_rest.html') 


@login_required(login_url='/login/hbp')
def download_zip(request):
    result_file_zip = request.session['result_file_zip']
    result_file_zip_name = request.session['result_file_zip_name']
    zip_file = open(result_file_zip, 'rb')
    response = HttpResponse(zip_file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % result_file_zip_name
    return response

@login_required(login_url='/login/hbp')
def access(request):
	return render(request, 'access.html') 



@login_required(login_url='/login/hbp')
def features_dict(request):
    '''Render the feature dictionary containing all feature names, grouped by feature type'''
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return HttpResponse(json.dumps(features_dict))

@login_required(login_url='/login/hbp')
def edit(request):
    '''Render the wiki edit form using the provided context query parameter'''

    #context = UUID(request.GET.get('ctx'))
    # get or build the wiki page
    return render(request, 'edit.html')

@login_required(login_url='/login/hbp')
def _reverse_url(view_name, context_uuid):
    """generate an URL for a view including the ctx query param"""
    return '%s?ctx=%s' % (reverse(view_name), context_uuid)


@login_required(login_url='/login/hbp')
def select_all_features(request):
    '''Render the feature dictionary containing all feature names, grouped by feature type'''
    with open(os.path.join(settings.BASE_DIR, 'static', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return features_dict

@login_required(login_url='/login/hbp')
def features_json(request):
    full_result_folder = request.session['full_result_folder']
    with open(os.path.join(full_result_folder, 'features.json')) as json_file:
        features_json = json.load(json_file) 
    return HttpResponse(json.dumps(features_json))

@login_required(login_url='/login/hbp')
def protocol_json(request):
    full_result_folder = request.session['full_result_folder']
    with open(os.path.join(full_result_folder, 'protocols.json')) as json_file:
        protocols_json = json.load(json_file) 
    return HttpResponse(json.dumps(protocols_json))

@login_required(login_url='/login/hbp')
def pdf_path(request):
    full_result_folder = request.session['full_result_folder']
    pdf_path = os.path.join(full_result_folder, "features_step.pdf")
    return HttpResponse(pdf_path)

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
    
    # list of uploaded files json file names
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
        name_abf_list.append(crr_file_name) 
        crr_local_filename = os.path.join(full_user_uploaded_folder, crr_file_name)
        names_full_path.append(crr_local_filename)

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

    #for root, dirs, files in os.walk(full_crr_uploaded_folder):
    for name in names_full_path:
        outfilename = '_'.join(manage_json.getCellInfo(name, upload_flag = True)) + '.json'
        outfilepath = os.path.join(full_user_uploaded_folder, outfilename)
        data = manage_json.genDataStruct(name, upload_flag = True)
        if os.path.isfile(outfilepath):
            os.remove(outfilepath)        
        with open(outfilepath, 'w') as f:
            json.dump(data, f)
        if outfilename[:-5] not in data_name_dict['all_json_names']:
            data_name_dict['all_json_names'].append(outfilename[:-5])

    access_token = request.session['access_token']
    storage_root = request.session['storage_root']
    doc_client = manage_collab_storage.create_doc_client(access_token)

    #doc_client.mkdir(os.path.join(storage_root, 'temptestfolder'))

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json") 

@login_required(login_url='/login/hbp')
def get_progress(request):
    """
     
    """
    crr_status_string = ""
    return HttpResponse(crr_status_string)


@login_required(login_url='/login/hbp')
def get_directory_structure(request):
    """ 
    Creates a nested dictionary that represents the folder structure of rootdir
    """
    rootdir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'app_data')
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

@login_required(login_url='/login/hbp')
def sf_tmp(request):
    return render_to_response("sf_tmp.html")

@login_required(login_url='/login/hbp')
@csrf_exempt
def create_session_var(request):
    # reading parameters from request.session
    username = request.session['username']
    context = request.session['context']
    headers = request.session['headers']
    collab_id = request.session['collab_id']
    
    # parameters for folder creation
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    etype = ['bAC','cAC','cNAC', 'udEt']

    # build local folder paths
    #data_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'app_data')
    #json_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'json_data')
    rel_result_folder = os.path.join('efel_gui', 'results')
    rel_uploaded_folder = os.path.join('efel_gui', 'uploaded')
    full_result_folder = os.path.join(settings.BASE_DIR, 'media', 'efel_data', rel_result_folder)
    full_uploaded_folder = os.path.join(settings.BASE_DIR, 'media', 'efel_data', rel_uploaded_folder)
    
    # build local folder complete paths
    rel_user_crr_results_folder = os.path.join(username, time_info)
    full_user_results_folder = os.path.join(full_result_folder, username)
    full_user_crr_results_folder = os.path.join(full_result_folder, rel_user_crr_results_folder)
    full_user_uploaded_folder = os.path.join(full_uploaded_folder, username)
    full_user_crr_res_res_folder = os.path.join(full_result_folder, username, time_info, 'u_res')
    full_user_crr_res_data_folder = os.path.join(full_result_folder, username, time_info, 'u_data')
    
    # storage relative path folder
    st_rel_user_results_folder = os.path.join(rel_result_folder, rel_user_crr_results_folder)
    st_rel_user_uploaded_folder = os.path.join(rel_uploaded_folder, username)
    
    request.session['st_rel_user_results_folder'] = st_rel_user_results_folder
    request.session['st_rel_user_uploaded_folder'] = st_rel_user_uploaded_folder
    request.session['full_user_crr_results_folder'] = full_user_crr_results_folder
    request.session['full_user_results_folder'] = full_user_results_folder
    request.session['full_user_crr_results_folder'] = full_user_crr_results_folder
    request.session['full_user_crr_res_res_folder'] = full_user_crr_res_res_folder
    request.session['full_user_crr_res_data_folder'] = full_user_crr_res_data_folder
    request.session['full_user_uploaded_folder'] = full_user_uploaded_folder

    # get services and access token    
    services = bsc.get_services()
    access_token = get_access_token(request.user.social_auth.get())

    # get clients from bbp python packages
    oidc_client = BBPOIDCClient.bearer_auth(services['oidc_service']['prod']['url'], access_token)
    bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    doc_client = DocClient(services['document_service']['prod']['url'], oidc_client)

    # extract project from collab_id
    project = doc_client.get_project_by_collab_id(collab_id)
    
    # extract collab storage root path
    storage_root = doc_client.get_path_by_id(project["_uuid"])
    
    # create global variables in request.session
    request.session['etype'] = etype
    request.session['time_info'] = time_info
    
    # create session variables for folders handling in request.session
    request.session['storage_root'] = storage_root
    request.session['access_token'] = access_token

    #doc_client.mkdir(os.path.join(storage_root, 'temptestfolder'))

    # render to html page
    return HttpResponse("") 



