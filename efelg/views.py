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
import json
import re
from . import manage_json
try:
    import cPickle as pickle
except:
    import pickle
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
    #return HttpResponse(json.dumps(selected_traces_rest_json))
    return render(request, 'efelg/select_features.html', {'feature_names': feature_names, 'features_dict': features_dict})


@login_required(login_url='/login/hbp')
@csrf_exempt
def upload_files_page(request):
    return render(request, 'upload_files_page.html')

# handle select_files template
@login_required(login_url='/login/hbp')
def select_files(request):
    all_name_list = []
    data_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'app_data')
    request.session['data_dir'] = data_dir
    etype = ['bAC','cAC','cNAC', ]
    request.session['etype'] = etype
    #for all the directories and files contained downwards in the dir tree
    for dirName, subdirList, fileList in os.walk(data_dir):
        # for every file, if it is an .abf, save its full path
        for fname in fileList:
            if fname[-4:]=='.abf':
                crrfullname = os.path.join(dirName, fname);
                all_name_list.append(crrfullname);

    # sort list
    all_name_list.sort

    # create session variable with all current path 
    request.session['all_name_list'] = all_name_list

    # create dictionary for all cell type
    cell_type_plt = {};
    cell_type_dict = {};
    for crr_file in all_name_list:
        crr_key = []
        crr_file_rel_path = crr_file[len(data_dir) + 1:]
        for crr_etype in etype:
            idx = crr_file_rel_path.find(crr_etype) 
            if idx != -1:
                crr_key = crr_file_rel_path[:idx + len(crr_etype)]
                crr_fin_name = crr_file_rel_path[idx + len(crr_etype):]
        r = neo.io.AxonIO(crr_file)
        bl = r.read_block(lazy=False, cascade=True)
        all_volt_val = []
        for i_seg, seg in enumerate(bl.segments):
            voltage = numpy.array(seg.analogsignals[0]).astype(numpy.float64)
            voltage = voltage.tolist()
            all_volt_val.append(voltage)
        if crr_fin_name in cell_type_plt:
            cell_type_plt[crr_fin_name].append(all_volt_val)
        else:
            cell_type_plt[crr_fin_name] = all_volt_val
            if crr_key in cell_type_dict:
                cell_type_dict[crr_key].append(crr_fin_name)
            else:
                cell_type_dict[crr_key] = [crr_fin_name]
            #break
    # for every abf file separate
    cell_type_plt = json.dumps(cell_type_plt)    
    return render_to_response('select_files.html', {'file_dict': cell_type_dict, 'file_plots': cell_type_plt, 'temp_var': all_name_list})

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
    full_crr_uploaded_folder = request.session['full_crr_uploaded_folder']
    

    if os.path.isfile(os.path.join(json_dir, cellname) + '.json'):
        cellname_path = os.path.join(json_dir, cellname) + '.json'
    elif os.path.isfile(os.path.join(full_crr_uploaded_folder, cellname) + '.json'):
        cellname_path = os.path.join(full_crr_uploaded_folder, cellname) + '.json'

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
    selected_traces_rest_json = request.session['selected_traces_rest_json'] 
    crr_user_folder = request.session['crr_user_folder'] 
    full_crr_result_folder = request.session['full_crr_result_folder']
    full_crr_uploaded_folder = request.session['full_crr_uploaded_folder']
    full_crr_data_folder = request.session['full_crr_data_folder']
    full_crr_user_folder = request.session['full_crr_user_folder']
    json_dir = request.session['json_dir']
    
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
        #return HttpResponse(json.dumps({'1': crr_file_dict}))
        
        crr_file_all_stim = crr_file_dict['traces'].keys()
        crr_file_sel_stim = selected_traces_rest_json[k]
        #return HttpResponse(json.dumps({'1': crr_file_sel_stim, '2': crr_file_all_stim}))

        crr_abf_file_path = crr_file_dict['abfpath']
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
   
    #return HttpResponse(json.dumps({'1': cell_dict}))
    
    final_cell_dict = {}  
    for key in cell_dict:
        crr_el = cell_dict[key]
        all_ch_stim = [item for sublist in crr_el['stim'] for item in sublist]
        crr_diff_stim = list(set(crr_el['all_stim']) - set(all_ch_stim))
        crr_exc = [float(i) for i in crr_diff_stim]
        final_cell_dict[cell_dict[key]['cell_name']] = {'v_corr':False, 'ljp':0, 'experiments':{'step': {'location':'soma', 'files': [str(i) for i in crr_el['files']]}}, 'etype':'etype', 'exclude':list(set(crr_exc))}
        
        #cell_dict[cell] = {'v_corr':False, 'ljp':0, 'experiments':{'step': {'location':'soma', 'files': [str(i) for i in final_param_file_dict[cell]]}}, 'etype':str(act_etype), 'exclude':list(set(crr_exc))}
    # build configuration dictionary
    config = {}
    config['features'] = {'step':[str(i) for i in check_features]}
    config['path'] = full_crr_data_folder
    config['format'] = 'axon'
    config['comment'] = []
    config['cells'] = final_cell_dict
    config['options'] = {'relative': False, 'tolerance': 0.02, 'target': [-1.0, -0.8, -0.6, -0.4, -0.2, 0.2, 0.4, 0.6, 0.8, 1.0], 'delay': 500, 'nanmean': False}
    #return HttpResponse(json.dumps({'1': config}))

    #return HttpResponse(json.dumps({'1': config}))
    extractor = bpext.Extractor(full_crr_result_folder, config)
    extractor.create_dataset()
    extractor.plt_traces()
    extractor.extract_features()
    extractor.mean_features()
    extractor.plt_features()
    extractor.feature_config_cells()
    extractor.feature_config_all()

    crr_result_folder = request.session['crr_result_folder']
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


    shutil.copy(os.path.join(full_crr_result_folder, 'features_step.pdf'), os.path.join(settings.BASE_DIR, 'static'))
    shutil.copy(os.path.join(full_crr_result_folder, 'protocols.json'), os.path.join(settings.BASE_DIR, 'static'))
    shutil.copy(os.path.join(full_crr_result_folder, 'features.json'), os.path.join(settings.BASE_DIR, 'static'))
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
def overview(request):
    request.user.social_auth.get()
    request.user.username
    services = bsc.get_services()
    access_token = get_access_token(request.user.social_auth.get())

    oidc_client = BBPOIDCClient.bearer_auth(services['oidc_service']['prod']['url'], access_token)
    bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    doc_client = DocClient(services['document_service']['prod']['url'], oidc_client)
    context_uuid = UUID(request.GET.get('ctx'))
    context = request.GET.get('ctx')
    svc_url = settings.HBP_COLLAB_SERVICE_URL
    url = '%scollab/context/%s/' % (svc_url, context)
    headers = {'Authorization': get_auth_header(request.user.social_auth.get())}
    res = requests.get(url, headers=headers)
    collab_id = res.json()['collab']['id']
    url = '%scollab/%s/permissions/' % (svc_url, collab_id)

    data_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'app_data')
    json_dir = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'json_data')
    full_result_folder = os.path.join(settings.BASE_DIR, 'media', 'efel_data', 'users_results')
    crr_user_folder = 'efel_hbp_'  + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    crr_result_folder = 'crr_result'
    crr_uploaded_folder = 'crr_uploaded'
    crr_data_folder = 'crr_data'

    # build complete paths
    full_crr_user_folder = os.path.join(full_result_folder, crr_user_folder) 
    full_crr_result_folder = os.path.join(full_crr_user_folder, crr_result_folder) 
    full_crr_uploaded_folder = os.path.join(full_crr_user_folder, crr_uploaded_folder) 
    full_crr_data_folder = os.path.join(full_crr_user_folder, crr_data_folder) 

    #
    request.session['data_dir'] = data_dir
    request.session['json_dir'] = json_dir
    request.session['crr_user_folder'] = crr_user_folder
    request.session['crr_result_folder'] = crr_result_folder
    request.session['full_result_folder'] = full_result_folder
    request.session['full_crr_result_folder'] = full_crr_result_folder
    request.session['full_crr_user_folder'] = full_crr_user_folder
    request.session['full_crr_uploaded_folder'] = full_crr_uploaded_folder
    request.session['full_crr_data_folder'] = full_crr_data_folder
    etype = ['bAC','cAC','cNAC', 'udEt']
    request.session['etype'] = etype

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    if not os.path.exists(full_result_folder):
        os.makedirs(full_result_folder)

    if not os.path.exists(full_crr_result_folder):
        os.makedirs(full_crr_result_folder)

    if not os.path.exists(full_crr_uploaded_folder):
        os.makedirs(full_crr_uploaded_folder)
    services = bsc.get_services()

    task_client = bbp_client.client.TaskClient(get_services()['task_service']['prod']['url'], bearer_client)
    prov_client = bbp_client.client.ProvClient(get_services()['prov_service']['prod']['url'], bearer_client)
    document_client = bbp_client.client.DocumentClient(get_services()['document_service']['prod']['url'], bearer_client)
    mimetype_client = bbp_client.client.MIMETypeClient(get_services()['mimetype_service']['prod']['url'])

    myclient =  bbp_client.client.Client(task_client = task_client, prov_client = prov_client, document_client = document_client,    mimetype_client = mimetype_client)
    storage = myclient.document
    #myclient =  bbp_client.client.Client(task_client = bbp_client.client.TaskClient(get_services()['task_service']['prod']['url'], bearer_client), prov_client = bbp_client.client.ProvClient(get_services()['prov_service']['prod']['url'], bearer_client), document_client = bbp_client.client.DocumentClient(get_services()['document_service']['prod']['url'], bearer_client),    mimetype_client = bbp_client.client.MIMETypeClient(get_services()['mimetype_service']['prod']['url']))
    
    hdr = myclient.task.oauth_client.get_auth_header()
    resp = requests.get('https://services.humanbrainproject.eu/collab/v0/collab/context/' + context + '/permissions/', headers={'Authorization': hdr}, verify=False)

    get_collab_storage_path = lambda: ('/' + myclient.document.get_project_by_collab_id('1256')['_name']) 

    return render(request, 'efelg/overview.html',{'temp_var': {'1': request.user.username, '2': request.session.items(), '3': get_access_token(request.user.social_auth.get()), '4': storage, '5': services, '6': collab_id, '7': DocClient.getcwd(doc_client), '8': bearer_client}})

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
        #selected_traces = request.POST.getlist('check_traces')
        #selected_traces = request.POST.getlist('check_traces')
        #request.session['selected_traces'] = selected_traces
        #feature_names = efel.getFeatureNames()
        #return HttpResponse(request, 'select_features.html', {'feature_names': feature_names, 'features_dict': features_dict})
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
def upload_files(request):
    """
    Upload file to local folder
    """
    full_crr_uploaded_folder = request.session['full_crr_uploaded_folder']
    for root, dirs, files in os.walk(full_crr_uploaded_folder):
        for f in files:
            os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    user_files = request.FILES.getlist('user_files')
    data_name_dict = {"all_json_names" : []}
    logger.info('uploading')
    for k in user_files:
        crr_file_name = k.name
        logger.info(crr_file_name)
        final_file = open(os.path.join(full_crr_uploaded_folder, crr_file_name), 'w')
        if k.multiple_chunks():
            for chunk in k.chunks():
                final_file.write(chunk)
            final_file.close()
        else:
            final_file.write(k.read())
            final_file.close()

    for root, dirs, files in os.walk(full_crr_uploaded_folder):
        for name in files:
            if name.endswith('.abf'):
                logger.info(name)
                infilepath = os.path.join(root, name)
                logger.info(infilepath)
                outfilename = '_'.join(manage_json.getCellInfo(infilepath, True)) + '.json'
                logger.info(outfilename)
                outfilepath = os.path.join(full_crr_uploaded_folder, outfilename)
                if not os.path.isfile(outfilepath):
                    data = manage_json.genDataStruct(infilepath, True)
                    logger.info('uploading data')
                    logger.info(outfilepath)
                    with open(outfilepath, 'w') as f:
                        json.dump(data, f)
                if outfilename[:-5] not in data_name_dict['all_json_names']:
                    data_name_dict['all_json_names'].append(outfilename[:-5])
    
    return HttpResponse(json.dumps(data_name_dict), content_type="application/json") 

@login_required(login_url='/login/hbp')
def get_progress(request):


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
