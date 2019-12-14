#!/usr/bin/python3

# 16x2 LCD Alarm

from time import sleep
from datetime import datetime, timedelta, date
import RPi.GPIO as GPIO
import adafruit_character_lcd.character_lcd as characterlcd
import subprocess
import digitalio
import board
import json

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

GREEN_BUTTON = 17
BLUE_BUTTON = 27
RED_BUTTON = 22


def load_config(filename):
    with open(filename, "r") as f:
        config = json.loads(f.read())

    ALARM_TIME = datetime.strptime(
        config["ALARM"]["TIME"], "%H:%M:%S")
    TONE = config["ALARM"]["TONE"]
    DURATION = int(config["ALARM"]["DURATION"])
    return ALARM_TIME, TONE, DURATION


def get_times(ALARM_TIME):
    tomorrow_format = "%Y-%m-%d %H:%M"
    today_format = "%b %d  %H:%M:%S"

    tomorrow = date.today() + timedelta(days=1)
    alarm_time = datetime.strptime(f"{tomorrow} {ALARM_TIME}", tomorrow_format) + timedelta(seconds=1)
    diff = alarm_time - datetime.now()

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    hours = str(hours).zfill(2)
    minutes = str(minutes).zfill(2)
    seconds = str(seconds).zfill(2)

    lcd_line_1 = datetime.now().strftime(today_format) + "\n"
    lcd_line_2 = f"{datetime.now().strftime('%a')}     {hours}:{minutes}:{seconds}"
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


def main():
    lcd_columns = 16
    lcd_rows = 2

    ALARM_TIME, TONE, DURATION = load_config("settings.json")

    # Initialize the buttons
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BLUE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(RED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Initialise the lcd class
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                        lcd_d7, lcd_columns, lcd_rows)
    lcd.clear()

    while True:
        if datetime.now().strftime("%H:%M:%S") == ALARM_TIME.strftime("%H:%M:%S"):
            play_alarm(lcd, TONE, DURATION)
        elif (datetime.now() + timedelta(seconds=1)).strftime("%H:%M:%S") == ALARM_TIME.strftime("%H:%M:%S"):
            play_alarm(lcd, TONE, DURATION)

        lcd.message = get_times(ALARM_TIME.strftime("%H:%M"))

        i = 0
        while GPIO.input(RED_BUTTON) == GPIO.HIGH:
            if i == 0:
                lcd.clear()

            lcd.message = f"Quitting in {3 - i}"

            if i == 3:
                lcd.clear()
                lcd.message = "Goodbye!"
                sleep(1)
                lcd.clear()
                exit(0)

            i += 1
            sleep(1)

        while GPIO.input(BLUE_BUTTON) == GPIO.HIGH:
            ALARM_TIME, TONE, DURATION = load_config("settings.json")
            lcd.clear()
            lcd.message = "Reloaded Config"
            sleep(2)
            lcd.clear()

        sleep(1)


if __name__ == "__main__":
    main()
