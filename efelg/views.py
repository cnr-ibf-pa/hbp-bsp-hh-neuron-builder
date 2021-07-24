import functools
import math
import re
import shutil
import urllib.parse as urllib
import zipfile

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse, HttpResponseBadRequest

from hh_neuron_builder import settings
from efelg.tools import resources, manage_json
from efelg.tools.manage_storage import EfelStorage

import efel
import requests
import datetime
import logging
import sys
import os
import json

import bluepyefe as bpefe


# Create your views here.


def overview(request, wfid=None):
    """
    This function serves the first page of the NFE and instantiates the environment variables
    """

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'anonymous'
  
    # if Efelg is run from HHNB the workflow ID is set as time_info to successfully retrive session variables
    if wfid:
        time_info = wfid.split('_')[0]
    else:
        time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    
    request.session["username"] = username
    request.session["time_info"] = time_info
    
    request.session.save()
    return render(request, 'efelg/overview.html')


def select_features(request):
    """
    This function serves the application select-features page
    """

    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    # feature_names = efel.getFeatureNames() ## unused variable ?
    selected_traces_rest = request.POST.get('data')
    request.session['selected_traces_rest_json'] = json.loads(selected_traces_rest)
    request.session['global_parameters_json'] = json.loads(request.POST.get('global_parameters'))
    return render(request, 'efelg/select_features.html')


def show_traces(request):

    if EfelStorage.isThereEnoughFreeSpace():
        request.session['is_free_space_enough'] = True
    else:
        request.session['is_free_space_enough'] = False
        return redirect('/efelg/error_space_left/')
      
    return render(request, 'efelg/show_traces.html')


def get_list(request):
    """"
    Retrieve the list of .json files to be displayed for trace selection
    """
    
    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')
    
    output_file_path = os.path.join(EfelStorage.getMainJsonDir(), 'all_traces_metadata.json')

    try:
        with open(output_file_path, 'r') as f:
            output_json = json.load(f)
    except FileNotFoundError:
        return HttpResponse()

    return HttpResponse(json.dumps(output_json), content_type="application/json")


def get_data(request, cellname=""):
    """
    Return trace's information about the cell, passed as cellname, as a dictionary
    """
    
    print('get_data() called.')

    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    #current_authorized_files = request.session["current_authorized_files"]

    user_files_dir = EfelStorage.getUserFilesDir(request.session['username'], request.session['time_info'])
    traces_files_dir = EfelStorage.getTracesDir()

    # if the trace file exists on the disk will be used it otherwise it will be fetch from the server
    file_name = cellname + ".json"
    if file_name in os.listdir(user_files_dir): 
        path_to_file = os.path.join(user_files_dir, file_name)
    else:
        path_to_file = os.path.join(traces_files_dir, file_name)
        if not file_name in os.listdir(traces_files_dir):
            r = requests.get(EfelStorage.getTracesBaseUrl() + file_name)
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

    coefficient = int(math.floor(crr_sampling_rate / disp_sampling_rate))
    if coefficient < 1:
        coefficient = 1
        disp_sampling_rate = crr_sampling_rate

    # downsampling
    trace_info = {}
    trace_info['traces'] = {}
    for key in content['traces'].keys():
        trace_info['traces'][key] = content['traces'][key][::coefficient]

    trace_info['coefficient'] = coefficient
    trace_info['disp_sampling_rate'] = disp_sampling_rate
    trace_info['md5'] = content['md5']
    trace_info['sampling_rate'] = content['sampling_rate']
    trace_info['etype'] = content['etype']

    new_keys = {
        "type": "cell_type",
        "name": "cell_id",
        "area": "brain_structure",
        "sample": "filename",
        "species": "animal_species",
        "region": "cell_soma_location",
        "amp_unit": "stimulus_unit",
        "volt_unit": "voltage_unit",
        "v_unit": "voltage_unit"
    }

    for key in new_keys:
        if new_keys[key] in content:
            trace_info[new_keys[key]] = content[new_keys[key]]
        elif key in content:
            trace_info[new_keys[key]] = content[key]
        else:
            trace_info[new_keys[key]] = 'unknown'

    if 'contributors_affiliations' in content:
        trace_info['contributors_affiliations'] = content['contributors_affiliations']
    elif 'name' in content['contributors']:
        trace_info['contributors_affiliations'] = content['contributors']['name']
    else:
        #raise Exception("contributors_affiliations not found!")
        trace_info['contributors_affiliations'] = 'unknown'

    if "note" in content:
        trace_info["note"] = content["note"]

    return HttpResponse(json.dumps(json.dumps(trace_info)), content_type="application/json")


