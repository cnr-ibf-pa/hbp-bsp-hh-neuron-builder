import os
import sys
import json
import collections
import neo
import pprint
from datetime import datetime
import requests
import logging
import bluepyefe.formats.axon as fa

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def string_for_log(page_name, request, page_spec_string=''):
    """
    Create string to be printed to log files
    """

    pprint.pprint(request.META)
    # RU = request.META['REQUEST_URI']
    RU = 'test page'
    USER = str(request.user)
    DT = str(datetime.now())
    PSS = page_spec_string
    final_dict = collections.OrderedDict()

    final_dict['DT'] = DT
    final_dict['USER'] = USER
    final_dict['RU'] = RU
    final_dict['PSS'] = PSS

    if '?ctx=' in RU:
        PAGE_NAME = 'EFELG_HOMEPAGE'
        QS = request.META['QUERY_STRING']
        HUA = request.META['HTTP_USER_AGENT']
        HC = request.META['HTTP_COOKIE']
        SN = request.META['SERVER_NAME']
        RA = request.META['REMOTE_ADDR']
        # CC = request.META['CSRF_COOKIE']
        final_dict['PAGE'] = PAGE_NAME
        final_dict['QS'] = QS
        final_dict['HUA'] = HUA
        final_dict['HC'] = HC
        final_dict['SN'] = SN
        final_dict['RA'] = RA
        # final_dict['CC'] = CC
    else:
        PAGE_NAME = RU
        final_dict['PAGE'] = PAGE_NAME

    final_str = json.dumps(final_dict)
        
    return final_str


def print_citations(json_file_list, conf_file, final_file):
    """
    Print citation instructions
    """

    final_citations = {}
    with open(conf_file) as f:
        all_citations = json.load(f)

    for i in json_file_list:
        fin_key = i + '.json'
        if fin_key not in all_citations:
            continue
        crr_ref = all_citations[fin_key]
        crr_cit = list(crr_ref.keys())[0]
        if crr_cit not in final_citations:
            final_citations[crr_cit] = []
            final_citations[crr_cit].append(i)
        else:
            final_citations[crr_cit].append(i)

    print('CHECKING FOR DIRECTORY:\n %s' % ''.join(final_file.split(os.sep)[:-1]))
    if not os.path.exists(os.sep.join(final_file.split(os.sep)[:-1])):
        os.mkdir(os.sep.join(final_file.split(os.sep)[:-1]))

    with open(final_file, 'w') as tf:
        for key, val in final_citations.items():
            tf.write("For the following data:\n")
            for i in val:
                tf.write(i + "\n")
            tf.write("\n")
            tf.write("Use the following reference:\n\n")
            tf.write(key + "\n\n")
            tf.write("===========\n\n")