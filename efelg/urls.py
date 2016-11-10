from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

urlpatterns = [
    #url(r'^$', views.access),    
    url(r'^$', views.overview),    
    url('', include('social.apps.django_app.urls', namespace='social')),
    #url(r'^select_files/$', views.select_files),
    url(r'^login/hbp', auth_views.login),
    url(r'^show_traces/$', views.show_traces),
    url(r'^select_files_tree$', views.select_files_tree),
    url(r'^sf_tmp$', views.sf_tmp),
    url(r'^create_session_var$', views.create_session_var),
    url(r'^get_list$', views.get_list),
    url(r'^get_data/(?P<cellname>[0-9a-zA-Z_-]+)$', views.get_data),
    #url(r'^select_traces/$', views.select_traces),
    url(r'^select_features/$', views.select_features),
    url(r'^select_all_features/$', views.select_all_features),
    url(r'^extract_features_rest/$', views.extract_features_rest),
    url(r'^upload_files_page/$', views.upload_files_page),
    url(r'^edit/$', views.edit),
    url(r'^download_zip', views.download_zip),
    url(r'^features_dict', views.features_dict),
    url(r'^features_json', views.features_json),
    url(r'^protocol_json', views.protocol_json),
    url(r'^pdf_path/$', views.pdf_path),
    url(r'^get_directory_structure', views.get_directory_structure),
    url(r'^upload_files', views.upload_files),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
