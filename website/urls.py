from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^apply/$', views.apply, name='apply'),
    url(r'^add_attendee/$', views.add_attendee, name='add_attendee'),
    url(r'^submit_attendance/$', views.submit_attendance, name='submit_attendance'),
    url(r'^thankyou/$', views.thankyou, name='thankyou'),
    url(r'^calendar/$', views.IndexCalendar.as_view(), name='calendar'),
    url(r'^get_calendar_events/$', views.get_calendar_events, name='get_calendar_events'),
    url(r'^info/$', views.IndexInfo.as_view(), name='info'),
    url(r'^managers/$', views.IndexManager.as_view(), name='managers'),
    url(r'^contacts/$', views.IndexManagerContact.as_view(), name='contacts'),
    url(r'^members/$', views.IndexMember.as_view(), name='members'),
    url(r'^faq/$', views.IndexFaq.as_view(), name='faq'),
    url(r'^get_events/$', views.get_events, name='get_events'),
    url(r'^attendance_check_for_admin/(?P<e_id>\d+)$', views.IndexAttendanceCheck.as_view(), name='attendance_check'),
    #url(r'^about/$', views.IndexAbout.as_view(), name='about'),
    url(r'^download/$', views.download, name='download'),
    url(r'^blog/$', views.PostList.as_view(), name='blog'),
    url(r'^archive/$', views.IndexArchive.as_view(), name='archive'),
    path(r'blog/<slug:pk>', views.PostDetail.as_view(), name='post_detail'),
    url(r'^monthly/$', views.IndexMonthlyAllhands.as_view(), name='monthly'),
]
