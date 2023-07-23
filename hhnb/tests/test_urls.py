from django.test import SimpleTestCase
from django.urls import reverse, resolve
from hhnb import views


ROOT_URL = '/hh-neuron-builder'
EXC_CODE = 'tab_12345678901234'
HHF_FOLDER = 'configFolder'
HHF_FILE = 'parameters.json'


class TestResolverUrls(SimpleTestCase):


    def test_session_refresh(self):
        url = reverse('session-refresh')
        self.assertEqual(resolve(url).func, views.session_refresh)

    def test_status(self):
        url = reverse('status')
        self.assertEqual(resolve(url).func, views.status)

    def test_overview(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func, views.home_page)

    def test_workflow(self):
        url = reverse('workflow', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.workflow_page)

    def test_docs(self):
        url = reverse('hhnb-docs')
        self.assertEqual(resolve(url).func, views.index_docs)

    def test_docs_index(self):
        url = reverse('hhnb-docs-index')
        self.assertEqual(resolve(url).func, views.index_docs)

    def test_initialize_workflow(self):
        url = reverse('initialize-workflow')
        self.assertEqual(resolve(url).func, views.initialize_workflow)

    def test_upload_workflow(self):
        url = reverse('upload-workflow')
        self.assertEqual(resolve(url).func, views.upload_workflow)

    def test_store_workflow_in_session(self):
        url = reverse('store-workflow-in-session', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.store_workflow_in_session)

    def test_clone_workflow(self):
        url = reverse('clone-workflow', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.clone_workflow)

    def test_download_workflow(self):
        url = reverse('download-workflow', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.download_workflow)

    def test_get_workflow_properties(self):
        url = reverse('get-workflow-properties', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.get_workflow_properties)

    def test_upload_features(self):
        url = reverse('upload-features', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.upload_features)

    def test_upload_model(self):
        url = reverse('upload-model', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.upload_model)

    def test_upload_analysis(self):
        url = reverse('upload-analysis', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.upload_analysis)

    def test_upload_files(self):
        url = reverse('upload-files', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.upload_files)

    def test_generate_download_file(self):
        url = reverse('generate-download-file', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.generate_download_file)

    def test_download_file(self):
        url = reverse('download-file', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.download_file)

    def test_delete_file(self):
        url = reverse('delete-files', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.delete_files)

    def test_optimization_settings(self):
        url = reverse('optimization-settings', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.optimization_settings)

    def test_get_model_catalog_attribute_options(self):
        url = reverse('get-model-catalog-attribute-options')
        self.assertEqual(resolve(url).func, views.get_model_catalog_attribute_options)

    def test_fetch_models(self):
        url = reverse('fetch-models', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.fetch_models)

    def test_register_model(self):
        url = reverse('register-model', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.register_model)

    def test_get_user_avatar(self):
        url = reverse('get-user-avatar')
        self.assertEqual(resolve(url).func, views.get_user_avatar)

    def test_get_user_page(self):
        url = reverse('get-user-page')
        self.assertEqual(resolve(url).func, views.get_user_page)

    def test_get_authentication(self):
        url = reverse('get-authentication')
        self.assertEqual(resolve(url).func, views.get_authentication)

    def test_run_optimization(self):
        url = reverse('run-optimization', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.run_optimization)

    def test_fetch_jobs(self):
        url = reverse('fetch-jobs', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.fetch_jobs)

    def test_fetch_job_result(self):
        url = reverse('fetch-job-result', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.fetch_job_results)

    def test_run_analysis(self):
        url = reverse('run-analysis', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.run_analysis)

    def test_upload_to_naas(self):
        url = reverse('upload-to-naas', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.upload_to_naas)

    def test_hhf_comm(self):
        url = reverse('hhf-comm')
        self.assertEqual(resolve(url).func, views.hhf_comm)

    def test_hhf_etraces_dir(self):
        url = reverse('hhf-etraces-dir', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_etraces_dir)

    def test_hhf_list_files(self):
        url = reverse('hhf-list-files', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_list_files)

    def test_hhf_get_files_content(self):
        url = reverse('hhf-get-files-content', args=[HHF_FOLDER, EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_get_files_content)

    def test_hhf_get_model_key(self):
        url = reverse('hhf-get-model-key', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_get_model_key)

    def test_apply_model_key(self):
        url = reverse('hhf-apply-model-key', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_apply_model_key)

    def test_save_config_file(self):
        url = reverse('hhf-save-config-file', args=[HHF_FOLDER, HHF_FILE, EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_save_config_file)

    def test_hhf_load_parameters_template(self):
        url = reverse('hhf-load-parameters-template', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.hhf_load_parameters_template)

    def test_get_service_account_content(self):
        url = reverse('get-service-account-content')
        self.assertEqual(resolve(url).func, views.get_service_account_content)

    def test_show_results(self):
        url = reverse('show-results', args=[EXC_CODE])
        self.assertEqual(resolve(url).func, views.show_results)