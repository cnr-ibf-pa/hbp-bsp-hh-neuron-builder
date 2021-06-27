import functools
import math
import re
import shutil
import urllib.parse as urllib
import zipfile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse, HttpResponseBadRequest

from hh_neuron_builder import settings
from efelg.tools import resources, manage_json

import efel
import requests
import datetime
import logging
import sys
import os
import json

import bluepyefe as bpefe



# set logging up
#logging.basicConfig(stream=sys.stdout)
#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
#accesslogger = logging.getLogger('efelg_access.log')
#accesslogger.addHandler(logging.FileHandler('efelg_access.log'))
#accesslogger.setLevel(logging.DEBUG)


# Create your views here.


import pprint
# @login_required()
def overview(request):

    # set context
    request.session['ctx'] = request.GET.get('ctx', None)

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'anonymous'
        
    collab_id = '100000'

    request.session['main_json_dir'] = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'eg_json_data')
    request.session['traces_base_url'] = "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/"

    # save parameters in request.session
    request.session["username"] = username
    #request.session["user_id"] = user_id
    #request.session["current_authorized_files"] = []

    # request.session["headers"] = headers
    # request.session["authorized_data_list"] = []

    # reading parameters from request.session
    # username = request.session["username"]

    # parameters for folder creation
    time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    request.session["time_info"] = time_info
     
    user_base_dir =  os.path.join(
        settings.MEDIA_ROOT,
        "efel_data",
        "efel_gui",
        "results",
        username,
        "data_" + str(time_info)
    )

    # build local folder complete paths
    #u_time_f = os.path.join(userid, time_info)
    #user_crr_res_dir = os.path.join(result_dir, u_time_f)
    #u_crr_res_r_dir = os.path.join(result_dir, username, time_info, "u_res")
    #u_crr_res_d_dir = os.path.join(result_dir, username, time_info, 'u_data')

    # build media relative result path
    #media_rel_crr_user_res = os.path.join(res_dir,  userid, time_info, 'u_res')
    #media_abs_crr_user_res = os.path.join(settings.MEDIA_ROOT, 'efel_data', u_crr_res_r_dir)
    #media_abs_crr_user_res = os.path.join(res_dir, userid, time_info, 'u_res')

    # storage relative path folder
    #st_rel_user_results_folder = os.path.join(res_dir, u_time_f)
    #st_rel_user_uploaded_folder = os.path.join(up_dir, userid)

    user_files_dir = os.path.join(user_base_dir, "u_data")
    if not os.path.exists(user_files_dir):
        os.makedirs(user_files_dir)
    
    uploaded_files_dir = os.path.join(user_base_dir, "uploaded")
    if not os.path.exists(uploaded_files_dir):
        os.makedirs(uploaded_files_dir)

    user_results_dir = os.path.join(user_base_dir, "u_res")
    if not os.path.exists(user_results_dir):
        os.makedirs(user_results_dir)

    # store paths in request.session
    #request.session['media_rel_crr_user_res'] = media_rel_crr_user_res
    #request.session['media_abs_crr_user_res'] = media_abs_crr_user_res
    #request.session['st_rel_user_results_folder'] = st_rel_user_results_folder
    #request.session['st_rel_user_uploaded_folder'] = st_rel_user_uploaded_folder
    #request.session['user_crr_res_dir'] = user_crr_res_dir
    #request.session['user_res_dir'] = user_res_dir
    #request.session['user_crr_res_dir'] = user_crr_res_dir
    request.session['user_files_dir'] = user_files_dir
    request.session['uploaded_files_dir'] = uploaded_files_dir
    request.session['user_results_dir'] = user_results_dir

    #accesslogger.info(resources.string_for_log('overview', request))

    # render to html
    return render(request, 'efelg/overview.html')


