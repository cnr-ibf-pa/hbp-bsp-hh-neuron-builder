from django.urls import path

from efelg import views


urlpatterns = [
    path('', views.overview),
    path('overview/', views.overview),
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
    path('docs/file_formats/', views.file_formats_docs),

    path('get_result_dir/', views.get_result_dir),

    # url(r'^login/hbp', auth_views.login),
    # url(r'^logout/hbp', auth_views.logout),
    # path('generate_json_data', views.generate_json_data),
    # path('get_list_new', views.get_list_new),
    # path('get_data/(?P<cellname>[0-9a-zA-Z_-]+)', views.get_data),
    # path('status/', views.status),
    # path('features_json_path', views.features_json_path),
    # path('features_json_files_path', views.features_json_files_path),
    # path('protocols_json_path', views.protocols_json_path),
    # path('features_pdf_path', views.features_pdf_path),
    # path('get_directory_structure', views.get_directory_structure), 
    # path('upload_zip_file_to_storage', views.upload_zip_file_to_storage),
    # path('hbp-redirect/', views.hbp_redirect),
    
]
