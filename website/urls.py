from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^apply/$', views.apply, name='apply'),
    url(r'^thankyou/$', views.thankyou, name='thankyou'),
    #url(r'^about/$', views.IndexAbout.as_view(), name='about'),
]
