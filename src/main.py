import pyyeelight
import paho.mqtt.client as mqtt
import os
import time
import threading
from lightbulbstate import LightBulbState

MQTT_SERVER = os.getenv('MQTT_SERVER', "")
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_USER = os.getenv('MQTT_USER', "")
MQTT_PASS = os.getenv('MQTT_PASS', "")
QUERY_TIME = os.getenv('QUERY_TIME', 3)
PREFIX = os.getenv('PREFIX', 'home')

ips = dict({
	'192.168.1.51':'main-mono',
	'192.168.1.54':'main-color', 
	'192.168.1.52':'kitchen', 
	'192.168.1.53':'hall'
})
bulbs=[]
processNow = False
 
PATH_FMT = PREFIX + "/{model}/{sid}/{prop}" # short_id or sid ?

def prepare_mqtt():
	print("Connecting to MQTT server", MQTT_SERVER, ":", MQTT_PORT, "with username", MQTT_USER,":",MQTT_PASS)
	client = mqtt.Client()
	if (MQTT_USER != "" and MQTT_PASS != ""):
		client.username_pw_set(MQTT_USER, MQTT_PASS)
	client.connect(MQTT_SERVER, MQTT_PORT, 60)
 
	return client
 
def push_data(client, model, sid, data):
	for key, value in data.items():
		path = PATH_FMT.format(model=model,
							   sid=sid,
							   prop=key)
		client.publish(path, payload=value, qos=0, retain=True)

def init_lamps():
	lamps=[]
	for ip in ips:
		try:
			yeelight = pyyeelight.YeelightBulb(ip)
			yeelight.__name__ = ips[ip] #add name
			bulb = LightBulbState(ip, yeelight)
			bulb.update_properties()
			lamps.append(bulb)
		except Exception as e:
			print('Connection to ', str(ip) , ' error:', str(e))
	return lamps


def refresh_bulb_states(data_callback):
	for bulb in bulbs:
		try:
			hashold = bulb.hash()
			bulb.update_properties(force=True)
			hashnew = bulb.hash()
			# print(str(bulb.name),hashold, hashnew)

			if (hashold != hashnew):
				print("!!!! ", bulb.name, ":", hashold, "->", hashnew)
				if data_callback is not None:
					data = {'status':bulb.status, 'ct':bulb.color_temperature, 'bright':bulb.bright, 'rgb':bulb.rgb}
					data_callback("lamp", bulb.name, data)
		except Exception as e:
			print('Connection to ', str(bulb.name) , ' error:', str(e))

def on_mqtt_message(client, userdata, msg):
	global processNow
	print(msg.topic+" "+str(msg.payload))
	parts = msg.topic.split("/")
	if (len(parts) != 5):
		return
	name = parts[2] #name part
	param = parts[3] #param part
	value = (msg.payload).decode('utf-8')

	for bulb in bulbs:
		if (bulb.name != name):
			continue
		bulb.process_command(param, value)
		processNow=True

def on_connect(client, userdata, rc):
	client.subscribe(PREFIX + "/lamp/+/+/set")

def refresh_loop(client):
	global processNow
	cb = lambda m, s, d: push_data(client, m, s, d)
	while True:
		refresh_bulb_states(cb)
		for x in range(1,10):
			if (processNow):
				processNow=False
				break
			time.sleep(QUERY_TIME/10)

if __name__ == "__main__":
	client = prepare_mqtt()
	bulbs = init_lamps()
	client.on_message = on_mqtt_message
	client.on_connect = on_connect

	#start thread for lamp refresh loop
	t1 = threading.Thread(target=refresh_loop, args=[client])
	t1.start()

    # and process mqtt messages in this thread
	client.loop_forever()