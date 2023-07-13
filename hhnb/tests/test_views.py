"""
Test units for hhnb.views
"""

import os
import shutil
import json
from time import sleep
from urllib.parse import unquote
import requests
from uuid import uuid4 as uuid_generator
from django.test import SimpleTestCase, TestCase, Client, modify_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from hhnb import models
from hh_neuron_builder.settings import (
    MEDIA_ROOT, BASE_DIR, OIDC_OP_TOKEN_ENDPOINT
)


ROOT_URL = 'hh-neuron-builder/'
FILES_DIR = os.path.join(BASE_DIR, 'hhnb', 'tests', 'files',)
CONFIG_FILES_DIR = os.path.join(FILES_DIR, 'config')
MODEL_IDS = ['933b6b54-d458-40ce-bfb9-0d8236f9e837', 'df83ff36-5182-497a-b94a-ff0f11fb32a8a']


def get_user_token():
    """
    Get EBRAINS user token if the USERNAME and PASSWORD are set in
    os environment.
    """
    username = os.environ.get('EBRAINS_USERNAME')
    password = os.environ.get('EBRAINS_PASSWORD')
    if username and password:
        r = requests.post(
            OIDC_OP_TOKEN_ENDPOINT,
            auth=('hbp-bsp-hhnb-dev', ''),
            data={
                'grant_type':'password',
                'username': username,
                'password': password
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()['access_token']
        else:
            print(r.status_code, r.content)
    return None


def store_token_in_session(client: Client):
    """
    Store access token in client session.
    """
    session = client.session
    session['oidc_access_token'] = get_user_token()
    session.save()


class TestMiscViews(SimpleTestCase):
    """
    Test miscellaneous cases for hhnb.views
    """

    def test_status(self):
        """
        A function to test the status API.
        This function sends a GET request to the 'status' endpoint of the API
        and asserts that the response status code is 200. It also asserts that
        the response JSON is equal to {'hh-neuron-builder-status': 1}.
        """
        url = reverse('status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'hh-neuron-builder-status': 1})

    def test_session_refresh(self):
        """
        Test the session refresh functionality.

        This function tests the functionality of refreshing a session. It performs the following steps:
        1. Retrieves the URL for the 'session-refresh' endpoint.
        2. Sends a GET request to the 'session-refresh' endpoint.
        3. Asserts that the response status code is 400.
        4. Sends a POST request to the 'session-refresh' endpoint with the 'refresh_url' parameter to test the refresh url.
        5. Asserts that the response status code is 200.
        """
        url = reverse('session-refresh')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        # TODO: uncomment and check with a running server
        # response = self.client.post(url, data={'refresh_url': 'https://127.0.0.1:8000/hh-neuron-builder/'})
        # self.assertEqual(response.status_code, 200)


class TestPages(TestCase):
    """
    Test cases for hhnb.views that render pages.
    """


    def test_home_page(self):
        """
        Test the home page by checking if the response status code is 200
        and if the correct template is used.
        """
        home_url = reverse('home')
        response = self.client.get(home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hhnb/home.html')

    def test_workflow_page(self):
        """
        Test the workflow page.

        This function performs a series of tests on the workflow page.
        It initializes a workflow, retrieves the workflow URL, and
        verifies the response status code. Then, it checks if the JSON
        response contains the expected keys. Next, it retrieves the
        workflow URL again and verifies the response status code. Finally,
        it asserts that the template used is 'hhnb/workflow.html' and
        deletes the workflow directory.
        """
        init_wf_url = reverse('initialize-workflow')
        response = self.client.get(init_wf_url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['exc'])
        exc_code = response.json()['exc']
        wf_url = reverse('workflow', args=[exc_code])
        response = self.client.get(wf_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hhnb/workflow.html')
        wf_id = self.client.session[exc_code]['workflow_id']
        shutil.rmtree(os.path.join(MEDIA_ROOT, 'hhnb', 'workflows', 'anonymous', wf_id))

    def test_docs_page(self):
        """
        Test the docs page.
        """
        docs_url = reverse('docs')
        response = self.client.get(docs_url)
        self.assertEqual(response.status_code, 200)

    def test_index_docs_page(self):
        """
        Test the index docs page.
        """
        index_docs_url = reverse('docs-index')
        response = self.client.get(index_docs_url)
        self.assertEqual(response.status_code, 200)


class TestViews(TestCase):
    """
    Test cases for hhnb.views
    """

    @modify_settings(MIDDLEWARE={
        'remove': 'mozilla_django_oidc.middleware.SessionRefresh',
    })

    def setUp(self):
        """
        Set up test.
        """
        self.client = Client()

        # create nfe temp dir
        self.tmp_nfe_dir = 'tmp_nfe_dir'
        if os.path.exists(self.tmp_nfe_dir):
            shutil.rmtree(self.tmp_nfe_dir)
        os.mkdir(self.tmp_nfe_dir)

        # creating user object
        self.user = models.User(sub=str(uuid_generator()))
        self.user.save()
        self.username = 'anonymous'

        # store personal access token in client session and log in the temp user
        store_token_in_session(self.client)
        self.client.force_login(self.user, backend='auth.backend.MyOIDCBackend')
        self.username = str(self.user.sub)

        # initialize the workflow and store the exc code and the workflow id
        response = self.client.get(reverse('initialize-workflow'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['exc'])
        self.exc_code = response.json()['exc']
        response = self.client.get(reverse('get-workflow-id', args=[self.exc_code]))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['workflow_id'])
        self.workflow_id = response.json()['workflow_id']
        self.workflow_path = os.path.join(MEDIA_ROOT, 'hhnb', 'workflows',
                                          self.username, self.workflow_id)
        shutil.copytree(os.path.join(FILES_DIR, 'workflow'),
                        self.workflow_path, dirs_exist_ok=True)
        shutil.copytree(os.path.join(FILES_DIR, 'results'),
                        os.path.join(self.workflow_path, 'results'), dirs_exist_ok=True)
        shutil.copytree(os.path.join(FILES_DIR, 'analysis'),
                        os.path.join(self.workflow_path, 'analysis'), dirs_exist_ok=True)

    def tearDown(self):
        """
        Clean up test.
        """
        shutil.rmtree(
            os.path.join(MEDIA_ROOT, 'hhnb', 'workflows', self.username)
        )
        shutil.rmtree(self.tmp_nfe_dir)
        self.user.delete()

    def test_store_workflow_in_session(self):
        """
        Store workflow in session.
        """
        url = reverse('store-workflow-in-session', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_clone_workflow(self):
        """
        Clone workflow.
        """
        wf_url = reverse('clone-workflow', args=[self.exc_code])
        response = self.client.get(wf_url)
        self.assertEqual(response.status_code, 200)

    def test_download_and_upload_workflow(self):
        """
        Download and reupload workflow zip file to test both views.
        """

        # download workflow
        url = reverse('download-workflow', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['zip_path'])
        signed_zip_path = response.json()['zip_path']
        signed_zip_name = signed_zip_path.split('/')[-1]
        url = reverse('download-workflow', args=[self.exc_code])
        response = self.client.get(url, {'zip_path': signed_zip_path})
        self.assertEqual(response.status_code, 200)

        unsigned_zip_name = signed_zip_name.replace('_signed', '')
        unsigned_zip_path = '/'.join([os.path.split(signed_zip_path)[0], unsigned_zip_name])

        # upload workflow
        url = reverse('upload-workflow')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        with open(signed_zip_path, 'rb') as fd:
            response = self.client.post(
                url,
                {'name': signed_zip_name, 'file': fd},
                headers={'Content-Disposition': f'attachment; filename="{signed_zip_name}"'}
            )
            self.assertEqual(response.status_code, 200)
            self.assertListEqual(list(response.json().keys()), ['response', 'exc'])

        with open(unsigned_zip_path, 'rb') as fd:
            response = self.client.post(
                url,
                {'name': unsigned_zip_name, 'file': fd},
                headers={'Content-Disposition': f'attachment; filename="{unsigned_zip_name}"'}
            )
            self.assertEqual(response.status_code, 400)
            self.assertDictEqual(
                response.json(), {"response": "KO", "message": f"<b>Invalid file !</b><br><br>Upload a correct {unsigned_zip_name} archive."}
                )

        os.remove(unsigned_zip_path)
        os.remove(signed_zip_path)

    def test_get_workflow_properties(self):
        """
        Test case for the 'get_workflow_properties' function.

        This function tests the functionality of the 'get_workflow_properties' function
        by making a GET request to the specified URL and asserting that the response
        status code is 200. It also checks that the properties returned in the JSON
        response match the expected properties.
        """
        url = reverse('get-workflow-properties', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        properties = ['id', 'model', 'optimization_settings', 'etraces', 'job_submitted',
                      'results', 'resume', 'analysis', 'show_results', 'hhf_flag']
        self.assertListEqual(list(response.json().keys()), properties)

    def test_fetch_models(self):
        url = reverse('fetch-models', args=[self.exc_code])
        response = self.client.get(url, data={'model': 'all'})
        self.assertIn(response.status_code, [200, 204])
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['models'])
        response = self.client.get(url, data={'model': MODEL_IDS[1]})
        self.assertIn(response.status_code, [200, 400, 497, 498])
        if response.status_code == 400:
            self.assertEqual(response.content, b'<b>Something went wrong.</b><br><br>The download model file seems to be invalid file.<br>Please, try another model instance or contact the  <a href="https://ebrains.eu/support" class="alert-link" target="_blank">EBRAINS support</a>.')
        if response.status_code == 497:
            self.assertTrue(response.content.startswith(b'<b>Model Catalog error!</b>'))
        if response.status_code == 498:
            self.assertEqual(response.content, b'The Model Catalog is temporarily not available.<br>Please, try again later.')

    def test_upload_features(self):
        url = reverse('upload-features', args=[self.exc_code])

        # test case from NFE
        shutil.copy2(os.path.join(CONFIG_FILES_DIR, 'features.json'), self.tmp_nfe_dir)
        shutil.copy2(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), self.tmp_nfe_dir)
        response = self.client.post(url, data={'folder': self.tmp_nfe_dir})
        self.assertEqual(response.status_code, 200)

        # test form_file with features.json
        features = open(os.path.join(CONFIG_FILES_DIR, 'features.json'), 'rb')
        features_form_file = SimpleUploadedFile(name='features.json',
                                                content=features.read(),
                                                content_type='application/json')
        response = self.client.post(url, data={'formFile': [features_form_file]})
        self.assertEqual(response.status_code, 200)

        # test form_file with protocols.json
        protocols = open(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), 'rb')
        protocols_form_file = SimpleUploadedFile(name='protocols.json',
                                                 content=protocols.read(),
                                                 content_type='application/json')
        response = self.client.post(url, data={'formFile': [protocols_form_file]})
        self.assertEqual(response.status_code, 200)

        # test form_file with features.json and protocols.json
        response = self.client.post(url, data={'formFile': [features_form_file,
                                                            protocols_form_file]})
        self.assertEqual(response.status_code, 200)

        # test with no files
        response = self.client.post(url, data={'formFile': []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'No file was uploaded.')

        # test with different file
        other = open(os.path.join(CONFIG_FILES_DIR, 'morph.json'), 'rb')
        other_form_file = SimpleUploadedFile(name='morph.json',
                                             content=other.read(),
                                             content_type='application/json')
        response = self.client.post(url, data={'formFile': [other_form_file]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'The uploaded file/s is/are wrong.')

        # test with more than two files
        response = self.client.post(url, data={'formFile': [features_form_file,
                                                            protocols_form_file,
                                                            other_form_file]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'You can upload only 2 files.')

        features.close()
        protocols.close()
        other.close()

    # def test_upload_model(self):
    #     url = reverse('upload-model', args=[self.exc_code])
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 405)

    #     # test empty form file
    #     response = self.client.post(url, data={'formFile': []})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.content, b'No file was uploaded.')

    #     # test more then 1 file
    #     features = open(os.path.join(CONFIG_FILES_DIR, 'features.json'), 'rb')
    #     features_form_file = SimpleUploadedFile(name='features.json',
    #                                             content=features.read(),
    #                                             content_type='application/json')
    #     protocols = open(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), 'rb')
    #     protocols_form_file = SimpleUploadedFile(name='protocols.json',
    #                                              content=protocols.read(),
    #                                              content_type='application/json')
    #     response = self.client.post(url, data={'formFile': [features_form_file,
    #                                                         protocols_form_file]})
    #     self.assertEqual(response.status_code, 400)
    #     self.assertEqual(response.content, b'You can upload only a "model.zip" file.')

    #     features.close()
    #     protocols.close()

    def test_upload_analysis(self):
        pass

    def test_upload_files(self):
        pass

    def test_download_file(self):
        gen_url = reverse('generate-download-file', args=[self.exc_code])
        down_url = reverse('download-file', args=[self.exc_code])
        response = self.client.post(down_url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(down_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'No file selected to download.')

        # test features pack
        response = self.client.get(gen_url, data={'pack': 'features'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(response.content, [b'<b>Error !</b><br><br>File not found.',
                                             b'<b>Error !</b><br><br>File is not added yet.'])

        upload_url = reverse('upload-features', args=[self.exc_code])
        features = open(os.path.join(CONFIG_FILES_DIR, 'features.json'), 'rb')
        features_form_file = SimpleUploadedFile(name='features.json',
                                                content=features.read(),
                                                content_type='application/json')
        self.client.post(upload_url, data={'formFile': [features_form_file]})

        # test form_file with protocols.json
        protocols = open(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), 'rb')
        protocols_form_file = SimpleUploadedFile(name='protocols.json',
                                                 content=protocols.read(),
                                                 content_type='application/json')
        self.client.post(upload_url, data={'formFile': [protocols_form_file]})

        for pack in ['features', 'model', 'results', 'analysis']:
            response = self.client.get(gen_url, data={'pack': pack})
            self.assertEqual(response.status_code, 200)
            response = self.client.get(down_url, data={'filepath': response.content})
            self.assertEqual(response.status_code, 200)

    def show_results(self):
        url = reverse('show-results', args=[self.exc_code])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b'<b>Error !</b><br><br>File not found.')
        wf_analysis_path = os.path.join(self.workflow_path, 'analysis')
        for f in os.listdir(FILES_DIR):
            if 'analysis' in f and os.path.isdir(f):
                shutil.copytree(f, wf_analysis_path)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_files(self):
        pass

    def test_optimization_settings(self):
        url = reverse('optimization-settings', args=[self.exc_code])

        # test get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['settings', 'service-account', 'resume'])

        # test post pizdaint
        data = {
            "job_name":"test_unit",
            "gen-max":2,
            "offspring":10,
            "node-num":6,
            "core-num":24,
            "mode": "start",
            "hpc":"DAINT-CSCS",
            "runtime":"120m",
            "project":"ich002",
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # test post nsg with correct password
        data = {
            "job_name":"test_unit",
            "gen-max":2,
            "offspring":10,
            "node-num":6,
            "core-num":24,
            "mode": "start",
            "hpc": "NSG",
            "runtime": 2.0,
            "username_submit": os.environ['NSG_USERNAME'],
            "password_submit": os.environ['NSG_PASSWORD'],
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # test post nsg with incorrect password
        data.update({'password_submit': 'incorrect'})
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid credentials.')

        # test post without hpc
        data = {
            "job_name":"test_unit",
            "gen-max":2,
            "offspring":10,
            "node-num":6,
            "core-num":24,
            "mode": "start",
            "runtime": "120m"
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid settings')

    def test_run_optimization(self):

        url = reverse('run-optimization', args=[self.exc_code])

        # test with default workflow in DAINT
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])

    def test_fetch_jobs_with_daint(self):
        url = reverse('fetch-jobs', args=[self.exc_code])
        auth_url = reverse('get-authentication')

        # test without hpc
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'No HPC was selected.')

        # test authentication first
        response = self.client.get(auth_url)
        self.assertEqual(response.status_code, 200)

        # test in DAINT
        response = self.client.get(url, data={"hpc": "CSCS-DAINT"})
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])

    def test_fetch_jobs_with_nsg(self):
        url = reverse('fetch-jobs', args=[self.exc_code])
        auth_url = reverse('get-authentication')

        # test in NSG
        # set credentials first
        response = self.client.post(auth_url,
                                    data={'username': os.environ['NSG_USERNAME'],
                                          'password': os.environ['NSG_PASSWORD']})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, data={"hpc": "NSG"})
        self.assertIn(response.status_code, [200, 400])
        print(response.content)
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])

    def test_fetch_jobs_with_service_account(self):
        url = reverse('fetch-jobs', args=[self.exc_code])
        auth_url = reverse('get-authentication')

        response = self.client.get(url, data={"hpc": "SA", "saHPC": "pizdaint", "saProject": 'hhnb_daint_cscs'})
        self.assertIn(response.status_code, [200, 400])
        print(response.content)
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])

    def test_fetch_job_results(self):
        pass

    def test_run_analysis(self):
        url = reverse('run-analysis', args=[self.exc_code])
        response = self.client.get(url)
        print(response.status_code, response.content)
        self.assertEqual(response.status_code, 200)

    def test_upload_to_naas(self):
        pass

    def test_get_model_catalog_attribute_options(self):
        url = reverse('get-model-catalog-attribute-options')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 400:
            self.assertEqual(response.content, b'<b>Error !</b>')

    def test_register_model(self):
        pass

    def test_user_avatar(self):
        url = reverse('get-user-avatar')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 400:
            self.assertEqual(response.content, b'Avatar not found')

    def test_get_user_page(self):
        # can't test due to the user not being logged in
        pass

    def test_get_authentication(self):
        url = reverse('get-authentication')
        response_ebrains = self.client.get(url)
        response_nsg = self.client.post(url, data={'username': os.environ['NSG_USERNAME'],
                                                   'password': os.environ['NSG_PASSWORD']})
        self.assertIn(response_ebrains.status_code, [200, 400])
        self.assertIn(response_nsg.status_code, [200, 400])
        if response_ebrains.status_code == 400:
            self.assertEqual(response_ebrains.content, b'User is not authenticated')
        if response_ebrains.status_code == 400:
            self.assertEqual(response_nsg.content, b'User is not authenticated.')

    def test_hhf_comm(self):
        encoded_data = '{%22HHF-Comm%22:{%22morphology%22:{%22name%22:%22010710HP2%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252F325731aa-c302-471b-b9fa-2b4cd4cdb4fc%22},%22electrophysiologies%22:[{%22name%22:%2295810006%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252Fa42f0923-2bfa-43fe-aff4-670155d286ee%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810006_metadata.json%22},{%22name%22:%2295810007%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252F07a6c7d4-4ee2-41b5-bc7d-44476b4256d2%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810007_metadata.json%22},{%22name%22:%2295810008%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252Fca85bca0-6c40-496a-88cb-78562cc10639%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810008_metadata.json%22}],%22modFiles%22:[{%22name%22:%22bg2pyr.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fbg2pyr.mod%22},{%22name%22:%22cal2.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fcal2.mod%22},{%22name%22:%22h.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fh.mod%22}]}}'
        data = {'hhf_dict': unquote(encoded_data)}
        url = reverse('hhf-comm')
        sleep(1)
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        return response.context['exc']

    def test_hhf_etraces_dir(self):
        self.exc_code = self.test_hhf_comm()
        url = reverse('hhf-etraces-dir', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['hhf_etraces_dir'])

    def test_hhf_list_files(self):
        url = reverse('hhf-list-files', args=[self.exc_code])
        response = self.client.get(url)
        print(response.status_code, response.content)
        self.assertEqual(response.status_code, 200)

    def test_hhf_get_files_content(self):
        folders = ['morphologyFolder' , 'mechanismsFolder', 'configFolder',
                   'modelFolder', 'parametersFolder', 'optNeuronFolder']
        for folder in folders:
            url = reverse('hhf-get-files-content', args=[folder, self.exc_code])
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 400])

    def test_hhf_get_model_key(self):
        url = reverse('hhf-get-model-key', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json().keys()), {'model_key'})

    def test_hhf_apply_model_key(self):
        # files key are updated correctly but currently
        # the model key is taken from the model workflow path
        # and it can't be test
        url = reverse('hhf-apply-model-key', args=[self.exc_code])
        response = self.client.post(url, data={'model_key': 'test'})
        self.assertEqual(response.status_code, 200)

    def test_hhf_save_config_file(self):
        for config_file in os.listdir(CONFIG_FILES_DIR):
            url = reverse('hhf-save-config-file', args=['configFolder', config_file, self.exc_code])
            with open(os.path.join(CONFIG_FILES_DIR, config_file), 'r') as fd:
                content = fd.read()
            response = self.client.post(url, data={config_file: content})
            self.assertEqual(response.status_code, 200)

    def test_hhf_load_parameters_template(self):
        url = reverse('hhf-load-parameters-template', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        for parameter_type in ['pyramidal', 'interneuron']:
            response = self.client.post(url, data={'type': parameter_type})
            self.assertEqual(response.status_code, 200)

    def test_get_service_account_content(self):
        url = reverse('get-service-account-content')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json().keys()), {'service-account'})