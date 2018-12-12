from django.conf.urls import url, include
from django.contrib import admin
from django.shortcuts import redirect

urlpatterns = [
    url(r'^$', lambda r: redirect('crawling:main'), name='root'),
    url(r'^admin/', admin.site.urls),
    url(r'^crawling/', include('crawling.urls', namespace='crawling')),
]
