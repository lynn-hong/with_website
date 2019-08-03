import json
import requests
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from website.models import Event, EventApplication, Member

week = ('월', '화', '수', '목', '금', '토', '일')

def get_access_token_each_time(refreshToken) :
    url = "https://kauth.kakao.com/oauth/token"
    payload = "grant_type=refresh_token&client_id=b1dfd5bbf3bbd637449025f203d51e39&refresh_token=" + refreshToken
    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
    }
    reponse = requests.request("POST",url,data=payload, headers=headers)
    access_token = json.loads(reponse.text)
    return access_token

def sendText(registered_user, access_token) :
    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    applications = EventApplication.objects.filter(m=registered_user).filter(e__s_date__gte=datetime.today()).order_by('e__s_date')
    print(applications)
    if len(applications) > 0:
        application_tail_list = list()
        for app in applications:
            a_date = app.e.s_date.strftime('%-m/%d')
            a_day_of_week = week[app.e.s_date.weekday()]
            app_title = app.e.a.title if app.e.a.get_act_type_display() == '정기봉사' \
                else "{}({})".format(app.e.title, app.e.a.title)
            application_tail_list.append("- {}({}): {} {}\n".format(a_date, a_day_of_week,
                                                                    app_title, app.get_status_display()))
        application_tail = ''.join(application_tail_list)
    else:
        application_tail = "신청하신 봉사 내역이 없어요ㅜ.ㅜ 지금 바로 아래 버튼을 눌러 신청해보시면 어떨까요? :)"
    gender = '자매님' if registered_user.gender == 0 else '형제님'
    payloadDict = dict({
            "object_type" : "text",
            "text" : "[위드] 봉사 알리미(heart)\n"
                     "{} {} {}, 오늘 이후의 봉사 및 행사 신청 현황 알려드립니다!\n\n".
                         format(registered_user.name, registered_user.baptismal_name, gender,
                                )+application_tail,
            "link" : {
                "web_url" : "https:withlove.cf#events",
                "mobile_web_url" : "https://withlove.cf#events"
             },
            "button_title" : "봉사자 캘린더",
            })
    payload = 'template_object=' + json.dumps(payloadDict)
    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + access_token,
    }
    response = requests.request("POST", url, data=payload.encode('utf-8'), headers=headers)
    access_token = json.loads(response.text)
    return access_token

def send_remind(request):
    for registered_member in Member.objects.exclude(refresh_token=None).filter(id=1):
    #for registered_member in Member.objects.exclude(refresh_token=None):
        access_token = get_access_token_each_time(registered_member.refresh_token)['access_token']
        _ = sendText(registered_member, access_token)
    return HttpResponseRedirect(reverse_lazy('secret'))

def secret(request):
    return render(request, "kakao/secret.html", {})

def get_user_access_token(clientId, code) :
    # 세션 코드값 code 를 이용해서 ACESS TOKEN과 REFRESH TOKEN을 발급 받음
    url = "https://kauth.kakao.com/oauth/token"
    payload = "grant_type=authorization_code"
    payload += "&client_id=" + clientId
    payload += "&redirect_url=https://withlove.cf/kakao/oauth&code=" + code
    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    access_token = json.loads(response.text)
    return access_token

def get_user_email(accessToken) :
    url = 'https://kapi.kakao.com/v2/user/me'
    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + accessToken,
    }
    data = 'property_keys=["kakao_account.email"]'
    response = requests.request("POST", url, headers=headers, data=data)
    return json.loads(response.text)

def oauth(request):
    code = request.GET.get('code')
    response_token = get_user_access_token("b1dfd5bbf3bbd637449025f203d51e39", code)
    refresh_token = response_token['refresh_token']
    access_token = get_access_token_each_time(refresh_token)['access_token']
    response = get_user_email(access_token)
    kakao_user_id = response['id']
    email = response['kakao_account']['email']
    print("refresh_token: {}".format(refresh_token))
    print("response: {}".format(response))
    context = dict()
    for registered_user in Member.objects.filter(kakao_email=email):
        if registered_user.refresh_token is not None:
            print("Already registered!")
            context['message'] = '이미 봉사일정 카톡 알림을 신청 하셨습니다!'
        else:
            registered_user.kakao_user_id = kakao_user_id
            registered_user.refresh_token = refresh_token
            registered_user.save(update_fields=['kakao_user_id', 'refresh_token'])
            # send the first message
            for registered_user in Member.objects.filter(kakao_email=email):
                access_token = get_access_token_each_time(registered_user.refresh_token)['access_token']
                _ = sendText(registered_user, access_token)
                context['message'] = "봉사일정 카톡 알림신청이 완료되었습니다!"
    return render(request, "website/thankyou.html", context)