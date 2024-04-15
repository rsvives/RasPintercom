#!/usr/bin/env python3          
import os
import time
from dotenv import load_dotenv 
import requests                   
import signal                   
import sys
import RPi.GPIO as GPIO
import logging
import telepot
from dotenv import dotenv_values
config = dotenv_values(".env")


OPEN_BUTTON_GPIO = 16
LED_INTERCOM_GPIO = 26
API_URL = config['API_URL']
logger = logging.getLogger(__name__)
logging.basicConfig(filename='calls.log', 
                    level=logging.INFO,
                    encoding='utf-8',
                    format='[%(levelname)s] %(asctime)s: %(message)s')

def botListening(msg):

    if str(msg['from']['id']) == str(TG_CHAT_ID):

        if(msg['text']=="/open"):
            open_door()
            
        if(msg['text']=="/guests"):
            telegram_message("🤷🏻‍♂️ not yet implemented")
            
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
    requests.post(API_URL+'/calls',json=data)
    print("📝 Guardando llamada en el registro")
    logger.info("🔔 Llamada efectuada")

def check_booking():
    headersAuth = {
    'Authorization': 'Bearer '+ str(config['API_AUTH_TOKEN']),
}
    response = requests.get(API_URL+'/guests/today',headers=headersAuth)
    data = response.json()
    print(data)
    
    if len(data['guests'])>0:
        open_door()
    else:
        print('🚫 No esperamos a nadie')    

def open_door():
    time.sleep(2)
    print('🔓 Abriendo puerta')
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.HIGH )
    time.sleep(1)
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.LOW )
    logger.info("🔓 Puerta abierta")
    telegram_message("🔓 Puerta abierta")

def button_callback(channel):
    if GPIO.input(LED_INTERCOM_GPIO):
        print("🔔 Han llamado!")
        telegram_message("🔔 Han llamado al portero automático!")
        save_log()
        check_booking()
    else:
        print("🔚 Se acabó la llamada!")

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_INTERCOM_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(OPEN_BUTTON_GPIO, GPIO.OUT,initial=0)
    
    GPIO.add_event_detect(LED_INTERCOM_GPIO, GPIO.BOTH, 
            callback=button_callback, bouncetime=100)
    
    # telegram_message("test")

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()