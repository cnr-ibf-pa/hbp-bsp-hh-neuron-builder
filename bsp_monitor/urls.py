from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.index),    
    url(r'^login/hbp', auth_views.login),
    url(r'^get-access-token/(?P<token_type>ganalytics|gsheet|all)/$', views.get_access_token),    
    url(r'^get-gs/$', views.get_gs),    
    url(r'^get-all-no-alex/$', views.get_all_no_alex),    
    url(r'^get-exec-member/$', views.get_exec_member),    
    url(r'^get-exec-not_member/$', views.get_exec_not_member),    
    url(r'^get-uc-item-list/$', views.get_uc_item_list),    
    url(r'^get-uc/(?P<start_date>0|[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<end_date>0|[0-9]{4}-[0-9]{2}-[0-9]{2})/$', views.get_uc),    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
