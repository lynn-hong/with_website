import json
from datetime import datetime, time, date
import uuid

from django.views.generic import TemplateView
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F, Q
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .models import Event, EventApplication, Member, APPLICATION_STATUS



class Index(TemplateView):
    template_name = 'website/index.html'

    def get_event_applications(self, e_id):
        applications = EventApplication.objects.filter(e__id=e_id).all().\
            order_by('-m__is_staff', 'm__category', 'm__name')
        returned_applications = list()
        for a in applications:
            if a.m.baptismal_name is not None:
                a.m.name = "{} {}".format(a.m.name, a.m.baptismal_name)
            if a.m.get_category_display() == '게스트':
                a.m.name = "(게스트) {}".format(a.m.name)
                if a.m.recommender is not None:
                    a.m.name = a.m.name + " (invited by {} {})".format(a.m.recommender.name, a.m.recommender.baptismal_name)
            returned_applications.append(
                {'name': a.m.name, 'status': a.get_status_display()}
            )
        return returned_applications

    def get_event(self):
        event_arr = []
        all_events = Event.objects.all()
        for e in all_events:
            event_sub_arr = {}
            applications = self.get_event_applications(e_id=e.id)
            event_sub_arr['title'] = "[{}] {}".format(e.a.title, e.title)
            event_sub_arr['desc'] = e.desc.replace("\n", "<br />")
            if e.s_time is not None:
                start_time = time.strftime(e.s_time, "%H:%M:%S")
            else:
                start_time = time.strftime(e.a.s_time, "%H:%M:%S")
            if e.e_time is not None:
                end_time = time.strftime(e.e_time, "%H:%M:%S")
            else:
                end_time = time.strftime(e.a.e_time, "%H:%M:%S")
            if e.location is None:
                e.location = e.a.location
            start_datetime = "{} {}".format(datetime.strftime(e.s_date, "%Y-%m-%d"), start_time)
            if e.e_date is not None:
                end_datetime = "{} {}".format(datetime.strftime(e.e_date, "%Y-%m-%d"), end_time)
            else:
                end_datetime = "{} {}".format(datetime.strftime(e.s_date, "%Y-%m-%d"), end_time)
            event_sub_arr['location'] = e.location
            event_sub_arr['start'] = start_datetime
            event_sub_arr['end'] = end_datetime
            event_sub_arr['applications'] = json.dumps(applications, cls=DjangoJSONEncoder)
            event_arr.append(event_sub_arr)
        special_days_arr = []
        for d in Member.objects.filter(category=0).values('name', 'baptismal_name', 'birthday', 'feast_day', 'gender'):
            gender_desc = "자매님" if d['gender'] == 0 else "형제님"
            if d['birthday'] is not None:
                special_days_arr.append({'title': "[생일] {} {}".format(d['name'], d['baptismal_name']),
                                         'start': str(date.today().year) + '-' + d['birthday'].strftime('%m-%d'),
                                         'desc': "{} {} {}의 생일을 축하합니다!".format(d['name'], d['baptismal_name'], gender_desc),
                                         'color': 'pink'})
            if d['feast_day'] is not None:
                special_days_arr.append({'title': "[축일] {} {}".format(d['name'], d['baptismal_name']),
                                         'start': str(date.today().year) + '-' + d['feast_day'].strftime('%m-%d'),
                                         'desc': "{} {} {}의 축일을 축하합니다!".format(d['name'], d['baptismal_name'], gender_desc),
                                         'color': 'skyblue'})
        return event_arr, special_days_arr

    # 신청, 미정, 불참 등 choice 가져오기
    def get_app_choices(self):
        return_list = list()
        for item in APPLICATION_STATUS:
            return_list.append({'name': item[1], 'value': item[0]})
        return return_list

    # 이미 신청한 사람들 목록을 체크해서 이 사람들은 목록에 뜨지 않도록 함
    def get_already_applied_member(self, app_events):
        app_event_ids = [app_event.id for app_event in app_events]
        app_applications = EventApplication.objects.filter(e__id__in=app_event_ids).all()
        applicants = app_applications.values('m').annotate(count=Count('m'), member=F('m__id')).values(
            'count', 'member')
        full_applied = [a['member'] for a in applicants if a['count'] >= len(app_event_ids)]
        print(full_applied)
        return full_applied

    # 실제 index에 들어가는 context들 만들기
    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        context['events'], context['special_days'] = self.get_event()
        context['app_events'] = Event.objects.all().filter(a__title='새봉 ')\
            .filter(Q(s_date=datetime.now().date(), s_time__gte=datetime.now().time())|Q(s_date__gt=datetime.now().date()))\
            .order_by('s_date')
        already_applied = self.get_already_applied_member(context['app_events'])
        context['members'] = Member.objects.all().filter(category=0).exclude(id__in=already_applied).order_by('name')  # 위드
        context['guests'] = Member.objects.all().filter(category__in=[1,3]).exclude(id__in=already_applied).order_by(
            'name')  # 타단체청년, 게스트
        context['all_members'] = Member.objects.all().order_by('name')
        context['app_choices'] = self.get_app_choices()
        return context

class HaltException(Exception):
    pass

@csrf_protect
def apply(request):
    if request.method == 'POST':
        print(request.POST)
        if request.POST['cat_id'] == 'with':
            member_id = int(request.POST['member_id'])
        elif request.POST['cat_id'] == 'guest':
            member_id = request.POST['guest_id']
            if member_id != 'new':
                member_id = int(member_id)
            else:  # add new_member
                if request.POST['recommender_dropdown'] == 'dont_know':
                    recommender = None
                else:
                    recommender = request.POST['recommender_dropdown']
                Member.objects.create(category=3,  # 게스트
                                      member_status=3,  # 해당없음
                                      email="{}@temp.com".format(uuid.uuid4().hex),
                                      name=request.POST['new_name'].strip(),
                                      baptismal_name=request.POST['new_baptismal_name'].strip(),
                                      cellphone=request.POST['new_contact'].strip(),
                                      gender=int(request.POST['gender_dropdown'][0]),
                                      recommender_id=recommender)
                member_id = Member.objects.filter(cellphone=request.POST['new_contact'].strip()).values('id')
                if len(member_id) > 1:
                    print("Error: duplicate contact number ({})".format(request.POST['new_contact'].strip()))
                member_id = member_id[0]['id']
        applys = [{'event': int(a.split('-')[1]),
                   'value': int(request.POST[a][0])} for a in request.POST.keys() if a.startswith('app_id')]
        for apply in applys:
            EventApplication.objects.create(e_id=apply['event'], m_id=member_id, status=apply['value'])
    return HttpResponseRedirect(reverse_lazy('index'))

def thankyou(request):
    return render(request, 'website/thankyou_application.html')
