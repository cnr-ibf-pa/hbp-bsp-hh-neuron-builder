import functools
import math
import re
import shutil
import urllib.parse as urllib
import zipfile

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest

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


def overview(request, wfid=None):
    """
    Render the NeuroFeatureExtract main page
    """
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'anonymous'

    if wfid:
        time_info = wfid.split('_')[0]
    else:
        time_info = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    # save username and time info in the session variable dictionary
    request.session["username"] = username
    request.session["time_info"] = time_info

    # update session variable dictionary
    request.session.save()
    return render(request, 'efelg/overview.html')


def select_features(request):
    """
    Render the application select-features page
    """

    # if not context variable exists exit the application
    if not request.session.get("is_free_space_enough"):
        # display error page
        return redirect('/efelg/error_space_left/')

    # get all feature names
    feature_names = efel.getFeatureNames()
    selected_traces_rest = request.POST.get('data')
    request.session['selected_traces_rest_json'] = \
        json.loads(selected_traces_rest)
    request.session['global_parameters_json'] = \
        json.loads(request.POST.get('global_parameters'))

    return render(request, 'efelg/select_features.html')


def show_traces(request):
    """
    Render the trace selection page
    """

    # check the space left on disk and show a message in case >10GB are left
    if EfelStorage.isThereEnoughFreeSpace():
        request.session['is_free_space_enough'] = True
    else:
        request.session['is_free_space_enough'] = False
        return redirect('/efelg/error_space_left/')
    #
    return render(request, 'efelg/show_traces.html')


def get_list(request):
    """"
    Retrieve the list of .json data files to be displayed for trace selection
    """

    # if no context variable is present exit the application
    if not request.session.get("is_free_space_enough"):
        return redirect('/efelg/error_space_left/')

    metadata_path = os.path.join(
        EfelStorage.getMainJsonDir(), "all_traces_metadata.json")

    try:
        r = requests.get(EfelStorage.getMetadataTracesUrl())
        if 200 <= r.status_code <= 299:
            with open(metadata_path, "w") as f:
                json.dump(r.json(), f)
            output_json = r.json()
        else:
            with open(metadata_path, "r") as f:
                output_json = json.load(f)
    except:
        print("Error loading metadata!")

    return HttpResponse(json.dumps(output_json),
                        content_type="application/json")


def get_data(request, cellname=""):
    """
    Get eletctrophysiological data to be displayed
    """

    # if not enough space is left display error page
    if not request.session.get("is_free_space_enough"):
        # display error page
        return redirect('/efelg/error_space_left/')

    user_files_dir = EfelStorage.getUserFilesDir(request.session['username'],
                                                 request.session['time_info'])
    traces_files_dir = EfelStorage.getTracesDir()

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

    # extract data sampling rate
    disp_sampling_rate = 5000
    if type(content['sampling_rate']) == list:
        crr_sampling_rate = int(content['sampling_rate'][0])
    else:
        crr_sampling_rate = int(content['sampling_rate'])

    # compute downsampled rate for display purposes exclusively
    coefficient = int(math.floor(crr_sampling_rate / disp_sampling_rate))
    if coefficient < 1:
        coefficient = 1
        disp_sampling_rate = crr_sampling_rate

    # create dictionary to be sent to the frontend
    trace_info = {}
    trace_info['traces'] = {}
    for key in content['traces'].keys():
        trace_info['traces'][key] = content['traces'][key][::coefficient]

    trace_info['coefficient'] = coefficient
    trace_info['disp_sampling_rate'] = disp_sampling_rate
    trace_info['md5'] = content['md5']
    trace_info['sampling_rate'] = content['sampling_rate']
    trace_info['etype'] = content['etype']

    keys = [
        "md5", "sampling_rate", "etype", "cell_type", "cell_id",
        "brain_structure", "filename", "animal_species", "cell_soma_location",
        "stimulus_unit", "voltage_unit", "contributors_affiliations"
    ]
    for key in keys:
        if key in content:
            trace_info[key] = content[key]
        else:
            trace_info[key] = 'unknown'

    if "note" in content:
        trace_info["note"] = content["note"]

    return HttpResponse(json.dumps(json.dumps(trace_info)), content_type="application/json")


