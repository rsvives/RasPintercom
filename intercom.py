#!/usr/bin/env python3          
# import os
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#------

import time
import requests                   
import signal                   
import sys
import RPi.GPIO as GPIO
import logging
import telepot
from dotenv import dotenv_values
config = dotenv_values(".env")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
creds = None

OPEN_BUTTON_GPIO = 16
LED_INTERCOM_GPIO = 6
API_URL = config['API_URL']
logger = logging.getLogger(__name__)
logging.basicConfig(filename='calls.log', 
                    level=logging.INFO,
                    encoding='utf-8',
                    format='[%(levelname)s] %(asctime)s: %(message)s')
headersAuth = {
    'Authorization': 'Bearer '+ str(config['API_AUTH_TOKEN']),
}

def botListening(msg):

    if str(msg['from']['id']) == str(TG_CHAT_ID):

        if(msg['text']=="/open"):
            open_door()
            
        if(msg['text']=="/new_guest"):
            telegram_message("🤷🏻‍♂️ not yet implemented")

        if(msg['text']=="/upcoming_guests"):
            # telegram_message("🤷🏻‍♂️ not yet implemented")
            check_booking()
            
        if(msg['text']=="/logs"):
            data=""
            with open('calls.log') as file:
                lines = file.readlines()
            for l in lines:
                data += l
            telegram_message("✅ Registro completo:\n"+data)

        if(msg['text']=="/calls"): 
   
            response = requests.get(API_URL+'/calls')
            data = response.json()
            print (data)
            registro = ''
            for d in data['calls']:
                registro+= d['date']+"\n"
            print(registro)
            telegram_message("🔔 Registro de llamadas:\n"+ registro)


TG_TOKEN=config['TG_TOKEN']
TG_CHAT_ID=config['TG_CHAT_ID']
TG_BOT = telepot.Bot(TG_TOKEN)
TG_BOT.message_loop(botListening)

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def telegram_message(message):
    TG_BOT.sendMessage(TG_CHAT_ID,message)



def save_log():
    data={'user': config['USER_ID']}
    requests.post(API_URL+'/calls',json=data, headers=headersAuth)
    print("📝 Guardando llamada en el registro")
    logger.info("🔔 Llamada efectuada")


def check_booking():

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    try:
        service = build("calendar", "v3", credentials=creds)
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        events_result = (
            service.events()
            .list(
                calendarId="5797a4540d40657212fb1b300dd134c9231d8feb30ae8724760267c39171435c@group.calendar.google.com",
                timeMax=now,
                maxResults=1,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items")

        if not events:
            print('🚫 No esperamos a nadie ahora')  
            return
        
        event, *_ = events
        print(f"{event['description']} - {event['summary']}: {event.get('start').get('dateTime')} -> {event.get('end').get('dateTime')}")
        open_door()

    except HttpError as error:
        print(f"Error: {error}")

def open_door():
    # time.sleep(1)
    print('🔓 Abriendo puerta')
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.HIGH )
    time.sleep(1)
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.LOW )
    logger.info("🔓 Puerta abierta")
    telegram_message("🔓 Puerta abierta")

def button_callback(channel):
    # print(GPIO.input(LED_INTERCOM_GPIO))
    if GPIO.input(LED_INTERCOM_GPIO):
        print("🔔 Han llamado!")
        telegram_message("🔔 Han llamado al portero automático!")
        save_log()
        check_booking()
    else:
        print("🔚 Se acabó la llamada!")

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_INTERCOM_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(OPEN_BUTTON_GPIO, GPIO.OUT, initial=0)
    creds = None



    
    GPIO.add_event_detect(LED_INTERCOM_GPIO, GPIO.BOTH, 
            callback=button_callback, bouncetime=100)

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()