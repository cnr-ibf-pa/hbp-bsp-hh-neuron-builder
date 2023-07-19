from django.urls import path, register_converter
from hhnb.utils.converters import ExcConverter
from efelg import views

register_converter(ExcConverter, 'exc')


urlpatterns = [
    path('', views.overview, name=''),
    path('overview/', views.overview, name='overview'),
    path('error_space_left/', views.error_space_left, name='error-space-left'),
    path('get_list', views.get_list, name='get-list'),
    path('get_data/<slug:cellname>', views.get_data, name='get-data'),
    path('show_traces/', views.show_traces, name='show-traces'),
    path('upload_files', views.upload_files, name='upload-files'),
    path('select_features/', views.select_features, name='select-features'),
    path('features_dict', views.features_dict, name='features-dict'),
    path('extract_features', views.extract_features, name='extract-features'),
    path('results/', views.results, name='results'),
    path('download_zip', views.download_zip, name='download-zip'),
    path('docs/file_formats/', views.file_formats_docs, name='docs-file-formats'),
    path('get_dataset/', views.get_dataset, name='get-dataset'),
    path('get_result_dir/', views.get_result_dir, name='get-result-dir'),
    #path('hhf_etraces/<workflow_id:wfid>', views.hhf_etraces),
    path('hhf_etraces/<exc:exc>', views.hhf_etraces, name='hhf-etraces'),
    path('load_hhf_etraces/', views.load_hhf_etraces, name='load-hhf-etraces'),

    path('docs/', views.index_docs, name='docs'),
    path('docs/index/', views.index_docs, name='docs-index'),
    path('docs/dataset/', views.dataset, name='docs-dataset'),
]
