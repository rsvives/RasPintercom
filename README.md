# RasPintercom | Raspberry Pi Access Control System

This is a Raspberry Pi based Access Control System for 2 Wire Digital Intercoms

## Pre-requisites
- A 2 Wire Digital Intercom
- An API withfor managing access:
- Your own MongoDB Atlas account for the API DB
- 

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
1. Create and configure an .env file with an `ACCESS_TOKEN`
1. Open the folder an run `python3 intercom.py`

## Connections

- GPIO 16: Relay switch
- GPIO 26: LED observer