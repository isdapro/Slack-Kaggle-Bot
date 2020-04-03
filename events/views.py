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
from .tasks import send_direct_response
from .tasks import initial_scrape
from django.utils import timezone
# Create your views here.

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
        if 'datamonitor' in msg.lower():
            try:
                searchtext = urlparse(msg.split()[1]).path.strip('/').split('/')[-1]
                dataobj = api.datasets_list(search = searchtext)[0]
            except IndexError:
                Client.chat_postMessage(channel = channel,
                                text = "<@{}> Are you sure the link is correct?".format(user))
                return HttpResponse(status=200)

            send_direct_response.delay(channel,bot_success_text)
            initial_scrape.delay(0,msg,dataobj,user)


            return HttpResponse(status=200)
        elif 'kernelmonitor' in msg.lower():
            try:
                searchtext = urlparse(msg.split()[1]).path.strip('/').split('/')[-1]
                krnlobj = api.kernels_list(search = searchtext)[0]
            except IndexError:
                Client.chat_postMessage(channel = channel,
                                text = "<@{}> Are you sure the link is correct?".format(user))
                return HttpResponse(status=200)

            send_direct_response.delay(channel,bot_success_text)
            initial_scrape.delay(1,msg,krnlobj,user)

            return HttpResponse(status=200)

        else:
            send_direct_response.delay(channel,bot_text_1)

    return HttpResponse(status=200)