# @login_required()
def select_features(request):
    """
    This function serves the application select-features page
    """

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')


    """
    # read features groups
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features_dict = json.load(json_file)
    """

    feature_names = efel.getFeatureNames()
    selected_traces_rest = request.POST.get('data')
    request.session['selected_traces_rest_json'] = json.loads(selected_traces_rest)
    request.session['global_parameters_json'] = json.loads(request.POST.get('global_parameters'))
    #accesslogger.info(resources.string_for_log('select_features', request, page_spec_string=selected_traces_rest))
    return render(request, 'efelg/select_features.html')


# @login_required()
def show_traces(request):
    """"
    Render the efel/show_traces.html page
    """

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')


    #accesslogger.info(resources.string_for_log('show_traces', request))
    #time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    #accesslogger.info("user " + request.session['username'] + " has accepted terms and conditions at this time " + time_info)
    return render(request, 'efelg/show_traces.html')


# @login_required()
def get_list(request):
    """"
    Retrieve the list of .json files to be displayed for trace selection
    """
    
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    # metadata file path
    output_file_path = os.path.join(request.session['main_json_dir'], 'all_traces_metadata.json')
    #file_auth_fullpath = os.path.join(request.session['main_json_dir'], "files_authorization.json")

    """
    # final list of authorized files
    allfiles = []
    

    with open(file_auth_fullpath) as f:
        files_auth = json.load(f)

    for f in files_auth:
        if files_auth[f] == "all":
            allfiles.append(f[:-5])
    """
    """
    for i in os.listdir(request.session['main_json_dir']):
        crr_file_path = os.path.join(request.session['main_json_dir'], i)
        if i in files_auth:
            crr_file_auth = files_auth[i]
            if crr_file_auth[0] == 'all':
                allfiles.append(i[:-5])
    """

    #request.session["current_authorized_files"] = allfiles

    """
    # if metadata all already computed, avoid extraction
    if os.path.isfile(output_file_path):
        with open(output_file_path, 'r') as f:
            output_json = json.load(f)

    else:
        output_json = manage_json.generate_json_output(allfiles, json_dir)
        with open(output_file_path, 'w') as f:
            json.dump(output_json, f)
    """

    try:
        with open(output_file_path, 'r') as f:
            output_json = json.load(f)
    except FileNotFoundError:
        return HttpResponse()

    # return HttpResponse(json.dumps(allfiles), content_type="application/json")
    return HttpResponse(json.dumps(output_json), content_type="application/json")


#####
# @login_required(login_url='/login/hbp/')
def get_data(request, cellname=""):
    
    print('get_data() called.')

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    #current_authorized_files = request.session["current_authorized_files"]

    """
    if cellname not in current_authorized_files and not os.path.isfile(os.path.join(u_up_dir, cellname)):
        return HttpResponse("")

    if os.path.isfile(os.path.join(json_dir, cellname) + '.json'):
        cellname_path = os.path.join(json_dir, cellname) + '.json'

    elif os.path.isfile(os.path.join(u_up_dir, cellname) + '.json'):
        cellname_path = os.path.join(u_up_dir, cellname) + '.json'

    with open(cellname_path) as f:
        content_json = f.read()
    content = json.loads(content_json)
    """

    user_files_dir = request.session['user_files_dir']
    print(user_files_dir)
    file_name = cellname + ".json"
    print(file_name)
    path_to_file = os.path.join(user_files_dir, file_name)
    print(os.listdir(user_files_dir))
    print('looking for ' + file_name)
    if not file_name in os.listdir(user_files_dir):
        r = requests.get(request.session['traces_base_url'] + file_name)
        with open(path_to_file, "w") as f:
            json.dump(r.json(), f)

    with open(path_to_file, "r") as f:
        content = json.loads(f.read())

    # extract data to be sent to frontend
    disp_sampling_rate = 5000
    if type(content['sampling_rate']) == list:
        crr_sampling_rate = int(content['sampling_rate'][0])
    else:
        crr_sampling_rate = int(content['sampling_rate'])

    #crr_sampling_rate = int(content['sampling_rate'][0])
    coefficient = int(math.floor(crr_sampling_rate / disp_sampling_rate))
    if coefficient < 1:
        coefficient = 1
        disp_sampling_rate = crr_sampling_rate

    trace_info = {}
    trace_info['traces'] = {}
    for key in content['traces'].keys():
        trace_info['traces'][key] = content['traces'][key][::coefficient]

    trace_info['md5'] = content['md5']
    trace_info['sampling_rate'] = content['sampling_rate']
    trace_info['etype'] = content['etype']
    trace_info['type'] = content['type']
    trace_info['contributors'] = content['contributors']
    trace_info['coefficient'] = coefficient
    trace_info['disp_sampling_rate'] = disp_sampling_rate

    new_keys = {
        "name": "cell_id",
        "area": "brain_structure",
        "sample": "filename",
        "species": "animal_species",
        "region": "cell_soma_location",
        "amp_unit": "stimulus_unit",
        "volt_unit": "voltage_unit"
    }

    for key in new_keys:
        if new_keys[key] in content:
            trace_info[new_keys[key]] = content[new_keys[key]]
        elif key in content:
            trace_info[new_keys[key]] = content[key]
        else:
            #raise Exception(new_keys[key] + " not found!")
            trace_info[new_keys[key]] = 'unknown'

    if 'contributors_affiliations' in content:
        trace_info['contributors_affiliations'] = content['contributors_affiliations']
    elif 'name' in content['contributors']:
        trace_info['contributors_affiliations'] = content['contributors']['name']
    else:
        #raise Exception("contributors_affiliations not found!")
        trace_info['contributors_affiliations'] = 'unknown'

    return HttpResponse(json.dumps(json.dumps(trace_info)), content_type="application/json")


