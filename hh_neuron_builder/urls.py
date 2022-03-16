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
from django.shortcuts import redirect
from django.urls import path, include, register_converter
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('oidc/', include('mozilla_django_oidc.urls')),

    path('', lambda request: redirect('hh-neuron-builder/', permanent=True)),
    path('hh-neuron-builder/', include('hhnb.urls')),
    
    path('efelg/', include('efelg.urls')),

    path('status', lambda request: redirect('hh-neuron-builder/status', permanent=True)),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
