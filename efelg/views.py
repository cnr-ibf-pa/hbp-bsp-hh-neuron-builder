'''Views'''

from hbp_app_python_auth.auth import HbpAuth 
from nose.tools import eq_, ok_
from mock import MagicMock
from mock import patch 

import os
import urllib
from uuid import UUID
import sys, datetime, shutil, zipfile, pprint
import numpy, efel, neo
import math
import matplotlib
matplotlib.use('Agg')
import requests
#requests.packages.urllib3.disable_warnings()
import json
import re
import logging
import bluepyextract as bpext
import bluepyefe as bpefe

# import django libs
from django.http import JsonResponse
from django.shortcuts import render_to_response, render, redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.context import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
#from django.contrib.auth import logout

# import hbp/bbp modules
from hbp_app_python_auth.auth import get_access_token, \
        get_token_type, get_auth_header
from hbp_app_python_auth.views import logout as auth_logout
from bbp_client.oidc.client import BBPOIDCClient
from bbp_client.document_service.client import Client as DocClient
import bbp_client
from bbp_client.client import *
import bbp_services.client as bsc

# import local tools
from tools import manage_json
from tools import resources
from tools import manage_collab_storage

# import common tools library for the bspg project
sys.path.append(os.path.join(settings.BASE_DIR))
from ctools import manage_auth

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
accesslogger = logging.getLogger('efelg_access.log')
accesslogger.addHandler(logging.FileHandler('/var/log/bspg/efelg_access.log'))
accesslogger.setLevel(logging.DEBUG)

##### serve overview.html
@login_required(login_url='/login/hbp/')
def overview(request):

    # if not in DEBUG mode check whether authentication token is valid
    if not settings.DEBUG:

        if not 'ctx' in request.session:
            # read context
            context = request.GET.get('ctx', None)
        else:
            context = request.session['ctx']

        # if not ctx exit the application 
        if not context:
            return render(request, 'efelg/hbp_redirect.html')

        # set context
        request.session['ctx'] = context

        # get headers for requests
        headers = {'Authorization': \
            get_auth_header(request.user.social_auth.get())}

        # build path for getting credentials 
        my_url = settings.HBP_MY_USER_URL
        hbp_collab_service_url = settings.HBP_COLLAB_SERVICE_URL + 'collab/context/'

        # request user and collab details
        res = requests.get(my_url, headers = headers)
        collab_res = requests.get(hbp_collab_service_url + context, \
                headers = headers)
        
        if res.status_code != 200 or collab_res.status_code != 200:
            manage_auth.Token.renewToken(request)
            
            headers = {'Authorization': \
                get_auth_header(request.user.social_auth.get())}
            
            res = requests.get(my_url, headers = headers)
            collab_res = requests.get(hbp_collab_service_url + context, \
                headers = headers)

        if res.status_code != 200 or collab_res.status_code != 200:
            return render(request, 'efelg/hbp_redirect.html')

        # extract information on user credentials and collab
        username = res.json()['username']
        userid = res.json()['id']
        collab_id = collab_res.json()['collab']['id']
    else:
        username = 'test'
        headers = {}
        context = 'local'
        collab_id = -1

    # build data and json dir strings
    data_dir = os.path.join(settings.MEDIA_ROOT, \
            'efel_data', 'app_data', 'efelg_rawdata')
    main_json_dir = os.path.join(settings.MEDIA_ROOT, \
            'efel_data', 'eg_json_data')
    app_data_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data')  

    json_dir = os.path.join(main_json_dir, 'traces')
    conf_dir = os.path.join(main_json_dir, 'conf_json')
    metadata_dir = os.path.join(main_json_dir, 'metadata')

    request.session['conf_dir'] = conf_dir
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
    request.session["username"] = username
    request.session["userid"] = userid
    request.session["headers"] = headers
    request.session["authorized_data_list"] = []
    request.session["current_authorized_files"] = []

    # reading parameters from request.session
    username = request.session["username"]
    
    # parameters for folder creation
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    # create global variables in request.session
    request.session["time_info"] = time_info

    # build local folder paths
    res_dir = os.path.join("efel_gui", "results")
    r_up_dir = os.path.join("efel_gui", "uploaded")
    res_dir = os.path.join(settings.MEDIA_ROOT, \
            "efel_data", res_dir)
    up_dir = os.path.join(settings.MEDIA_ROOT, \
            "efel_data", r_up_dir)
    
    # build local folder complete paths
    u_time_f = os.path.join(userid, time_info)
    user_res_dir = os.path.join(res_dir, userid)
    user_crr_res_dir = os.path.join(res_dir, u_time_f)
    u_up_dir = os.path.join(up_dir, userid)
    u_crr_res_r_dir = os.path.join(res_dir, userid, time_info, "u_res")
    u_crr_res_d_dir = os.path.join(res_dir, userid, time_info, 'u_data')
    
    # build media relative result path
    media_rel_crr_user_res = os.path.join('media', 'efel_data', \
            res_dir, userid, time_info, 'u_res')
    media_abs_crr_user_res = os.path.join(settings.MEDIA_ROOT, 'efel_data', \
            res_dir, userid, time_info, 'u_res')

    # storage relative path folder
    st_rel_user_results_folder = os.path.join(res_dir, \
            u_time_f)
    st_rel_user_uploaded_folder = os.path.join(r_up_dir, userid)
    
    if not os.path.exists(user_res_dir):
        os.makedirs(user_res_dir)

    # store paths in request.session
    request.session['media_rel_crr_user_res'] = media_rel_crr_user_res 
    request.session['media_abs_crr_user_res'] = media_abs_crr_user_res 
    request.session['st_rel_user_results_folder'] = st_rel_user_results_folder
    request.session['st_rel_user_uploaded_folder'] = st_rel_user_uploaded_folder
    request.session['user_crr_res_dir'] = user_crr_res_dir
    request.session['user_res_dir'] = user_res_dir
    request.session['user_crr_res_dir'] = user_crr_res_dir
    request.session['u_crr_res_r_dir'] = u_crr_res_r_dir
    request.session['u_crr_res_d_dir'] = u_crr_res_d_dir
    request.session['u_up_dir'] = u_up_dir
    
    accesslogger.info(resources.string_for_log('overview', request))

    # render to html 
    return render(request, 'efelg/overview.html')


