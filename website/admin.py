from django.forms import TextInput, Textarea, widgets, ModelChoiceField
from django.db import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import Activity, Event, EventApplication, History, Member, Miscellaneous, Staff, Post


textinput_width = '100'

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'act_type', 'day', 'title', 'desc', 'location', 's_time', 'e_time', 'min_people', 'max_people']
    list_display_links = ['title']
    list_filter = ['act_type']
    search_fields = ['title', 'desc']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': textinput_width})},
    }


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('a', 'title', 'subtitle', 'desc', 's_date', 'e_date', 'location', 's_time', 'e_time', 'is_simple', 'is_open')}),
        (_('Additional info'), {'fields': ('num_of_homeless', 'menu', 'attendee_feedback', 'special_issue')}),
    )
    list_display = ['id', 'a', 'title', 'subtitle', 'desc', 's_date', 'e_date', 's_time', 'e_time', 'is_simple', 'is_open']
    list_display_links = ['title']
    list_filter = ['a', 's_date', 'is_open']
    search_fields = ['a', 'title', 'subtitle', 'desc']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': textinput_width})},
    }
    ordering = ('-s_date',)


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['event_date', 'event_icon', 'event_title', 'event_desc']
    list_display_links = ['event_title']
    list_filter = ['event_date']
    search_fields = ['event_date', 'event_title', 'event_desc']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': textinput_width})},
    }
    ordering = ('-event_date',)


@admin.register(Member)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    exclude = ('first_name', 'last_name', 'username')
    fieldsets = (
        (None, {'fields': ('category', 'member_status', 'name', 'baptismal_name', 'affiliation', 'registered_location',
                           'recommender', 'email', 'kakao_email', 'password')}),
        (_('Personal info'), {'fields': ('gender', 'birthday', 'feast_day', 'baptism_day', 'confirmation_day',
                                         'cellphone', 'address', 'picture')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'name', 'baptismal_name', 'member_status', 'is_kakao_registered','gender', 'category', 'is_staff', 'affiliation', 'date_joined')
    search_fields = ('email', 'kakao_email', 'name', 'baptismal_name', 'affiliation')
    list_filter = ['category', 'is_staff', 'member_status']
    ordering = ('name',)

    def full_name(obj):
        return '{} {}'.format(obj.name, obj.baptismal_name)

    def is_registered(obj):
        if obj.refresh_token is None:
            return True
        else:
            return False

@admin.register(EventApplication)
class EventApplicationAdmin(admin.ModelAdmin):
    list_display = ['e', 'm', 'status', 'morning_call', 'attendance', 'applied_datetime']
    list_display_links = ['e']
    list_filter = ['e__title', 'm__name', 'attendance']
    search_fields = ['e__title', 'm__name', 'e__id']


@admin.register(Miscellaneous)
class MiscellaneousAdmin(admin.ModelAdmin):
    list_display = ['misc_type', 'faq_category', 'ordering', 'title', 'body']
    list_filter = ['misc_type', 'faq_category']
    search_fields = ['title', 'body']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': textinput_width})},
    }


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['m', 'staff_category', 'staff_year']
    list_display_links = ['m']
    list_filter = ['m', 'staff_category', 'staff_year']
    search_fields = ['m', 'staff_category']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'press_date', 'content', 'created_on', 'updated_on', 'status']
    list_display_links = ['title']
    list_filter = ['status', 'category']
    search_fields = ['title', 'author', 'category', 'content', 'created_on', 'updated_on']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': textinput_width})},
    }
    ordering = ('press_date', '-created_on',)
