#!/usr/bin/python3

# 16x2 LCD Alarm

from time import sleep
from distutils.util import strtobool
from datetime import datetime, timedelta, date
import RPi.GPIO as GPIO
import adafruit_character_lcd.character_lcd as characterlcd
import subprocess
import digitalio
import board
import json
import os

"""
BCM PINS
RS - 18
EN - 23
D4 - 24
D5 - 25
D6 - 8
D7 - 7
"""

lcd_rs = digitalio.DigitalInOut(board.D18)
lcd_en = digitalio.DigitalInOut(board.D23)
lcd_d4 = digitalio.DigitalInOut(board.D24)
lcd_d5 = digitalio.DigitalInOut(board.D25)
lcd_d6 = digitalio.DigitalInOut(board.D8)
lcd_d7 = digitalio.DigitalInOut(board.D7)

BACKLIGHT = 5
GREEN_BUTTON = 17
BLUE_BUTTON = 27
RED_BUTTON = 22

BACKLIGHT_STATUS = True


def load_config(filename):
    with open(filename, "r") as f:
        config = json.loads(f.read())

    ALARM_TIME = datetime.strptime(
        config["ALARM"]["TIME"], "%H:%M:%S")
    TONE = config["ALARM"]["TONE"]
    DURATION = int(config["ALARM"]["DURATION"])
    WEEKDAYS_ONLY = strtobool(config["ALARM"]["WEEKDAYS_ONLY"])
    return ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY


def get_times(ALARM_TIME, weekdays_only=False):
    tomorrow_format = "%Y-%m-%d %H:%M"
    today_format = "%b %d  %H:%M:%S"

    tomorrow = date.today() + timedelta(days=1)
    if weekdays_only:
        while tomorrow.weekday() > 4:
            tomorrow += timedelta(days=1)

    alarm_time = datetime.strptime(
        f"{tomorrow} {ALARM_TIME}", tomorrow_format) + timedelta(seconds=1)
    diff = alarm_time - datetime.now()

    hours, remainder = divmod(diff.seconds, 3600)
    if diff.days > 1:
        lcd_line_2 = f"{datetime.now().strftime('%a')}     {str(diff.days).zfill(2)}d {str(hours).zfill(2)}h"
        alarm = False
    else:
        minutes, seconds = divmod(remainder, 60)
        hours = str(hours).zfill(2)
        minutes = str(minutes).zfill(2)
        seconds = str(seconds).zfill(2)
        lcd_line_2 = f"{datetime.now().strftime('%a')}     {hours}:{minutes}:{seconds}"
        alarm = True

    lcd_line_1 = datetime.now().strftime(today_format) + "\n"
    return lcd_line_1 + lcd_line_2, alarm


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


def safe_exit(lcd):
    lcd.clear()
    lcd.message = "Goodbye!"
    sleep(2)
    GPIO.output(BACKLIGHT, False)
    lcd.clear()
    exit(0)


def main():
    lcd_columns = 16
    lcd_rows = 2

    ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY = load_config("settings.json")

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
    global lcd
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                          lcd_d7, lcd_columns, lcd_rows)
    lcd.clear()

    try:
        while True:
            lcd.message, alarm = get_times(
                ALARM_TIME.strftime("%H:%M"), WEEKDAYS_ONLY)
            current_time = datetime.now()

            if alarm:
                if current_time.hour == ALARM_TIME.hour and current_time.minute == ALARM_TIME.minute and current_time.second == ALARM_TIME.second:
                    play_alarm(lcd, TONE, DURATION)

            i = 0
            while GPIO.input(RED_BUTTON) == GPIO.HIGH:
                if i == 0:
                    lcd.clear()

                lcd.message = f"Shutting down {3 - i}"

                if i == 3:
                    lcd.clear()
                    lcd.message = "Goodbye!"
                    sleep(2)
                    GPIO.output(BACKLIGHT, False)
                    lcd.clear()
                    os.system("poweroff")
                    exit(0)

                i += 1
                sleep(1)

            while GPIO.input(BLUE_BUTTON) == GPIO.HIGH:
                ALARM_TIME, TONE, DURATION, WEEKDAYS_ONLY = load_config(
                    "settings.json")
                lcd.clear()
                lcd.message = "Reloaded Config"
                sleep(2)
                lcd.clear()

            sleep(1)
    except KeyboardInterrupt:
        safe_exit(lcd)


if __name__ == "__main__":
    main()
