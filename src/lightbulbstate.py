import pyyeelight
import os
import time
import threading

class LightBulbState:
	bright = 0
	color_temperature = 0
	status = "off"
	rgb = 0
	
	ip = ""
	name = ""
	yeelight = None # yeelight object

	def __init__(self, ip, yeelightObj):
		self.yeelight = yeelightObj
		self.name = yeelightObj.__name__
		self.ip = ip

	def update_properties(self, force = False):
		if (force):
			self.yeelight.refresh_property()
		prop = self.yeelight.get_all_properties()
		# print(prop)
		self.bright = prop["bright"]
		self.color_temperature = prop["ct"]
		self.status = prop["power"]
		self.rgb = prop["rgb"]

	def hash(self):
		return str(self.bright) + ":" + str(self.color_temperature) + ":" + str(self.status) + ":" + str(self.rgb)
	
	def is_int(self, x):
		try:
			tmp = int(x)
			return True
		except Exception as e:
			return False

	def process_command(self, param, value):
		try:
			if (param == 'status'):
				if (value == "on"):
					print("Turning on bulb", self.name)
					self.yeelight.turn_on()
				if (value == "off"):
					print("Turning off bulb", self.name)
					self.yeelight.turn_off()
			if (param == 'bright' and self.is_int(value)):
				print("Setting brightness of bulb", self.name, 'to', value)
				self.yeelight.set_brightness(int(value))
			if (param == 'ct' and self.is_int(value)):
				print("Setting temperature of bulb", self.name, 'to', value)
				self.yeelight.set_color_temperature(int(value))
			if (param == 'rgb' and self.is_int(value)):
				intval = int(value)
				Blue =  intval & 255
				Green = (intval >> 8) & 255
				Red =   (intval >> 16) & 255
				print("Setting rgb of bulb", self.name, 'to', value)
				self.yeelight.set_rgb_color(Red, Green, Blue)
		except Exception as e:
			print ('Error while set value of bulb', self.name , ' error:', e)