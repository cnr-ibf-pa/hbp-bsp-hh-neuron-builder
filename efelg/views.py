from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# from hbp_login.views import login as hbp_login
from hh_neuron_builder import settings
from efelg.tools import resources

import requests
import datetime
import logging
import sys
import os


# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create logger if not in DEBUG mode
accesslogger = logging.getLogger('efelg_access.log')
accesslogger.addHandler(logging.FileHandler('efelg_access.log'))
accesslogger.setLevel(logging.DEBUG)


# Create your views here.

DEBUG = True


@login_required()
def overview(request):
    print(request.user.social_auth)

    # if not in DEBUG mode check whether authentication token is valid
    if not DEBUG:

        if 'ctx' not in request.session:
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
        headers = {'Authorization': get_auth_header(request.user.social_auth.get())}

        # build path for getting credentials
        my_url = settings.HBP_MY_USER_URL
        hbp_collab_service_url = settings.HBP_COLLAB_SERVICE_URL + 'collab/context/'

        # request user and collab details
        res = requests.get(my_url, headers=headers)
        collab_res = requests.get(hbp_collab_service_url + context, headers=headers)

        if res.status_code != 200 or collab_res.status_code != 200:
            manage_auth.Token.renewToken(request)

            headers = {'Authorization': get_auth_header(request.user.social_auth.get())}

            res = requests.get(my_url, headers=headers)
            collab_res = requests.get(hbp_collab_service_url + context, headers=headers)

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
        userid = '00001'

    # build data and json dir strings
    data_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'app_data', 'efelg_rawdata')
    main_json_dir = os.path.join(settings.MEDIA_ROOT, 'efel_data', 'eg_json_data')
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
    request.session["userid"] = 0000  # userid
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
    res_dir = os.path.join(settings.MEDIA_ROOT, "efel_data", res_dir)
    up_dir = os.path.join(settings.MEDIA_ROOT, "efel_data", r_up_dir)

    # build local folder complete paths
    u_time_f = os.path.join(userid, time_info)
    user_res_dir = os.path.join(res_dir, userid)
    user_crr_res_dir = os.path.join(res_dir, u_time_f)
    u_up_dir = os.path.join(up_dir, userid)
    u_crr_res_r_dir = os.path.join(res_dir, userid, time_info, "u_res")
    u_crr_res_d_dir = os.path.join(res_dir, userid, time_info, 'u_data')

    # build media relative result path
    media_rel_crr_user_res = os.path.join('media', 'efel_data', res_dir, userid, time_info, 'u_res')
    media_abs_crr_user_res = os.path.join(settings.MEDIA_ROOT, 'efel_data', res_dir, userid, time_info, 'u_res')

    # storage relative path folder
    st_rel_user_results_folder = os.path.join(res_dir, u_time_f)
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
    return render(request, 'overview.html')
