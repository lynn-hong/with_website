import os
import json
import re
from datetime import datetime, time, date
import uuid
import collections
import shutil
import pandas as pd
import xlwt

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView, ListView, DetailView

from .models import Event, EventDetail, EventApplication, History, Member, Miscellaneous, Staff, \
    APPLICATION_STATUS, APPLICATION_STATUS_SIMPLE, FQT_CATEGORY, STAFF_CATEGORY, MEMBER_STATUS, Post


PAGE_TITLE = "{}"

class Index(TemplateView):
    template_name = 'website/index.html'

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
    # TODO: 추후 with&guest 여부 dropdown을 선택하면 그때 interactive하게 요청 보내서 목록 받아오는 방식으로 변경 필요
    # TODO: 지금은 단원 신청 시에도 게스트까지 목록을 받아오도록 되어 있어 시간이 2배로 소요됨
    def get_already_applied_member(self):
        full_applied = list()
        for member in Member.objects.all().order_by('id'):
            activity_category = check_event_able_to_apply(member.id, member.category,
                                                          member_status=member.member_status, baptismal_name=member.baptismal_name)
            event_ids = [event.id for event in fetch_events_by_condition(activity_category)]
            already_applied_events = EventApplication.objects.filter(e__id__in=event_ids).filter(m__id=member.id).all()
            if len(event_ids) == len(already_applied_events):
                full_applied.append(member.id)
        return full_applied


    # 실제 index에 들어가는 context들 만들기
    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        #context['events'], context['special_days'] = self.get_event()
        activity_category = ['새봉', '은봉', '정기회합', '위드X빈첸시오', '위드행사', '청년사목회 행사', '미사 관련 봉사', '외부봉사', '청소봉사']
        context['app_events'] = fetch_events_by_condition(activity_category)
        already_applied = self.get_already_applied_member()
        context['members'] = Member.objects.all().filter(category=0).exclude(member_status=2).exclude(id__in=already_applied).order_by('name')  # 위드(탈단원 제외)
        context['guests'] = Member.objects.all().filter(category__in=[1, 3]) | Member.objects.all().filter(category=0).filter(member_status=2) # 타단체청년, 게스트 or 위드에서 탈단원
        context['guests'] = context['guests'].exclude(id__in=already_applied).order_by('name')
        context['all_members'] = Member.objects.all().order_by('name')
        context['app_choices'] = self.get_app_choices()
        context['app_choices_simple'] = self.get_app_choices(is_simple=True)
        context['upcoming_volunteers'] = EventDetail.objects.filter(a_type__icontains = "봉").\
                                         filter(s_date__gte = datetime.now().replace(hour=0,minute=0,second=0)).all()[:5]
        context['upcoming_events'] = EventDetail.objects.exclude(a_type__contains="봉").\
                                         filter(s_date__gte = datetime.now().replace(hour=0,minute=0,second=0)).all()[:5]
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['page_title'] = PAGE_TITLE.format('HOME')
        return context


def fetch_events_by_condition(activity_category):
    events = Event.objects.all().filter(is_open=True).filter(a__title__in=activity_category) \
        .filter(Q(s_date=datetime.now().date(), s_time__gte=datetime.now().time()) | Q(
        s_date__gt=datetime.now().date())) \
        .order_by('s_date')
    return events

def check_event_able_to_apply(member_id, member_category, member_status=None, baptismal_name=None):
    if member_id == 'new':
        activity_category = ['새봉']  # 처음 오는 게스트는 새봉만 신청 가능
    else:
        if member_status is None and baptismal_name is None:
            member_info = Member.objects.values('member_status', 'baptismal_name').filter(id=member_id)
            if int(member_category) == 1:  # 위드 단원
                is_catholic = False if list(member_info)[0]['member_status'] == 4 else True  # 4 is 비신자단원
            else:
                is_catholic = False if list(member_info)[0]['baptismal_name'] in ['', None] else True  # None is 비신자게스트
        else:
            if int(member_category) == 1:  # 위드 단원
                is_catholic = False if member_status == 4 else True  # 4 is 비신자단원
            else:
                is_catholic = False if baptismal_name in ['', None] else True  # None is 비신자게스트
        if int(member_category) == 1:  # 위드 단원
            if is_catholic:
                activity_category = ['새봉', '은봉', '정기회합', '위드X빈첸시오', '위드행사', '청년사목회 행사', '미사 관련 봉사',
                                     '외부봉사', '청소봉사']
            else:
                activity_category = ['새봉', '정기회합', '위드X빈첸시오', '위드행사', '청년사목회 행사', '청소봉사']
        else:  # 게스트
            if is_catholic:
                activity_category = ['새봉', '은봉', '청소봉사', '외부봉사']
            else:
                activity_category = ['새봉', '청소봉사']
    return activity_category

