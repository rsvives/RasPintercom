#!/usr/bin/env python3          
# import os
import datetime
import os.path
import json

from google.auth.transport.requests import Request # type: ignore
from google.oauth2.credentials import Credentials # type: ignore
from google.oauth2 import service_account
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
SERVICE_ACCOUNT_FILE='./service-intercom.json'
CALENDAR_ID=config['CALENDAR_ID']
NOW = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

OPEN_BUTTON_GPIO = 16
LED_INTERCOM_GPIO = 6 #6
API_URL = config['API_URL']
logger = logging.getLogger(__name__)
logging.basicConfig(filename='calls.log', 
                    level=logging.INFO,
                    encoding='utf-8',
                    format='[%(levelname)s] %(asctime)s: %(message)s')
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.INFO)

headersAuth = {
    'Authorization': 'Bearer '+ str(config['API_AUTH_TOKEN']),
}

def botListening(msg):

    if str(msg['from']['id']) == str(TG_CHAT_ID):

        if(msg['text']=="/open"):
            open_door()
            
        if(msg['text']=="/test"):
            telegram_message("🤷🏻‍♂️ nothing to test")
            # check_booking()
            # check_guests(timeMin=datetime.utcnow().isoformat() + "Z",timeMax=None,maxResults=3)

        if(msg['text']=="/upcoming_guests"):
            # telegram_message("🤷🏻‍♂️ not yet implemented")
            check_booking()
            
        if(msg['text']=="/logs"):
            data=""
            with open('calls.log') as file:
                lines = file.readlines()
            for l in lines:
                data += l
            
            try:
                telegram_message("✅ Registro completo:\n"+data)
            except :
                telegram_message("😣 Algo no ha salido como debía...")
                print("❌ Error enviando registro")
                

        if(msg['text']=="/calls"): 
   
            response = requests.get(API_URL+'/calls')
            data = response.json()
            print (data)
            registro = ''
            for d in data['calls']:
                registro+= d['date']+"\n"
            print(registro)

            try:
                telegram_message("🔔 Registro de llamadas:\n"+ registro)
            except :
                telegram_message("😣 Algo no ha salido como debía...")
                print("❌ Error enviando registro")


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
    try:
        requests.post(API_URL+'/calls',json=data, headers=headersAuth)
        print("📝 Guardando llamada en el registro")
        telegram_message("📝 Guardando llamada en el registro")
        logger.info("🔔 Llamada efectuada")
    except:
        print("Error guardando datos en API")
        telegram_message("Error guardando datos en API")


def check_booking():
    
    guests = check_guests(timeMin=None,timeMax=datetime.utcnow().isoformat() + "Z",maxResults=None)
    if not guests:
        print('😵‍💫 Error al buscar invitados')  
        telegram_message('😵‍💫 Error al buscar invitados')  
        return
    
    *_,guest = guests
    checkoutDate = datetime.fromisoformat(guest.get('end').get('dateTime'))
    nowDate  = datetime.now(timezone.utc)
    
    if(nowDate < checkoutDate):
        print(f"{guest['location']} - {guest['summary']}:\n{datetime.fromisoformat(guest.get('start').get('dateTime')).strftime('%d/%m/%Y %H:%M')}\n{datetime.fromisoformat(guest.get('end').get('dateTime')).strftime('%d/%m/%Y %H:%M')}\n")
        telegram_message(f"{guest['location']} - {guest['summary']}:\n{datetime.fromisoformat(guest.get('start').get('dateTime')).strftime('%d/%m/%Y %H:%M')}\n{datetime.fromisoformat(guest.get('end').get('dateTime')).strftime('%d/%m/%Y %H:%M')}")
        open_door()
        # print('open door')
    else:
        print('🚫 No esperamos a nadie ahora') 
        telegram_message('🚫 No esperamos a nadie ahora')
    
def check_guests(timeMin, timeMax, maxResults):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
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
        telegram_message(f"HTTP Error: {error.error_details}")

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
        check_booking()
        save_log()
    else:
        print("🔚 Se acabó la llamada!")

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_INTERCOM_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(OPEN_BUTTON_GPIO, GPIO.OUT, initial=0)
    
    GPIO.add_event_detect(LED_INTERCOM_GPIO, GPIO.BOTH, 
            callback=button_callback, bouncetime=100)
    
    print('✨ Inicializando Intercom')
    telegram_message('✨ Inicializando Intercom')

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()