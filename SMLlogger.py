#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
########################################################################
#
#   SMLlogger:  
#		7.2.2016 Dirk Clemens 
#		read data using a IR-USB-Head from a SML-counter (OBIS)
#		tested with "Zweirichtungszähler eHZ-IW8E2Axxx"
#	
#	based on 
#		http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/edl21-ehz
#		http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/emh-ehz-h1
#		http://volkszaehler.org/pipermail/volkszaehler-users/2012-September/000451.html
#		http://wiki.volkszaehler.org/software/sml
#		http://www.mscons.net/obis_kennzahlen.pdf
#		https://www.mikrocontroller.net/attachment/89888/Q3Dx_D0_Spezifikation_v11.pdf
#		https://eclipse.org/paho/clients/python/ 
#
#	requirements:
#	sudo apt-get install python-dev python-pip python-serial python3-serial 
#	sudo pip install paho-mqtt
#
########################################################################

from __future__ import print_function 
import sys
import os
import serial
import time
import logging
from datetime import datetime
import math
import paho.mqtt.client as paho

# MQTT Callback events #
# connection event
def on_connect(client, data, flags, rc):
	print('Connected, rc: ' + str(rc))
# subscription event
def on_subscribe(client, userdata, mid, gqos):
	print('Subscribed: ' + str(mid))
# received message event
def on_message(client, obj, msg):
	print(msg.topic+" "+str(msg.payload))

# hex string to signed integer 32 bit
# unfortunately this function is not correct, but the best one I found
def hexstr2signed32int(hexstr):
	num = long(hexstr, 16)
	if num >> 31: 
		num = num - 2**32 
	if num > -100000000 and num < 100000000: # ok, this is not good ;-)
		return num
	else:
		logging.debug("%s %s" % (hexstr, num))
	
# parse hex string from USB serial stream and extract values for obis_id
# print result and publish as mqtt message 
def parseSML(data_hex, obis_id, obis_string, pos, len):
	obis_value = 0
	# find position of OBIS-Kennzahl 
	position = data_hex.find(obis_string)
	
	# break, do not send mqtt message
	if position == 0: 
		return 0 

	# extract reading from position start: 34 lenght: 10 (for 1.8.0.)
	hex_value = data_hex[position+pos:position+pos+len]
	
	# convert to integer
	obis_value = hexstr2signed32int(hex_value)/10.0

	# publish value as mosquitto message
	mqtt_topic = "smarthome/vzlogger/%s/state" % (obis_id,)
	#print (mqtt_topic)
	client.publish(mqtt_topic, obis_value )
	
	# wait ...
	time.sleep(1)	
	return obis_value

########################################################################
# MAIN  	
# 1b1b1b1b010101017607000b06d8119a620062007263010176010107000b025c05de0b0901454d4800004735c7010163a74e007607000b06d8119b620062007263070177010b0901454d4800004735c7070100620affff72620165025cd8f87a77078181c78203ff0101010104454d480177070100000009ff010101010b0901454d4800004735c70177070100010800ff6401018201621e52ff56000308cff70177070100020800ff6401018201621e52ff5600015fc1450177070100010801ff0101621e52ff56000308cff70177070100020801ff0101621e52ff5600015fc1450177070100010802ff0101621e52ff5600000000000177070100020802ff0101621e52ff5600000000000177070100100700ff0101621b52ff5500000b940177078181c78205ff0172620165025cd8f801018302841ead39cbefc83a615721f4639f94b453d6793c0f28883a1a2291deb9b7905b9af9e8bcc3955444cdb68d7078d1351b0101016323d4007607000b06d8119e6200620072630201710163527100001b1b1b1b1a01684c 
#
########################################################################
def main():

	# logging
	global logging
	logging.basicConfig(filename='/log/vzlogger.log', 
					level=logging.DEBUG, 
					format='%(asctime)s %(message)s', 
					datefmt='%Y-%m-%d %H:%M:%S')

	#logger = logging.getLogger(__name__)
	#logger.setLevel(logging.DEBUG)

	# eHZ-Datentelegramme können mittels eines optischen Auslesekopfs nach DIN EN 62056-21 
	# z. B. über die serielle Schnittstelle eines PC ausgelesen werden.
	# Einstellung: bit/s= 9600, Datenbit = 7, Parität = gerade, Stoppbits = 1, Flusssteuerung = kein.
	ser = serial.Serial(
		port='/dev/ttyUSB0', 
		baudrate=9600, 
		bytesize=8, 
		parity='N', 
		stopbits=1, 
		timeout=2, 
		xonxoff=False, 
		rtscts=False, 
		dsrdtr=False)
	ser.flushInput()
	ser.flushOutput()

	data_hex = ''
	reading_ok = False
	try:
		# read n chars, change that in case it's too short
		while (1):
			data_raw = ser.read(50)
			#print(data_raw.encode("hex"))

			# find start escape sequence: 1b1b1b1b0101010176
			if data_raw.encode("hex").find("1b1b1b1b0101010176") >= 0 :
				data_raw += ser.read(750) #lenght is 792
				reading_ok = True 
				break # found enough data, stop reading serial port
	except serial.serialutil.SerialException, e:
		reading_ok = False
		logging.debug("Error reading serial port: %s" % (e,))
		print("Error reading serial port: ", e)

	# convert reading to hex:
	data_hex = data_raw.encode("hex")
	# print (data_hex)

	if reading_ok:
		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
		file = open(os.path.join(__location__, "vzlogger.txt"), "a")		
		tstamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

		# tested with eHZ-IW8E2Axxx
		sml180 = parseSML(data_hex, "180", '070100010800ff', 34, 10) 
		file.write("%s;180;%s\n" % (tstamp, sml180))
		print ("180: ", sml180)
		
		sml280 = parseSML(data_hex, "280", '070100020800ff', 34, 10)
		file.write("%s;280;%s\n" % (tstamp, sml280))
		print ("280: ", sml280) 
		
		sml167 = parseSML(data_hex, "167", '070100100700ff', 28, 8) 
		file.write("%s;167;%s\n" % (tstamp, sml167))
		print ("167: ", sml167)
		
		file.close()


########################################################################
#
########################################################################
global client
if __name__ == "__main__":

	# create the MQTT client
	client = paho.Client()
	# assign event callbacks
	#client.on_connect = on_connect
	#client.on_message = on_message
	# client connection to MQTT server address
	client.connect("smarthome", 1883, 60)	

	main()
	
	client.disconnect()



