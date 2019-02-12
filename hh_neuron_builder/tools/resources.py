import os
import sys
import json
import collections
import neo
import pprint
from datetime import datetime
import requests
from django.conf import settings
if not settings.DEBUG:
    from hbp_app_python_auth.auth import get_auth_header
# create logger
import logging

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

##### create string to be printed to log files
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
