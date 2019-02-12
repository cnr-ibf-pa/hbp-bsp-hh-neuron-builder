"""bspg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import os

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('hbp_app_python_auth.urls', namespace='hbp-social')),
    url(r'^efelg/', include('efelg.urls'), name='efelg'),
    url(r'^hh-neuron-builder/', include('hh_neuron_builder.urls'), name='hh_neuron_builder'),
    url(r'^bsp-monitor/', include('bsp_monitor.urls'), name='bsp_monitor'),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if 'HBPDEV' not in os.environ:
    urlpatterns.append(url(r'^sitemap/', include('sitemap.urls'), name='sitemap'))
