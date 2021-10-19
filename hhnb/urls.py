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
    
    # pages
    path('', views.home),
    path('workflow/<exc:exc>', views.workflow),
    
    # home page apis
    path('initialize-workflow/', views.initialize_workflow),
    path('upload-workflow/', views.upload_workflow),
    path('clone-workflow/<exc:exc>', views.clone_workflow),
    path('download-workflow/<exc:exc>', views.download_workflow),

    # workflow apis
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
]