import datetime
from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# import hbp/bbp modules
from hbp_app_python_auth.auth import get_access_token, \
        get_token_type, get_auth_header
from hbp_app_python_auth.views import logout as auth_logout

#
import os
import json
import datetime 
import bisect
import numpy as np
import pprint

from tools import g

@login_required(login_url='/login/hbp/')
def index(request):
    return render(request, 'bsp_monitor/index.html')


@login_required(login_url='/login/hbp/')
def get_access_token(request, token_type=""):
    '''
    Get token to grant access to google services
    '''
    if token_type == "ganalytics" or token_type == "gsheet":
        g.GoogleStatManager.get_token(token_type)
        return HttpResponse(json.dumps({'access_token'+'_'+token_type: g.GoogleStatManager.get_token(token_type)}), content_type="application/json")

    elif token_type == "all":
        access_token_ganalytics = g.GoogleStatManager.get_token("ganalytics")
        access_token_gsheet = g.GoogleStatManager.get_token("gsheet")
        final_dict  = {"access_token_ganalytics":access_token_ganalytics,\
                "access_token_gsheet":access_token_gsheet}
        return HttpResponse(json.dumps(final_dict), content_type="application/json")


@login_required(login_url='/login/hbp/')
def get_gs(request):
    client = g.GoogleStatManager.get_gs_client()
    sheet = client.open('Usecases - Collabs (Responses)').sheet1
    usecases = sheet.get_all_records()
    return HttpResponse(json.dumps({"Response":"OK"}), content_type="application/json")

@login_required(login_url='/login/hbp/')
def get_uc(request, start_date="0", end_date="0"):
    """
    Get usecases stats
    """

    sheet = g.GoogleStatManager.get_gs_sheet()
    result = sheet.col_values(1)

    uc_name = []
    uc_topics = []

    dates = g.GoogleStatManager.convert_to_datetime(result[1:], "long")

    if start_date == "0":
        last_day = datetime.datetime.today()
        first_day = last_day - datetime.timedelta(days=1)
    else:
        first_day = g.GoogleStatManager.convert_to_datetime([start_date], "short")[0]
        last_day = g.GoogleStatManager.convert_to_datetime([end_date], "short")[0]

    lower = bisect.bisect_left(dates, first_day)
    upper = bisect.bisect_right(dates, last_day)
    
    if lower == upper:
        response = "KO"
        rt_uc_num = 0
        uc_topics = []
        uc_topics_count = []
    else:
        uc_names = sheet.range("C" + str(lower) + ":C" + str(upper))
        uc_names_str = [x.value for x in uc_names]

        uc_list = g.FileManager.get_uc_json()
        uc_topics_names = g.FileManager.get_name_convention()

        uc_topics = []

        # create final dictionary
        uc_full = {}
        for i in uc_list:
            uctn = uc_topics_names[uc_list[i]]
            if uctn not in uc_full:
                uc_full[uctn] = {}
            if i not in uc_full[uctn]:
                uc_full[uctn][i] = 0

        for i in uc_names_str:
            if i not in uc_list:
                continue
            uctn = uc_topics_names[uc_list[i]]
            uc_topics.append(uctn)
            if start_date is not "0":
                uc_full[uctn][i] += 1

        uc_topics_np = np.array(uc_topics)
        uc_topics_unique, uc_topics_count = np.unique(uc_topics_np, return_counts=True)

        rt_uc_num = upper - lower

        response = "OK"

    return HttpResponse(json.dumps({"Response":response, "rt_uc_num":rt_uc_num, \
            "uc_topics":list(uc_topics_unique),\
            "uc_topics_count":list(uc_topics_count), \
            "uc_topics_full": uc_full}), \
            content_type="application/json")

@login_required(login_url='/login/hbp/')
def get_uc_item_list(request):
    uc_topics_names = g.FileManager.get_name_convention()
    return HttpResponse(json.dumps({"Response":"OK", "UC_TOPICS_NAMES":uc_topics_names}), content_type="application/json")


def get_all_no_alex(request):
    path = "/app/media/bsp_monitor/assets"
    with open(os.path.join(path, "all_no_alex.json")) as fh:
        data = json.load(fh)

    counter = 0
    counter_out = 0
    out_list = []

    uc_list = g.FileManager.get_uc_json()
    uc_topics_names = g.FileManager.get_name_convention()
    uc_old_names = g.FileManager.get_old_uc_names()

    uc_topics = []

    # create final dictionary
    uc_full = {}
    for i in uc_list:
        uctn = uc_topics_names[uc_list[i]]
        if uctn not in uc_full:
            uc_full[uctn] = {}
        if i not in uc_full[uctn]:
            uc_full[uctn][i] = 0

    for i in data:
        if i not in uc_list:
            if i in uc_old_names:
                print("old")
                print(i)
                uctn = uc_topics_names[uc_old_names[i]]
                print(uctn)
            else:
                continue
        else:
            print("new")
            uctn = uc_topics_names[uc_list[i]]
            print(uctn)
            
        print("range data i")
        print(int(data[i]))
        for j in range(data[i]):
            uc_topics.append(uctn)
        
        counter += int(data[i])

    uc_topics_np = np.array(uc_topics)
    uc_topics_unique, uc_topics_count = np.unique(uc_topics_np, return_counts=True)

    return HttpResponse(json.dumps({"Response":"OK", \
            "uc_topics":list(uc_topics_unique),\
            "uc_topics_count":list(uc_topics_count), \
            }), \
            content_type="application/json")


def get_exec_member(request):
    path = "/app/media/bsp_monitor/assets"
    with open(os.path.join(path, "member.json")) as fh:
        data = json.load(fh)

    d = data.keys()
    dd = sorted(d, key=lambda x: datetime.datetime.strptime(x, '%Y/%m/%d'))
    dates = []
    count = []
    for k in dd:
        print(k)
        dates.append(k)
        count.append(data[k])
    return HttpResponse(json.dumps({"dates":dates, "count":count}))

def get_exec_not_member(request):
    path = "/app/media/bsp_monitor/assets"
    with open(os.path.join(path, "not_member.json")) as fh:
        data = json.load(fh)
    pprint.pprint(data)
    dates = []
    count = []
    for k in data:
        dates.append(k)
        count.append(data[k])
    return HttpResponse(json.dumps({"dates":dates, "count":count}))