def filter_events_by_member(member_id, member_category):
    activity_category = check_event_able_to_apply(member_id, member_category)
    events = Event.objects.all().filter(is_open=True).filter(a__title__in=activity_category) \
        .filter(
        Q(s_date=datetime.now().date(), s_time__gte=datetime.now().time()) | Q(s_date__gt=datetime.now().date())) \
        .order_by('s_date')
    if member_id == 'new':
        event_applications = []
    else:
        event_applications = EventApplication.objects.all().filter(m__id=member_id).filter(
            Q(e__s_date=datetime.now().date(), e__s_time__gte=datetime.now().time()) | Q(e__s_date__gt=datetime.now().date())) \
            .order_by('e__s_date')
    applied_event_id = []
    for event_application in event_applications:
        applied_event_id.append(event_application.e.id)
    not_applied_events = []
    event_cnt_list = EventApplication.objects.exclude(e__id__in=applied_event_id).filter(status__in=[0, 3, 4]).values('m__id').\
        annotate(count=Count('e__id')).values('e__id', 'count')
    for event in events:
        each_dict = dict()
        if event.id not in applied_event_id:
            each_dict['id'] = event.id
            each_dict['title'] = event.title
            each_dict['a_title'] = event.a.title
            each_dict['s_date'] = event.s_date
            each_dict['is_simple'] = event.is_simple
            each_dict['desc'] = event.desc
            each_dict['s_time'] = event.s_time if event.s_time is not None else event.a.s_time
            each_dict['e_time'] = event.e_time if event.e_time is not None else event.a.e_time
            register_cnt = len(event_cnt_list.filter(e__id=event.id))
            each_dict['alert'] = None
            if event.a.act_type in [0, 2]:
                if register_cnt > event.a.max_people:
                    each_dict['alert'] = '봉사자가 너무 많아요! 다른 날은 어떠세요?'
                    each_dict['alert_color'] = 'blue'
                elif register_cnt < event.a.min_people:
                    each_dict['alert'] = '봉사자가 부족해요ㅜㅜ 시간 혹시 안되시나요?'
                    each_dict['alert_color'] = 'red'
            not_applied_events.append(each_dict)
    return sorted(not_applied_events, key=lambda i: (i['s_date'], i['s_time']), reverse=True)


# 봉사&행사 신청 시 멤버를 선택하면 그에 따라 맞춤형으로 아직 신청하지 않은 것만 뜨게 됨
def get_events(request):
    member_id = request.GET.get('member_id', None)
    member_category = request.GET.get('member_category', None)
    app_events_by_member = filter_events_by_member(member_id, member_category)
    return HttpResponse(json.dumps(app_events_by_member, sort_keys=True, indent=1, cls=DjangoJSONEncoder),
                        content_type='application/json; charset=utf-8')


@method_decorator(login_required, name='dispatch')
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
            each_ea['m_contact'] = ea.m.cellphone
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
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['page_title'] = PAGE_TITLE.format('출석체크')
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


