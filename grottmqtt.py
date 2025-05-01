#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import datetime
import logging
import signal

from datetime import datetime

import logging.handlers as Handlers

import paho
import paho.mqtt.client as mqtt

#--------------------------------------------------
sig_int 	= False
mqtt_client	= None
mqtt_status 	= 0


#============================================================================

# The callback for when the client receives a CONNACK response from the server.
def mqtt_on_connect(client, userdata, flags, rc, properties):
	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.

	global sig_int, mqtt_status

	if not rc.is_failure:
		logging.info( f"MQTT connection successfull" )
#		client.subscribe( userdata + "/#" )
	else:	
		logging.error( f"MQTT connection error: {rc}" )
#		client.disconnect()
		mqtt_status = rc


def mqtt_on_disconnect(client, userdata, flags, rc, properties):
	global sig_int, mqtt_status

	if rc > 0 and not sig_int and mqtt_status == 0:
		logging.warning( f"MQTT disconnected with result code {rc}" )
	else:
		logging.info( f"MQTT normal disconnection, exiting" )
		sig_int = True


def signal_sigint_handler( sig, frame ):
	global sig_int, mqtt_client

	logging.info( "SIGINT received, exiting" )
	sig_int = True
	if mqtt_client is not None:
		mqtt_client.loop_stop()
		mqtt_client.disconnect()



class publish:

	def single( 	topic: str,
			payload: str,
			qos: int = 0,
			retain: bool = False,
			hostname: str = 'localhost',
			port: int = 1883,
			client_id: str = '',
			keepalive: int = 60,
			auth: dict | None = None ) -> None:
		
		global sig_int, mqtt_client, mqtt_status
		
		if mqtt_client == None:
			# set defaults
			logging.basicConfig( stream = sys.stdout, level = logging.INFO, format = '[%(levelname)s] %(message)s', datefmt = '%d.%m.%Y %I:%M:%S' )
#			logging.getLogger().setLevel( "INFO" )

			logging.info( '============ GROTT MQTT Client starting ' + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + ' =======================' )

#			signal.signal( signal.SIGINT, signal_sigint_handler )
#			signal.signal( signal.SIGTERM, signal_sigint_handler )

			mqtt_client = mqtt.Client( mqtt.CallbackAPIVersion.VERSION2,
					client_id=client_id,
					transport="tcp" )

			mqtt_client.on_connect 		= mqtt_on_connect
			mqtt_client.on_disconnect 	= mqtt_on_disconnect

			mqtt_client.username_pw_set( auth[ 'username' ], auth[ 'password' ] )

		if mqtt_client != None:
			if not mqtt_client.is_connected():
				logging.info( 'MQTT (re)starting the connection' )
				mqtt_client.loop_stop()
				mqtt_client.connect( hostname, port, keepalive )
				mqtt_client.loop_start()

			mqtt_client.publish( topic=topic, payload=payload, qos=qos, retain=retain )
			logging.info( 'MQTT message published' )

		if sig_int:
			mqtt_client.loop_stop()
			mqtt_client.disconnect()

			if mqtt_status == 0:
				exit( 0 )
			else:
				exit( mqtt_status.pack()[ 0 ] )

