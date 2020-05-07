from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
    url(r'', include('website.urls')),
    url(r'^kakao/', include('kakao.urls')),
]
