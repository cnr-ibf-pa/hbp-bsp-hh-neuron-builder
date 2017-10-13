from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.home),    
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('hbp_app_python_auth.urls', namespace='hbp-social')),
    url(r'^login/hbp', auth_views.login),
    url(r'^embedded-efel-gui/$', views.embedded_efel_gui),    
    url(r'^embedded-naas/$', views.embedded_naas),
    url(r'^set-optimization-parameters-fetch/$', views.set_optimization_parameters_fetch),
    url(r'^get_local_optimization_list$', views.get_local_optimization_list),
    url(r'^check-cond-exist$', views.check_cond_exist),
    url(r'^workflow/$', views.workflow),    
    url(r'^create-wf-folders/(?P<wf_type>new|cloned)/$', views.create_wf_folders),    
    url(r'^choose-opt-model/$', views.choose_opt_model),    
    url(r'^submit-run-param/$', views.submit_run_param),    
    url(r'^submit-fetch-param/$', views.submit_fetch_param),    
    url(r'^set-optimization-parameters/$', views.set_optimization_parameters),    
    url(r'^run-optimization/$', views.run_optimization),    
    url(r'^get_model_list$', views.get_model_list),    
    url(r'^get-nsg-job-list$', views.get_nsg_job_list),    
    url(r'^get-nsg-job-details/(?P<jobid>.*)/$', views.get_nsg_job_details),    
    url(r'^download-job/(?P<job_id>.*)/$', views.download_job),    
    url(r'^upload-to-naas$', views.upload_to_naas),    
    url(r'^copy-feature-files/(?P<featurefolder>.*)/$', views.copy_feature_files),
    url(r'^fetch-opt-set-file/(?P<source_opt_name>[_a-zA-Z0-9\-.]*)/$', views.fetch_opt_set_file),
    url(r'^model-loaded-flag$', views.model_loaded_flag),
    url(r'^delete-files/(?P<filetype>feat|optset|modsim)/$', views.delete_files),
    url(r'^modify-analysis-py$', views.modify_analysis_py),
    url(r'^zip-sim$', views.zip_sim),
    url(r'^upload-files/(?P<filetype>feat|modsim|optset)/$', views.upload_files),
    url(r'^download-zip/(?P<filetype>feat|modsim|optset)/$', views.download_zip),
    url(r'^save-wf-to-storage$', views.save_wf_to_storage),
    url(r'^get-context/$', views.get_context),
    #url(r'^upload-files$', views.upload_files),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
