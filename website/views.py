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

from .models import Event, EventApplication, Member, Miscellaneous, APPLICATION_STATUS, APPLICATION_STATUS_SIMPLE, FQT_CATEGORY


class Index(TemplateView):
    template_name = 'website/index.html'

    def get_event_applications(self, e_id):
        # 실참하지 않은 사람들은 띄워주지 않음
        applications = EventApplication.objects.filter(e__id=e_id).filter(attendance=True).all().\
            order_by('-m__is_staff', 'm__category', 'm__name')
        returned_applications = list()
        for a in applications:
            if a.m.baptismal_name is not None:
                a.m.name = "{} {}".format(a.m.name, a.m.baptismal_name)
            if a.m.get_category_display() != '위드':
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
        for d in Member.objects.filter(category=0).exclude(member_status=2).values('name', 'baptismal_name', 'birthday', 'feast_day', 'gender'):
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
    def get_app_choices(self, is_simple=False):
        return_list = list()
        if is_simple:
            for item in APPLICATION_STATUS_SIMPLE:
                return_list.append({'name': item[1], 'value': item[0]})
        else:
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
        return full_applied

    def get_faqs(self):
        FQT_CATEGORY2 = {x[1]: x[0] for x in FQT_CATEGORY}
        faq_list = [{'title': x[1], 'meaning': "", 'faqs': []}
                    for x in FQT_CATEGORY]
        for faq in faq_list:
            for m in Miscellaneous.objects.filter(misc_type=0)\
                    .filter(faq_category=FQT_CATEGORY2[faq['title']]).values('title', 'body')\
                    .order_by('ordering'):
                faq['faqs'].append({'title': m['title'], 'body': m['body']})
            faq['meaning'] = Miscellaneous.objects.filter(misc_type=1)\
                .filter(faq_category=FQT_CATEGORY2[faq['title']]).values('body')[0]['body']
        return faq_list

    # 실제 index에 들어가는 context들 만들기
    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        context['events'], context['special_days'] = self.get_event()
        context['app_events'] = Event.objects.all().filter(a__title__in=['새봉', '은봉', '정기회합', '위드X빈첸시오',
                                                                         '위드행사', '청년사목회 행사', '미사 관련 봉사'])\
            .filter(Q(s_date=datetime.now().date(), s_time__gte=datetime.now().time())|Q(s_date__gt=datetime.now().date()))\
            .order_by('s_date')
        already_applied = self.get_already_applied_member(context['app_events'])
        context['members'] = Member.objects.all().filter(category=0).exclude(member_status=2).exclude(id__in=already_applied).order_by('name')  # 위드(탈단원 제외)
        context['guests'] = Member.objects.all().filter(category__in=[1, 3]) | Member.objects.all().filter(category=0).filter(member_status=2) # 타단체청년, 게스트 or 위드에서 탈단원
        context['guests'] = context['guests'].exclude(id__in=already_applied).order_by(
            'name')  
        context['all_members'] = Member.objects.all().order_by('name')
        context['app_choices'] = self.get_app_choices()
        context['app_choices_simple'] = self.get_app_choices(is_simple=True)
        context['faqs'] = self.get_faqs()
        return context


class IndexAttendanceCheck(TemplateView):

    template_name = 'website/attendance_check.html'

    def create_application_data(self, e_id):
        # 불참 제외하고 가져옴
        coming_list = list()
        decided_list = list()
        not_decided_list = list()  # 미정인 사람들
        for ea in EventApplication.objects.all().filter(e__id=e_id).exclude(status=2). \
            order_by('status', 'm__category', 'm__name'):
            each_ea = dict()
            each_ea['status'] = ea.status
            each_ea['m_id'] = ea.m.id
            each_ea['m_category'] = ea.m.category
            each_ea['m_name'] = ea.m.name
            each_ea['m_baptismal_name'] = ea.m.baptismal_name if ea.m.baptismal_name is not None else ''
            each_ea['attended'] = '' if ea.status == 1 else 'checked'
            each_ea['is_guest'] = ' (게스트)' if ea.m.category != 0 else ''
            if ea.status == 1:
                not_decided_list.append(each_ea)
            else:
                decided_list.append(each_ea)
            coming_list.append(ea.m.id)
        return decided_list + not_decided_list, coming_list

    def get_context_data(self, **kwargs):
        e_id = self.kwargs['e_id']
        context = super(IndexAttendanceCheck, self).get_context_data(**kwargs)
        context['event_applications'], coming_list = self.create_application_data(e_id)
        context['event'] = Event.objects.all().filter(id=e_id)
        context['members'] = Member.objects.all().filter(category=0).exclude(member_status=2).exclude(id__in=coming_list).order_by('name')  # 위드(탈단원 제외)
        context['guests'] = Member.objects.all().filter(category__in=[1, 3]) | Member.objects.all().\
            filter(category=0).filter(member_status=2)  # 타단체청년, 게스트 or 위드에서 탈단원
        context['guests'] = context['guests'].exclude(id__in=coming_list).order_by('name')
        context['all_members'] = Member.objects.all().order_by('name')

        if len(context['event']) > 0:
            context['event'] = context['event'][0]
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


@csrf_protect
def add_attendee(request):
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
        event_info = Event.objects.filter(id=int(request.POST['e_id']))[0]
        member_info = Member.objects.filter(id=int(member_id))[0]
        event_application, created = EventApplication.objects.update_or_create(e=event_info, m=member_info,
                                                                defaults={"status": 0, "attendance": True})
        print("is_created: {}".format(created))
    return HttpResponseRedirect(reverse_lazy('index'))


@csrf_protect
def submit_attendance(request):
    if request.method == 'POST':
        print(request.POST)
        event_info = Event.objects.filter(id=int(request.POST['e_id']))[0]
        pass_key = ['e_id', 'num_of_homeless', 'menu', 'attendee_feedback', 'special_issue', 'csrfmiddlewaretoken']
        for m_id in [k for k in request.POST.keys() if k not in pass_key]:
            member_info = Member.objects.filter(id=int(m_id))[0]
            # 봉사 시작 당일 이후에는 펑크
            if datetime.today().date() >= [x['s_date'] for x in Event.objects.all().filter(id=request.POST['e_id']).values('s_date')][0]:
                status = int(request.POST[m_id][0])
                attendance = False if status == 1 else True
                event_application, created = EventApplication.objects.update_or_create(e=event_info, m=member_info,
                                                                                       defaults={"status":status ,
                                                                                                 "attendance": attendance})
            # 그 전에는 취소
            else:
                event_application, created = EventApplication.objects.update_or_create(e=event_info, m=member_info,
                                                                                       defaults={"status": str(request.POST[m_id][0]),
                                                                                                 "attendance": True})
        try:
            num_of_homeless = 0 if request.POST['num_of_homeless'].strip() == '' else int(request.POST['num_of_homeless'].strip())
            event, created = Event.objects.update_or_create(id=request.POST['e_id'],
                                                            defaults={"num_of_homeless": num_of_homeless,
                                                                      "menu": request.POST['menu'],
                                                                      "attendee_feedback": request.POST['attendee_feedback'],
                                                                      "special_issue": request.POST['special_issue']})
        except KeyError:
            event, created = Event.objects.update_or_create(id=request.POST['e_id'],
                                                            defaults={"attendee_feedback": request.POST['attendee_feedback'],
                                                                      "special_issue": request.POST['special_issue']})
    return HttpResponseRedirect(reverse_lazy('index'))

def thankyou(request):
    return render(request, 'website/thankyou_application.html')


