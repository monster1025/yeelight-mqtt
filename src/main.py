import logging
import time
import threading
import os
import json
import pyyeelight
from lightbulbstate import LightBulbState

#mine
import mqtt
import yamlparser

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)
QUERY_TIME = 2

bulbs=[]
processNow = False

def init_lamps(config):
	if config is None:
		raise "Config is None."
	sids = config.get("sids", "None")
	if sids is None:
		raise "Config -> sids is None."

	lamps=[]
	# sid is IP-address
	for sid in sids:
		if (sid is None):
			continue
		try:
			data = sids[sid]
			yeelight = pyyeelight.YeelightBulb(sid)
			name = data.get("name", sid)
			model = data.get("model", "light")
			yeelight.__name__ = name #add name
			bulb = LightBulbState(sid, model, yeelight)
			bulb.update_properties()
			lamps.append(bulb)
		except Exception as e:
			_LOGGER.error('Connection to ', str(sid) , ' error:', str(e))
	return lamps

def wait():
	global processNow
	for x in range(1,10):
		if (processNow):
			processNow=False
			break
		time.sleep(QUERY_TIME/10)

def process_lamp_states(client):
	global bulbs
	while True:
		wait();
		try:
			for bulb in bulbs:
				hashold = bulb.hash()
				bulb.update_properties(force=True)
				hashnew = bulb.hash()
				# _LOGGER.debug(str(bulb.name) + " ===> " + hashold + "-" + hashnew)

				if (hashold != hashnew):
					_LOGGER.info("!!!! " + bulb.name + ":" + hashold + "->" + hashnew)
					data = {'status':bulb.status, 'ct':bulb.color_temperature, 'bright':bulb.bright, 'rgb':bulb.rgb}
					client.publish(bulb.model, bulb.name, data)
		except Exception as e:
			_LOGGER.error('Error while sending from gateway to mqtt: ', str(e))

def process_mqtt_messages(client):
	global processNow, bulbs
	while True:
		try: 
			data = client._queue.get()
			_LOGGER.debug("data from mqtt: " + format(data))

			sid = data.get("sid", None)
			param = data.get("param", None)
			value = data.get("value", None)
			for bulb in bulbs:
				if (bulb.ip != sid):
					continue
				bulb.process_command(param, value)
				processNow=True

			client._queue.task_done()
		except Exception as e:
			_LOGGER.error('Error while sending from mqtt to gateway: ', str(e))

if __name__ == "__main__":
	_LOGGER.info("Loading config file...")
	config=yamlparser.load_yaml('config/config.yaml')

	_LOGGER.info("Init mqtt client.")
	client = mqtt.Mqtt(config)
	client.connect()
	#only this devices can be controlled from MQTT
	client.subscribe("light", "+", "+", "set")
	
	bulbs = init_lamps(config)

	t1 = threading.Thread(target=process_lamp_states, args=[client])
	t1.daemon = True
	t1.start()

	t2 = threading.Thread(target=process_mqtt_messages, args=[client])
	t2.daemon = True
	t2.start()

	while True:
		time.sleep(10)