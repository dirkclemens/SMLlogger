#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
########################################################################
#
#   SMLlogger:  
#		7.2.2016 Dirk Clemens 	iot@adcore.de
#		6.5.2017 Dirk Clemens	improvements, range check while converting hex to int
#		read data using a IR-USB-Head from a SML-counter (OBIS)
#		tested with "Zweirichtungszähler eHZ-IW8E2Axxx"
#	
#	based on 
#		http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/edl21-ehz
#		http://wiki.volkszaehler.org/hardware/channels/meters/power/edl-ehz/emh-ehz-h1
#		http://volkszaehler.org/pipermail/volkszaehler-users/2012-September/000451.html
#		http://wiki.volkszaehler.org/software/sml
#		https://sharepoint.infra-fuerth.de/unbundling/obis_kennzahlen.pdf
#		https://www.mikrocontroller.net/attachment/89888/Q3Dx_D0_Spezifikation_v11.pdf
#		https://eclipse.org/paho/clients/python/ 
#
#	requirements:
#	sudo apt-get install python-dev python-pip python-serial python3-serial 
#	sudo pip install RPi.GPIO
#	sudo pip install paho-mqtt
#
########################################################################

import sys
import os
import serial
import time
import logging
from datetime import datetime
import math
import paho.mqtt.client as paho
import ssl
import urllib

# ------------- #
# settings      #
# ------------- #

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

config = ConfigParser()
config.read('/root/.credentials/pycredentials') 

MQTT_SERVER = config['DEFAULT']['mqtt_server']    
MQTT_PORT = config['DEFAULT']['mqtt_port']    
MQTT_TLS =  config['DEFAULT']['mqtt_tls']
MQTT_SERVERIP = config['DEFAULT']['mqtt_serverip']
MQTT_CACERT = config['DEFAULT']['mqtt_cacert']

# hex string to signed integer, inkl. range check http://stackoverflow.com/a/6727975 
def hexstr2signedint(hexval):
	uintval = int(hexval,16)
	if uintval > 0x7FFFFFFF:		# > 2147483647
		uintval -= 0x100000000		# -= 4294967296 
	return uintval

# parse hex string from USB serial stream and extract values for obis_id
# print result and publish as mqtt message 
def parseSML(data_hex, obis_id, obis_string, pos, length):
	obis_value = 0
	# find position of OBIS-Kennzahl 
	position = data_hex.find(obis_string)
	
	# break, do not send mqtt message
	if position <= 0:
		return 0 

	# extract reading from position start: 34 length: 10 (for 1.8.0.)
	hex_value = data_hex[position+pos:position+pos+length]
	
	# convert to integer, check range  
	obis_value = hexstr2signedint(hex_value)
	
	# # publish value as mosquitto message
	mqtt_topic = "smarthome/SMLlogger/%s/state" % (obis_id,)
	# #print (mqtt_topic)
	client.publish(mqtt_topic, str(obis_value/10.0) )
	
	# wait ...
	time.sleep(1)	
	return obis_value

########################################################################
import sys
import glob
import serial
# http://stackoverflow.com/a/14224477
def checkUSB():
	if sys.platform.startswith('linux'):
		# this excludes your current terminal "/dev/tty"
		ports = glob.glob('/dev/ttyUSB*')
	else:
		raise EnvironmentError('Unsupported platform')
		pushover(e)
	result = []
	for port in ports:
		try:
			s = serial.Serial(port)
			s.close()
			result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result


########################################################################
# MAIN  	
# 1b1b1b1b010101017607000b06d8119a620062007263010176010107000b025c05de0b0901454d4800004735c7010163a74e007607000b06d8119b620062007263070177010b0901454d4800004735c7070100620affff72620165025cd8f87a77078181c78203ff0101010104454d480177070100000009ff010101010b0901454d4800004735c70177070100010800ff6401018201621e52ff56000308cff70177070100020800ff6401018201621e52ff5600015fc1450177070100010801ff0101621e52ff56000308cff70177070100020801ff0101621e52ff5600015fc1450177070100010802ff0101621e52ff5600000000000177070100020802ff0101621e52ff5600000000000177070100100700ff0101621b52ff5500000b940177078181c78205ff0172620165025cd8f801018302841ead39cbefc83a615721f4639f94b453d6793c0f28883a1a2291deb9b7905b9af9e8bcc3955444cdb68d7078d1351b0101016323d4007607000b06d8119e6200620072630201710163527100001b1b1b1b1a01684c 
#
########################################################################
def main():

	# logging
	global logging
	logging.basicConfig(filename='/var/log/SMLlogger.log', 
					level=logging.DEBUG, 
					format='%(asctime)s %(message)s', 
					datefmt='%Y-%m-%d %H:%M:%S')

	#logger = logging.getLogger(__name__)
	#logger.setLevel(logging.DEBUG)

	usbports = checkUSB()
	# print len(ports)
	if (len(usbports) == 1):
		#print(usbports[0])
		print("opening USB port :" + usbports[0])	
	else:
		print("SMLlogger: usbports: %s ports" % (len(usbports), ))
		pushover("SMLlogger: usbports: %s ports" % (len(usbports), ))
		sys.exit(1)

	# eHZ-Datentelegramme können mittels eines optischen Auslesekopfs nach DIN EN 62056-21 
	# z. B. über die serielle Schnittstelle eines PC ausgelesen werden.
	# Einstellung: bit/s= 9600, Datenbit = 7, Parität = gerade, Stoppbits = 1, Flusssteuerung = kein.
	ser = serial.Serial(
		port=usbports[0], #'/dev/ttyUSB1', 
		baudrate=9600, 
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
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
		############################################
		# error logging
		#
		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
		file = open(os.path.join(__location__, "energy.logger.txt"), "a")		
		tstamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

		# tested with eHZ-IW8E2Axxx
		sml180 = parseSML(data_hex, "180", '070100010800ff', 34, 10) 
		if (sml180 == 0):
			logging.debug("%s int:%s raw:%s" % ("180", sml180, data_hex))
			file.write("%s;180;%s;%s\n" % (tstamp, sml180, data_hex))
		print ("180: ", sml180)
		
		sml280 = parseSML(data_hex, "280", '070100020800ff', 34, 10)
		if (sml280 == 0):
			logging.debug("%s int:%s raw:%s" % ("280", sml280, data_hex))
			file.write("%s;280;%s;%s\n" % (tstamp, sml280, data_hex))
		print ("280: ", sml280) 
		
		sml167 = parseSML(data_hex, "167", '070100100700ff', 28, 8) 
		if (sml167 == 0):
			logging.debug("%s int:%s raw:%s" % ("167", sml167, data_hex))
			file.write("%s;167;%s;%s\n" % (tstamp, sml167, data_hex))
		print ("167: ", sml167)

########################################################################
#
########################################################################
global client
if __name__ == "__main__":

	# create the MQTT client
	client = paho.Client()
	if (MQTT_TLS == "True"):
		print("connecting using tls")
		#client.tls_set(MQTT_CACERT)
		client.tls_set(ca_certs="/home/chip/.ssh/ca.crt")
		#client.tls_insecure_set(True)     # prevents error - ssl.SSLError: Certificate subject does not match remote hostname.
	client.connect(MQTT_SERVER, int(MQTT_PORT), 60)  	

	main()
	
	client.disconnect()


