#!/usr/bin/python3
"""CoolPi fan controller"""

import os
import time
import logging
import configparser
import RPi.GPIO as GPIO

VERSION = "0.0.1"

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "coolpi.conf")

class FanCtrl:
    def __init__(self, cfg_path: str = CONFIG_PATH):
        self.cfg = self._load_config(cfg_path)
        self._setup_logging()

        self.gpio = int(self.cfg.get("fan", "gpio"))
        self.temp_high = float(self.cfg.get("fan", "temphigh"))
        self.temp_low = float(self.cfg.get("fan", "templow"))
        self.interval = int(self.cfg.get("fan", "interval"))
        self.active = bool(int(self.cfg.get("fan", "active")))

        self.fan_on = False
        if self.active:
            self._setup_gpio()
            logging.info("Fan control enabled on GPIO %s", self.gpio)
        else:
            logging.warning("Fan control disabled in configuration")

    def _setup_logging(self) -> None:
        level_map = {
            0: logging.DEBUG,
            1: logging.INFO,
            2: logging.WARNING,
            3: logging.ERROR,
            4: logging.CRITICAL,
        }
        level = int(self.cfg.get("console", "loglevel", fallback="1"))
        logging.basicConfig(
            level=level_map.get(level, logging.INFO),
            format="[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.info("CoolPi %s starting", VERSION)

    def _load_config(self, path: str) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        parser.read(path)
        return parser

    def _read_temp(self) -> float:
        raw = os.popen("vcgencmd measure_temp").readline()
        value = raw.replace("temp=", "").replace("'C\n", "")
        return float(value)

    def _setup_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio, GPIO.OUT)
        self.fan_on = bool(GPIO.input(self.gpio))

    def _switch_fan(self, on: bool) -> bool:
        if on != self.fan_on:
            GPIO.output(self.gpio, GPIO.HIGH if on else GPIO.LOW)
            self.fan_on = on
            return True
        return False

    def watch(self) -> None:
        if not self.active:
            return
        try:
            while True:
                temp = self._read_temp()
                if temp >= self.temp_high and self._switch_fan(True):
                    logging.info("Fan turned on at %.1f°C", temp)
                elif temp < self.temp_low and self._switch_fan(False):
                    logging.info("Fan turned off at %.1f°C", temp)
                else:
                    logging.debug("Temperature %.1f°C", temp)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            pass
        finally:
            self._switch_fan(True)
            logging.info("Fan turned on before exit")

if __name__ == "__main__":
    FanCtrl().watch()
