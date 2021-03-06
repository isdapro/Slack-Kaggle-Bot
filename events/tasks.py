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
from .models import BasicDatasets
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.utils import timezone
import dateutil.parser as dparser
from .others import SectionTemplate
from .others import ContextTemplate
from .others import DividerTemplate

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')


logger = get_task_logger(__name__)

Client = WebClient(config('SLACK_BOT_USER_TOKEN'))
chan_id = config('CHANNEL_ID')

@sleep_and_retry
@limits(calls=1,period=5)
def simple_scrapper(classname,urlname):
    driver = webdriver.Chrome(executable_path=config('CHROMEDRIVER_PATH'), chrome_options = chrome_options)
    driver.implicitly_wait(30)
    driver.set_page_load_timeout(30)
    find_class = driver.find_element_by_class_name
    find_xpath = driver.find_element_by_xpath

    try:
        driver.get(urlname)
        rval = int(find_class(classname).text.lstrip('(').rstrip(')'))
        driver.quit()
        return rval
    except Exception as e:
        print(e)
        driver.quit()
        return -1


@sleep_and_retry
@limits(calls=1,period=5)
def span_scrapper(nodeaddress,urlname):
    driver = webdriver.Chrome(executable_path=config('CHROMEDRIVER_PATH'), chrome_options = chrome_options)
    driver.implicitly_wait(30)
    driver.set_page_load_timeout(30)
    find_class = driver.find_element_by_class_name
    find_xpath = driver.find_element_by_xpath

    try:
        print(urlname)
        driver.get(urlname)
        rval = dparser.parse(find_xpath(nodeaddress).get_attribute("title").replace('GMT',''),fuzzy=True)
        driver.quit()
        return rval
    except Exception as e:
        print (e)
        driver.quit()
        return -1

@sleep_and_retry
@limits(calls=1,period=1)
def api_call_datasets(search_val,url):
    objt = api.datasets_list(search = search_val)
    for item in objt:
        if item['url']==url:
            return item

@sleep_and_retry
@limits(calls=1,period=1)
def api_call_kernels(search_val,url):
    objt = api.kernels_list(search = search_val)
    for item in objt:
        if item['url']==url:
            return item

@sleep_and_retry
@limits(calls=1,period=1)
def send_message(msg):
    Client.chat_postMessage(channel = chan_id, text = msg)

@periodic_task(
    run_every=(crontab(minute='0', hour='*/1')),
    name="task_check",
    ignore_result=True
)
def task_check():
    for entry in BasicDatasets.objects.all():
        mess = ""
        #print(entry.dat_name)
        try:
            updated_obj = api_call_datasets(urlparse(entry.dat_url).path.strip('/').split('/')[-1], entry.dat_url)
        except:
            continue
        if parser.isoparse(updated_obj['lastUpdated'])!=entry.last_updated:
            #print(entry.last_updated)
            #print(updated_obj['lastUpdated'])
            mess += ("The dataset " + "*"+str(entry.dat_name)+"*" + " has been updated recently check it out! \n")
            entry.last_updated = updated_obj['lastUpdated']
        if (mess):
            for use in entry.users.all():
                mess += "<@{}> ".format(str(use.user_id))
            send_message(mess+"\n"+str(entry.dat_url))
            entry.save()

    for entry in Datasets.objects.all():
        mess = ""
        #print(entry.dat_name)
        try:
            updated_obj = api_call_datasets(urlparse(entry.dat_url).path.strip('/').split('/')[-1], entry.dat_url)
        except:
            continue
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
        recent_disc_scrape = span_scrapper("//div[@class='topic-list-item__last-comment-time'][1]/span",entry.dat_url+"/discussion?sortBy=recent")
        if recent_disc_scrape!=-1 and recent_disc_scrape!=entry.most_recent_disc:
            mess += ("A new comment has been added to a discussion in the dataset " + "*"+str(entry.dat_name)+"*" + " recently. Check it out! \n")
            entry.most_recent_disc=recent_disc_scrape

        if (mess):
            for use in entry.users.all():
                mess += "<@{}> ".format(str(use.user_id))
            send_message(mess+"\n"+str(entry.dat_url))
            entry.save()
        #print(mess)


    for entry in Kernels.objects.all():
        mess = ""
        try:
            updated_obj = api_call_kernels(urlparse(entry.kernel_url).path.strip('/').split('/')[-1], entry.kernel_url)
        except:
            continue
        if updated_obj.lastRunTime.replace(tzinfo=pytz.UTC)!=entry.last_run:
            #print(updated_obj.lastRunTime)
            #print(entry.last_run)
            mess += ("The kernel " + "*"+str(entry.kernel_name)+"*" + " has been updated recently check it out! \n")
            entry.last_run = updated_obj.lastRunTime
        scrape_val = simple_scrapper("comment-list__title-count",entry.kernel_url)
        if scrape_val!=-1 and scrape_val!=entry.comment_count:
            mess += ("The kernel " + "*"+str(entry.kernel_name)+"*" + " has "+str(scrape_val-entry.comment_count)+" new comments recently check it out! \n")
            entry.comment_count = scrape_val
        if (mess):
            for use in entry.users.all():
                mess += "<@{}> ".format(str(use.user_id))
            send_message(mess+"\n"+str(entry.kernel_url))
            entry.save()
    logger.info("DONE!")

