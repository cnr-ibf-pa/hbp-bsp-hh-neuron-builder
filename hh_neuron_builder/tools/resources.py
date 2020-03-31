import os
import sys
import json
import collections
import neo
import pprint
from datetime import datetime
import requests
from django.conf import settings
import logging
if not settings.DEBUG:
    from hbp_app_python_auth.auth import get_auth_header

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create string to be printed to log files
def string_for_log(page_name, request, page_spec_string = ''):
    RU = request.META['REQUEST_URI']
    USER = str(request.user)
    DT = str(datetime.now())
    PSS = page_spec_string
    final_dict = collections.OrderedDict()

    final_dict['DT'] = DT
    final_dict['USER'] = USER
    final_dict['RU'] = RU
    final_dict['PSS'] = PSS

    if '?ctx=' in RU:
        PAGE_NAME = 'HHNB_HOMEPAGE'
        QS = request.META['QUERY_STRING']
        HUA = request.META['HTTP_USER_AGENT']
        HC = request.META['HTTP_COOKIE']
        SN = request.META['SERVER_NAME']
        RA = request.META['REMOTE_ADDR']
        CC = request.META['CSRF_COOKIE']
        final_dict['PAGE'] = PAGE_NAME
        final_dict['QS'] = QS
        final_dict['HUA'] = HUA
        final_dict['HC'] = HC
        final_dict['SN'] = SN
        final_dict['RA'] = RA
        final_dict['CC'] = CC
    else:
        PAGE_NAME = RU
        final_dict['PAGE'] = PAGE_NAME

    final_str = json.dumps(final_dict)
        
    return final_str


def get_token_from_refresh_token(mc_clb_user=""):
    # retrieve refresh token for accessing destination collab
    refresh_token = settings.USER_REFRESH_TOKENS[mc_clb_user]['refresh_token']

    # retrieve authorized user access token to access the destination collab storage
    token_url = settings.HBP_OIDC_TOKEK_URL 
    SOCIAL_AUTH_HBP_KEY = settings.SOCIAL_AUTH_HBP_KEY
    SOCIAL_AUTH_HBP_SECRET = settings.SOCIAL_AUTH_HBP_SECRET

    data = {
        "client_id": SOCIAL_AUTH_HBP_KEY,\
        "client_secret": SOCIAL_AUTH_HBP_SECRET,\
        "grant_type":"refresh_token",
        "refresh_token": refresh_token,
        }

    response = requests.post(token_url, data=data)
    clb_user_token = response.json()['access_token']

    return clb_user_token
