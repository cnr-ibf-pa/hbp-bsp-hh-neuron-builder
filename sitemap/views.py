from django.shortcuts import render, redirect, HttpResponse
from django.conf import settings
import os, json, sys
import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
from bspg import auth
import urllib
import requests
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import logout as views_logout

# Create your views here.

def sitemap(request):
    context = request.GET.get('ctx')
    nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))
    request.session['nextUrl'] = nextUrl
    request.session['this_ctx'] = context
    hdr =  auth.get_authorization_header(request)
    crr_user = auth.get_user(request)
    logger.info(crr_user)
    if not bool(hdr) or not bool(crr_user):
        auth_logout(request)
        return redirect('%s?next=%s' % (settings.LOGIN_URL, nextUrl))
    
    return render(request, 'sitemap/sitemap.html')


def tree_json(request):
    if 'sitemap' in request.session:
        return HttpResponse(json.dumps(request.session['sitemap']))
        
    hdr =  auth.get_authorization_header(request)
    logger.info("header from tree_json")
    logger.info("header from tree_json")
    logger.info("header from tree_json")
    logger.info("header from tree_json")
    logger.info("header from tree_json")
    logger.info("header from tree_json")
    logger.info(hdr)
    bsp_url = settings.HBP_COLLAB_SERVICE_URL + 'collab/161/nav/all/'
    res = requests.get(bsp_url, headers = hdr)
    if res.status_code != 200:
        logger.info('bad code')
        logger.info('bad code')
        logger.info('bad code')
        logger.info('bad code')
        #context = request.GET.get('ctx')
        #request.session.flush()
        views_logout(request)
        auth_logout(request)
        #nextUrl = urllib.quote('%s?ctx=%s' % (request.path, context))
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.session['nextUrl']))
        #return redirect('%s?next=%s' % (settings.LOGIN_URL, 'sitemap'))
        #return redirect('https://bspg.pa.ibf.cnr.it/sitemap')

    all_data = res.json()
    first_level_collab = []
    for i in all_data:
        if i['type'] == 'CO':
            crr_app_id = i['app_id']
            crr_parent = i['id']
            crr_app_context = i['context']
            crr_app_context_url = settings.HBP_COLLAB_SERVICE_URL + 'config/' + crr_app_context
            crr_res = requests.get(crr_app_context_url, headers = hdr)
            crr_res_json = crr_res.json()
            crr_content = crr_res_json['content']
            crr_collab_dict = json.loads(crr_content)
            crr_collab_id = crr_collab_dict['collabId']
            crr_url = settings.HBP_COLLAB_SERVICE_URL + 'collab/' + str(crr_collab_id) + '/nav/all/'
            fin_res = requests.get(crr_url, headers = hdr)
            fin_res_json = fin_res.json()
            if 'detail' in fin_res_json and fin_res_json['detail'] == 'No access to the collab':
                i['name'] = i['name'] + ' --NO ACCESS--'
                continue
            for z in fin_res_json:
                if z['name'] == 'root':
                    continue
                z['parent'] = crr_parent
                first_level_collab.append(z)
    for j in first_level_collab:
        all_data.append(j)
    users = []
    all_parents = []
    all_children = []
    all_ids = []
    for i in all_data:
        if i['type'] == 'IT':
            crr_id = '(ITEM)'
        elif i['type'] == 'FO':
            crr_id = '(FOLDER)'
        elif i['type'] == 'CO':
            crr_id = '(COLLAB)'
        users.append({'name': i['name'] + ' ' + crr_id, 'parent':i['parent'], 'id':i['id'], 'size': 30, 'app_id':i['app_id']})
        all_parents = i['parent']
        all_ids = i['id']

    users_map = {}
    for user in users:
        users_map[user['id']] = user

    users_tree = []
    users_tree_dict = {}  

    for user in users:
        if user['parent'] is None:
            user['name'] = 'Brain Simulation Platform'
            users_tree.append(user) 
        else:
            parent = users_map[user['parent']]
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(user)
    with open('static/flare.json', 'w') as outfile:
        json.dump(users_tree[0], outfile)
    request.session['sitemap'] = users_tree[0]
    return HttpResponse(json.dumps(users_tree[0]))
