#! /usr/bin/python3
# -*- coding: utf-8 -*-
# A dirty little script for dirty little interpretation.
import configparser
import mysql.connector
from datetime import datetime

VERSION = 'stats.py v0.1.2' # fanctrl.py v0.3+ compatible

class Stats():
    
    def __init__(self):
        print(VERSION)
        self.load_config()
        self.connect_mysql()
    
    def load_config(self):
        file = 'fanctrl.conf'
        self.Config = configparser.ConfigParser()
        try:
            self.Config.read(file)
        except Exception:
            print('error reading fanctrl.conf')
    
    def connect_mysql(self):
        try:
            self.DB = mysql.connector.connect(
                host = self.Config['mysql']['host'],
                user = self.Config['mysql']['user'],
                database = self.Config['mysql']['database'],
                password = self.Config['mysql']['password']
            )
            self.Cursor = self.DB.cursor()
        except Exception:
            self.DB = False
            print('error while connecting mysql')
        if self.DB: print('mysql connected')
    
    def print_config(self):
        print('\nConfiguration:')
        for section in self.Config.sections():
            print('')
            for (key, value) in self.Config.items(section):
                if section == 'mysql' and key == 'password':
                    value = '***'
                print(section+'_'+key+': '+value)
    
    def analyze(self):
        query = "SELECT * FROM fanctrl_log \
            WHERE event != 'measure' AND event != 'init' \
            ORDER BY id ASC"
        self.Cursor.execute(query)
        data = self.Cursor.fetchall()
        last = False
        raise_speed_sum = float(0)
        raise_speed_count = 0
        drop_speed_sum = float(0)
        drop_speed_count = 0
        total_time_on = 0
        total_time_off = 0
        total_temp = float(0)
        total_temp_count = 0
        print('\nEvents:\n')
        for Event in data:
            num = Event[0]
            timestamp = Event[1]
            timedate = str(datetime.fromtimestamp(timestamp))
            state = Event[2]
            event = Event[3]
            temp = Event[4]
            temp_high = Event[5]
            temp_low = Event[6]
            print(timedate+' '+str(temp)+' '+event)
            if last:
                if event == 'switch on':
                    query = "SELECT * FROM fanctrl_log \
                        WHERE time >= %s AND time <= %s \
                        AND event != 'init' \
                        AND event != 'switch on' AND event != 'switch off' \
                        ORDER BY id ASC"
                    d = (last_timestamp, timestamp)
                    self.Cursor.execute(query, d)
                    D = self.Cursor.fetchall()
                    for E in D:
                        t = E[4]
                        total_temp += t
                        total_temp_count += 1
                    raise_time = timestamp - last_timestamp
                    total_time_off += raise_time
                    raise_temp = temp - last_temp
                    raise_speed = raise_temp / raise_time * 60
                    raise_speed_sum += raise_speed
                    raise_speed_count += 1
                    raise_temp = "{:0.1f}".format(raise_temp)
                    raise_speed = "{:0.2f}".format(raise_speed)
                    p1 = 'raise: '+str(raise_temp)+'°C in '
                    p2 = str(raise_time)+' sec ('
                    p3 = raise_speed+' °C/min)'
                    print(p1+p2+p3)
                elif event == 'switch off':
                    query = "SELECT * FROM fanctrl_log \
                        WHERE time >= %s AND time <= %s \
                        AND event != 'init' \
                        AND event != 'switch on' AND event != 'switch off' \
                        ORDER BY id ASC"
                    d = (last_timestamp, timestamp)
                    self.Cursor.execute(query, d)
                    D = self.Cursor.fetchall()
                    for E in D:
                        t = E[4]
                        total_temp += t
                        total_temp_count += 1
                    drop_time = timestamp - last_timestamp
                    total_time_on += drop_time
                    drop_temp = last_temp - temp
                    drop_speed = drop_temp / drop_time * 60
                    drop_speed_sum += drop_speed
                    drop_speed_count += 1
                    drop_temp = "{:0.1f}".format(drop_temp)
                    drop_speed = "{:0.2f}".format(drop_speed)
                    p1 = 'drop: '+str(drop_temp)+'°C in '
                    p2 = str(drop_time)+' sec ('
                    p3 = drop_speed+' °C/min)'
                    print(p1+p2+p3)
            last = True
            last_num = num
            last_timestamp = timestamp
            last_timedate = timedate
            last_state = state
            last_event = event
            last_temp = temp
            last_temp_high = temp_high
            last_temp_low = temp_low
        try:
            average_raise_speed = raise_speed_sum / raise_speed_count
            average_drop_speed = drop_speed_sum / drop_speed_count
            raise_drop_ratio = average_raise_speed / average_drop_speed * 100
            on_off_ratio = float(total_time_on) / float(total_time_off) * 100
            temp_average = total_temp / total_temp_count
            total_efficiency = 100 - (raise_drop_ratio + on_off_ratio) / 2
            average_raise_speed = "{:0.2f}".format(average_raise_speed)
            average_drop_speed = "{:0.2f}".format(average_drop_speed)
            raise_drop_ratio = "{:0.2f}".format(raise_drop_ratio)
            on_off_ratio = "{:0.2f}".format(on_off_ratio)
            temp_average = "{:0.1f}".format(temp_average)
            total_efficiency = "{:0.1f}".format(total_efficiency)
            print('\nSummary:')
            print('\nAverage raise speed: '+str(average_raise_speed)+' °C/min')
            print('Average drop speed: '+str(average_drop_speed)+' °C/min')
            print('Raise-Drop-Ratio: '+str(raise_drop_ratio)+' %')
            print('\nTotal time on: '+str(total_time_on)+' sec')
            print('Total time off: '+str(total_time_off)+' sec')
            print('On-Off-Ratio: '+str(on_off_ratio)+' %')
            print('\nTemperature settings: High = '+str(temp_high)+' / Low = '+str(temp_low))
            print('Average temperature: '+str(temp_average)+' °C')
            print('Total efficiency: *** '+str(total_efficiency)+' % ***')
        except Exception:
            print('\nNot enough data, try again later')
    
    def show(self):
        self.print_config()
        self.analyze()
    
    def end(self):
        self.Cursor.close()
        self.DB.close()

if __name__ == '__main__':
    stats = Stats()
    stats.show()
    stats.end()
