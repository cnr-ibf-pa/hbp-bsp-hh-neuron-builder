from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.overview),    
    url(r'^overview/$', views.overview),    
    url(r'^login/hbp', auth_views.login),
    url(r'^logout/hbp', auth_views.logout),
    url(r'^show_traces/$', views.show_traces),
    url(r'^generate_json_data$', views.generate_json_data),
    url(r'^get_list$', views.get_list),
    url(r'^get_list_new$', views.get_list_new),
    url(r'^get_data/(?P<cellname>[0-9a-zA-Z_-]+)$', views.get_data),
    url(r'^select_features/$', views.select_features),
    url(r'^extract-features$', views.extract_features),
    url(r'^results/$', views.results),
    url(r'^download_zip', views.download_zip),
    url(r'^features_dict', views.features_dict),
    url(r'^features_json_path', views.features_json_path),
    url(r'^features-json-files-path', views.features_json_files_path),
    url(r'^protocols_json_path', views.protocols_json_path),
    url(r'^features_pdf_path', views.features_pdf_path),
    url(r'^get_directory_structure', views.get_directory_structure),
    url(r'^upload_files', views.upload_files),
    url(r'^upload_zip_file_to_storage', views.upload_zip_file_to_storage),
    url(r'^hbp-redirect/$', views.hbp_redirect),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
