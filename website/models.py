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
MEMBER_CATEGORY = (
    (0, '위드'),
    (1, '타단체-청년'),
    (2, '타단체-어르신'),
    (3, '게스트'),
    (4, '기타'),
)
MEMBER_STATUS = (
    (0, '활동중'),
    (1, '휴단'),
    (2, '탈단'),
    (3, '해당없음')
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
    (2, '새봉 대표봉사자'),
    (3, '새봉 부대표봉사자'),
    (4, '은봉 대표봉사자'),
    (5, '나봉 대표봉사자')
)

YEAR_CHOICES = [(r,r) for r in range(1984, datetime.date.today().year+1)]

class Activity(models.Model):
    act_type = models.IntegerField(_('Activity type'), choices=ACTIVITY_TYPE, default=0)
    day = models.IntegerField(_('Day'), choices=DAYS_OF_WEEK, blank=True, null=True)
    title = models.CharField(_('Title'), unique=True, max_length=45)
    desc = models.TextField(_('Description'), blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True, null=True)
    s_time = models.TimeField(_('Start'), blank=True, null=True)
    e_time = models.TimeField(_('End'), blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ACTIVITY'

    def __str__(self):
        return self.title


class Event(models.Model):
    a = models.ForeignKey(Activity, verbose_name='Activity title', on_delete=models.PROTECT)
    title = models.CharField(_('Event title'), max_length=255, default="")
    desc = models.TextField(_('Description'), blank=True, null=True)
    s_date = models.DateField(_('Start date'), blank=True, null=True)
    e_date = models.DateField(_('End date'), blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True, null=True)
    s_time = models.TimeField(_('Start time'), blank=True, null=True)
    e_time = models.TimeField(_('End time'), blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'EVENT'

    def __str__(self):
        if self.e_date is None:
            return "{} - {} ({})".format(self.a.title, self.title, self.s_date)
        else:
            return "{} - {} ({}~{})".format(self.a.title, self.title, self.s_date, self.e_date)



def user_directory_path(instance, filename):
    pic_path = {0: 'with', 1: 'youth_other', 2: 'elder_other', 3: 'guest', 4: 'etc'}
    return os.path.join('images', 'member', pic_path[instance.category], filename)

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return '{} {}'.format(self.name, self.baptismal_name)


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

    def __str__(self):
        return "[{}] {} - {}".format(self.status, self.e.title, self.m.name)


class Staff(models.Model):
    m = models.ForeignKey(Member, verbose_name='Member', on_delete=models.PROTECT)
    staff_category = models.IntegerField(_('Staff category'), choices=STAFF_CATEGORY, default=None)
    staff_year = models.IntegerField(_('Year'), choices=YEAR_CHOICES, default=datetime.datetime.now().year)

    class Meta:
        managed = True
        db_table = 'STAFF'

    def __str__(self):
        return self.m.name