@shared_task
def send_direct_response(c, t, b=''):
    if b:
        Client.chat_postMessage(channel = c, text = t, blocks = b)
    else:
        Client.chat_postMessage(channel = c, text = t)

@shared_task
def send_list_response(c, userobject):
    b = list()
    b.append(SectionTemplate("*You are subscribed to the following*"))
    b.append(DividerTemplate())
    b.append(SectionTemplate("*Datasets (Basic Monitoring)*"))
    if len(userobject.basicdatasets_set.all())==0:
        b.append(SectionTemplate("No items"))
    for item in userobject.basicdatasets_set.all():
        name = item.dat_name
        url = item.dat_url
        b.append(SectionTemplate(name))
        b.append(ContextTemplate(url))

    b.append(DividerTemplate())
    b.append(SectionTemplate("*Datasets (Full Monitoring)*"))
    if len(userobject.datasets_set.all())==0:
        b.append(SectionTemplate("No items"))
    for item in userobject.datasets_set.all():
        name = item.dat_name
        url = item.dat_url
        b.append(SectionTemplate(name))
        b.append(ContextTemplate(url))


    b.append(DividerTemplate())
    b.append(SectionTemplate("*Kernels*"))
    if len(userobject.kernels_set.all())==0:
        b.append(SectionTemplate("No items"))
    for item in userobject.kernels_set.all():
        name = item.kernel_name
        url = item.kernel_url
        b.append(SectionTemplate(name))
        b.append(ContextTemplate(url))

    Client.chat_postMessage(channel = c, text = "You are subscribed to the following:", blocks = json.dumps(b))


@shared_task
def initial_scrape(state,msg,created_obj,user,lvl=0):
    if state==0:
        check_url = msg.split()[1].lstrip('<').rstrip('>')
        if lvl==0:
            new_user, created_user = Users.objects.get_or_create(user_id = user)
            if new_user.datasets_set.all().filter(dat_url = check_url).exists():
                datobj = new_user.datasets_set.all().get(dat_url = check_url)
                datobj.users.remove(new_user)

            new_dataset,created = BasicDatasets.objects.get_or_create(dat_url = check_url,
            defaults = {'dat_name':created_obj['title'],'last_updated':created_obj['lastUpdated']})


            new_dataset.users.add(new_user)
            new_dataset.save()
        else:
            new_user, created_user = Users.objects.get_or_create(user_id = user)
            if new_user.basicdatasets_set.all().filter(dat_url = check_url).exists():
                datobj = new_user.basicdatasets_set.all().get(dat_url = check_url)
                datobj.users.remove(new_user)
            recent_disc_scrape = span_scrapper("//div[@class='topic-list-item__last-comment-time'][1]/span",check_url+"/discussion?sortBy=recent")

            if (recent_disc_scrape==-1):
                recent_disc_scrape = timezone.now()

            new_dataset,created = Datasets.objects.get_or_create(dat_url = check_url,
            defaults = {'dat_name':created_obj['title'],'last_updated':created_obj['lastUpdated'],'disc_count':created_obj['topicCount'],
            'kernel_count':created_obj['kernelCount'], 'most_recent_disc':recent_disc_scrape})


            new_dataset.users.add(new_user)
            new_dataset.save()

    else:
        check_url = msg.split()[1].lstrip('<').rstrip('>')
        scrape_val = simple_scrapper("comment-list__title-count",check_url)
        new_krnl,created = Kernels.objects.get_or_create(kernel_url = check_url,
        defaults = {'kernel_name': created_obj.title,'last_run': created_obj.lastRunTime, 'comment_count':scrape_val})

        new_user, created_user = Users.objects.get_or_create(user_id = user)
        new_krnl.users.add(new_user)
        new_krnl.save()

@shared_task
def deletion_util(state,msg,user):
    deluobj = Users.objects.get(user_id = user)
    check_url = msg.split()[2].lstrip('<').rstrip('>')
    if state==0:
        if not deluobj.basicdatasets_set.all().filter(dat_url = check_url).exists():
            datobj = deluobj.datasets_set.all().get(dat_url = check_url)
            datobj.users.remove(deluobj)
            if not datobj.users.exists():
                Datasets.objects.get(dat_url = check_url).delete()
        else:
            datobj = deluobj.basicdatasets_set.all().get(dat_url = check_url)
            datobj.users.remove(deluobj)
            if not datobj.users.exists():
                BasicDatasets.objects.get(dat_url = check_url).delete()

    else:
        kernobj = Kernels.objects.get(kernel_url = check_url)
        kernobj.users.remove(deluobj)
        if not kernobj.users.exists():
            Kernels.objects.get(kernel_url = check_url).delete()
