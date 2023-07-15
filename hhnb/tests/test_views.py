"""
Test units for hhnb.views
"""

import os
import shutil
import json
from time import sleep
from urllib.parse import unquote
from uuid import uuid4 as uuid_generator
import requests
from django.test import SimpleTestCase, TestCase, Client, modify_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from hhnb import models
from hhnb.utils import messages
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
            auth=('ebrains-drive', ''),
            data={
                'grant_type':'password',
                'username': username,
                'password': password
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()['access_token']
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

        This function tests the functionality of refreshing a session.
        It performs the following steps:
        1. Retrieves the URL for the 'session-refresh' endpoint.
        2. Sends a GET request to the 'session-refresh' endpoint.
        3. Asserts that the response status code is 400.
        4. Sends a POST request to the 'session-refresh' endpoint
           with the 'refresh_url' parameter to test the refresh url.
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

    def test_get_workflow_id(self):
        """
        Test the get_workflow_id function.

        This function tests the functionality of the get_workflow_id API endpoint.
        It sends a GET request to the endpoint with the specified exception code as an argument.
        response JSON is equal to {'workflow_id': self.workflow_id}.
        The function then asserts that the response status code is 200 and the
        """
        url = reverse('get-workflow-id', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'workflow_id': self.workflow_id})

    def test_fetch_models(self):
        """
        Test the fetch_models function.

        This test method verifies the behavior of the fetch_models function.
        It sends a GET request to the 'fetch-models' endpoint with different
        parameters and checks the response status code and content.
        """
        url = reverse('fetch-models', args=[self.exc_code])
        response = self.client.get(url, data={'model': 'all'})
        self.assertIn(response.status_code, [200, 204])
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['models'])
        response = self.client.get(url, data={'model': MODEL_IDS[1]})
        self.assertIn(response.status_code, [200, 400, 497, 498])
        if response.status_code == 400:
            self.assertEqual(response.content.decode(),
                             messages.MODEL_CATALOG_INVALID_DOWNLOADED_FILE)
        if response.status_code == 497:
            self.assertTrue(response.content.startswith(b'<b>Model Catalog error!</b>'))
        if response.status_code == 498:
            self.assertEqual(response.content.decode(),
                             messages.MODEL_CATALOG_NOT_AVAILABLE)

    def test_download_and_upload_features(self):
        """
        Test the download and upload of features.
        This function tests the download and upload of features by performing
        a series of HTTP requests using the Django testing client. It verifies
        that the HTTP responses have the expected status codes and content.
        """
        download_url = reverse('generate-download-file', args=[self.exc_code])
        response = self.client.get(download_url, data={'pack': 'features'})
        self.assertEqual(response.status_code, 200)

        upload_url = reverse('upload-features', args=[self.exc_code])

        # test case from NFE
        shutil.copy2(os.path.join(CONFIG_FILES_DIR, 'features.json'), self.tmp_nfe_dir)
        shutil.copy2(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), self.tmp_nfe_dir)
        response = self.client.post(upload_url, data={'folder': self.tmp_nfe_dir})
        self.assertEqual(response.status_code, 200)

        # test form_file with features.json
        features = open(os.path.join(CONFIG_FILES_DIR, 'features.json'), 'rb')
        features_form_file = SimpleUploadedFile(name='features.json',
                                                content=features.read(),
                                                content_type='application/json')
        response = self.client.post(upload_url, data={'formFile': [features_form_file]})
        self.assertEqual(response.status_code, 200)

        # test form_file with protocols.json
        protocols = open(os.path.join(CONFIG_FILES_DIR, 'protocols.json'), 'rb')
        protocols_form_file = SimpleUploadedFile(name='protocols.json',
                                                 content=protocols.read(),
                                                 content_type='application/json')
        response = self.client.post(upload_url, data={'formFile': [protocols_form_file]})
        self.assertEqual(response.status_code, 200)

        # test form_file with features.json and protocols.json
        response = self.client.post(upload_url, data={'formFile': [features_form_file,
                                                            protocols_form_file]})
        self.assertEqual(response.status_code, 200)

        # test with no files
        response = self.client.post(upload_url, data={'formFile': []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), messages.NO_FILE_UPLOADED)

        # test with different file
        other = open(os.path.join(CONFIG_FILES_DIR, 'morph.json'), 'rb')
        other_form_file = SimpleUploadedFile(name='morph.json',
                                             content=other.read(),
                                             content_type='application/json')
        response = self.client.post(upload_url, data={'formFile': [other_form_file]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), messages.WRONG_UPLOADED_FILE)

        # test with more than two files
        response = self.client.post(upload_url, data={'formFile': [features_form_file,
                                                            protocols_form_file,
                                                            other_form_file]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), messages.NO_MORE_THEN.format('2 files'))

        features.close()
        protocols.close()
        other.close()

    def test_download_and_upload_model(self):
        """
        This function tests the download and upload functionality of the model.
        """
        download_url = reverse('generate-download-file', args=[self.exc_code])
        response = self.client.get(download_url, data={'pack': 'model'})
        self.assertEqual(response.status_code, 200)
        zip_path = response.content.decode()
        upload_url = reverse('upload-model', args=[self.exc_code])
        with open(zip_path, 'rb') as fd:
            form_file = SimpleUploadedFile(name='model.zip',
                                           content=fd.read(),
                                           content_type='application/zip')
            response = self.client.post(upload_url, data={'formFile': [form_file]})
            self.assertEqual(response.status_code, 200)

    def test_download_and_upload_analysis(self):
        """
        Test the download and upload analysis functionality.

        This function tests the download and upload analysis
        functionality of the system. It performs the following steps:
        1. Retrieves the download URL for the generated file
           using the `generate-download-file` API endpoint.
        2. Sends a GET request to the download URL with
           the necessary data to download the analysis pack.
        3. Verifies that the response status code is 200.
        4. Retrieves the path of the downloaded ZIP file.
        5. Retrieves the upload URL for the analysis using the `upload-analysis` API endpoint.
        6. Opens the downloaded ZIP file in binary mode.
        7. Creates a `SimpleUploadedFile` object with the contents of the ZIP file.
        8. Sends a POST request to the upload URL with the `formFile`
           parameter set to the `SimpleUploadedFile` object.
        9. Removes the downloaded ZIP file from the local filesystem.
        10. Verifies that the response status code is 200.
        """
        download_url = reverse('generate-download-file', args=[self.exc_code])
        response = self.client.get(download_url, data={'pack': 'analysis'})
        self.assertEqual(response.status_code, 200)
        zip_path = response.content.decode()
        upload_url = reverse('upload-analysis', args=[self.exc_code])
        with open(zip_path, 'rb') as fd:
            form_file = SimpleUploadedFile(name='analysis.zip',
                                           content=fd.read(),
                                           content_type='application/zip')
            response = self.client.post(upload_url, data={'formFile': [form_file]})
            os.remove(zip_path)
            self.assertEqual(response.status_code, 200)

    def test_download_and_upload_files(self):
        """
        This function tests the download and upload functionality for files.

        This function performs the following steps:
        1. Creates the paths for the morphology, config, and mechanisms directories.
        2. Retrieves a list of files in each directory.
        3. Serializes the file paths as a JSON object.
        4. Sends a GET request to the 'generate-download-file' endpoint with the serialized data.
        5. Asserts that the response status code is 200.
        6. Sends a POST request to the 'upload-files' endpoint
           for each file in the morphology directory.
        7. Asserts that the response status code is 200.
        8. Sends a POST request to the 'upload-files' endpoint
           for each file in the config directory.
        9. Asserts that the response status code is 200
           for all files except 'morph.json'.
        10. Sends a POST request to the 'upload-files' endpoint
            for each file in the mechanisms directory.
        11. Asserts that the response status code is 200 for all files.
        """

        morphology_dir = os.path.join(self.workflow_path, 'model', 'morphology')
        config_dir = os.path.join(self.workflow_path, 'model', 'config')
        mechanisms_dir = os.path.join(self.workflow_path, 'model', 'mechanisms')
        files_list = []
        files_list += ['morphology/' + f for f in os.listdir(morphology_dir)]
        files_list += ['config/' + f for f in os.listdir(config_dir)]
        files_list += ['mechanisms/' + f for f in os.listdir(mechanisms_dir)]
        data = json.dumps({'path': files_list})

        download_url = reverse('generate-download-file', args=[self.exc_code])
        response = self.client.get(download_url,
                                   data={'file_list': data},
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

        upload_url = reverse('upload-files', args=[self.exc_code])

        # test morphology
        morph_file = os.listdir(morphology_dir)[0]
        with open(os.path.join(morphology_dir, morph_file), 'rb') as fd:
            form_file = SimpleUploadedFile(name=morph_file,
                                           content=fd.read(),
                                           content_type='octet-stream')
            response = self.client.post(upload_url,
                                        data={'file': [form_file], 'folder': 'morphology/'})
            self.assertEqual(response.status_code, 200)

        # test config
        config_files = os.listdir(config_dir)
        for config_file in config_files:
            with open(os.path.join(config_dir, config_file), 'rb') as fd:
                form_file = SimpleUploadedFile(name=config_file,
                                               content=fd.read(),
                                               content_type='octet-stream')
                response = self.client.post(upload_url,
                                            data={'file': [form_file], 'folder': 'config/'})
                if config_file == 'morph.json':
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.content.decode(),
                                     messages.UPLOADED_WRONG_CONFIG_FILE)
                else:
                    self.assertEqual(response.status_code, 200)

        # test mechanisms
        for mechanism in os.listdir(mechanisms_dir):
            with open(os.path.join(mechanisms_dir, mechanism), 'rb') as fd:
                form_file = SimpleUploadedFile(name=mechanism,
                                               content=fd.read(),
                                               content_type='octet-stream')
                response = self.client.post(upload_url,
                                            data={'file': [form_file], 'folder': 'mechanisms/'})
                self.assertEqual(response.status_code, 200)

    def test_show_results(self):
        """
        Test the behavior of the show_results API endpoint.

        This function sends a POST request to the show-results
        endpoint with a specific exception code. It then sends a
        GET request to the same endpoint and checks the response status codes.
        """
        url = reverse('show-results', args=[self.exc_code])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_files(self):
        """
        Tests the functionality of deleting files.
        """
        url = reverse('delete-files', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        morphology_dir = os.path.join(self.workflow_path, 'model', 'morphology')
        config_dir = os.path.join(self.workflow_path, 'model', 'config')
        mechanisms_dir = os.path.join(self.workflow_path, 'model', 'mechanisms')
        files_list = []
        files_list += ['morphology/' + f for f in os.listdir(morphology_dir)]
        files_list += ['config/' + f for f in os.listdir(config_dir)]
        files_list += ['mechanisms/' + f for f in os.listdir(mechanisms_dir)]
        data = json.dumps({'file_list': files_list})

        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_optimization_settings(self):
        """
        Test the optimization settings API endpoint.

        This function performs a series of tests on the optimization settings API endpoint.
        It tests both GET and POST requests with various data inputs.
        """
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
        self.assertEqual(response.content.decode(), messages.AUTHENTICATION_INVALID_CREDENTIALS)

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
        """
        This function is used to test the 'run_optimization' endpoint of the API.
        It performs multiple tests with different optimization
        settings and checks the response status code.
        """
        url = reverse('run-optimization', args=[self.exc_code])

        # test with DAINT, default optimization settings
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])

        # test with NSG, overriding runtime and hpc
        with open(os.path.join(self.workflow_path, 'optimization_settings.json'), 'r') as fd:
            jj = json.load(fd)
        jj['hpc'] = 'NSG'
        jj['runtime'] = 0.1
        jj['username_submit'] = os.environ['NSG_USERNAME']
        jj['password_submit'] = os.environ['NSG_PASSWORD']
        opt_url = reverse('optimization-settings', args=[self.exc_code])
        response = self.client.post(opt_url, json.dumps(jj), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_fetch_jobs_and_results_in_daint(self):
        """
        Test the fetch_jobs_and_results_in_daint function.

        This function tests the fetch_jobs_and_results_in_daint function of the API
        class. It performs a series of HTTP GET requests to different endpoints and
        asserts the response status code, content, and JSON keys.
        """
        url = reverse('fetch-jobs', args=[self.exc_code])
        auth_url = reverse('get-authentication')

        # test without hpc
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(),
                         messages.NO_HPC_SELECTED)

        # test authentication first
        response = self.client.get(auth_url)
        self.assertEqual(response.status_code, 200)

        # test in DAINT
        response = self.client.get(url, data={"hpc": "DAINT-CSCS"})
        self.assertIn(response.status_code, [200, 400])

        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])
            # test download results
            if len(list(response.json()['jobs'])) > 0:
                url = reverse('fetch-job-result', args=[self.exc_code])
                response = self.client.get(
                    url,
                    data={'job_id': list(response.json()['jobs'].keys())[0],
                        'hpc': 'DAINT-CSCS'}
                )
                self.assertEqual(response.status_code, 200)

    def test_fetch_jobs_and_results_in_nsg(self):
        """
        Test the fetch jobs and results in NSG.

        The function sends a POST request to the 'get-authentication' endpoint
        to set the credentials for NSG. It then sends a GET request to the
        'fetch-jobs' endpoint with the 'hpc' parameter set to 'NSG' to fetch jobs.
        If the response status code is 200, it asserts that the response contains a list of jobs.
        If there are jobs available, it sends a GET request to the 'fetch-job-result'
        endpoint with the 'job_id' and 'hpc' parameters to fetch the job results.
        The function asserts that the response status code is either 200 or 404.
        """
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
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])
            # test download results
            if len(list(response.json()['jobs'])) > 0:
                url = reverse('fetch-job-result', args=[self.exc_code])
                response = self.client.get(
                    url,
                    data={'job_id': list(response.json()['jobs'].keys())[0],
                        'hpc': 'NSG'}
                )
                self.assertIn(response.status_code, [200, 404])

    def test_fetch_jobs_and_results_in_service_account(self):
        """
        Test fetching jobs and results in service account.

        This function sends a GET request to the 'fetch-jobs'
        endpoint with the specified parameters:
        - `hpc`: "SA"
        - `saHPC`: "pizdaint"
        - `saProject`: "hhnb_daint_cscs"

        The response status code is checked to be either 200 or 400.
        If it is 200, the response JSON is expected to have a key named 'jobs'.
        If the length of the list of 'jobs' is greater than 0, another GET request is
        sent to the 'fetch-job-result' endpoint with the following parameters:
        - `job_id`: The first key in the 'jobs' dictionary of the response JSON
        - `hpc`: "SA"
        - `saHPC`: "pizdaint"
        - `saProject`: "hhnb_daint_cscs"

        The response status code is again checked to be either 200 or 404.

        This test ensures that the 'fetch-jobs' and 'fetch-job-result'
        endpoints in the service account API are functioning correctly.
        """
        url = reverse('fetch-jobs', args=[self.exc_code])
        response = self.client.get(url, data={"hpc": "SA", "saHPC": "pizdaint",
                                              "saProject": 'hhnb_daint_cscs'})
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            self.assertListEqual(list(response.json().keys()), ['jobs'])
            if len(list(response.json()['jobs'])) > 0:
                url = reverse('fetch-job-result', args=[self.exc_code])
                response = self.client.get(
                    url,
                    data={'job_id': list(response.json()['jobs'].keys())[0],
                        'hpc': 'SA', 'saHPC': 'pizdaint',
                        'saProject': 'hhnb_daint_cscs'}
                )
                print(response.status_code, response.content)
                self.assertIn(response.status_code, [200, 404])

    def test_run_analysis(self):
        """
        Test the run_analysis endpoint.

        This function sends a GET request to the run-analysis endpoint with the specified
        exception code. It then asserts that the response status code is 200.
        """
        url = reverse('run-analysis', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_upload_to_naas(self):
        """
        Test the upload_to_naas function.

        This function tests the functionality of the upload_to_naas function.
        It performs the following steps:
        1. Calls the reverse function to generate the URL for the 'upload-to-naas'
           endpoint, passing the self.exc_code as an argument.
        2. Sends a GET request to the generated URL using the self.client object.
        3. Asserts that the response status code is either 200 or 500.
        4. If the response status code is 500, it asserts that the response content
           is equal to the messages.BLUE_NAAS_NOT_AVAILABLE constant.
        """
        url = reverse('upload-to-naas', args=[self.exc_code])
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 500:
            self.assertEqual(response.content.decode(),
                             messages.BLUE_NAAS_NOT_AVAILABLE)

    def test_get_model_catalog_attribute_options(self):
        """
        Test the 'get_model_catalog_attribute_options' function.
        """
        url = reverse('get-model-catalog-attribute-options')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 400:
            self.assertEqual(response.content, b'<b>Error !</b>')

    def test_register_model(self):
        """
        Test the registration of a model.

        This function tests the registration of a model by sending a POST request
        to the 'register-model' API endpoint. It ensures that the response status code
        is either 200 or 400, indicating a successful or unsuccessful registration.
        """
        url = reverse('register-model', args=[self.exc_code])
        form_data = {
            'authorLastName': 'test',
            'authorFirstName': 'test',
            'modelOrganization': 'test',
            'modelCellType': 'test',
            'modelScope': 'test',
            'modelAbstraction': 'test',
            'modelBrainRegion': 'test',
            'modelSpecies': 'test',
            'modelLicense': 'test',
            'modelDescription': 'test',
            'modelPrivate': True
        }
        response = self.client.post(url, data=json.dumps(form_data), content_type='application/json')
        self.assertIn(response.status_code, [200, 400])

    def test_user_avatar(self):
        """
        Test the the get-user-avatar url.
        Returns a 200 response with the user's avatar image otherwise 404.
        """
        # can't be used due to the user is not being logged in
        url = reverse('get-user-avatar')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 404:
            self.assertEqual(response.content, b'Avatar not found')

    def test_get_user_page(self):
        """
        Test the `get_user_page` API endpoint.
        Returns a 302 redirect with the EBRAINS user's page url.
        """
        # can't test due to the user not being logged in
        url = reverse('get-user-page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_get_authentication(self):
        """
        Test the get_authentication function.

        This function tests the functionality of the get_authentication function.
        It sends a GET request to the 'get-authentication' URL to test the EBRAINS
        authentication and a POST request with username and password data for NSG.
        The function then checks the status codes of the responses and verifies
        that they are either 200 or 400. If the status code is 400, the function
        also checks the content of the response to ensure it matches the expected value.
        """
        url = reverse('get-authentication')
        response_ebrains = self.client.get(url)
        response_nsg = self.client.post(url, data={'username': os.environ['NSG_USERNAME'],
                                                   'password': os.environ['NSG_PASSWORD']})
        self.assertIn(response_ebrains.status_code, [200, 400])
        self.assertIn(response_nsg.status_code, [200, 400])
        if response_ebrains.status_code == 400:
            self.assertEqual(response_ebrains.content.decode(),
                             messages.NOT_AUTHENTICATED)
        if response_ebrains.status_code == 400:
            self.assertEqual(response_nsg.content.decode(),
                             messages.NOT_AUTHENTICATED)

    def test_hhf_comm(self):
        """
        Test case for the `test_hhf_comm` function.

        This function sends a GET request to the `hhf-comm` API endpoint
        with the `hhf_dict` parameter set to the encoded data.
        The encoded data is a JSON string that contains information about
        the `HHF-Comm` morphology and electrophysiologies.
        The function then asserts that the response status code is 200
        and returns the exception context from the response.
        """
        encoded_data = '{%22HHF-Comm%22:{%22morphology%22:{%22name%22:%22010710HP2%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252F325731aa-c302-471b-b9fa-2b4cd4cdb4fc%22},%22electrophysiologies%22:[{%22name%22:%2295810006%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252Fa42f0923-2bfa-43fe-aff4-670155d286ee%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810006_metadata.json%22},{%22name%22:%2295810007%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252F07a6c7d4-4ee2-41b5-bc7d-44476b4256d2%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810007_metadata.json%22},{%22name%22:%2295810008%22,%22url%22:%22https%3A%2F%2Fbbp.epfl.ch%2Fnexus%2Fv1%2Ffiles%2Fpublic%2Fhippocampus-hub%2Fhttps%253A%252F%252Fbbp.epfl.ch%252Fneurosciencegraph%252Fdata%252Fca85bca0-6c40-496a-88cb-78562cc10639%22,%22metadata%22:%22https%3A%2F%2Fobject.cscs.ch%2Fv1%2FAUTH_c0a333ecf7c045809321ce9d9ecdfdea%2Fweb-resources-bsp%2Fdata%2FNFE%2FMetadataHippocampusHub%2F95810008_metadata.json%22}],%22modFiles%22:[{%22name%22:%22bg2pyr.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fbg2pyr.mod%22},{%22name%22:%22cal2.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fcal2.mod%22},{%22name%22:%22h.mod%22,%22url%22:%22https%3A%2F%2Fsenselab.med.yale.edu%2Fmodeldb%2FgetModelFile%3Fmodel%3D150288%26AttrID%3D23%26s%3Dyes%26file%3D%2F%252fKimEtAl2013%252fh.mod%22}]}}'
        data = {'hhf_dict': unquote(encoded_data)}
        url = reverse('hhf-comm')
        sleep(1)
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        return response.context['exc']

    def test_hhf_etraces_dir(self):
        """
        Test the 'hhf-etraces-dir' endpoint by sending a GET request with a specific exception code.
        """
        self.exc_code = self.test_hhf_comm()
        url = reverse('hhf-etraces-dir', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['hhf_etraces_dir'])

    def test_hhf_list_files(self):
        """
        Test the 'hhf-list-files' API endpoint.

        This function sends a GET request to the 'hhf-list-files' URL with the
        appropriate arguments. It then checks that the response status code is
        200, indicating a successful request.
        """
        url = reverse('hhf-list-files', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_hhf_get_files_content(self):
        """
        Tests the "hhf_get_files_content" API endpoint by making GET requests to retrieve
        the content of files in various folders. It verifies that the response status code
        is either 200 or 400.
        """
        folders = ['morphologyFolder' , 'mechanismsFolder', 'configFolder',
                   'modelFolder', 'parametersFolder', 'optNeuronFolder']
        for folder in folders:
            url = reverse('hhf-get-files-content', args=[folder, self.exc_code])
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 400])

    def test_hhf_get_model_key(self):
        """
        Test the `hhf_get_model_key` function.

        This function tests the `hhf_get_model_key` function by making
        a GET request to the `hhf-get-model-key` endpoint and checking
        if the response status code is 200 and if the returned JSON contains the key `model_key`.
        """
        url = reverse('hhf-get-model-key', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json().keys()), {'model_key'})

    def test_hhf_apply_model_key(self):
        """
        Test the `hhf_apply_model_key` API endpoint.

        This function tests if the `files` key is updated correctly.
        However, the current implementation takes the model key from
        the model workflow path, which makes it impossible to test.
        """
        # files key are updated correctly but currently
        # the model key is taken from the model workflow path
        # and it can't be test
        url = reverse('hhf-apply-model-key', args=[self.exc_code])
        response = self.client.post(url, data={'model_key': 'test'})
        self.assertEqual(response.status_code, 200)

    def test_hhf_save_config_file(self):
        """
        Test case for the `hhf_save_config_file` method.

        This test case checks the behavior of the `hhf_save_config_file`
        method in the `TestClassName` class. It verifies that the method
        correctly saves a configuration file.
        """
        for config_file in os.listdir(CONFIG_FILES_DIR):
            url = reverse('hhf-save-config-file', args=['configFolder', config_file, self.exc_code])
            with open(os.path.join(CONFIG_FILES_DIR, config_file), 'r') as fd:
                content = fd.read()
            response = self.client.post(url, data={config_file: content})
            self.assertEqual(response.status_code, 200)

    def test_hhf_load_parameters_template(self):
        """
        This function is used to test the 'hhf-load-parameters-template' API endpoint.
        """
        url = reverse('hhf-load-parameters-template', args=[self.exc_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        for parameter_type in ['pyramidal', 'interneuron']:
            response = self.client.post(url, data={'type': parameter_type})
            self.assertEqual(response.status_code, 200)

    def test_get_service_account_content(self):
        """
        Test the 'get_service_account_content' API endpoint.

        This function sends a POST request to the 'get-service-account-content' URL
        and asserts that the response status code is 405. Then it sends a GET request
        to the same URL and asserts that the response status code is 200.
        Finally, it asserts that the response JSON contains the key 'service-account'.
        """
        url = reverse('get-service-account-content')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json().keys()), {'service-account'})