#####
# @login_required(login_url='/login/hbp/')
def extract_features(request):

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    print('EXTRACTING FEATURES')
    
    selected_traces_rest_json = request.session['selected_traces_rest_json']
    global_parameters_json = request.session['global_parameters_json']
    allfeaturesnames = efel.getFeatureNames()

    """
    crr_user_folder = request.session['time_info']
    full_crr_result_folder = request.session['u_crr_res_r_dir']
    full_crr_uploaded_folder = request.session['user_upload_dir']
    full_crr_data_folder = request.session['u_crr_res_d_dir']
    full_crr_user_folder = request.session['user_crr_res_dir']
    """

    conf_dir = request.session['main_json_dir']
    uploaded_files_dir = request.session['uploaded_files_dir']
    user_files_dir = request.session['user_files_dir']
    user_results_dir = request.session['user_results_dir']
    time_info = request.session['time_info']
    selected_features = request.session["selected_features"]

    cell_dict = {}

    print('STEP 1')

    for k in selected_traces_rest_json:
        print("FILE: " + str(k))
        path_to_file = os.path.join(user_files_dir, k + '.json')
        with open(path_to_file) as f:
            crr_file_dict = json.loads(f.read()) 
        crr_file_all_stim = list(crr_file_dict['traces'].keys())
        crr_file_sel_stim = selected_traces_rest_json[k]['stim']

        """
        if os.path.isfile(os.path.join(json_dir, crr_file_rest_name)):
            crr_json_file = os.path.join(json_dir, crr_file_rest_name)
        elif os.path.isfile(os.path.join(full_crr_uploaded_folder, crr_file_rest_name)):
            crr_json_file = os.path.join(full_crr_uploaded_folder, crr_file_rest_name)
        else:
            continue

        with open(crr_json_file) as f:
            crr_file_dict_read = f.read()
        """

        if "stimulus_unit" in crr_file_dict:
            crr_file_amp_unit = crr_file_dict["stimulus_unit"]
        elif "amp_unit" in crr_file_dict:
            crr_file_amp_unit = crr_file_dict["amp_unit"]
        else:
            raise Exception("stimulus_unit not found!")

        if "cell_id" in crr_file_dict:
            crr_cell_name = crr_file_dict["cell_id"]
        elif "name" in crr_file_dict:
            crr_cell_name = crr_file_dict["name"]
        else:
            raise Exception("cell_id not found!")

        """
        cell_results_folder = os.path.join(user_results_dir, crr_cell_name)
        if not os.path.exists(cell_results_folder):
            os.makedirs(cell_results_folder)
        shutil.copy2(path_to_file, cell_results_folder)
        """

        print('STEP 1.5')

        new_keys = [
            ("animal_species", "species") , 
            ("brain_structure", "area"),
            ("cell_soma_location", "region"),
            ("cell_type", "type"),
            ("etype", "etype"),
            ("cell_id", "name")
        ]

        keys = [crr_file_dict[t[0]] if t[0] in crr_file_dict else crr_file_dict[t[1]] for t in new_keys]
        print(keys)
        keys2 = []
        for kk2 in keys:
            if not type(kk2) == list:
                keys2.append(kk2)
            else:
                for kkk in kk2:
                    keys2.append(kkk)

        crr_key = '____'.join(keys2)
        
        print(json.dumps(selected_traces_rest_json[k], indent=4))
        crr_vcorr = float(selected_traces_rest_json[k]['v_corr'])
        if crr_key in cell_dict:
            cell_dict[crr_key]['stim'].append(crr_file_sel_stim)
            cell_dict[crr_key]['files'].append(k)
            cell_dict[crr_key]['v_corr'] = float(crr_vcorr)
        else:
            cell_dict[crr_key] = {}
            cell_dict[crr_key]['stim'] = [crr_file_sel_stim]
            cell_dict[crr_key]['files'] = [k]
            cell_dict[crr_key]['cell_name'] = crr_cell_name
            cell_dict[crr_key]['all_stim'] = crr_file_all_stim
            cell_dict[crr_key]['v_corr'] = 0

    print('STEP 2')

    target = []
    final_cell_dict = {}
    final_exclude = []

    for key in cell_dict:
        crr_el = cell_dict[key]
        for c_stim_el in crr_el['stim']:
            [target.append(float(i)) for i in c_stim_el if float(i) not in target]
        exc_stim_lists = [list(set(crr_el['all_stim']) - set(sublist)) for sublist in crr_el['stim']]
        crr_exc = []
        for crr_list in exc_stim_lists:
            crr_stim_val = [float(i) for i in crr_list]
            crr_exc.append(crr_stim_val)
        final_cell_dict[cell_dict[key]['cell_name']] = \
            {
                'v_corr': crr_el['v_corr'],
                'ljp': 0,
                'experiments': {
                    'step': {
                        'location': 'soma',
                        'files': [str(i) for i in crr_el['files']]
                    }
                },
                'etype': 'etype',
                'exclude': crr_exc,
                'exclude_unit': [crr_file_amp_unit for i in range(len(crr_exc))]
            }

    print('STEP 3')
    # build configuration dictionary

    config = {}
    config['features'] = {'step': [str(i) for i in selected_features]}
    config['path'] = user_files_dir
    config['format'] = 'ibf_json'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {
        # 'featconffile': './pt_conf.json',
        # 'featzerotonan': False,
        'zero_to_nan': {
            'flag': bool(global_parameters_json['zero_to_nan']),
            'value': global_parameters_json['value'],
            'mean_features_no_zeros': global_parameters_json['mean_features_no_zeros']
            },
        'relative': False,
        'tolerance': 0.02,
        'target': target,
        'target_unit': 'nA',
        'delay': 500,
        'nanmean': True,
        'logging': True,
        'nangrace': 0,
        # 'spike_threshold': 1,
        'amp_min': -1e22,
        'zero_std': bool(global_parameters_json['zero_std']),
        'trace_check': False,
        'strict_stiminterval': {
            'base': True
        },
        'print_table': {
            'flag': True,
            'num_events': int(global_parameters_json['num_events']),
        }
    }

    try:
        main_results_folder = os.path.join(user_results_dir, time_info + "_nfe_results")
        extractor = bpefe.Extractor(main_results_folder, config)
        extractor.create_dataset()
        extractor.plt_traces()
        if global_parameters_json['threshold'] != '':
            extractor.extract_features(threshold=int(global_parameters_json['threshold']))
        else:
            extractor.extract_features(threshold=-20)
        extractor.mean_features()
        extractor.plt_features()
        extractor.feature_config_cells(version="legacy")
        extractor.feature_config_all(version="legacy")
    except ValueError as e:
        print('SOME ERROR OCCURED')
        print(e)
        # return render(request, 'efelg/hbp_redirect.html', {"status": "KO",
        #                                                    "message": "An error occured while extracting the features. \
        #         Either you selected too many data or the traces were corrupted."})

    print('STEP 4')

    conf_cit = os.path.join(conf_dir, 'citation_list.json')
    final_cit_file = os.path.join(main_results_folder, 'HOWTOCITE.txt')
    resources.print_citations(selected_traces_rest_json, conf_cit, final_cit_file)

    zip_name = time_info + '_nfe_results.zip'
    zip_path = os.path.join(user_results_dir, zip_name)
    request.session['nfe_result_file_zip'] = zip_path
    request.session['nfe_result_file_zip_name'] = zip_name

    #parent_folder = os.path.dirname(full_crr_result_folder)
    contents = os.walk(main_results_folder)
    try:
        zip_file = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(main_results_folder + os.sep, '')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(main_results_folder + os.sep, '')
                zip_file.write(absolute_path, relative_path)
                print('STEP 5')
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

    print('EXTRACTION OK 200')
    # accesslogger.info(resources.string_for_log('extract_features', request, page_spec_string='___'.join(check_features)))
    return HttpResponse(json.dumps({"status": "OK"}))



