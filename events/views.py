from django.shortcuts import render
from django.conf import settings
from slack import WebClient
from decouple import config
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Datasets
from .models import Kernels
from .models import Users
from kaggle import api
from urllib.parse import urlparse
from .tasks import *
from django.utils import timezone
from .others import BotTextGenerator

cache_dict = dict()
bottext = json.dumps(BotTextGenerator())

def startmonitor(channel,msg,user):
    try:
        searchtext = urlparse(msg.split()[1]).path.strip('/').split('/')[-1]
        if 'datamonitor' in msg.lower():
            if user in cache_dict.keys():
                send_direct_response.delay(channel,"<@{}> I guess you haven't responded to a previous confirmation prompt. Could you please do that?".format(user))
                return HttpResponse(status=200)
            cache_dict[user] = msg
            send_direct_response.delay(channel,"<@{}> I support two types of datamonitor. Please type 'full' if you want me to monitor all kernels, comments and updates to the data OR type 'basic' if you want me to monitor only updates to the data".format(user))
            return HttpResponse(status=200)
        elif 'kernelmonitor' in msg.lower():
            obj = api.kernels_list(search = searchtext)[0]
            qtype = 1
        else:
            send_direct_response.delay(channel,"<@{}> I couldn't get you?".format(user))
            return HttpResponse(status=200)

    except IndexError:
        send_direct_response.delay(channel,"<@{}> Are you sure the link is correct?".format(user))
        return HttpResponse(status=200)

    send_direct_response.delay(channel,"<@{}> Thanks. I'm on it!".format(user))
    initial_scrape.delay(qtype,msg,obj,user)
    return HttpResponse(status=200)

def stopmonitor(channel,msg,user):
    try:
        if 'datamonitor' in msg.lower():
            state = 0
        elif 'kernelmonitor' in msg.lower():
            state = 1
        deletion_util.delay(state,msg,user)
    except:
        send_direct_response.delay(channel,"<@{}> Oops... something went wrong can you check the link or probably you weren't subscribed. Type 'list' to know what you're subscribed to!".format(user))
        return HttpResponse(status=200)
    send_direct_response.delay(channel,"<@{}> Done!".format(user))
    listit(channel,user)
    return HttpResponse(status=200)

def data_confirm(channel,msg,user):
    try:
        cache_m = cache_dict[user]
        searchtext = urlparse(cache_m.split()[1]).path.strip('/').split('/')[-1]
        qtype = 0
        obj = api.datasets_list(search = searchtext)[0]

        if 'basic' in msg.lower():
            lvl = 0
        elif 'full' in msg.lower():
            lvl = 1
        else:
            send_direct_response.delay(channel,"<@{}> Please enter a valid response".format(user))
            return HttpResponse(status=200)
    except:
        if user in cache_dict.keys():
            del cache_dict[user]
        send_direct_response.delay(channel,"<@{}> Recheck the link or maybe session expired".format(user))
        return HttpResponse(status=200)
    send_direct_response.delay(channel,"<@{}> Thanks. I'm on it!".format(user))
    initial_scrape.delay(qtype,cache_m,obj,user,lvl)
    del cache_dict[user]
    return HttpResponse(status=200)

def listit(channel,user):
    try:
        obj = Users.objects.get(user_id = user)
        send_list_response.delay(channel, obj)
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=200)


Client = WebClient(config('SLACK_BOT_USER_TOKEN'))
@csrf_exempt
def post(request,*args,**kwargs):
    slack_message = json.loads(request.body)
    #print(slack_message)
    if slack_message.get('token')!=config('SLACK_VERIFICATION_TOKEN'):
        return HttpResponse(status=403)
    #verification challenge
    if slack_message.get('type')=='url_verification':
        return HttpResponse(slack_message.get('challenge'),status=200)
    # greet
    if 'event' in slack_message:
        event_message = slack_message.get('event')

        #ignore bot message
        if 'bot_id' in event_message:
            return HttpResponse(status=200)
        user = event_message.get('user')
        msg = event_message.get('text')
        if (not msg):
            return HttpResponse(status=200)
        channel = event_message.get('channel')
        bot_text_1 = "Hi :wave: I can help you with staying up to date with the Kaggle world. Just type 'datamonitor' space the link of the dataset you want me to monitor OR type 'kernelmonitor' space the link of the kernel you want me to monitor"
        bot_success_text = "<@{}> Thanks. I'm on it!".format(user)
        if 'stop' in msg.lower():
            return stopmonitor(channel,msg,user)
        elif 'monitor' in msg.lower():
            return startmonitor(channel,msg,user)
        elif 'basic' in msg.lower() or 'full' in msg.lower():
            return data_confirm(channel,msg,user)
        elif 'list' in msg.lower():
            return listit(channel,user)

        else:
            send_direct_response.delay(channel,"Hi :wave: follow the instructions below",bottext)

    return HttpResponse(status=200)