def extract_features(request):
    """

    """

    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    selected_traces_rest_json = request.session['selected_traces_rest_json']
    global_parameters_json = request.session['global_parameters_json']
    allfeaturesnames = efel.getFeatureNames()

    username = request.session['username']
    time_info = request.session['time_info']

    # retrieve all user's workflow paths
    conf_dir = EfelStorage.getMainJsonDir()
    # traces_files_dir = request.session['user_files_dir']
    traces_files_dir = EfelStorage.getTracesDir()
    # user_files_dir = request.session['user_files_dir']
    user_files_dir = EfelStorage.getUserFilesDir(username, time_info)
    user_results_dir = EfelStorage.getResultsDir(username, time_info)

    selected_features = request.session["selected_features"]

    cell_dict = {}

    for k in selected_traces_rest_json:
        path_to_file = os.path.join(user_files_dir, k + '.json')
        if k + '.json' not in os.listdir(user_files_dir):
            shutil.copy2(os.path.join(traces_files_dir, k + '.json'), path_to_file)
        with open(path_to_file) as f:
            crr_file_dict = json.loads(f.read()) 
        crr_file_all_stim = list(crr_file_dict['traces'].keys())
        crr_file_sel_stim = selected_traces_rest_json[k]['stim']

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

        new_keys = ["animal_species", "brain_structure", "cell_soma_location", "cell_type", "etype", "cell_id"]

        keys = [crr_file_dict[t] for t in new_keys]
        keys2 = []
        for kk2 in keys:
            if not type(kk2) == list:
                keys2.append(kk2)
            else:
                for kkk in kk2:
                    keys2.append(kkk)

        crr_key = '____'.join(keys2)

        cell_dict[crr_key] = {}
        cell_dict[crr_key]['stim'] = [crr_file_sel_stim]
        cell_dict[crr_key]['files'] = [k]
        cell_dict[crr_key]['cell_name'] = crr_cell_name
        cell_dict[crr_key]['all_stim'] = crr_file_all_stim
        cell_dict[crr_key]['v_corr'] = [int(selected_traces_rest_json[k]['v_corr'])]

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
        print('SOME ERROR OCCUREED')
        print(e)

    conf_cit = os.path.join(conf_dir, 'citation_list.json')
    final_cit_file = os.path.join(main_results_folder, 'HOWTOCITE.txt')
    resources.print_citations(selected_traces_rest_json, conf_cit, final_cit_file)

    zip_name = time_info + '_nfe_results.zip'
    zip_path = os.path.join(user_results_dir, zip_name)
    request.session['nfe_result_file_zip'] = zip_path
    request.session['nfe_result_file_zip_name'] = zip_name

    for k in selected_traces_rest_json:
        f = os.path.join(user_results_dir, k + ".json")
        if os.path.exists(f):
            os.remove(f)

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

    # accesslogger.info(resources.string_for_log('extract_features', request, page_spec_string='___'.join(check_features)))
    return HttpResponse(json.dumps({"status": "OK"}))



def results(request):
    """
    Serve results page 
    """


    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')
    
    # Render final page containing the link to the result zip file if any

    request.session["selected_features"] = request.POST.getlist('crr_feature_check_features')
    return render(request, 'efelg/results.html')


