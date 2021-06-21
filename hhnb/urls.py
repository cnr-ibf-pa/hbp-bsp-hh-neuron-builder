"""hh_neuron_builder URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, register_converter
from django.conf.urls.static import static
from hhnb import views
from hhnb.utils import converters


register_converter(converters.ExcConverter, 'exc')
# register_converter(converters.CtxConverter, 'ctx')  # replaced by uuid
register_converter(converters.AnyCharConvert, 'any')
register_converter(converters.NewOrCloneConvert, 'new_or_cloned')
register_converter(converters.FeatOrOptsetOrModsimConverter, 'feat_or_optset_or_modsim')
register_converter(converters.FeatOrOptsetOrModsimOrOptresConverter, 'feat_or_optset_or_modsim_or_optres')
register_converter(converters.SourceOptConverter, 'source_opt_id')
register_converter(converters.WorkflowIdConverter, 'workflow_id')
register_converter(converters.CurrentOrStorageCollabConverter, 'current_or_storage_collab')
register_converter(converters.HpcConverter, 'hpc')
register_converter(converters.JobIdConverter, 'jobid')
register_converter(converters.FolderConverter, 'folder')
register_converter(converters.ConfigFileConverter, 'config_file')

required = '<exc:exc>/<uuid:ctx>'
# required = ''

urlpatterns = [
    path('', views.home),
    path('check-cond-exist/' + required, views.check_cond_exist),
    path('choose-opt-model/', views.choose_opt_model),
    #path('copy-feature-files/<any:feature_folder>/' + required + '/', views.copy_feature_files),
    path('copy-feature-files/' + required + '/', views.copy_feature_files),
    path('create-wf-folders/<new_or_cloned:wf_type>/' + required, views.create_wf_folders, name='create_wf_folders'),
    path('delete-files/<feat_or_optset_or_modsim:file_type>/' + required + '/', views.delete_files),
    path('download-job/<jobid:job_id>/' + required + '/', views.download_job),
    path('download-zip/<feat_or_optset_or_modsim_or_optres:file_type>/' + required + '/', views.download_zip),
    path('embedded-efel-gui/' + required + '/', views.embedded_efel_gui),
    path('embedded-naas/' + required + '/', views.embedded_naas),
    path('fetch-opt-set-file/<source_opt_id:source_opt_name>/<source_opt_id:source_opt_id>/' + required + '/', views.fetch_opt_set_file),
    path('get-data-model-catalog/' + required + '/', views.get_data_model_catalog),
    path('get_local_optimization_list', views.get_local_optimization_list),
    path('get_model_list/' + required, views.get_model_list),
    path('get-job-details/<uuid:jobid>/' + required + '/', views.get_job_details),
    path('get-job-details2/<jobid:jobid>/' + required + '/', views.get_job_details2),
    path('get-job-list/' + required, views.get_job_list),
    path('get-job-list/<hpc:hpc>/' + required, views.get_job_list2),
    path('get-user-clb-permissions/' + required, views.get_user_clb_permissions),
    path('initialize/' + required, views.initialize),
    path('model-loaded-flag/' + required, views.model_loaded_flag),
    path('register-model-catalog/<current_or_storage_collab:reg_collab>/' + required + '/', views.register_model_catalog),
    path('run-analysis/' + required, views.run_analysis),
    path('run-optimization/' + required + '/', views.run_optimization),
    path('save-wf-to-storage/' + required, views.save_wf_to_storage),
    path('set-exc-tags/' + required + '/', views.set_exc_tags),
    path('status/', views.status),
    path('submit-run-param/' + required + '/', views.submit_run_param),
    path('submit-fetch-param/' + required + '/', views.submit_fetch_param),
    # path('upload-files/<feat_or_optset_or_modsim:file_type>/' + required + '/', views.upload_files),
    path('upload-to-naas/' + required, views.upload_to_naas),
    path('wf-storage-list/' + required + '/', views.wf_storage_list),
    path('workflow/', views.workflow),
    path('zip-sim/<any:job_id>/' + required, views.zip_sim),

    path('workflow-upload/' + required, views.workflow_upload),
    path('workflow-download/' + required, views.workflow_download),
    path('simulation-result-download/' + required, views.simulation_result_download),

    path('get-user-avatar', views.get_user_avatar),
    path('get-user-page', views.get_user_page),
    
    path('clone-workflow/' + required + '/', views.clone_workflow),
    path('workflow/' + required + '/', views.workflow),

    path('upload-files/feat/' + required + '/', views.upload_feat_files),
    path('upload-files/optset/' + required + '/', views.upload_optset_files),
    path('upload-files/modsim/' + required + '/', views.upload_modsim_files),

    path('get-authentication', views.get_authentication),
    path('check-nsg-login/' + required + '/', views.check_nsg_login),

    path('store-workflow-in-session/' + required + '/', views.store_workflow_in_session),

    # path('hhf-comm/<any:hhf_dict>', views.hhf_comm),
    path('hhf-comm', views.hhf_comm),
    path('hhf-get-files/' + required + '/', views.hhf_get_files),
    path('hhf-get-files-content/<folder:folder>/' + required, views.hhf_get_files_content),
    path('hhf-download-files/<folder:folder>/' + required, views.hhf_download_files),
    path('hhf-download-files/parameters/' + required, views.hhf_download_parameters),
    path('hhf-download-files/optneuron/' + required, views.hhf_download_optneuron),
    path('hhf-upload-files/<folder:folder>/' + required + '/', views.hhf_upload_files),
    path('hhf-delete-files/<folder:folder>/' + required, views.hhf_delete_files),
    path('hhf-apply-model-key/' + required + '/<any:model_key>', views.hhf_apply_model_key),
    path('hhf-get-model-key/' + required + '/', views.hhf_get_model_key),
    path('hhf-save-config-file/<config_file:config_file>/' + required, views.hhf_save_config_file),
    path('hhf-delete-all/' + required, views.hhf_delete_all),
    path('hhf-download-all/' + required, views.hhf_download_all),

    # test endpoint TODO: to be remove
    path('hhf-etraces-test/', views.hhf_etraces_test),
]

