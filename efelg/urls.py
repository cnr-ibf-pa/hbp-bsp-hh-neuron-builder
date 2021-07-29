from django.urls import path, register_converter
from hhnb.utils.converters import WorkflowIdConverter
from efelg import views


register_converter(WorkflowIdConverter, 'workflow_id')


urlpatterns = [
    path('', views.overview),
    path('overview/', views.overview),
    path('error_space_left/', views.error_space_left),
    path('get_list', views.get_list),
    path('get_data/<slug:cellname>', views.get_data),
    path('show_traces/', views.show_traces),
    path('upload_files', views.upload_files),
    path('select_features/', views.select_features),
    path('features_dict', views.features_dict),
    path('extract_features', views.extract_features),
    path('results/', views.results),
    path('download_zip', views.download_zip),
    path('docs/', views.index_docs),
    path('docs/index/', views.index_docs),
    path('docs/dataset/', views.dataset),
    path('docs/file_formats/', views.file_formats_docs),
    path('get_result_dir/', views.get_result_dir),
    path('hhf_etraces/<workflow_id:wfid>', views.hhf_etraces),
    path('load_hhf_etraces/', views.load_hhf_etraces),
]
