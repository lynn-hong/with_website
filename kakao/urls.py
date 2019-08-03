from django.conf.urls import url
from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    url(r'send_remind/$', views.send_remind, name='send_remind'),
    url(r'oauth/$', views.oauth, name='oauth'),
    url(r'secret/$', views.secret, name='secret'),
    url(r'register/$', RedirectView.as_view(
        url='https://kauth.kakao.com/oauth/authorize?client_id=b1dfd5bbf3bbd637449025f203d51e39'
            '&redirect_uri=https://withlove.cf/kakao/oauth&response_type=code&scope=talk_message,account_email')),
]
