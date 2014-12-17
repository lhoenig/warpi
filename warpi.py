#!/usr/bin/env python

from wifi import Cell
import Adafruit_CharLCD as LCD
import gps
import signal
import sqlite3


# init lcd
lcd = LCD.Adafruit_CharLCDPlate()
lcd.clear()


# init database
conn = sqlite3.connect("warpi.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS \"geodata\" (\"time\" TEXT, \"lat\" TEXT, \"lon\" TEXT, \"wifi_data_key\" INTEGER);")
c.execute("CREATE TABLE IF NOT EXISTS \"wifi_data\" (\"key\" INTEGER, \"ssid\" TEXT, \"signal\" INTEGER, \"quality\" TEXT, \"frequency\" TEXT, \"bitrates\" TEXT, \"encrypted\" TEXT, \"encryption_type\" TEXT, \"channel\" INTEGER, \"address\" TEXT, \"mode\" TEXT);")
conn.commit()


# turn off lcd on receiving sigint
def on_int(signal, frame):
  conn.close()
  lcd.set_backlight(0)
  lcd.enable_display(False)
  quit()

# register signal handler
signal.signal(signal.SIGINT, on_int)


# message displayed on lcd
lcd_msg = ""


# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947") 
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)


def max_key():
  c.execute("SELECT wifi_data_key FROM geodata ORDER BY wifi_data_key DESC LIMIT 1")
  key = c.fetchone()
  if key is None:
    key = 0
  else:
    key = key[0]
  return key


def save_dataset(cells, report):
  insert_key = max_key() + 1
  
  # insert geodata
  c.execute("INSERT INTO geodata VALUES (\"" + report.time + "\", \"" 
    + `report.lat` + "\", \"" 
    + `report.lon` + "\", " 
    + `insert_key` + ")")
  
  # insert wifi data
  for cell in cells:
    print "INSERT INTO wifi_data VALUES (" + `insert_key` + ", \""  + `cell.ssid` + ", \""+ `cell.signal` + ", \""+ `cell.quality` + ", \""+ `cell.frequency` + ", \""+ `cell.bitrates` + ", \""+ `cell.encrypted` + ", \""+ cell.encryption_type + ", \""+ `cell.channel` + ", \""+ `cell.address` + ", \""+ `cell.mode` + ")"
    c.execute("INSERT INTO wifi_data VALUES (" + `insert_key` + ", \"" 
    + `cell.ssid` + ", \""
    + `cell.signal` + ", \""
    + `cell.quality` + ", \""
    + `cell.frequency` + ", \""
    + `cell.bitrates` + ", \""
    + `cell.encrypted` + ", \""
    + cell.encryption_type + ", \""
    + `cell.channel` + ", \""
    + `cell.address` + ", \""
    + `cell.mode` + ")")

  # save db
  conn.commit()


while True:
  try :
    # next gps pulse
    report = session.next()
    #print report
    
    if report['class'] == 'TPV' and hasattr(report, 'time'):
      
      cells = Cell.all("wlan0")   # scan for networks
      save_dataset(cells, report)

      # update lcd message if new
      tmp_msg = "%.4f" % report.lat + " " + "%.4f" % report.lon + "\n" + `len(cells)` + " networks"
      if lcd_msg != tmp_msg:
        lcd.clear()
        lcd_msg = tmp_msg
        lcd.message(lcd_msg)
        print lcd_msg
  
  except KeyError:
    pass
  except KeyboardInterrupt:
    quit()
  except StopIteration:
    session = None
    print "GPSD has terminated"