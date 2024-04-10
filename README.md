# RasPintercom | Raspberry Pi Access Control System

This is a Raspberry Pi based Access Control System for 2 Wire Digital Intercoms

## Pre-requisites
- A 2 Wire Digital Intercom
- An API for managing access
- Your own MongoDB Atlas account for the API DB

## How it works
1. You should have an API running with an endpoint with all the dates the intercom should open (like [this one](#))
1. When the intercom recieves a call, the LED will switch off, and the Raspberry will detect somebody is calling 
1. When someone calls, the program saves the date of the call into the database and check if theres any register in the DB for today
    - if so: will activate the relay for opening the door
    - if not: it just saves the date of the call into the database 


## Material
- Raspberry Pi
- 5v DC Relay
- Soldering Iron + solder wire
- Breadboard
- Thin wires

## Instructions
1. Disconnect your intercom and remove the PCB
1. Solder wires into your intercom "Open door button" and into the LED pilot
1. Check that the voltage is 3.3v in both of them
1. Connect the wires
1. Power up the Raspi (with an already installed OS)
1. SSH into the Raspi and clone this repository
1. Open the folder an run `python3 intercom.py`
<!-- 1. Create and configure an .env file with an `ACCESS_TOKEN` -->

## Connections
For a Raspberry Pi 4 B:

- GPIO 16: Relay switch
- GPIO 26: LED observer