def download_zip(request):
    """
    Return a zip file of the extracted features on the selected traces
    """
    
    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    zip_file = open(request.session['nfe_result_file_zip'], 'rb')
    response = HttpResponse(zip_file, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="%s"' % request.session['nfe_result_file_zip_name']
    return response


def features_dict(request):
    
    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    # Render the feature dictionary containing all feature names, grouped by feature type
    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg', 'efel_features_final.json')) as json_file:
        features = json.load(json_file)
    return HttpResponse(json.dumps(features))


@csrf_exempt
def upload_files(request):

    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    username = request.session['username']
    time_info = request.session['time_info']

    upload_files_dir = EfelStorage.getUploadedFilesDir(username, time_info)
    user_files_dir = EfelStorage.getUserFilesDir(username, time_info)

    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    if request.POST["file_name"] != "":
        old_filepath = os.path.join(user_files_dir, request.POST["file_name"])
        with open(old_filepath, "r") as old_file:
            data = json.load(old_file)
        os.remove(old_filepath)
        manage_json.update_file_name(data, request.POST)
        new_filename = manage_json.create_file_name(data)
        new_filepath = os.path.join(user_files_dir, new_filename)
        with open(new_filepath, "w") as new_file:
            json.dump(data, new_file)
        data_name_dict['all_json_names'].append(new_filename)
        
    else:
        names_full_path = []

        # for every files to be uploaded, save them on local folders:
        for k in request.FILES.getlist('user_files'):
            if k.name.endswith('.abf') or k.name.endswith('.json'):
                file_name = re.sub('-', '_', k.name)
                path_to_file = os.path.join(upload_files_dir, file_name)

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
                output_filename = manage_json.create_file_name(data)
                output_filepath = os.path.join(user_files_dir, output_filename)
                if os.path.isfile(output_filepath):
                    os.remove(output_filepath)
                with open(output_filepath, 'w') as f:
                    json.dump(data, f)
                data_name_dict['all_json_names'].append(output_filename)
            except:
                data_name_dict['refused_files'].append(f[f.rindex("/")+1:])   

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json")


def get_result_dir(request):

    # if not ctx exit the application
    if request.session["is_free_space_enough"] is None or request.session["is_free_space_enough"] is False:
        return redirect('/efelg/error_space_left/')

    user_results_dir = EfelStorage.getResultsDir(request.session['username'], request.session['time_info'])
    data = {'result_dir': user_results_dir}
    return JsonResponse(data=json.dumps(data), status=200, safe=False)


def index_docs(request):
    return render(request, 'efelg/docs/index.html')


def file_formats_docs(request):
    return render(request, 'efelg/docs/file_formats.html')


def hhf_etraces(request, wfid):

    print("Workflow ID: " + wfid)
    print(request.session)
    r = overview(request, wfid)
    context = {'hhf_etraces_dir': True, 'wfid': wfid} 
    return render(request, 'efelg/show_traces.html', context)


@csrf_exempt
def load_hhf_etraces(request):

    if EfelStorage.isThereEnoughFreeSpace():
        request.session['is_free_space_enough'] = True
    else:
        request.session['is_free_space_enough'] = False
        return redirect('/efelg/error_space_left/')

    hhf_etraces_dir = request.POST.get('hhf_etraces_dir', None)
    wfid = request.POST.get('wfid', None) 
    
    if not hhf_etraces_dir:
        return HttpResponseBadRequest('"hhf_etraces_dir" not found')

    try:
        username = request.session['username']
        time_info = request.session['time_info']
    except KeyError:
        if not wfid:
            try:
                wfid = request.session['wfid']
            except KeyError:
                return HttpResponse(json.dumps({'resp': 'KO', 'message': 'key error occurred'}))

    time_info, username = wfid.split('_')

    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    try:
    
        if hhf_etraces_dir == 'True':
            for k in request.session.keys():
                try:
                    if 'wf_id' in request.session[k].keys() and request.session[k]['wf_id'] == wfid:
                        try:
                            hhf_etraces_dir = request.session[k]['hhf_etraces_dir']
                        except:
                            # if exception is thrown then "hhf_etraces_dir" is not present and an error code is returned
                            return JsonResponse({'resp': 'KO', 'message': 'etraces dir not present error'})
                except AttributeError:
                    continue

        for f in os.listdir(hhf_etraces_dir):
            if not f.endswith('.abf'):
                continue
            try:
                with open(os.path.join(hhf_etraces_dir, f[:-4] + '_metadata.json'), 'r') as fd:
                    metadata_dict = json.load(fd)
                data = manage_json.extract_data(os.path.join(hhf_etraces_dir, f), metadata_dict=metadata_dict)
                output_filename = manage_json.create_file_name(data)
                output_filename = output_filename.replace(' ', '_')
                #with open(os.path.join(request.session['user_files_dir'], output_filename), 'w') as fd:
                with open(os.path.join(EfelStorage.getUserFilesDir(username, time_info), output_filename), 'w') as fd:
                    json.dump(data, fd, indent=4)
                if output_filename[:-5] not in data_name_dict['all_json_names']:
                    data_name_dict['all_json_names'].append(output_filename[:-5])
            except Exception as e:
                print('metadata not found')
    
    except FileNotFoundError:
        return HttpResponse(json.dumps({'resp':'KO', 'message': 'file not found error'}))

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json")


def error_space_left(request):
    return render(request, 'efelg/error_space_left.html')