#####
# @login_required(login_url='/login/hbp/')
def results(request):
    
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')
    
    # Render final page containing the link to the result zip file if any

    request.session["selected_features"] = request.POST.getlist('crr_feature_check_features')
    return render(request, 'efelg/results.html')


#####

# @login_required(login_url='/login/hbp/')
def download_zip(request):
    
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    # accesslogger.info(resources.string_for_log('download_zip', request))
    zip_file = open(request.session['nfe_result_file_zip'], 'rb')
    response = HttpResponse(zip_file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % request.session['nfe_result_file_zip_name']
    return response


#####
# @login_required(login_url='/login/hbp/')
def features_dict(request):
    
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    # Render the feature dictionary containing all feature names, grouped by feature type
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features = json.load(json_file)
    return HttpResponse(json.dumps(features))


#####
# @login_required(login_url='/login/hbp/')
@csrf_exempt
def upload_files(request):
    """
    Upload file to local folder
    """

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/overview.html')

    uploaded_files_dir = request.session['uploaded_files_dir']
    user_files_dir = request.session['user_files_dir']
    #all_authorized_files = request.session["current_authorized_files"]

    # list of modified names of uploaded files
    # name_abf_list = []

    # list of json files that have the corresponding abf file
    # name_json_list = []

    # list of standalone json files
    # name_standalone_json_list = []

    # list of uploaded files full paths

    names_full_path = []

    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    cell_name = "up_cell_" + request.POST['cell_name']

    user_files = request.FILES.getlist('user_files')
    # for every files to be uploaded, save them on local folders:
    for k in user_files:
        if k.name.endswith('.abf') or k.name.endswith('.json'):
            file_name = re.sub('-', '_', k.name)
            path_to_file = os.path.join(uploaded_files_dir, file_name)

            # if file exists delete and recreate it
            if os.path.isfile(path_to_file):
                os.remove(path_to_file)

            with open(path_to_file, 'wb') as f:

                # save chunks or entire file based on dimensions
                if k.multiple_chunks():
                    for chunk in k.chunks():
                        f.write(chunk)
                else:
                    f.write(k.read())

                if not k.name.endswith('_metadata.json'):
                    names_full_path.append(path_to_file)

    for f in names_full_path:
        try:
            data = manage_json.extract_data(f, request.POST)
            #outfilename = '____'.join(manage_json.get_cell_info(metadata, upload_flag=True, cell_name=cell_name)) + '.json'
            output_filename = manage_json.create_file_name(data)
            output_filepath = os.path.join(user_files_dir, output_filename)
            if os.path.isfile(output_filepath):
                os.remove(output_filepath)
            with open(output_filepath, 'w') as f:
                json.dump(data, f)
            if output_filename[:-5] not in data_name_dict['all_json_names']:
                data_name_dict['all_json_names'].append(output_filename[:-5])
                #all_authorized_files.append(output_filename[:-5])
        except:
            pass   


    #request.session["current_authorized_files"] = all_authorized_files

    # accesslogger.info(resources.string_for_log('upload_files', request, page_spec_string=str(len(names_full_path))))
    return HttpResponse(json.dumps(data_name_dict), content_type="application/json")


def index_docs(request):
    return render(request, 'efelg/docs/index.html')


def file_formats_docs(request):
    return render(request, 'efelg/docs/file_formats.html')



def get_result_dir(request):
    username = request.session['username']
    time_info = request.session['time_info']
    user_base_dir =  os.path.join(
        settings.MEDIA_ROOT,
        "efel_data",
        "efel_gui",
        "results",
        username,
        "data_" + str(time_info)
    )
    
    user_results_dir = os.path.join(user_base_dir, "u_res")
    data = {'result_dir': user_results_dir}
    return JsonResponse(data=json.dumps(data), status=200, safe=False)


def hhf_etraces(request):
    r = overview(request)
    return render(request, 'efelg/show_traces.html')


@csrf_exempt
def load_hhf_etraces(request):
    hhf_etraces_dir = request.POST.get('hhf_etraces_dir', None)
    if not hhf_etraces_dir:
        return HttpResponseBadRequest()

    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    for f in os.listdir(hhf_etraces_dir):
        if not f.endswith('.abf'):
            continue
        try:
            with open(os.path.join(hhf_etraces_dir, f[:-4] + '_metadata.json'), 'r') as fd:
                metadata_dict = json.load(fd)
            data = manage_json.extract_data(os.path.join(hhf_etraces_dir, f), metadata_dict=metadata_dict)
            output_filename = manage_json.create_file_name(data)
            output_filename = output_filename.replace(' ', '_')
            #output_filename = output_filename.replace('.abf', '')
            print(output_filename)
            with open(os.path.join(request.session['user_files_dir'], output_filename), 'w') as fd:
                json.dump(data, fd, indent=4)
            if output_filename[:-5] not in data_name_dict['all_json_names']:
                data_name_dict['all_json_names'].append(output_filename[:-5])
                #all_authorized_files.append(output_filename[:-5])
        except Exception as e:
            print(e)

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json")


"""
def status(request):
    return HttpResponse(json.dumps({"efel-gui-status": 1}), content_type="application/json")
"""


"""
# @login_required()
def hbp_redirect(request):
    return render(request, 'efelg/hbp_redirect.html')
"""

"""
# build .json files containing data and metadata
# @login_required()
def generate_json_data(request):

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

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
                    files_authorization[outfilename] = crr_file_auth_collab

                # if the .json file has not been created
                if not os.path.isfile(outfilepath):
                    path_dd_name = os.path.join(data_dir, name)
                    data = manage_json.gen_data_struct(path_dd_name, metadata_file)
                    with open(outfilepath, 'w') as f:
                        json.dump(data, f)
    #
    file_auth_fullpath = os.path.join(app_data_dir, "files_authorization.json")
    with open(file_auth_fullpath, 'w') as fa:
        json.dump(files_authorization, fa)

    return HttpResponse("")
"""


#####
"""
Retrieve the list of .json files to be displayed for trace selection
"""

"""
# @login_required(login_url='/login/hbp/')
def get_list_new(request):
    json_file = open(os.path.join(settings.MEDIA_ROOT, 'efel_data', 'eg_json_data', 'output.json'))
    return HttpResponse(json_file, content_type="application/json")
"""


"""
#####
# @login_required(login_url='/login/hbp/')
def features_json(request):
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    u_crr_res_r_dir = request.session['u_crr_res_r_dir']
    with open(os.path.join(u_crr_res_r_dir, 'features.json')) as json_file:
        features = json.load(json_file)
    return HttpResponse(json.dumps(features))
"""


"""
#####
# @login_required(login_url='/login/hbp/')
def features_json_path(request):
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    abs_url = request.session['media_abs_crr_user_res']
    full_feature_json_file = os.path.join(abs_url, 'features.json')
    return HttpResponse(json.dumps({'path': full_feature_json_file}))
"""


"""
#####
# @login_required(login_url='/login/hbp/')
def features_json_files_path(request):
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    abs_url = request.session['media_abs_crr_user_res']
    return HttpResponse(json.dumps({'path': abs_url}))
"""


"""
#####
# @login_required(login_url='/login/hbp/')
def protocols_json_path(request):
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'protocols.json')
    return HttpResponse(json.dumps({'path': os.path.join(os.sep, full_feature_json_file)}))
"""


"""
#####
# @login_required(login_url='/login/hbp/')
def features_pdf_path(request):
    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    rel_url = request.session['media_rel_crr_user_res']
    full_feature_json_file = os.path.join(rel_url, 'features_step.pdf')
    return HttpResponse(json.dumps({'path': os.path.join(os.sep, full_feature_json_file)}))
"""


"""
# @login_required(login_url='/login/hbp/')
def get_directory_structure(request):
    Creates a nested dictionary that represents the folder structure of root_dir

    # if not ctx exit the application
    if "ctx" not in request.session:
        return render(request, 'efelg/hbp_redirect.html')

    # accesslogger.info(resources.string_for_log('get_directory_structure', request))
    root_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data')
    root_dir = root_dir.rstrip(os.sep)
    start = root_dir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(root_dir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = functools.reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    with open(os.path.join(settings.BASE_DIR, 'static', 'efel_features_final.json')) as json_file:
        features = json.load(json_file)
    return HttpResponse(json.dumps(features))
"""

"""
# handle file upload to storage collab
def upload_zip_file_to_storage(request):
    #TODO: get token
    access_token = {'token': 'token'} # get_access_token(request.user.social_auth.get())
    # retrieve data from request.session
    headers = request.session['headers']
    collab_id = request.session['collab_id']
    st_rel_user_results_folder = request.session['st_rel_user_results_folder']
    st_rel_user_uploaded_folder = request.session['st_rel_user_uploaded_folder']
    crr_user_folder = request.session['time_info']
    output_path = request.session['result_file_zip']
    context = request.session['context']
    # services = bsc.get_services()

    # get clients from bbp python packages
    # oidc_client = BBPOIDCClient.bearer_auth(services['oidc_service']['prod']['url'], access_token)
    # bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    # doc_client = DocClient(services['document_service']['prod']['url'], oidc_client)

    context = request.session['context']
    # logout(request)
    next_url = urllib.quote('%s?ctx=%s' % (request.path, context))

    # extract project from collab_id
    # project = doc_client.get_project_by_collab_id(collab_id)

    # extract collab storage root path
    # storage_root = doc_client.get_path_by_id(project["_uuid"])
    # crr_collab_storage_folder = os.path.join(storage_root, st_rel_user_results_folder)
    # if not doc_client.exists(crr_collab_storage_folder):
    #     doc_client.makedirs(crr_collab_storage_folder)
    #
    # final zip collab storage path
    # zip_collab_storage_path = os.path.join(crr_collab_storage_folder, crr_user_folder + '_results.zip')
    #
    # bypassing uploading data to collab storage
    # if not doc_client.exists(zip_collab_storage_path):
    #     doc_client.upload_file(output_path, zip_collab_storage_path)
    #
        # render to html page
    return HttpResponse("")
"""
