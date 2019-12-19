#!/usr/bin/python3

# 16x2 LCD Alarm

import adafruit_character_lcd.character_lcd as characterlcd
import RPi.GPIO as GPIO
import subprocess
import digitalio
import board
import json

from datetime import datetime, timedelta, date
from distutils.util import strtobool
from time import sleep

from alarm import Alarm

# BCM PINS
# RS - 18
# EN - 23
# D4 - 24
# D5 - 25
# D6 - 8
# D7 - 7

# LCD Pin Constants - BCM Numbering
lcd_rs = digitalio.DigitalInOut(board.D18)
lcd_en = digitalio.DigitalInOut(board.D23)
lcd_d4 = digitalio.DigitalInOut(board.D24)
lcd_d5 = digitalio.DigitalInOut(board.D25)
lcd_d6 = digitalio.DigitalInOut(board.D8)
lcd_d7 = digitalio.DigitalInOut(board.D7)
BACKLIGHT = 5

# LCD Size
LCD_COLUMNS = 16
LCD_ROWS = 2


# Button Pins - BCM Numbering
RED_BUTTON = 22
BLUE_BUTTON = 27
GREEN_BUTTON = 17

BACKLIGHT_STATUS = True
SETTINGS = "settings.json"


def load_config(filename):
    with open(filename, "r") as f:
        config = json.loads(f.read())

    ALARM_TIME = datetime.strptime(
        config["ALARM"]["TIME"], "%H:%M:%S")
    TONE = config["ALARM"]["TONE"]
    DURATION = int(config["ALARM"]["DURATION"])
    WEEKDAYS_ONLY = strtobool(config["ALARM"]["WEEKDAYS_ONLY"])
    ENABLED = strtobool(config["ALARM"]["ENABLED"])

    return ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY, ENABLED


def get_formatted_times(ALARM_TIME, weekdays_only=False, enabled=True):
    tomorrow_format = "%Y-%m-%d %H:%M"
    today_format = "%b %d  %H:%M:%S"

    next_alarm = date.today() + timedelta(days=1)
    if weekdays_only and next_alarm.weekday() > 4:
        next_alarm += timedelta(days=(6 - next_alarm.weekday()))

    alarm_time = datetime.strptime(
        f"{next_alarm} {ALARM_TIME}", tomorrow_format) + timedelta(seconds=1)
    diff = alarm_time - datetime.now()

    hours, remainder = divmod(diff.seconds, 3600)
    if diff.days > 1:
        lcd_line_2 = f"{datetime.now().strftime('%a')}     {str(diff.days).zfill(2)}d {str(hours).zfill(2)}h"
    else:
        minutes, seconds = divmod(remainder, 60)
        hours = str(hours).zfill(2)
        minutes = str(minutes).zfill(2)
        seconds = str(seconds).zfill(2)
        lcd_line_2 = f"{datetime.now().strftime('%a')}     {hours}:{minutes}:{seconds}"

    lcd_line_1 = datetime.now().strftime(today_format) + "\n"
    if not enabled:
        lcd_line_2 = datetime.now().strftime('%a')

    return lcd_line_1 + lcd_line_2


def play_alarm(lcd, tone, duration):

    i = 0
    lcd.clear()

    p = subprocess.Popen(["mpg321", tone], stdout=None, stderr=None)

    while i < duration and p.poll() is None:
        # Stop alarm on button press
        if GPIO.input(BLUE_BUTTON) == GPIO.HIGH:
            p.terminate()
            return

        lcd_line_1 = f"ALARM:  {datetime.now().strftime('%H:%M:%S')}"
        lcd.message = lcd_line_1

        sleep(0.5)
        lcd.clear()
        sleep(0.5)

        i += 1
    p.terminate()


def toggle_backlight(event):
    global BACKLIGHT_STATUS
    BACKLIGHT_STATUS = not BACKLIGHT_STATUS
    GPIO.output(BACKLIGHT, BACKLIGHT_STATUS)


def message(lcd, message):
    lcd.clear()
    lcd.message = message
    sleep(2)
    lcd.clear()


def safe_exit(lcd, alarm):
    alarm.kill()
    lcd.clear()
    lcd.message = "Goodbye!"
    sleep(2)
    GPIO.output(BACKLIGHT, False)
    lcd.clear()
    exit(0)


def main():
    ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY, ENABLED = load_config(SETTINGS)

    # Initialize the buttons
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BLUE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(RED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Backlight Toggle
    GPIO.setup(BACKLIGHT, GPIO.OUT)
    GPIO.output(BACKLIGHT, BACKLIGHT_STATUS)
    GPIO.add_event_detect(GREEN_BUTTON, GPIO.RISING, callback=toggle_backlight)

    # Initialise the lcd class
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                          lcd_d7, LCD_COLUMNS, LCD_ROWS)
    lcd.clear()

    alarm = Alarm(ALARM_TIME, lcd, TONE, DURATION)
    if ENABLED:
        alarm.start()

    try:
        while True:
            # Don't overwrite alarm text with stock times
            while alarm.alarming:
                # Stop the alarm with blue button press.
                while GPIO.input(BLUE_BUTTON) == GPIO.HIGH:
                    alarm.stop_alarm()
                    message(lcd, "Stopped Alarm")
                sleep(1)

            # Grab and display time
            lcd.message = get_formatted_times(
                ALARM_TIME.strftime("%H:%M"), weekdays_only=WEEKDAYS_ONLY, enabled=ENABLED)

            # Power off if red button is held for 3 seconds
            while GPIO.input(RED_BUTTON) == GPIO.HIGH:
                for i in range(3):
                    if i == 0:
                        lcd.clear()
                    lcd.message = f"Shutting down {3 - i}"
                    if i == 3:
                        safe_exit(lcd, alarm)
                    sleep(1)

            # Reload the config on blue button press.
            while GPIO.input(BLUE_BUTTON) == GPIO.HIGH and not alarm.alarming:
                ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY, ENABLED = load_config(
                    SETTINGS)

                alarm.kill()
                if ENABLED:
                    alarm = Alarm(ALARM_TIME, lcd, TONE, DURATION)
                    alarm.start()
                message(lcd, "Reloaded Config")
            sleep(1)

    except KeyboardInterrupt:
        safe_exit(lcd, alarm)


if __name__ == "__main__":
    main()
