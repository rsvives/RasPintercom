#!/usr/bin/env python3          
import os
import time
from dotenv import load_dotenv 
import requests                   
import signal                   
import sys
import RPi.GPIO as GPIO


OPEN_BUTTON_GPIO = 16
LED_INTERCOM_GPIO = 26
API_URL = 'http://192.168.0.40:3001/api'

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def save_log():
    # response = requests.post(API_URL+'/calls')
    # print(response.json())
    print("📝 Guardando llamada en el registro")

def check_booking():
    response = requests.get(API_URL+'/guests/today')
    data = response.json()
    print(data)
    
    if len(data)>0:
        open_door()
    else:
        print('❌ No esperamos a nadie')    

def open_door():
    time.sleep(2)
    print('🔓 Abriendo puerta')
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.HIGH )
    time.sleep(1)
    GPIO.output( OPEN_BUTTON_GPIO , GPIO.LOW )

def button_callback(channel):
    if GPIO.input(LED_INTERCOM_GPIO):
        print("🔔 Han llamado!")
        save_log()
        check_booking()
    else:
        print("🔚 Se acabó la llamada!")

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_INTERCOM_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(OPEN_BUTTON_GPIO, GPIO.OUT)

    GPIO.add_event_detect(LED_INTERCOM_GPIO, GPIO.BOTH, 
            callback=button_callback, bouncetime=100)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()