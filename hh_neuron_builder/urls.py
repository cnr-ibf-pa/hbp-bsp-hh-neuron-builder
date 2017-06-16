from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.home),    
    url(r'^embedded-efel-gui/$', views.embedded_efel_gui),    
    url(r'^embedded-naas/$', views.embedded_naas),
    url(r'^set-optimization-parameters-fetch/$', views.set_optimization_parameters_fetch),
    url(r'^get_local_optimization_list$', views.get_local_optimization_list),
    url(r'^workflow/$', views.workflow),    
    url(r'^choose-opt-model/$', views.choose_opt_model),    
    url(r'^set-optimization-parameters/$', views.set_optimization_parameters),    
    url(r'^run-optimization/$', views.run_optimization),    
    url(r'^get_model_list$', views.get_model_list),    
    url(r'^get-nsg-job-list$', views.get_nsg_job_list),    
    url(r'^upload-to-naas$', views.upload_to_naas),    
    #url(r'^set-feature-folder/(?P<featurefolder>[a-zA-Z0-9/\-.]*)/$', views.set_feature_folder),
    url(r'^set-feature-folder/(?P<featurefolder>.*)/$', views.set_feature_folder),
    url(r'^set-optimization-name/(?P<optimizationname>[_a-zA-Z0-9.]*)/$', views.set_optimization_name),
    url(r'^set-gen-num/(?P<gennum>.*)/$', views.set_gen_num),
    url(r'^set-off-size/(?P<offsize>.*)/$', views.set_off_size),
    url(r'^set-node-num/(?P<nodenum>.*)/$', views.set_node_num),
    url(r'^set-core-num/(?P<corenum>.*)/$', views.set_core_num),
    url(r'^set-run-time/(?P<runtime>.*)/$', views.set_run_time),
    url(r'^set-username/(?P<username>.*)/$', views.set_username),
    url(r'^set-password/(?P<password>.*)/$', views.set_password),
    url(r'^model-loaded-flag$', views.model_loaded_flag),
    #url(r'^overview/$', views.overview),    
    #url('', include('social.apps.django_app.urls', namespace='social')),
    #url('', include('hbp_app_python_auth.urls', namespace='hbp-social')),
    #url(r'^login/hbp', auth_views.login),
    #url(r'^show_traces/$', views.show_traces),
    #url(r'^generate_json_data$', views.generate_json_data),
    #url(r'^create_session_var$', views.create_session_var),
    #url(r'^get_list$', views.get_list),
    #url(r'^get_data/(?P<cellname>[0-9a-zA-Z_-]+)$', views.get_data),
    #url(r'^select_features/$', views.select_features),
    #url(r'^extract_features/$', views.extract_features),
    #url(r'^download_zip', views.download_zip),
    #url(r'^features_dict', views.features_dict),
    #url(r'^features_json_path', views.features_json_path),
    #url(r'^protocols_json_path', views.protocols_json_path),
    #url(r'^features_pdf_path', views.features_pdf_path),
    #url(r'^get_directory_structure', views.get_directory_structure),
    #url(r'^upload_files', views.upload_files),
    #url(r'^upload_zip_file_to_storage', views.upload_zip_file_to_storage),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
