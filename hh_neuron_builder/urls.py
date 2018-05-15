from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

exc_pattern = 'tab_[0-9]{14}'    
ctx_pattern = '[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}'
req_pattern = '(?P<exc>' + exc_pattern  + ')/(?P<ctx>' + ctx_pattern + ')'

urlpatterns = [
    url(r'^$', views.home),    
    url(r'^login/hbp', auth_views.login),
    url(r'^logout/hbp', auth_views.logout),
    url(r'^check-cond-exist/' + req_pattern + '$', views.check_cond_exist),
    url(r'^choose-opt-model/$', views.choose_opt_model),    
    url(r'^copy-feature-files/(?P<featurefolder>.*)/' + req_pattern  +'/$', views.copy_feature_files),
    url(r'^create-wf-folders/(?P<wf_type>new|cloned)/' + req_pattern  + '$', views.create_wf_folders, name="create_wf_folders"),    
    url(r'^delete-files/(?P<filetype>feat|optset|modsim)/' + req_pattern + '/$', views.delete_files),
    url(r'^download-job/(?P<job_id>.*)/' + req_pattern  + '/$', views.download_job),    
    url(r'^download-zip/(?P<filetype>feat|modsim|optset|optres)/' + req_pattern  +'/$', views.download_zip),
    url(r'^embedded-efel-gui/$', views.embedded_efel_gui),    
    url(r'^embedded-naas/' + req_pattern  + '/$', views.embedded_naas),
    url(r'^fetch-opt-set-file/(?P<source_opt_name>[_a-zA-Z0-9\-.]*)/' + req_pattern  + '/$', views.fetch_opt_set_file),
    url(r'^fetch-wf-from-storage/(?P<wfid>[0-9]{14}_[0-9]+)/' + req_pattern  + '/$', views.fetch_wf_from_storage),
    url(r'^get_local_optimization_list$', views.get_local_optimization_list),
    url(r'^get_model_list/' + req_pattern  + '$', views.get_model_list),    
    url(r'^get-nsg-job-details/(?P<jobid>.*)/'+ req_pattern + '/$', views.get_nsg_job_details),    
    url(r'^get-nsg-job-list/' + req_pattern  + '$', views.get_nsg_job_list),    
    url(r'^initialize/(?P<exc>' + exc_pattern + ')/(?P<ctx>' + ctx_pattern + ')$', views.initialize),    
    url(r'^model-loaded-flag/' + req_pattern  + '$', views.model_loaded_flag),
    url(r'^modify-analysis-py/' + req_pattern  + '$', views.modify_analysis_py),
    url(r'^run-optimization/' + req_pattern  + '/$', views.run_optimization),    
    url(r'^save-wf-to-storage/' +  req_pattern  + '$', views.save_wf_to_storage),
    url(r'^submit-run-param/' + req_pattern  + '/$', views.submit_run_param),    
    url(r'^submit-fetch-param/' + req_pattern  + '/$', views.submit_fetch_param),    
    url(r'^upload-files/(?P<filetype>feat|modsim|optset)/' + req_pattern + '/$', views.upload_files),
    url(r'^upload-to-naas/' + req_pattern  + '$', views.upload_to_naas),    
    url(r'^wf-storage-list/' + req_pattern  + '/$', views.wf_storage_list),
    url(r'^workflow/$', views.workflow),    
    url(r'^zip-sim/' + req_pattern  + '$', views.zip_sim),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
