from datetime import datetime
from time import sleep
import subprocess
import threading
import logging


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
        logging.info("Alarm Started Ringing")
        i = 0
        p = subprocess.Popen(["/usr/binmpg321", self.tone],
                             stdout=None, stderr=None)
        self.lcd.clear()

        i = 0
        # Flash ALARM + Current time while alarm is ringing
        while self.running and i < self.duration and p.poll() is None:
            self.alarming = True
            current_time = datetime.now().strftime('%H:%M:%S')
            self.lcd.message = f"ALARM: {current_time}"

            sleep(0.5)
            self.lcd.clear()
            sleep(0.5)
            i += 1
        logging.info("Alarm stopped ringing")

        # Kill music subprocess and reset state
        logging.info("Alarm Stopped Ringing")
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
            sleep(0.5)

    def kill(self):
        self.running = False
