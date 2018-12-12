from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^$', views.main_view, name='main'),
    url(r'^data_list/$', views.data_list, name='data_list'),
]