@login_required(login_url='/login/hbp/')
def select_features(request):
    '''
    This function serves the application select-features page
    '''

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html', {"status":"KO", "message":"Problem"})

    # read features groups
    with open(os.path.join(settings.BASE_DIR, 'static', \
            'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    feature_names = efel.getFeatureNames()
    selected_traces_rest = request.POST.get('data')
    selected_traces_rest_json = json.loads(selected_traces_rest)
    request.session['selected_traces_rest_json'] = selected_traces_rest_json

    accesslogger.info(resources.string_for_log('select_features', request, \
            page_spec_string = selected_traces_rest))
    
    return render(request, 'efelg/select_features.html')

@login_required(login_url='/login/hbp/')
def hbp_redirect(request):
    return render(request, 'efelg/hbp_redirect.html')

# build .json files containing data and metadata
@login_required(login_url='/login/hbp/')
def generate_json_data(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

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
                outfilename = \
                        '____'.join(manage_json.get_cell_info(metadata_file)) \
                        + '.json'
                outfilepath = os.path.join(json_dir, outfilename)
                crr_file_auth_collab = \
                        manage_json.extract_authorized_collab(metadata_file)
                if outfilepath not in files_authorization:
                    files_authorization[outfilename] = crr_file_auth_collab

                # if the .json file has not been created
                if not os.path.isfile(outfilepath):
                    path_dd_name = os.path.join(data_dir, name)
                    data = manage_json.gen_data_struct(path_dd_name,\
                            metadata_file)
                    with open(outfilepath, 'w') as f:
                        json.dump(data, f)
    #
    app_data_dir = request.session['app_data_dir']
    file_auth_fullpath = os.path.join(app_data_dir, "files_authorization.json")
    with open(file_auth_fullpath, 'w') as fa:
        json.dump(files_authorization, fa)

    return HttpResponse("")


@login_required(login_url='/login/hbp/')
def show_traces(request):
    '''
    Render the efel/show_traces.html page
    '''

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    accesslogger.info(resources.string_for_log('show_traces', request))
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    username = request.session['username']
    userid = request.session['userid']
    accesslogger.info("user " + \
            username + " has accepted terms and conditions at this time " + \
            time_info)
    accesslogger.info("user " + \
            userid + " has accepted terms and conditions at this time " + \
            time_info)
    return render(request, 'efelg/show_traces.html')


@login_required(login_url='/login/hbp/')
def get_list(request):
    '''
    Retrieve the list of .json files to be displayed for trace selection
    '''

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    
    # final list of authorized files
    allfiles = []

    #retrieve data from session variables
    json_dir = request.session['json_dir']
    
    # extract the list of the collabs the current user belongs to
    my_collabs_url = settings.HBP_MY_COLLABS_URL
    crr_auth_data_list = resources.user_collab_list(my_collabs_url, \
            request.user.social_auth.get()) 

    # retrieve the file containing the authorizations for each data file
    conf_dir = request.session['conf_dir']
    file_auth_fullpath = os.path.join(conf_dir, "files_authorization.json")
    with open(file_auth_fullpath) as f:
        files_auth = json.load(f)
    
    #  
    for i in os.listdir(json_dir):
        crr_file_path = os.path.join(json_dir, i)
        #if crr_file_path in files_auth:

        if i in files_auth:
            #crr_file_auth = files_auth[crr_file_path]
            crr_file_auth = files_auth[i]
            if any(j in crr_file_auth for j in crr_auth_data_list) or \
                    crr_file_auth[0]=="all":
                allfiles.append(i[:-5])

    request.session["current_authorized_files"] = allfiles 

    output_json = manage_json.generate_json_output(allfiles, json_dir)

    user_dir = request.session['user_res_dir']
    with open(os.path.join(user_dir, 'output.json'), 'w') as f:
        json.dumps(output_json, f)


    #return HttpResponse(json.dumps(allfiles), content_type="application/json")
    return HttpResponse(json.dumps(output_json), content_type="application/json")


##### 
'''
Retrieve the list of .json files to be displayed for trace selection
'''
# @login_required(login_url='/login/hbp/')
def get_list_new(request):
    
    # final list of authorized files
    # allfiles = []

    #retrieve data from session variables
    # json_dir = request.session['json_dir']

    # extract the list of the collabs the current user belongs to
    # my_collabs_url = settings.HBP_MY_COLLABS_URL
    # crr_auth_data_list = resources.user_collab_list(my_collabs_url, \
    #         request.user.social_auth.get())

    # retrieve the file containing the authorizations for each data file
    # conf_dir = request.session['conf_dir']
    # conf_dir = os.path.join(settings.MEDIA_ROOT,  'efel_data', 'eg_json_data', 'conf_json')
    #
    # file_auth_fullpath = os.path.join(conf_dir, "files_authorization.json")
    # with open(file_auth_fullpath) as f:
    #     files_auth = json.load(f)
    #
    #  
    # for i in os.listdir(json_dir):
    #     crr_file_path = os.path.join(json_dir, i)
    #     if crr_file_path in files_auth:
    #
    #      if i in files_auth:
    #          crr_file_auth = files_auth[crr_file_path]
    #          crr_file_auth = files_auth[i]
    #          if any(j in crr_file_auth for j in crr_auth_data_list) or \
    #                  crr_file_auth[0]=="all":
    #     allfiles.append(i[:-5])
    # request.session["current_authorized_files"] = allfiles

    # return HttpResponse(json.dumps(allfiles), content_type="application/json")
    json_file = open(os.path.join(settings.MEDIA_ROOT, 'efel_data', 'eg_json_data', 'output.json'))
    return HttpResponse(json_file, content_type="application/json")

#####
@login_required(login_url='/login/hbp/')
def get_data(request, cellname=""):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')


    disp_sampling_rate = 5000
    json_dir = request.session['json_dir']
    u_up_dir = request.session['u_up_dir']
    current_authorized_files = request.session["current_authorized_files"]

    if cellname not in current_authorized_files and not \
            os.path.isfile(os.path.join(u_up_dir, cellname)):
        return HttpResponse("")
    
    if os.path.isfile(os.path.join(json_dir, cellname) + '.json'):
        cellname_path = os.path.join(json_dir, cellname) + '.json'
        
    elif os.path.isfile(os.path.join(u_up_dir, cellname) \
            + '.json'):
        cellname_path = os.path.join(u_up_dir, cellname) \
                + '.json'

    with open(cellname_path) as f:
        content_json = f.read()
    content = json.loads(content_json)

    # extract data to be sent to frontend
    crr_sampling_rate = content['sampling_rate']
    coefficient = int(math.floor(crr_sampling_rate/disp_sampling_rate))
    if coefficient < 1:
        coefficient = 1
        disp_sampling_rate = crr_sampling_rate
    
    trace_info = {}
    trace_info['traces'] = {}
    for key in content['traces'].keys():
        trace_info['traces'][key] = content['traces'][key][::coefficient]
    trace_info['md5'] = content['md5']
    trace_info['species'] = content['species']
    trace_info['sampling_rate'] = content['sampling_rate']
    trace_info['area'] = content['area']
    trace_info['region'] = content['region']
    trace_info['etype'] = content['etype']
    trace_info['type'] = content['type']
    trace_info['name'] = content['name']
    trace_info['sample'] = content['sample']
    trace_info['amp_unit'] = content['amp_unit']
    trace_info['contributors'] = content['contributors']
    trace_info['coefficient'] = coefficient
    trace_info['volt_unit'] = content['volt_unit']
    trace_info['disp_sampling_rate'] = disp_sampling_rate

    
    return HttpResponse(json.dumps(json.dumps(trace_info)), content_type="application/json")


#####
@login_required(login_url='/login/hbp/')
def extract_features(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    data_dir = request.session['data_dir']
    json_dir = request.session['json_dir']
    selected_traces_rest_json = request.session['selected_traces_rest_json'] 
    allfeaturesnames = efel.getFeatureNames()
    
    crr_user_folder = request.session['time_info'] 
    full_crr_result_folder = request.session['u_crr_res_r_dir']
    full_crr_uploaded_folder = request.session['u_up_dir']
    full_crr_data_folder = request.session['u_crr_res_d_dir']
    full_crr_user_folder = request.session['user_crr_res_dir']
    check_features = request.session["check_features"] 
    request.session['selected_features'] = check_features 
    cell_dict = {}
    selected_traces_rest = []

    for k in selected_traces_rest_json:
        #crr_vcorr = selected_traces_rest_json[k]['vcorr']
        crr_file_rest_name = k + '.json'
        crr_name_split = k.split('____')
        crr_cell_name = crr_name_split[5]
        crr_sample_name = crr_name_split[6]
        crr_key = crr_name_split[0] + '____' + crr_name_split[1] + '____' + \
                crr_name_split[2] + '____' + crr_name_split[3] + '____' + \
                crr_name_split[4] +  '____' + crr_name_split[5]
        if os.path.isfile(os.path.join(json_dir, crr_file_rest_name)):
            crr_json_file = os.path.join(json_dir, crr_file_rest_name)
        elif os.path.isfile(os.path.join(full_crr_uploaded_folder, \
                crr_file_rest_name)):
            crr_json_file = os.path.join(full_crr_uploaded_folder, \
                    crr_file_rest_name)
        else:
            continue

        with open(crr_json_file) as f:
            crr_file_dict_read = f.read()

        crr_file_dict = json.loads(crr_file_dict_read)
        crr_file_all_stim = crr_file_dict['traces'].keys()
        crr_file_sel_stim = selected_traces_rest_json[k]['stim']

        crr_cell_data_folder = os.path.join(full_crr_data_folder, crr_cell_name)
        crr_cell_data_folder = full_crr_data_folder
        if not os.path.exists(crr_cell_data_folder):
            os.makedirs(crr_cell_data_folder)
        shutil.copy2(crr_json_file, crr_cell_data_folder)

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
        exc_stim_lists = [list(set(crr_el['all_stim']) - set(sublist)) for \
                sublist in crr_el['stim']]
        crr_exc = []
        for crr_list in exc_stim_lists:
            crr_stim_val = [float(i) for i in crr_list]
            crr_exc.append(crr_stim_val)
        final_cell_dict[cell_dict[key]['cell_name']] = {'v_corr':v_corr, \
                'ljp':0, 'experiments':{'step': {'location':'soma', 'files': \
                [str(i) for i in crr_el['files']]}}, 'etype':'etype', \
                'exclude':crr_exc}

    # build configuration dictionary
    config = {}
    config['features'] = {'step':[str(i) for i in check_features]}
    config['path'] = crr_cell_data_folder
    config['format'] = 'ibf_json'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {'relative': False, 'tolerance': 0.02, \
            'target': target, 'delay': 500, 'nanmean': False, 'logging':False, \
            'nangrace': 0, 'spike_threshold': 1, 'amp_min': 0,
            'strict_stiminterval': {'base': True}}
    try:
        extractor = bpefe.Extractor(full_crr_result_folder, config, use_git=False)
        extractor.create_dataset()
        extractor.plt_traces()
        extractor.extract_features()
        extractor.mean_features()
        extractor.plt_features()
        extractor.feature_config_cells(version="legacy")
        extractor.feature_config_all(version="legacy")
    except:
        return render(request, 'efelg/hbp_redirect.html', {"status":"KO", \
                "message": "An error occured while extracting the features. \
                Either you selected too many data or the traces were corrupted."})


    conf_dir = request.session['conf_dir']
    conf_cit = os.path.join(conf_dir, 'citation_list.json')
    final_cit_file = os.path.join(full_crr_result_folder, 'HOWTOCITE.txt')
    resources.print_citations(selected_traces_rest_json, conf_cit, final_cit_file)   

    crr_result_folder = request.session['time_info']
    output_path = os.path.join(full_crr_user_folder, crr_user_folder + \
            '_results.zip')
    request.session['result_file_zip'] = output_path
    request.session['result_file_zip_name'] = crr_user_folder + '_results.zip'
    parent_folder = os.path.dirname(full_crr_result_folder)
    contents = os.walk(full_crr_result_folder)
    try:
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(parent_folder + \
                        os.sep, '')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(parent_folder + \
                        os.sep, '')
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


    accesslogger.info(resources.string_for_log('extract_features', \
            request, page_spec_string = '___'.join(check_features)))
    return HttpResponse(json.dumps({"status": "OK"})) 


#####
@login_required(login_url='/login/hbp/')
def results(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    '''Render final page containing the link to the result zip file if any'''

    check_features = request.POST.getlist('crr_feature_check_features')
    request.session["check_features"] = check_features
    return render(request, 'efelg/results.html')

#####

@login_required(login_url='/login/hbp/')
def download_zip(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    accesslogger.info(resources.string_for_log('download_zip', request))
    result_file_zip = request.session['result_file_zip']
    result_file_zip_name = request.session['result_file_zip_name']
    zip_file = open(result_file_zip, 'rb')
    response = HttpResponse(zip_file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % \
            result_file_zip_name
    return response


#####
@login_required(login_url='/login/hbp/')
def features_dict(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    '''Render the feature dictionary containing all feature names, grouped by feature type'''
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg',\
            'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return HttpResponse(json.dumps(features_dict))


#####
@login_required(login_url='/login/hbp/')
def features_json(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    u_crr_res_r_dir = request.session['u_crr_res_r_dir']
    with open(os.path.join(u_crr_res_r_dir, 'features.json')) \
            as json_file:
        features_json = json.load(json_file) 
    return HttpResponse(json.dumps(features_json))


#####
@login_required(login_url='/login/hbp/')
def features_json_path(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    abs_url = request.session['media_abs_crr_user_res']
    full_feature_json_file = os.path.join(abs_url, 'features.json')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, \
            full_feature_json_file)}))

#####
@login_required(login_url='/login/hbp/')
def features_json_files_path(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    abs_url = request.session['media_abs_crr_user_res']
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, abs_url)}))

#####
@login_required(login_url='/login/hbp/')
def protocols_json_path(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'protocols.json')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, \
            full_feature_json_file)}))


