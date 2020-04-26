'''Additional functions or templates that we may need for main tasks'''
from abc import ABC, abstractmethod

def SectionTemplate(newtext):
    tempdict = {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Sample text"
                }
			}

    tempdict["text"]["text"] = newtext
    return tempdict

def DividerTemplate():
    tempdict = {
			"type": "divider"
			}
    return tempdict

def ContextTemplate(newtext):
    tempdict = {
			"type": "context",
			"elements": [
                {
				"type": "mrkdwn",
				"text": "Sample text"
                }
			]
            }

    tempdict["elements"][0]["text"] = newtext
    return tempdict

def BotTextGenerator():
    bottext = [
    	{
    		"type": "section",
    		"text": {
    			"type": "mrkdwn",
    			"text": "Hi, :wave: To monitor a Dataset type *datamonitor* space the link of the dataset \n To monitor a Kernel type *kernelmonitor* space the link of the kernel \n Eg: datamonitor https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge"

    		}
    	},
    	{
    		"type": "divider"
    	},
    	{
    		"type": "section",
    		"text": {
    			"type": "mrkdwn",
    			"text": "To stop monitoring anything just prefix the above commands with a *stop* \n Eg: stop datamonitor https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge"

    		}
    	},
    	{
    		"type": "divider"
    	},
    	{
    		"type": "section",
    		"text": {
    			"type": "mrkdwn",
    			"text": "To view the current items you are monitoring, just type *list* \n PS: A GUI is coming very soon to make all this beautiful and intuitive stay tuned!"

    		}
    	}
    ]
    return bottext