def extract_features(request):
    """
    Extract features from the selected traces
    """

    # if not enough space is left on disk display error page
    if not request.session.get("is_free_space_enough"):
        # render error page
        return redirect('/efelg/error_space_left/')

    # get variables from the session dictionary
    selected_traces_rest_json = request.session['selected_traces_rest_json']
    global_parameters_json = request.session['global_parameters_json']
    username = request.session['username']
    time_info = request.session['time_info']

    # get feature names
    allfeaturesnames = efel.getFeatureNames()

    # get folder paths for feature extraction
    conf_dir = EfelStorage.getMainJsonDir()
    traces_files_dir = EfelStorage.getTracesDir()
    user_files_dir = EfelStorage.getUserFilesDir(username, time_info)
    user_results_dir = EfelStorage.getResultsDir(username, time_info)

    # get features selected by the user
    selected_features = request.session["selected_features"]

    # initialize final cell dictionary
    final_cell_dict = {}

    # initialize final target values array
    target = []

    # initialize final exclude values array
    final_exclude = []

    # build data configuration dictionary for every cell
    for k in selected_traces_rest_json:
        path_to_file = os.path.join(user_files_dir, k + '.json')
        if k + '.json' not in os.listdir(user_files_dir):
            shutil.copy2(os.path.join(traces_files_dir, k + '.json'),
                         path_to_file)
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

        new_keys = ["animal_species", "brain_structure",
                    "cell_soma_location", "cell_type", "etype", "cell_id"]

        keys = [crr_file_dict[t] for t in new_keys]
        keys2 = []
        for kk2 in keys:
            if not type(kk2) == list:
                keys2.append(kk2)
            else:
                for kkk in kk2:
                    keys2.append(kkk)

        crr_key = '____'.join(keys2)

        # update final target array
        for c_stim_el in crr_file_sel_stim:
                if float(c_stim_el) not in target:
                    target.append(float(c_stim_el))

        # extract stimuli to be excluded
        exc_stim_lists = []
        for cstim in crr_file_all_stim:
            if cstim not in crr_file_sel_stim:
                exc_stim_lists.append(float(cstim))

        if crr_cell_name not in final_cell_dict:
            # create cell dict
            final_cell_dict[crr_cell_name] = {}

            # set etype and ljp (common for all files)
            final_cell_dict[crr_cell_name]['etype'] = 'etype'
            final_cell_dict[crr_cell_name]['ljp'] = 0
            
            # initialize arrays
            final_cell_dict[crr_cell_name]['exclude'] = []
            final_cell_dict[crr_cell_name]['exclude_unit'] = []
            final_cell_dict[crr_cell_name]['experiments'] = \
                {'step': {'files': [], 'location':'soma'}}
            final_cell_dict[crr_cell_name]['v_corr'] = []

        # append current file name
        final_cell_dict[crr_cell_name]['experiments']['step']['files'].append(
            k)
        
        # set list of stimuli to be excluded
        final_cell_dict[crr_cell_name]['exclude'].append(exc_stim_lists)

        # set exclude unit
        final_cell_dict[crr_cell_name]['exclude_unit'].append(
            crr_file_amp_unit)

        # set v_corr
        final_cell_dict[crr_cell_name]['v_corr'].append(
            int(selected_traces_rest_json[k]['v_corr']))
  
    # build option configuration dictionary for the feature extraction
    config = {}
    config['features'] = {'step': [str(i) for i in selected_features]}
    config['path'] = user_files_dir
    config['format'] = 'ibf_json'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {
        'zero_to_nan': {
            'flag': bool(global_parameters_json['zero_to_nan']),
            'value': global_parameters_json['value'],
            'mean_features_no_zeros':
            global_parameters_json['mean_features_no_zeros']
        },
        'relative': False,
        'tolerance': 0.02,
        'target': target,
        'target_unit': 'nA',
        'delay': 500,
        'nanmean': True,
        'logging': True,
        'nangrace': 0,
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

    # launch the feature extraction process
    try:
        main_results_folder = os.path.join(user_results_dir,
                                           time_info + "_nfe_results")
        extractor = bpefe.Extractor(main_results_folder, config)
        extractor.create_dataset()
        extractor.plt_traces()
        if global_parameters_json['threshold'] != '':
            extractor.extract_features(threshold=int(
                global_parameters_json['threshold']))
        else:
            extractor.extract_features(threshold=-20)
        extractor.mean_features()
        extractor.plt_features()
        extractor.feature_config_cells(version="legacy")
        extractor.feature_config_all(version="legacy")
    except ValueError as e:
        print('SOME ERROR OCCURED')
        print(e)

    # manage how to cite instructions
    conf_cit = os.path.join(conf_dir, 'citation_list.json')
    final_cit_file = os.path.join(main_results_folder, 'HOWTOCITE.txt')
    resources.print_citations(selected_traces_rest_json, conf_cit,
                              final_cit_file)

    # set result .zip file parameters
    zip_name = time_info + '_nfe_results.zip'
    zip_path = os.path.join(user_results_dir, zip_name)
    request.session['nfe_result_file_zip'] = zip_path
    request.session['nfe_result_file_zip_name'] = zip_name

    for k in selected_traces_rest_json:
        f = os.path.join(user_results_dir, k + ".json")
        if os.path.exists(f):
            os.remove(f)

    # create result .zip files
    contents = os.walk(main_results_folder)
    try:
        zip_file = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(main_results_folder +
                                                      os.sep, '')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(main_results_folder +
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

    return HttpResponse(json.dumps({"status": "OK"}))


def results(request):
    """
    Render result page
    """

    # if not enough space is left on disk display error page
    if not request.session.get("is_free_space_enough"):
        # render error page
        return redirect('/efelg/error_space_left/')

    # render final page containing the link to the result zip file if any
    request.session["selected_features"] = \
        request.POST.getlist('crr_feature_check_features')
    return render(request, 'efelg/results.html')


def download_zip(request):
    """
    Provide file to be downloaded
    """

    # if not enough space is left on disk display error page
    if not request.session.get("is_free_space_enough"):
        # render html page
        return redirect('/efelg/error_space_left/')

    zip_file = open(request.session['nfe_result_file_zip'], 'rb')
    response = HttpResponse(
        zip_file, content_type='application/force-download')
    response['Content-Disposition'] = \
        'attachment; filename="%s"' % \
        request.session['nfe_result_file_zip_name']
    return response


def features_dict(request):
    """
    Return the feature dictionary containing all feature names, 
    grouped by feature type
    """

    # if not enough space is left on disk display error page
    if not request.session.get("is_free_space_enough"):
        return redirect('/efelg/error_space_left/')

    with open(os.path.join(settings.BASE_DIR, 'static', 'efelg',
                           'efel_features_final.json')) as json_file:
        features = json.load(json_file)
    return HttpResponse(json.dumps(features))


@csrf_exempt
def upload_files(request):

    if not request.session.get("is_free_space_enough"):
        return redirect('/efelg/error_space_left/')

    username = request.session['username']
    time_info = request.session['time_info']

    # get user's folders
    upload_files_dir = EfelStorage.getUploadedFilesDir(username, time_info)
    user_files_dir = EfelStorage.getUserFilesDir(username, time_info)

    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    if request.POST["file_name"] != "":
        for old_filename in request.POST["file_name"].split(","):
            old_filepath = os.path.join(user_files_dir, old_filename)
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
            #try:
            data = manage_json.extract_data(f, request.POST)
            output_filename = manage_json.create_file_name(data)
            output_filepath = os.path.join(user_files_dir, output_filename)
            if os.path.isfile(output_filepath):
                os.remove(output_filepath)
            with open(output_filepath, 'w') as f:
                json.dump(data, f)
            data_name_dict['all_json_names'].append(output_filename)
            #except:
            #    data_name_dict['refused_files'].append(f[f.rindex("/")+1:])

    return HttpResponse(json.dumps(data_name_dict), content_type="application/json")


def get_result_dir(request):
    """
    Return results dir
    """

    # if not enough space is left on disk display error page
    if not request.session.get("is_free_space_enough"):
        return redirect('/efelg/error_space_left/')

    user_results_dir = \
        EfelStorage.getResultsDir(request.session['username'],
                                  request.session['time_info'])
    data = {'result_dir': user_results_dir}
    return JsonResponse(data=json.dumps(data), status=200, safe=False)


def index_docs(request):
    """
    Render Guidebook main page
    """
    return render(request, 'efelg/docs/index.html')


def file_formats_docs(request):
    """
    Render Guidebook file formats page
    """
    return render(request, 'efelg/docs/file_formats.html')


def get_dataset(request):
    """
    Return dataset metadata
    """

    with open(os.path.join(settings.BASE_DIR,
                           'static', 'efelg', 'dataset.json')) as json_file:
        dataset = json.load(json_file)
    return HttpResponse(json.dumps(dataset))


def dataset(request):
    """
    Return Guidebook dataset page
    """

    return render(request, 'efelg/docs/dataset.html')


def hhf_etraces(request):
    """ 
    Render NFE trace selection page in case electrophysiological signals have
    been sent from the Hippocampus Hub
    """
    
    exc = request.GET.get('exc')
    hhf_etraces_dir = request.session[exc].get('hhf_etraces_dir')
    wfid = request.GET.get('wfid')

    r = overview(request, wfid)
    context = {'hhf_etraces_dir': hhf_etraces_dir, 'wfid': wfid}
    return render(request, 'efelg/show_traces.html', context)


@csrf_exempt
def load_hhf_etraces(request):

    # if not enough space is left on disk display error page
    if EfelStorage.isThereEnoughFreeSpace():
        request.session['is_free_space_enough'] = True
    else:
        request.session['is_free_space_enough'] = False
        return redirect('/efelg/error_space_left/')

    # get directory where traces sent from the hippocampus hub have been sent
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
                return HttpResponse(json.dumps({'resp': 'KO', 'message':
                                                'key error occurred'}))

    time_info, username = wfid.split('_')
    data_name_dict = {
        "all_json_names": [],
        "refused_files": []
    }

    try:
        if hhf_etraces_dir == 'True':
            for k in request.session.keys():
                try:
                    if ('wf_id' in request.session[k].keys() and
                            request.session[k]['wf_id'] == wfid):
                        try:
                            hhf_etraces_dir = \
                                request.session[k]['hhf_etraces_dir']
                        except:
                            # if exception is thrown then "hhf_etraces_dir" is
                            # not present and an error code is returned
                            return JsonResponse({'resp': 'KO', 'message':
                                                 'etraces dir not present error'
                                                 })
                except AttributeError:
                    continue

        # save data files sent from the HippocampusHub in the appropriate folder
        for f in os.listdir(hhf_etraces_dir):
            if not f.endswith('.abf'):
                continue
            #try:
            with open(os.path.join(hhf_etraces_dir, f[:-4] + '_metadata.json'), 'r') as fd:
                metadata_dict = json.load(fd)
            data = manage_json.extract_data(os.path.join(hhf_etraces_dir, f), metadata_dict=metadata_dict)
            output_filename = manage_json.create_file_name(data)
            output_filename = output_filename.replace(' ', '_')
            with open(os.path.join(EfelStorage.getUserFilesDir(
                    username, time_info), output_filename), 'w') as fd:
                json.dump(data, fd, indent=4)
            if output_filename[:-5] not in data_name_dict['all_json_names']:
                data_name_dict['all_json_names'].append(
                   output_filename[:-5])
            #except Exception as e:
            #    print('metadata not found')

    except FileNotFoundError:
        return HttpResponse(json.dumps({'resp': 'KO', 'message':
                                        'file not found error'}))

    
    return HttpResponse(json.dumps(data_name_dict),
                        content_type="application/json")


def error_space_left(request):
    """
    Render no-space-left error page
    """

    return render(request, 'efelg/error_space_left.html')