#####
@login_required(login_url='/login/hbp/')
def features_pdf_path(request):

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'features_step.pdf')
    return HttpResponse(json.dumps({'path' : os.path.join(os.sep, \
            full_feature_json_file)}))


#####
@login_required(login_url='/login/hbp/')
def upload_files(request):
    """
    Upload file to local folder
    """
    u_up_dir = request.session['u_up_dir']
    if not os.path.exists(u_up_dir):
        os.makedirs(u_up_dir)
    
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
        crr_local_filename = os.path.join(u_up_dir, \
                crr_file_name)

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
        outfilename = '____'.join(manage_json.get_cell_info(name, \
                upload_flag = True)) + '.json'
        outfilepath = os.path.join(u_up_dir, outfilename)

        data = manage_json.gen_data_struct(name, "",  upload_flag = True)
        if os.path.isfile(outfilepath):
            os.remove(outfilepath)        
        with open(outfilepath, 'w') as f:
            json.dump(data, f)
        if outfilename[:-5] not in data_name_dict['all_json_names']:
            data_name_dict['all_json_names'].append(outfilename[:-5])
            all_authorized_files.append(outfilename[:-5])
    
    request.session["current_authorized_files"] = all_authorized_files

    accesslogger.info(resources.string_for_log('upload_files', request, \
            page_spec_string = str(len(names_full_path))))

    return HttpResponse(json.dumps(data_name_dict), \
            content_type="application/json") 


