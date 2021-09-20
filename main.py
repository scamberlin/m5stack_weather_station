"""
hello.py

    Writes "Hello!" in random colors at random locations on a
    M5Stack core display.

"""

import config
import time
import utime
import network

import random
import _thread
import ntptime

import esp
esp.osdebug(None)

import gc
gc.collect()

import random
from machine import SoftI2C, Pin, RTC, UART, SPI
import uasyncio as asyncio

import ili9342c
import vga1_8x8 as font1
import vga1_8x16 as font2
import vga1_bold_16x16 as font3
import vga1_bold_16x32 as font4


import axp202c

try:
  import urequests as requests
except:
  import upip
  upip.install('urequests')

try:
  import ujson as json
except:
  import upip
  upip.install('json')

try :
  rtc = RTC()
  ntptime.settime()
except Exception as e:
  print("Exception RTC: {}".format(e))

try:
  i2c = SoftI2C(
    sda=machine.Pin(21),
    scl=machine.Pin(22),
    freq=100000) # valid for M5Stack grey and basic
  devices = i2c.scan()
  if len(devices) == 0:
    print("Error: no I2C device !")
  else:
    for d in devices:
      print("Decimal address: ",d," | Hexa address: ",hex(d))
except Exception as e:
  print("Exception I2C: {}".format(e))

days = [ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Sat', 'Sun' ]
months = [ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ]

def cettime():
  year = time.localtime()[0]       #get current year
  HHMarch   = time.mktime((year,3 ,(31-(int(5*year/4+4))%7),1,0,0,0,0,0)) #Time of March change to CEST
  HHOctober = time.mktime((year,10,(31-(int(5*year/4+1))%7),1,0,0,0,0,0)) #Time of October change to CET
  now=time.time()
  if now < HHMarch :               # we are before last sunday of march
    cet=time.localtime(now+3600) # CET:  UTC+1H
  elif now < HHOctober :           # we are before last sunday of october
    cet=time.localtime(now+7200) # CEST: UTC+2H
  else:                            # we are after last sunday of october
    cet=time.localtime(now+3600) # CET:  UTC+1H
  return(cet)

def _time():
  while True:
    cet = cettime()    # get the date and time in UTC
    date = '{}, {} {} {}'.format(days[cet[6]], cet[2], months[cet[1] - 1], cet[0])
    time = '{:02}:{:02}'.format(cet[3], cet[4])
    tft.text(font1, date, 56, 0, ili9342c.WHITE, ili9342c.BLACK)
    tft.text(font4, time, 80, 10, ili9342c.WHITE, ili9342c.BLACK)
    utime.sleep(1)

def _weather():
  while True:
    weather_data = requests.get(config.OWM_API_URL)
    for i in range(0,7,1):
      weather_icon = weather_data.json().get('list')[i].get('weather')[0].get('icon')[:2]
      weather_description = weather_data.json().get('list')[i].get('weather')[0].get('description')
      weather_temp = str(weather_data.json().get('list')[i].get('main').get('temp')-273.15)[:4]
      weather_temp_min = str(weather_data.json().get('list')[i].get('main').get('temp_min')-273.15)[:2]
      weather_temp_max = str(weather_data.json().get('list')[i].get('main').get('temp_max')-273.15)[:2]
      if i == 0:
        tft.jpg("jpg/wunderground/big/{}.jpg".format(weather_icon), 35 , 50)
        tft.text(font2, weather_description, int((((240/2)-(len(weather_description)*8))/2)+120), 60, ili9342c.WHITE, ili9342c.BLACK)
        tft.text(font4, "{}C".format(weather_temp), 140, 80, ili9342c.WHITE, ili9342c.BLACK)
        tft.text(font2, "{}/{}".format(weather_temp_min, weather_temp_max), 160, 110, ili9342c.WHITE, ili9342c.BLACK)
      elif i < 4:
        tft.text(font2, "{}".format(days[time.localtime()[6]+i]), 28 + ((i-1)*80), 140, ili9342c.WHITE, ili9342c.BLACK)
        tft.jpg("jpg/wunderground/small/{}.jpg".format(weather_icon), 15 + ((i-1)*80), 160)
        tft.text(font2, "{}/{}".format(weather_temp_min, weather_temp_max), 20 + ((i-1)*80), 210, ili9342c.WHITE, ili9342c.BLACK)
      else:
        tft.text(font2, "{}".format(days[time.localtime()[6]+i]), 28 + ((i-4)*80), 230, ili9342c.WHITE, ili9342c.BLACK)
        tft.jpg("jpg/wunderground/small/{}.jpg".format(weather_icon), 15 + ((i-4)*80), 250)
        tft.text(font2, "{}/{}".format(weather_temp_min, weather_temp_max), 20 + ((i-4)*80), 300, ili9342c.WHITE, ili9342c.BLACK)
    utime.sleep(600)

axp = axp202c.PMU(address=0x34)
axp.enablePower(axp202c.AXP192_LDO2)
axp.setDC3Voltage(3000)

spi = SPI(
  2,
  baudrate=60000000,
  sck=Pin(18),
  mosi=Pin(23))

tft = ili9342c.ILI9342C(
  spi,
  320,
  240,
  reset=Pin(33, Pin.OUT),
  cs=Pin(5, Pin.OUT),
  dc=Pin(15, Pin.OUT),
  rotation=1)

tft.init()
tft.fill(ili9342c.BLACK)
time.sleep(1)

tft.fill(0)
col_max = tft.width() - font1.WIDTH*6
row_max = tft.height() - font1.HEIGHT

_thread.start_new_thread(_time,())
_thread.start_new_thread(_weather,())

