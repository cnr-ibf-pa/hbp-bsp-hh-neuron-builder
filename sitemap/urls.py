from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
#from django.contrib import admin

from sitemap import views

urlpatterns = [
    url(r'^$', views.sitemap),    
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^login/hbp', auth_views.login),
    url(r'^tree_json$', views.tree_json),
]
