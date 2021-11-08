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
from functools import update_wrapper
from django.urls import path, register_converter
from django.conf.urls.static import static
from hhnb.utils import converters
from hhnb import views


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


register_converter(converters.FileTypeConverter, 'file_type')


urlpatterns = [
    # session refresh
    path('session-refresh/<exc:exc>', views.session_refresh),
    
    # pages
    path('', views.home_page),
    path('workflow/<exc:exc>', views.workflow_page),
    
    # workflow apis
    path('initialize-workflow', views.initialize_workflow),
    path('upload-workflow', views.upload_workflow),
    path('store-workflow-in-session/<exc:exc>', views.store_workflow_in_session),
    path('clone-workflow/<exc:exc>', views.clone_workflow),
    path('download-workflow/<exc:exc>', views.download_workflow),
    path('get-workflow-properties/<exc:exc>', views.get_workflow_properties), 

    # files apis
    path('upload-features/<exc:exc>', views.upload_features),
    path('upload-model/<exc:exc>', views.upload_model),
    path('upload-analysis/<exc:exc>', views.upload_analysis),
    path('upload-files/<exc:exc>', views.upload_files),

    path('download-files/<exc:exc>', views.download_files),
    path('delete-files/<exc:exc>', views.delete_files),

    # optimization settings api
    path('optimization-settings/<exc:exc>', views.optimization_settings),

    # model catalog
    path('fetch-models/<exc:exc>', views.fetch_models),

    # user avatar
    path('get-user-avatar', views.get_user_avatar),
    path('get-authentication', views.get_authentication),

    # jobs apis
    path('run-optimization/<exc:exc>', views.run_optimization),
    path('fetch-jobs/<exc:exc>', views.fetch_jobs),
    path('fetch-job-result/<exc:exc>', views.fetch_job_results),

    # analysis apis
    path('run-analysis/<exc:exc>', views.run_analysis),

    # blue-naas apis
    path('upload-to-naas/<exc:exc>', views.upload_to_naas),

    # hippocampus hub api
    path('hhf-comm', views.hhf_comm),
    path('hhf-etraces-dir', views.hhf_etraces_dir),
    path('hhf-list-files/<exc:exc>', views.hhf_list_files),

    # these functions below will be deprecated soon
    path('hhf-get-files-content/<folder:folder>/<exc:exc>', views.hhf_get_files_content),
    path('hhf-get-model-key/<exc:exc>', views.hhf_get_model_key),
    path('hhf-apply-model-key/<exc:exc>', views.hhf_apply_model_key),
    path('hhf-save-config-file/<folder:folder>/<config_file:config_file>/<exc:exc>', views.hhf_save_config_file),
]