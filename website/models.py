# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import os
import datetime
from django import utils
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from phonenumber_field.modelfields import PhoneNumberField

ACTIVITY_TYPE = (
    (0, '정기봉사'),
    (1, '정기회합'),
    (2, '비정기봉사'),
    (3, '본당행사'),
    (4, '외부행사'),
)
APPLICATION_STATUS = (
    (0, '참석'),
    (1, '미정'),
    (2, '불참'),
    (3, '늦참'),
    (4, '일찍가야함'),
)
APPLICATION_STATUS_SIMPLE = (
    (0, '참석'),
    (1, '미정'),
    (2, '불참')
)
MEMBER_CATEGORY = (
    (0, '위드'),
    (1, '타단체-청년'),
    (2, '타단체-어르신'),
    (3, '게스트'),
    (4, '기타'),
)
MEMBER_STATUS = (
    (0, '정단원'),
    (1, '휴단원'),
    (2, '탈단원'),
    (3, '해당없음'),
    (4, '비신자단원'),
    (5, '준단원'),
)
GENDER = (
    (0, '여성'),
    (1, '남성'),
)
DAYS_OF_WEEK = (
    (0, '월'),
    (1, '화'),
    (2, '수'),
    (3, '목'),
    (4, '금'),
    (5, '토'),
    (6, '일'),
)
STAFF_CATEGORY = (
    (0, '단장'),
    (1, '부단장'),
    (2, '새벽배식봉사 대표봉사자'),
    (3, '새벽배식봉사 부대표봉사자'),
    (4, '은혜로운집 봉사 대표봉사자'),
    (5, '나눔의집 봉사 대표봉사자'),
    (6, '꿈나무마을 봉사 대표봉사자'),
    (7, '총무'),
    (8, '성가정복지병원 봉사 대표봉사자')
)

STAFF_STATUS = (
    (0, '재임'),
    (1, '사임'),
)

FQT_CATEGORY = {
    (0, 'W.I.T.H 관련 질문들'),
    (1, '봉사 관련 질문들'),
    (2, '홈페이지 사용 관련 질문들'),
}

MISCELLANEOUS_TYPE = {
    (0, 'FAQ'),
    (1, 'FAQ_description'),
    (2, 'Info_ko'),
    (3, 'Info_en'),
    (4, 'related_institution'),
}

INVENTORY_CATEGORY = {
    (0, '양념'),
    (1, '장'),
    (3, '가루'),
    (4, '기름'),
    (2, '소스'),
    (5, '술'),
    (6, '기타'),
}

STOCK_AMOUNT = {
    (0, '구입 필요'),
    (1, '적당'),
    (2, '많음'),
}

POST_STATUS = (
    (0, 'Draft'),
    (1, 'Publish')
)

POST_CATEGORY = (
    (0, '공지사항'),
    (1, '홍보'),
    (2, '보도자료'),
    (3, '자료')
)

YEAR_CHOICES = [(r,r) for r in range(1984, datetime.date.today().year+2)]

