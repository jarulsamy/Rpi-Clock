#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# RED 22
# BLUE 27
# GREEN 17

REBOOT_BUTTON = 17
GPIO.setup(REBOOT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    i = 0
    while GPIO.input(REBOOT_BUTTON) == GPIO.HIGH:
        i += 1
        time.sleep(1)
        if i == 5:
            print("Exiting...")
            exit(0)
