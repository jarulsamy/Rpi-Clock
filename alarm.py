from datetime import datetime
from time import sleep
import subprocess
import threading
import os


class Alarm(threading.Thread):
    def __init__(self, TIME, LCD, TONE, DURATION):
        # Call parent thread constructor
        super(Alarm, self).__init__()

        # Extract when to set off the alarm
        self.hour = TIME.hour
        self.minute = TIME.minute
        self.second = TIME.second
        self.lcd = LCD
        self.tone = TONE
        self.duration = DURATION

        # Way to kill
        self.running = True
        self.alarming = False

    def play_alarm(self):
        i = 0
        p = subprocess.Popen(["mpg321", self.tone], stdout=None, stderr=None)
        self.lcd.clear()

        while self.running and i < self.duration and p.poll() is None:
            self.alarming = True
            lcd_line_1 = f"ALARM:  {datetime.now().strftime('%H:%M:%S')}"
            self.lcd.message = lcd_line_1

            sleep(0.5)
            self.lcd.clear()
            sleep(0.5)

            i += 1

        # Kill music subprocess and reset state
        self.alarming = False
        p.terminate()

    def stop_alarm(self):
        self.running = False
        sleep(1)
        self.running = True

    def run(self):
        while self.running:
            now = datetime.now()
            if (now.hour == self.hour and now.minute == self.minute and now.second == self.second):
                self.play_alarm()
            sleep(0.1)

    def kill(self):
        self.running = False