@login_required(login_url='/login/hbp/')
def get_directory_structure(request):
    """ 
    Creates a nested dictionary that represents the folder structure of rootdir
    """

    # if not ctx exit the application 
    if not "ctx" in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    accesslogger.info(resources.string_for_log('get_directory_structure', \
            request))
    rootdir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data')
    media_dir_dict = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1 
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    with open(os.path.join(settings.BASE_DIR, 'static', \
            'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file) 
    return HttpResponse(json.dumps(features_dict))




########### handle file upload to storage collab
def upload_zip_file_to_storage(request):

    access_token = get_access_token(request.user.social_auth.get())
    # retrieve data from request.session
    headers = request.session['headers']
    collab_id = request.session['collab_id']
    st_rel_user_results_folder = request.session['st_rel_user_results_folder']
    st_rel_user_uploaded_folder = request.session['st_rel_user_uploaded_folder']
    crr_user_folder = request.session['time_info'] 
    output_path = request.session['result_file_zip']
    context = request.session['context']
    services = bsc.get_services()
    
    # get clients from bbp python packages
    oidc_client = BBPOIDCClient.bearer_auth(\
            services['oidc_service']['prod']['url'], access_token)
    bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    doc_client = DocClient(\
            services['document_service']['prod']['url'], oidc_client)

    context = request.session['context']
    #logout(request)
    nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))

    # extract project from collab_id
    project = doc_client.get_project_by_collab_id(collab_id)
        
    # extract collab storage root path
    storage_root = doc_client.get_path_by_id(project["_uuid"])
    crr_collab_storage_folder = os.path.join(storage_root, \
            st_rel_user_results_folder)
    if not doc_client.exists(crr_collab_storage_folder):
        doc_client.makedirs(crr_collab_storage_folder)

    # final zip collab storage path
    zip_collab_storage_path = os.path.join(crr_collab_storage_folder, \
            crr_user_folder + '_results.zip')

    # bypassing uploading data to collab storage
    if not doc_client.exists(zip_collab_storage_path):
        doc_client.upload_file(output_path, zip_collab_storage_path) 

    # render to html page
    return HttpResponse("") 

