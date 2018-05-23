from __future__ import print_function

from hbp_app_python_auth.auth import get_access_token, get_token_type, get_auth_header
from bbp_client.oidc.client import BBPOIDCClient
from bbp_client.document_service.client import Client as DocClient
import bbp_client
from bbp_client.client import *
import bbp_services.client as bsc

import os
import re
import neo
import json
import hashlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

def create_doc_client(access_token):
    
    services = bsc.get_services()

    # get clients from bbp python packages
    oidc_client = BBPOIDCClient.bearer_auth(services['oidc_service']['prod']['url'], access_token)
    bearer_client = BBPOIDCClient.bearer_auth('prod', access_token)
    doc_client = DocClient(services['document_service']['prod']['url'], oidc_client)
    
    return doc_client


