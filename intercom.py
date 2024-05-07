#!/usr/bin/env python3          
# import os
from datetime import datetime, timedelta, timezone
import os.path

from google.auth.transport.requests import Request # type: ignore
from google.oauth2.credentials import Credentials # type: ignore
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
CALENDAR_ID="5797a4540d40657212fb1b300dd134c9231d8feb30ae8724760267c39171435c@group.calendar.google.com"
NOW = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time


OPEN_BUTTON_GPIO = 16
LED_INTERCOM_GPIO = 6
API_URL = config['API_URL']
logger = logging.getLogger(__name__)
logging.basicConfig(filename='calls.log', 
                    level=logging.INFO,
                    encoding='utf-8',
                    format='[%(levelname)s] %(asctime)s: %(message)s')
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

headersAuth = {
    'Authorization': 'Bearer '+ str(config['API_AUTH_TOKEN']),
}

def botListening(msg):

    if str(msg['from']['id']) == str(TG_CHAT_ID):

        if(msg['text']=="/open"):
            open_door()
            
        if(msg['text']=="/new_guest"):
            telegram_message("🤷🏻‍♂️ not yet implemented")
            # check_booking()

        if(msg['text']=="/upcoming_guests"):
            # nextMonth = (datetime.now() + timedelta(days=60)).isoformat() + "Z"
            guests = check_guests(timeMin=datetime.utcnow().isoformat() + "Z",timeMax=None,maxResults=3)
            print(guests)
            if not guests:
                print('🚫 No esperamos a nadie ahora')  
                return
            
            message=""
            print("📅 Próximos invitados:")
            for guest in guests:
                data = (f"{guest['location']} - {guest['summary']}:\n{datetime.fromisoformat(guest.get('start').get('dateTime')).strftime('%d/%m/%Y %H:%M')}\n{datetime.fromisoformat(guest.get('end').get('dateTime')).strftime('%d/%m/%Y %H:%M')}")
                print(data+"\n")
                message+=data+"\n\n"

            telegram_message("📅 Próximos invitados:\n\n"+message)    
            
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

            registro = ''
            for d in data['calls']:
                registro+= d['date']+"\n"
            print("🔔 Registro de llamadas:")
            # print(data)
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
    requests.post(API_URL+'/calls',json=data, headers=headersAuth)
    print("📝 Guardando llamada en el registro")
    logger.info("🔔 Llamada efectuada")


def check_booking():
    
    guests = check_guests(timeMin=None,timeMax=datetime.utcnow().isoformat() + "Z",maxResults=None)
    if not guests:
        print('😵‍💫 Error al buscar invitados')  
        telegram_message('😵‍💫 Error al buscar invitados')  
        return
    
    *_,guest = guests
    checkoutDate = datetime.fromisoformat(guest.get('end').get('dateTime'))
    nowDate  = datetime.now(timezone.utc)
    
    print(f"{guest['description']} - {guest['summary']}: {guest.get('start').get('dateTime')} -> {guest.get('end').get('dateTime')}")
    telegram_message(f"{guest['description']} - {guest['summary']}: {guest.get('start').get('dateTime')} -> {guest.get('end').get('dateTime')}")
    
    if(nowDate < checkoutDate):
        open_door()
        # print('open door')
    else:
        print('🚫 No esperamos a nadie ahora') 
        telegram_message('🚫 No esperamos a nadie ahora')
    
def check_guests(timeMin, timeMax, maxResults):
    creds = None
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
        service = build("calendar", "v3", credentials=creds,cache_discovery=False)
        # Call the Calendar API
        
        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=timeMin,
                timeMax=timeMax,
                maxResults=maxResults,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items")

        return events

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
    
    GPIO.add_event_detect(LED_INTERCOM_GPIO, GPIO.BOTH, 
            callback=button_callback, bouncetime=100)

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()