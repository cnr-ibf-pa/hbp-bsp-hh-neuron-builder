"""
Test all urls resolvers.
"""

from django.test import SimpleTestCase
from django.urls import reverse, resolve
from efelg import views


class TestUrlResolver(SimpleTestCase):

    def test_resolve_overview(self):
        url = reverse('')
        self.assertEqual(resolve(url).func, views.overview)
        url = reverse('overview')
        self.assertEquals(resolve(url).func, views.overview)

    def test_resolve_error_space_left(self):
        url = reverse('error-space-left')
        self.assertEqual(resolve(url).func, views.error_space_left)

    def test_get_list(self):
        url = reverse('get-list')
        self.assertEqual(resolve(url).func, views.get_list)

    def test_get_data(self):
        url = reverse('get-data', args=['some-cell-name'])
        self.assertEqual(resolve(url).func, views.get_data)

    def test_show_traces(self):
        url = reverse('show-traces')
        self.assertEqual(resolve(url).func, views.show_traces)

    def test_upload_files(self):
        url = reverse('upload-files')
        self.assertEqual(resolve(url).func, views.upload_files)

    def test_select_features(self):
        url = reverse('select-features')
        self.assertEqual(resolve(url).func, views.select_features)

    def test_features_dict(self):
        url = reverse('features-dict')
        self.assertEqual(resolve(url).func, views.features_dict)

    def test_extract_features(self):
        url = reverse('extract-features')
        self.assertEqual(resolve(url).func, views.extract_features)

    def test_results(self):
        url = reverse('results')
        self.assertEqual(resolve(url).func, views.results)

    def test_download_zip(self):
        url = reverse('download-zip')
        self.assertEqual(resolve(url).func, views.download_zip)

    def test_get_dataset(self):
        url = reverse('get-dataset')
        self.assertEqual(resolve(url).func, views.get_dataset)

    def test_get_result_dir(self):
        url = reverse('get-result-dir')
        self.assertEqual(resolve(url).func, views.get_result_dir)

    def test_hhf_etraces(self):
        url = reverse('hhf-etraces', args=['tab_12345678901234'])
        self.assertEqual(resolve(url).func, views.hhf_etraces)

    def test_load_hhf_etraces(self):
        url = reverse('load-hhf-etraces')
        self.assertEqual(resolve(url).func, views.load_hhf_etraces)

    def test_docs(self):
        url = reverse('docs')
        self.assertEqual(resolve(url).func, views.index_docs)

    def test_docs_index(self):
        url = reverse('docs-index')
        self.assertEqual(resolve(url).func, views.index_docs)

    def test_docs_dataset(self):
        url = reverse('docs-dataset')
        self.assertEqual(resolve(url).func, views.dataset)
