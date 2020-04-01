from django.shortcuts import render
from django.conf import settings
from slack import WebClient
from decouple import config
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Datasets
from .models import Kernels
from kaggle import api
from ratelimit import limits, sleep_and_retry
from slack import WebClient
from dateutil import parser
from urllib.parse import urlparse
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from celery import shared_task
import pytz

logger = get_task_logger(__name__)

Client = WebClient(config('SLACK_BOT_USER_TOKEN'))
chan_id = config('CHANNEL_ID')

@sleep_and_retry
@limits(calls=1,period=1)
def api_call_datasets(search_val):
    return api.datasets_list(search = search_val)[0]

@sleep_and_retry
@limits(calls=1,period=1)
def api_call_kernels(search_val):
    return api.kernels_list(search = search_val)[0]

@sleep_and_retry
@limits(calls=1,period=1)
def send_message(msg):
    Client.chat_postMessage(channel = chan_id, text = msg)

@periodic_task(
    run_every=(crontab(minute=0, hour='*/1')),
    name="task_check",
    ignore_result=True
)
def task_check():

    for entry in Datasets.objects.all():
        mess = ""
        #print(entry.dat_name)
        updated_obj = api_call_datasets(urlparse(entry.dat_url).path.strip('/').split('/')[-1])
        if parser.isoparse(updated_obj['lastUpdated'])!=entry.last_updated:
            #print(entry.last_updated)
            #print(updated_obj['lastUpdated'])
            mess += ("The dataset " + "*"+str(entry.dat_name)+"*" + " has been updated recently check it out! \n")
            entry.last_updated = updated_obj['lastUpdated']
        if updated_obj['topicCount']>entry.disc_count:
            mess += (str(updated_obj['topicCount']-entry.disc_count) + " new discussions added to " + "*"+str(entry.dat_name)+"*" + "\n")
            entry.disc_count = updated_obj['topicCount']
        if updated_obj['kernelCount']>entry.kernel_count:
            mess += (str(updated_obj['kernelCount']-entry.kernel_count) + " new kernels added to " + "*"+str(entry.dat_name)+"*" + "\n")
            entry.kernel_count = updated_obj['kernelCount']
        if (mess):
            for use in entry.users.all():
                mess += "<@{}> ".format(str(use.user_id))
            send_message(mess+"\n"+str(entry.dat_url))
            entry.save()
        #print(mess)


    for entry in Kernels.objects.all():
        mess = ""
        updated_obj = api_call_kernels(urlparse(entry.kernel_url).path.strip('/').split('/')[-1])
        if updated_obj.lastRunTime.replace(tzinfo=pytz.UTC)!=entry.last_run:
            #print(updated_obj.lastRunTime)
            #print(entry.last_run)
            mess += ("The kernel " + "*"+str(entry.kernel_name)+"*" + " has been updated recently check it out! \n")
            entry.last_run = updated_obj.lastRunTime
        if (mess):
            for use in entry.users.all():
                mess += "<@{}> ".format(str(use.user_id))
            send_message(mess+"\n"+str(entry.kernel_url))
            entry.save()
    logger.info("DONE!")

@shared_task
def send_direct_response(c, t):
    Client.chat_postMessage(channel = c, text = t)
