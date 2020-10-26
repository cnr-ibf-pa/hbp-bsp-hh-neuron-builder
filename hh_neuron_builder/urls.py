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
from django.urls import path, include, register_converter

# from hhnb.utils.converters import AnyCharConvert
# register_converter(AnyCharConvert, 'any')


urlpatterns = [
    # path('hbp-login/', login_view.login, name='hbp-login'),
    # path('hbp-login/?ctx=<uuid:ctx>', login_view.login, name='hbp-login'),
    # path('hbp-login/?next=/?ctx=<uuid:ctx>', login_view.login, name='hbp-login'),
    # path('hbp-login/<any:path>', login_view.login, name='hbp-login'),
    path('oidc/', include('mozilla_django_oidc.urls')),

    path('efelg/', include('efelg.urls')),
    path('hh-neuron-builder/', include('hhnb.urls')),
]