class IndexCalendar(TemplateView):

    template_name = 'website/calendar.html'

    def get_event_applications(self, e_id):
        # 실참하지 않은 사람들은 띄워주지 않음
        applications = EventApplication.objects.filter(e__id=e_id).exclude(status=2).filter(attendance=True).all().\
            order_by('m__category', 'm__name')
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

    def get_event(self, start, end):
        event_arr = []
        all_events = Event.objects.all().filter(s_date__gte=start).filter(s_date__lte=end)
        for e in all_events:
            event_sub_arr = {}
            applications = self.get_event_applications(e_id=e.id)
            event_sub_arr['title'] = "[{}] {}".format(e.a.title, e.title)
            event_sub_arr['description'] = e.desc.replace("\n", "<br />")
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
            event_sub_arr['id'] = e.id
            event_sub_arr['location'] = e.location
            event_sub_arr['start'] = start_datetime
            event_sub_arr['end'] = end_datetime
            event_sub_arr['applications'] = json.dumps(applications, cls=DjangoJSONEncoder, ensure_ascii=False)
            event_arr.append(event_sub_arr)

        for d in Member.objects.filter(category=0).exclude(member_status=2).values('name', 'baptismal_name', 'birthday', 'feast_day', 'gender'):
            gender_desc = "자매님" if d['gender'] == 0 else "형제님"
            if d['birthday'] is not None:
                event_arr.append({'title': "[생일] {} {}".format(d['name'], d['baptismal_name']),
                                         'start': str(date.today().year) + '-' + d['birthday'].strftime('%m-%d'),
                                         'description': "{} {} {}의 생일을 축하합니다!".format(d['name'], d['baptismal_name'], gender_desc),
                                         'color': 'pink'})
            if d['feast_day'] is not None:
                event_arr   .append({'title': "[축일] {} {}".format(d['name'], d['baptismal_name']),
                                         'start': str(date.today().year) + '-' + d['feast_day'].strftime('%m-%d'),
                                         'description': "{} {} {}의 축일을 축하합니다!".format(d['name'], d['baptismal_name'], gender_desc),
                                         'color': 'skyblue'})
        return event_arr


    def get_context_data(self, **kwargs):
        context = super(IndexCalendar, self).get_context_data(**kwargs)
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'calendar'
        context['page_title'] = PAGE_TITLE.format('이벤트 캘린더')
        return context

# calendar events
def get_calendar_events(request):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    c = IndexCalendar()
    events = c.get_event(start, end)
    return HttpResponse(json.dumps(events, sort_keys=True, indent=1, cls=DjangoJSONEncoder),
                        content_type='application/json; charset=utf-8')


class IndexManager(TemplateView):

    template_name = 'website/managers.html'

    def get_staff_by_year(self):
        return_dict = collections.OrderedDict()
        for s in Staff.objects.all().order_by('-staff_year', 'staff_category', '-staff_status'):
            if s.staff_year not in return_dict:
                return_dict[s.staff_year] = [s]
            else:
                return_dict[s.staff_year].append(s)
        return return_dict

    def get_context_data(self, **kwargs):
        context = super(IndexManager, self).get_context_data(**kwargs)
        context['staff_years'] = self.get_staff_by_year()
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'info'
        context['page_title'] = PAGE_TITLE.format('역대 운영진')
        return context


class IndexManagerContact(TemplateView):

    template_name = 'website/contacts.html'

    def get_context_data(self, **kwargs):
        context = super(IndexManagerContact, self).get_context_data(**kwargs)
        context['staffs'] = Staff.objects.filter(staff_year=date.today().year).exclude(staff_status=1).all().\
            order_by('staff_category', '-staff_status')
        print(context['staffs'][0].m.id)
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['page_title'] = PAGE_TITLE.format('운영진 연락처')
        return context


class IndexArchive(TemplateView):

    template_name = 'website/board/archive.html'

    def get_context_data(self, **kwargs):
        context = super(IndexArchive, self).get_context_data(**kwargs)
        context['posts'] = Post.objects.filter(status=1).filter(category=3).order_by('-press_date', '-created_on')
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'blog'
        context['page_title'] = PAGE_TITLE.format('자료실')
        return context


class IndexInfo(TemplateView):

    template_name = 'website/info.html'

    def get_context_data(self, **kwargs):
        context = super(IndexInfo, self).get_context_data(**kwargs)
        context['past_events'] = History.objects.all().order_by('-event_date')
        context['info_ko'] = Miscellaneous.objects.filter(misc_type=2)
        context['info_en'] = Miscellaneous.objects.filter(misc_type=3)
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'info'
        context['page_title'] = PAGE_TITLE.format('소개 & 연혁')
        return context


class IndexMember(TemplateView):

    template_name = 'website/members.html'

    def get_members(self):
        return_dict = collections.OrderedDict()
        for m in Member.objects.all().filter(category=0).exclude(member_status=2).order_by('member_status', 'name'):
            if m.get_member_status_display() not in return_dict:
                return_dict[m.get_member_status_display()] = [m]
            else:
                return_dict[m.get_member_status_display()].append(m)
        return return_dict

    def get_context_data(self, **kwargs):
        context = super(IndexMember, self).get_context_data(**kwargs)
        context['member_status'] = self.get_members()
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'info'
        context['page_title'] = PAGE_TITLE.format('단원 현황')
        return context


