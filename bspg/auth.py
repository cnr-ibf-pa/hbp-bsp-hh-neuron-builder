
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
from django.conf import settings
import requests
from social.apps.django_app.default.models import UserSocialAuth
from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
import json
from datetime import date
from django.shortcuts import render
from django.forms.models import model_to_dict
from django.views.generic import View
from django.http import (HttpResponse, JsonResponse,
        HttpResponseBadRequest,     # 400
        HttpResponseForbidden,      # 403
        HttpResponseNotFound,       # 404
        HttpResponseNotAllowed,     # 405
        HttpResponseNotModified,    # 304
        HttpResponseRedirect)       # 302
from django.core.serializers.json import DjangoJSONEncoder

def get_authorization_header(request):
    auth = request.META.get("HTTP_AUTHORIZATION", None)
    if auth is None:
        try:
            auth = get_auth_header(request.user.social_auth.get())
            logger.debug("Got authorization from database")
        except AttributeError:
            #pass
            return {}
    # in case of 401 error, need to trap and redirect to login
    else:
        logger.debug("Got authorization from HTTP header")
    return {'Authorization': auth}


def get_permissions(request, context):
    """
    Obtain the permissions of the associated Collab for the user associated with the
    Bearer token in the Authentication header.
    """
    svc_url = settings.HBP_COLLAB_SERVICE_URL
    url = '%scollab/context/%s/' % (svc_url, context)
    headers = get_authorization_header(request)
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {}
    collab_id = res.json()['collab']['id']
    url = '%scollab/%s/permissions/' % (svc_url, collab_id)
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {}
    return res.json()


def get_admin_list(request):
    url = 'https://services.humanbrainproject.eu/idm/v1/api/group/hbp-neuromorphic-platform-admin/members'
    headers = get_authorization_header(request)
    res = requests.get(url, headers=headers)
    logger.debug(headers)
    if res.status_code != 200:
        raise Exception("Couldn't get list of administrators." + res.content + str(headers))
    data = res.json()
    assert data['page']['totalPages'] == 1
    admins = [user['id'] for user in data['_embedded']['users']]
    return admins


def is_admin(request):
    try:
        admins = get_admin_list(request)
    except Exception as err:
        logger.warning(err.message)
        return False
    try:
        user_id = get_user(request)["id"]
    except Exception as err:
        logger.warning(err.message)
        return False
    return user_id in admins


def get_user(request):
    url = "{}/user/me".format(settings.HBP_IDENTITY_SERVICE_URL)
    headers = get_authorization_header(request)
    logger.debug("Requesting user information for given access token")
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        logger.debug("Error" + res.content)
        return {}
        #raise Exception(res.content)
    logger.debug("User information retrieved")
    return res.json()


def notify_coordinators(request, project):
    coordinators = get_admin_list(request)
    url = 'https://services.humanbrainproject.eu/stream/v0/api/notification/'
    headers = get_authorization_header(request)
    targets = [{"type": "HBPUser", "id": id} for id in coordinators]
    payload = {
            "summary": "New access request for the Neuromorphic Computing Platform: {}".format(project.title),
            "targets": targets,
            "object": {
                "type": "HBPCollaboratoryContext",
                "id": "346173bb-887c-4a47-a8fb-0da5d5980dfc"
                }
            }
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code not in (200, 204):
        logger.error("Unable to notify coordinators. {}: {}".format(res.status_code, res.content))
        return False
    return True

