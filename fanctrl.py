#! /usr/bin/python3
# -*- coding: utf-8 -*-
import time, sys, os
from datetime import datetime
import configparser
import RPi.GPIO as GPIO

VERSION = 'fanctrl.py v1.0.0'

class FanCtrl():
    
    def __init__(self):
        print(VERSION)
        # config
        cfgfile = 'fanctrl.conf'
        self.CFG = self.get_config(cfgfile)
        mysql = bool(int(self.CFG['mysql']['active']))
        # mysql
        if mysql:
            self.log_console(1, 'mysql enabled')
            host = self.CFG['mysql']['host']
            user = self.CFG['mysql']['user']
            password = self.CFG['mysql']['password']
            database = self.CFG['mysql']['database']
            if self.connect_mysql(host, user, password, database):
                self.create_tables()
                self.log_console(0, 'mysql OK')
            else:
                self.log_console(5, 'mysql connection FAILED')
                sys.exit('mysql error, exit')
        else:
            self.log_console(3, 'mysql disabled in ' + cfgfile)
        # fan
        if bool(int(self.CFG['fan']['active'])):
            self.log_console(1, 'fan control enabled')
            timestamp = int(time.time())
            timedate = str(datetime.fromtimestamp(timestamp))
            gpio = int(self.CFG['fan']['gpio'])
            self.setup_gpio(gpio)
            temp = self.get_CpuTemp()
            self.log_console(2, str(temp)+' °C @ '+timedate)
            if temp >= float(self.CFG['fan']['temphigh']):
                self.switch_fan(gpio, True)
                self.log_console(2, 'switch fan on')
            else:
                self.switch_fan(gpio, False)
                self.log_console(2, 'switch fan off')
            if mysql:
                self.log_mysql(timestamp, self.get_state(gpio), 'init', temp)
            time.sleep(1)
        else:
            self.log_console(3, 'fan control disabled in ' + cfgfile)
    
    def get_config(self, file):
        confighandler = configparser.ConfigParser()
        if not os.path.isfile(file):
            confighandler.add_section('console')
            confighandler.set('console', 'loglevel', '1')
            confighandler.add_section('fan')
            confighandler.set('fan', 'active', '0') # bool
            confighandler.set('fan', 'temphigh', '45.0') # float °C
            confighandler.set('fan', 'templow', '40.0') # float °C
            confighandler.set('fan', 'interval', '5') # int seconds
            confighandler.set('fan', 'gpio', '18') # int gpio (BCM)
            confighandler.add_section('mysql')
            confighandler.set('mysql', 'active', '0') # bool
            confighandler.set('mysql', 'truncate', '0') # bool
            confighandler.set('mysql', 'host', 'localhost') # string ip
            confighandler.set('mysql', 'user', '') # string
            confighandler.set('mysql', 'database', '') # string
            confighandler.set('mysql', 'password', '') # string
            fileHandler = open(file, 'w')
            confighandler.write(fileHandler)
            fileHandler.close()
        confighandler.read(file)
        return confighandler
    
    def log_console(self, lvl, msg):
        pre = {
            0: '[VBS] ', # verbose
            1: '[NRM] ', # normal
            2: '[INF] ', # info
            3: '[WRN] ', # warning
            4: '[ERR] ', # error
            5: '[FAT] '  # fatal
        }
        loglevel = int(self.CFG['console']['loglevel'])
        if lvl >= loglevel:
            if loglevel == 0:
                level = pre[lvl]
            else:
                level = ''
            print(level+msg)
    
    def connect_mysql(self, host, user, password, database):
        import mysql.connector
        try:
            self.DB = mysql.connector.connect(
                host = host,
                user = user,
                database = database,
                password = password
            )
            return True
        except Exception as E:
            self.DB = False
            self.log_console(4, 'mysql error: ' + str(E))
            return False
    
    def create_tables(self):
        self.Cursor = self.DB.cursor()
        query = "CREATE TABLE IF NOT EXISTS fanctrl_log \
        (id INT NOT NULL AUTO_INCREMENT, \
         time INT NOT NULL, \
         state TINYINT NOT NULL, \
         event VARCHAR(16) NOT NULL, \
         temp FLOAT NOT NULL, \
         temp_high FLOAT NOT NULL, \
         temp_low FLOAT NOT NULL, \
         info VARCHAR(256) NOT NULL, \
         PRIMARY KEY (id)) ENGINE = InnoDB;"
        self.Cursor.execute(query)
        self.DB.commit()
        if bool(int(self.CFG['mysql']['truncate'])):
            query = "TRUNCATE TABLE fanctrl_log"
            self.Cursor.execute(query)
            self.DB.commit()
    
    def log_mysql(self, time, state, event, temp=0, info=''):
        if event != 'init':
            temp_high = float(self.CFG['fan']['temphigh'])
            temp_low = float(self.CFG['fan']['templow'])
        else:
            temp_high = 0
            temp_low = 0
        query = "INSERT INTO fanctrl_log \
            (time, state, event, temp, temp_high, temp_low, info) \
            VALUES (%s, %s, %s, %s, %s, %s, %s)"
        data = (time, state, event,
            temp, temp_high, temp_low, info)
        self.Cursor.execute(query, data)
        self.DB.commit()
    
    def get_CpuTemp(self):
        raw = os.popen("vcgencmd measure_temp").readline()
        temp = raw.replace("temp=", "").replace("'C\n", "")
        return float(temp)
    
    def setup_gpio(self, gpio):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(gpio, GPIO.OUT)
    
    def get_state(self, gpio):
        return GPIO.input(gpio)
    
    def switch_fan(self, gpio, state):
        old_state = self.get_state(gpio)
        if state: # switch on
            if not old_state: # fan is off, turn on
                GPIO.output(gpio, GPIO.HIGH)
                return True
        else: # switch off
            if old_state: # fan is on, turn off
                GPIO.output(gpio, GPIO.LOW)
                return True
        return False
    
    def watch(self):
        fan = bool(int(self.CFG['fan']['active']))
        temp_high = float(self.CFG['fan']['temphigh'])
        temp_low = float(self.CFG['fan']['templow'])
        gpio = int(self.CFG['fan']['gpio'])
        mysql = bool(int(self.CFG['mysql']['active']))
        self.log_console(2, 'start monitoring with settings:')
        self.log_console(2, 'temp_high: ' + str(temp_high))
        self.log_console(2, 'temp_low: ' + str(temp_low))
        try:
            while True:
                timestamp = int(time.time())
                timedate = str(datetime.fromtimestamp(timestamp))
                temp = self.get_CpuTemp()
                evaluation = ' [OK]'
                if temp >= temp_high:
                    evaluation = ' [HIGH]'
                    self.log_console(0, 'temp: '+str(temp)+evaluation)
                    if fan:
                        if self.switch_fan(gpio, True):
                            self.log_console(1, 'switch fan on ('+str(temp)+' °C @ '+timedate+')')
                            if mysql:
                                self.log_mysql(timestamp, 1, 'switch on', temp)
                elif temp < temp_low:
                    evaluation = ' [LOW]'
                    self.log_console(0, 'temp: '+str(temp)+evaluation)
                    if fan:
                        if self.switch_fan(gpio, False):
                            self.log_console(1, 'switch fan off ('+str(temp)+' °C @ '+timedate+')')
                            if mysql:
                                self.log_mysql(timestamp, 0, 'switch off', temp)
                else:
                    self.log_console(0, 'temp: '+str(temp)+evaluation)
                if mysql:
                    if fan:
                        state = self.get_state(gpio)
                    else:
                        state = 0
                    self.log_mysql(timestamp, state, 'measure', temp)
                time.sleep(int(self.CFG['fan']['interval']))
        except KeyboardInterrupt:
            pass
        finally:
            if bool(int(self.CFG['fan']['active'])):
                self.switch_fan(gpio, True)
                self.log_console(2, 'switch fan on')
            if bool(int(self.CFG['mysql']['active'])):
                self.log_mysql(int(time.time()), 1, 'exit', temp)
                self.Cursor.close()
                self.DB.close()

if __name__ == '__main__':
    fanctrl = FanCtrl()
    fanctrl.watch()