class IndexFaq(TemplateView):

    template_name = 'website/faq.html'

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

    def get_context_data(self, **kwargs):
        context = super(IndexFaq, self).get_context_data(**kwargs)
        context['faqs'] = self.get_faqs()
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'info'
        context['page_title'] = PAGE_TITLE.format('FAQs')
        return context


class PostList(ListView):
    template_name = 'website/board/blog.html'
    # category 3 == 자료: 별도 페이지에 있음(archive)
    queryset = Post.objects.exclude(category=3).filter(status=1).order_by('-press_date', '-created_on')

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data(**kwargs)
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'blog'
        context['page_title'] = PAGE_TITLE.format('소식')
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'website/board/blog_post_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data(**kwargs)
        context['institutions'] = Miscellaneous.objects.filter(misc_type=4).values('title', 'body', 'img_file').order_by('?')
        context['current'] = 'blog'
        context['page_title'] = PAGE_TITLE.format('post detail')
        return context


def fetch_volunteer_history(s_date, e_date):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM PAST_EVENT_ATTENDEE WHERE s_date >= %s AND s_date < %s;", [s_date, e_date])
        rows = cursor.fetchall()
        if len(rows) < 1:
            return None
        else:
            field_names = [i[0] for i in cursor.description]
            df = pd.DataFrame(list(rows))
            df.columns = field_names
            df['status'] = ['참석' if x == 0 else '불참' for x in df['status']]
            df['category'] = ['단원' if x == 0 else '게스트' for x in df['category']]
            return df

date_regex = re.compile(r"(\d{4}-\d{2}-\d{2}) - (\d{4}-\d{2}-\d{2})")
def get_date(date_range):
    d = date_regex.search(date_range)
    s_date = d.group(1)
    e_date = d.group(2)
    return s_date, e_date

@csrf_protect
def download(request):
    # Get data from database
    if request.method == "GET":
        # Stuff here to render the view for a GET request
        context = {'page_title': PAGE_TITLE.format('통계자료 다운로드'),
                   'institutions': Miscellaneous.objects.filter(misc_type=4).\
                        values('title', 'body', 'img_file').order_by('?'),
                   'current': 'download'}
        return render(request, 'website/statistics.html', context)
    elif request.method == "POST":
        request_name = request.POST.get('request_name', False)
        if request_name == 'download_excel':
            date_range = request.POST.get('date_range', False)
            s_date, e_date = get_date(date_range)

            try:
                shutil.rmtree(os.path.join(settings.STATIC_ROOT, 'tmp'), ignore_errors=True)
            except FileNotFoundError:
                pass
            os.mkdir(os.path.join(settings.STATIC_ROOT, 'tmp'))
            file_name = '{}_{}.xlsx'.format(s_date, e_date)
            file_path = os.path.join(settings.STATIC_ROOT, 'tmp', file_name)
            print(file_path)
            df = fetch_volunteer_history(s_date, e_date)
            if df is not None:
                # response = HttpResponse()
                # response['content_type'] = 'application/vnd.ms-excel'
                # response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)
                #
                # # creating workbook
                # wb = xlwt.Workbook(encoding='utf-8')
                #
                # # adding sheet
                # ws = wb.add_sheet("sheet1")
                #
                # # Sheet header, first row
                # font_style = xlwt.XFStyle()
                # row_num = 0
                # # get your data, from database or from a text file...
                # while row_num < df.shape[0]:
                #     col_num = 0
                #     while col_num < df.shape[1]:
                #         ws.write(row_num, col_num, df.values[row_num][col_num], font_style)
                #         col_num += 1
                #     row_num += 1
                # wb.save(response)
                #
                # print(response['Content-Disposition'])
                # return response

                # import io
                # import xlsxwriter
                # with io.BytesIO() as b:
                #     # Use the StringIO object as the filehandle.
                #     writer = pd.ExcelWriter(b, engine='xlsxwriter')
                #     df.to_excel(writer, sheet_name='Sheet1')
                #     writer.save()
                #     return HttpResponse(b.getvalue(), content_type='application/vnd.ms-excel')

                with pd.ExcelWriter(file_path) as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                if os.path.exists(file_path):
                    response = HttpResponse('/'.join(file_path.split('/')[-2:]), content_type="txt")
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_name)
                    return response
                raise Http404

            else:
                msg = "요청하신 날짜 범위에 데이터가 없습니다."
                print(msg)
                response = JsonResponse({"success": False, "error": msg})
                response.status_code = 500
                return response