class Activity(models.Model):
    act_type = models.IntegerField(_('Activity type'), choices=ACTIVITY_TYPE, default=0)
    day = models.IntegerField(_('Day'), choices=DAYS_OF_WEEK, blank=True, null=True)
    title = models.CharField(_('Title'), unique=True, max_length=45)
    desc = models.TextField(_('Description'), blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True, null=True)
    s_time = models.TimeField(_('Start'), blank=True, null=True)
    e_time = models.TimeField(_('End'), blank=True, null=True)
    min_people = models.IntegerField(_('최소 인원'), default=0, blank=True, null=True)
    max_people = models.IntegerField(_('최대 인원'), default=10000, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ACTIVITY'

    def __str__(self):
        return self.title


class Event(models.Model):
    a = models.ForeignKey(Activity, verbose_name='Activity title', on_delete=models.PROTECT)
    title = models.CharField(_('Event title'), max_length=255, default="")
    subtitle = models.CharField(_('Event subtitle'), max_length=255, blank=True, null=True)
    desc = models.TextField(_('Description'), blank=True, null=True)
    s_date = models.DateField(_('Start date'), blank=True, null=True)
    e_date = models.DateField(_('End date'), blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True, null=True)
    s_time = models.TimeField(_('Start time'), blank=True, null=True)
    e_time = models.TimeField(_('End time'), blank=True, null=True)
    is_simple = models.BooleanField(_('약식 신청옵션을 사용할 지 여부'), default=False)
    num_of_homeless = models.IntegerField(_('노숙인 숫자(새봉만 사용)'), default=0, blank=True, null=True)
    menu = models.TextField(_('식사 메뉴(새봉만 사용)'), blank=True, null=True, default="")
    attendee_feedback = models.TextField(_('참석자 피드백&코멘트'), blank=True, null=True, default="")
    special_issue = models.TextField(_('특이사항&이슈'), blank=True, null=True, default="")
    is_open = models.BooleanField(_('이벤트 신청을 오픈할 지 여부'), default=True)
    google_cal_event_id = models.CharField(_('Event subtitle'), max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'EVENT'

    def __str__(self):
        if self.e_date is None:
            return "{} - {} ({})".format(self.a.title, self.title, self.s_date)
        else:
            return "{} - {} ({}~{})".format(self.a.title, self.title, self.s_date, self.e_date)


def user_directory_path(instance, filename):
    if type(instance) == Miscellaneous:
        return os.path.join('miscellaneous', filename)
    elif type(instance) == Member:
        pic_path = {0: 'with', 1: 'youth_other', 2: 'elder_other', 3: 'guest', 4: 'etc'}
        return os.path.join('images', 'member', pic_path[instance.category], filename)
    elif type(instance) == Post:
        post_path = {0: 'notification', 1: 'ad', 2: 'press', 3: 'archive'}
        return os.path.join(post_path[instance.category], filename)


class EventDetail(models.Model):
    a_type = models.CharField(_('Title'), unique=True, max_length=45)
    title = models.CharField(_('Event title'), max_length=255, default="")
    desc = models.TextField(_('Description'), blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True, null=True)
    s_date = models.DateField(_('Start date'), blank=True, null=True)
    e_date = models.DateField(_('End date'), blank=True, null=True)
    s_time = models.TimeField(_('Start time'), blank=True, null=True)
    e_time = models.TimeField(_('End time'), blank=True, null=True)
    google_cal_event_id = models.CharField(_('Event subtitle'), max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'EVENT_DETAIL'

    def __str__(self):
        if self.e_date is None:
            return "{} - {} ({})".format(self.a_type, self.title, self.s_date)
        else:
            return "{} - {} ({}~{})".format(self.a_type, self.title, self.s_date, self.e_date)


class Member(AbstractUser):
    email = models.EmailField(_('Email address'), unique=True)
    category = models.IntegerField(choices=MEMBER_CATEGORY, default=0)
    member_status = models.IntegerField(choices=MEMBER_STATUS, default=0)
    name = models.CharField(_('이름'), max_length=45)
    baptismal_name = models.CharField(_('세례명'), max_length=45, blank=True, null=True)
    feast_day = models.DateField(_('축일'), blank=True, null=True)
    birthday = models.DateField(_('생일'), blank=True, null=True)
    baptism_day = models.DateField(_('세례일'), blank=True, null=True)
    confirmation_day = models.DateField(_('견진일'), blank=True, null=True)
    affiliation = models.CharField(_('소속'), max_length=45, blank=True, null=True)
    cellphone = models.CharField(_('휴대폰 번호'), max_length=45, blank=True, null=True)
    address = models.CharField(_('주소'), blank=True, null=True, max_length=255)
    registered_location = models.CharField(_('교적지'), blank=True, null=True, max_length=45)
    gender = models.IntegerField(_('성별'), choices=GENDER, default=0)
    recommender = models.ForeignKey('self', verbose_name='Recommender', on_delete=models.PROTECT, blank=True, null=True)
    picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    kakao_user_id = models.IntegerField(blank=True, null=True)
    kakao_email = models.EmailField(_('카카오톡 이메일 계정'), unique=True, blank=True, null=True)
    is_kakao_registered = models.BooleanField(_('카카오톡 인증 여부'), default=0)
    refresh_token = models.CharField(max_length=225, blank=True, null=True)

    first_name = None
    last_name = None
    username = None
    password = models.CharField(max_length=128, # 서교동위드
                                default='pbkdf2_sha256$120000$cY8mjCwGDJF4$05jAvpHPhzMYStzRDUlkBIk2pv9zWa1yjI2YD8iNoDM=')

    class Meta:
        managed = True
        db_table = 'member'
        unique_together = (('name', 'baptismal_name', 'cellphone'),)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return '{} {}'.format(self.name, self.baptismal_name)


class Miscellaneous(models.Model):
    misc_type = models.IntegerField(_('운영용 항목 타입'), choices=MISCELLANEOUS_TYPE, default=0)
    faq_category = models.IntegerField(_('FAQ 카테고리'), choices=FQT_CATEGORY, default=0, blank=True, null=True)
    title = models.CharField(_('제목'), max_length=255, blank=True, null=True)
    body = models.TextField(_('본문'), blank=True, null=True)
    img_file = models.ImageField(_('이미지 파일'), upload_to=user_directory_path, blank=True, null=True)
    ordering = models.IntegerField(_('노출 순서'), default=0)

    class Meta:
        managed = True
        db_table = 'MISCELLANEOUS'

    def __str__(self):
        return "{}: {}".format(self.misc_type, self.title)


class EventApplication(models.Model):
    e = models.ForeignKey(Event, verbose_name='Event', on_delete=models.PROTECT)
    m = models.ForeignKey(Member, verbose_name='Member', on_delete=models.PROTECT)
    status = models.IntegerField(_('Application status'), choices=APPLICATION_STATUS, default=0)
    morning_call = models.TimeField(_('Morning call'), blank=True, null=True)
    attendance = models.BooleanField(_('실제 참석 여부'), default=True)
    applied_datetime = models.DateTimeField(_('Applied datetime'), auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'EVENT_APPLICATION'
        unique_together = (('e', 'm'),)

    def __str__(self):
        return "[{}] {} - {}".format(self.status, self.e.title, self.m.name)


class History(models.Model):
    event_date = models.DateField(_('이벤트 날짜'), blank=True, null=True)
    event_title = models.CharField(_('이벤트 제목'), max_length=255)
    event_desc = models.CharField(_('이벤트 설명'), max_length=255)
    event_icon = models.CharField(_('이벤트 아이콘'), max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'HISTORY'

    def __str__(self):
        return "{}({})".format(self.event_title, self.event_date)


class Staff(models.Model):
    m = models.ForeignKey(Member, verbose_name='Member', on_delete=models.PROTECT)
    staff_category = models.IntegerField(_('Staff category'), choices=STAFF_CATEGORY, default=None)
    staff_year = models.IntegerField(_('Year'), choices=YEAR_CHOICES, default=datetime.datetime.now().year)
    staff_status = models.IntegerField(_('Staff statue'), choices=STAFF_STATUS, default=0)

    class Meta:
        managed = True
        db_table = 'STAFF'

    def __str__(self):
        return self.m.name


class Post(models.Model):

    id = models.AutoField(primary_key=True)
    title = models.CharField(_('제목'), max_length=255, unique=True)
    author = models.ForeignKey(Member, verbose_name='Member', on_delete=models.PROTECT)
    category = models.IntegerField(_('카테고리'), choices=POST_CATEGORY, default=0)
    content = models.TextField(_('본문'), )
    press_date = models.DateField(_('보도일자'), blank=True, null=True)
    outlink = models.CharField(_('외부 링크'), max_length=255, blank=True, null=True)
    attachment = models.FileField(_('첨부 파일'), upload_to=user_directory_path, blank=True, null=True)
    created_on = models.DateTimeField(_('작성일시'), auto_now_add=True)
    updated_on = models.DateTimeField(_('최종 업데이트 일시'), auto_now=True)
    status = models.IntegerField(_('post 상태'), choices=POST_STATUS, default=0)

    class Meta:
        ordering = ['-press_date', '-created_on']

    def __str__(self):
        return self.title
