import time
import pyvisa as visa

class PSUControll:
	def __init__(self):
		self.rm = visa.ResourceManager()
		self.instrument = None
		self.connected = False
		

	def connect_to_psu(self, ip_address='192.168.20.126'):
		try:
			self.instrument = self.rm.open_resource(f'TCPIP::{ip_address}::5025::SOCKET')
			print('self.instrument is: ', self.instrument)
			self.instrument.write_termination = '\n'
			self.instrument.read_termination = '\n'
			self.instrument.write('*IDN?')

			response = self.instrument.read()
			print(f'[INFO] Connected to PSU: {response}')
			self.connected = True
			return True
		except Exception as e:
			print(f'[ERROR] while connecting to PSU: {e}')
			return False
	
	def disconnect_psu(self):
		try:
			if self.instrument is not None and self.rm is not None:
				self.rm.close()
				self.instrument = None
				self.connected = False
				print('[INFO] Disconnected from PSU')
				return True
			else:
				print('[INFO] PSU already disconnected or not connected at all')
				return True
		except Exception as e:
			print(f'[ERROR] while disconnecting from PSU: {e}')
			return False


	def set_volt_curr(self, channel, voltage, current):
			if voltage == 0 and current == 0:
				self.turn_channel(channel, False)
			else:
				if current == 0 and voltage > 0:
					current = 0.5

				response_1 = self.send_command('INST:SEL OUT{}'.format(channel))
				response_2 = self.send_command('APPLY {:.2f},{:.2f}'.format(voltage, current))
				time.sleep(1)
				
				print(f'[INFO] Setting voltage and current to {voltage}V and {current}A')
				print(f'[INFO] Response 1 (set_volt_curr): {response_1}')
				print(f'[INFO] Response 2 (set_volt_curr): {response_2}')

				if response_1 and response_2:
					print(f'[INFO] Voltage and current set to {voltage}V and {current}A')
					# make sure to turn on the channel!
					self.turn_channel(channel, True)
					time.sleep(1)
				else:
					return False

				vol = self.get_voltage(channel)
				print('Measured voltage (set_volt_curr): ', float(vol))

				curr = self.get_current(channel)
				print('Measured current (set_volt_curr): ', curr)
				return True


	def send_command(self, command):
		if self.instrument is not None:
			response = self.instrument.write(command)
			print(f'[INFO] Sent command: {command}')
			return response
		else:
			print(f'[ERROR] PSU not connected')
			return False

	def read_response(self, command):
		try:
			self.instrument.write(command)
			response = self.instrument.read()
			print(f'[DEBUG] Float Response: {float(response)}')
			return float(response)
		except Exception as e:
			print('Error while reading cmd: ',e)
			return False
	

	def get_voltage(self, channel):
		response_1 = self.send_command('INST:SEL OUT{}'.format(channel))
		print(f'[INFO] Response 1 (get_voltage): {response_1}')

		result = self.read_response('MEAS:VOLT?')
		#result = round(result, 1)
		return result
		

	def get_current(self, channel):
		response_1 = self.send_command('INST:SEL OUT{}'.format(channel))
		print(f'[INFO] Response 1 (get_current): {response_1}')
		result = self.read_response('MEAS:CURR?')
		result = float(result)
		return result

	def set_voltage(self, channel, voltage):
		response_1 = self.send_command('INST:SEL OUT{}'.format(channel))
		response_2 = self.send_command('SOUR:VOLT {:.2f}'.format(voltage))
		print(f'[INFO] Response 1: {response_1}')
		print(f'[INFO] Response 2: {response_2}')

		return True

	def set_current(self, channel, current):
		response_1 = self.send_command('INST:SEL OUT{}'.format(channel))
		response_2 = self.send_command('SOUR:CURR {:.2f}'.format(current))
		print(f'[INFO] Response 1: {response_1}')
		print(f'[INFO] Response 2: {response_2}')

		return True
	
	def turn_channel(self, channel, status):
		self.send_command('INST:SEL OUT{}'.format(channel))
		if not self.send_command('OUTP {}'.format('1' if status else '0')):
			return False
		return True

	def start_psu(self, ip_address):
		try:
			print('Start PSU in psu.py')
			if self.connected:
				print('[INFO] PSU already connected')
				# set current, voltage and turn off the battery
				if not self.set_volt_curr(1, 14, 0.5):
					print('[ERROR] Could not set voltage and current')
					return False
				self.turn_channel(2, False)
				return True

			result = self.connect_to_psu(ip_address)
			if not result or not self.connected:
				print('[ERROR] Could not connect to PSU')
				return False
			
			print('[INFO] Connected to PSU, setting voltage and current')
			if not self.set_volt_curr(1, 14, 0.5): 
				print('[ERROR] Could not set voltage and current')
				return False
			
			self.turn_channel(1, True)
			# turn off the battery
			self.turn_channel(2, False)
			return True
		except Exception as e:
			print('Error while starting psu (psu.py)', e)
			return False

	def start_measuring(self):
		self.failed_tests = []

		# 0. - check if psu is connected first
		# 1. Reset Desk reset_desk + turn on main power and battery, turn off main power
		# 2. Test Low Power Detection test_low_power_detection
		# 3. Test Rise Edge
		# 4. Test Battery Charging
		# 5. Test Max Power Consumption
		# 6. Final Reset
		print('[INFO] Checking connection')
		# 0 test - to check connection
		if not self.connected:
			if not self.connect_to_psu():
				return False, 'Nepodařilo se připojit ke zdroji'
		
		print('[INFO] Starting measuring')
		# 1st Test
		if not self.reset_desk():
			print('[ERROR] Could not reset desk')
			self.failed_tests.append('1 - desk_reset')
			#return False, 'Reset desky selhal'
		
		# 2nd Test
		if not self.test_low_power_detection():
			print('[ERROR] Low power detection test failed')
			self.failed_tests.append('2 - low_power_detection')
			#return False, 'Test detekce nízké spotřeby selhal '
		
		# 3rd Test
		if not self.test_rise_edge():
			print('[ERROR] Rise edge test failed')
			self.failed_tests.append('3 - rise_edge')
			#return False, 'Test náběžné hrany selhal'
		
		# 4th Test
		if not self.test_battery_charging():
			print('[ERROR] Battery charging test failed')
			self.failed_tests.append('4 - battery_charging')
			#return False, 'Test baterie selhal'
		
		# 5th Test
		if not self.test_power_consuption():
			print('[ERROR] Max power consumption test failed')
			self.failed_tests.append('5 - max_power')
			#return False, 'Test maximální spotřeby selhal'
		
		# 6th Test
		if not self.final_reset():
			print('[ERROR] Final reset failed')
			self.failed_tests.append('6 - final_reset')
			#return False, 'Konečný reset desky selhal'
		if len(self.failed_tests) == 0:
			return True, 'Všechny testy proběhly úspěšně'
		else:
			return False, self.failed_tests
	
	def power_on_off(self, channel, value=0):
		try:
			self.set_voltage(channel, value)
			if value != 0:
				self.set_current(channel, 0.5)
				response = self.turn_channel(channel, True)
			else:
				response = self.turn_channel(channel, False)
			print('Power ON/OFF response: ', response)
			time.sleep(1)
			self.set_current(channel, value)

			measured_voltage = self.get_voltage(channel)
			float_measured_voltage = float(measured_voltage)

			measured_current = self.get_current(channel)
			float_measured_current = float(measured_current)

			if (abs(value - float_measured_voltage) < 0.5) and value != 0:
				print(f'Voltage and current on channel {channel} set to voltage: {float_measured_voltage} and current {float_measured_current}')
				return True
			if float_measured_voltage <= 0.1 and value == 0:
				print(f'Voltage and current on channel {channel} set to voltage: {float_measured_voltage} and current {float_measured_current}')
				return True
		except Exception as e:
			print('Error while power on/off: ', e)
			return False

	def reset_desk(self):
		try:
			self.turn_channel(1, False)
			self.turn_channel(2, False)

			# wait for it to turn off
			time.sleep(0.5)
			
			# turn on both battery and main power
			self.power_on_off(2, 8.3)
			self.power_on_off(1, 14)

			# wait for it to take effect
			time.sleep(0.5)

			# turn off main power, keep the battery on
			self.turn_channel(1, False)
			time.sleep(0.5)
			return True
		except Exception as e:
			print('Error while reseting desk: ', e)
			return False
	
	def test_low_power_detection(self):
		try:
			# make sure the battery is off
			self.turn_channel(1, False)

			measure = True
			current = 0
			timeout = 0

			while measure:
				time.sleep(1)

				# if current is less than 2mA, it's ok
				current = self.get_current(2)
				current = current * 1000
				print(f'[INFO] Current (test_low_power_detection): {current} mA')
				if (current < 3):
					measure = False
					print('[INFO] Low power detection test passed')
					return True
				
				timeout += 1
				if timeout > 16:
					print('[ERROR] Low power detection test failed')
					measure = False
					return False

		except Exception as e:
			print(f'[ERROR] while testing low power detection: {e}')
			return False
	
	def test_rise_edge(self):
		try:
			current = 0
			if not self.set_volt_curr(1, 14, 0.5):
				print('[ERROR] Could not set voltage and current')
				return False
			
			time.sleep(5)

			current = self.get_current(1)
			current = current * 1000
			print('[DEBUG] - Test Rise Edge Current: ', current)
			if (current < 30):
				print(('[ERROR] Rise edge test failed'))
				return False
			else:
				print('[INFO] Rise edge test passed')
				return True
		
		except Exception as e:
			print(f'[ERROR] while testing rise edge: {e}')
			return False
		
	def test_battery_charging(self):
		try:

			measure = True
			max_voltage = 0
			timeout = 0
			voltage = 0

			while measure:
				time.sleep(1)
				voltage = self.get_voltage(2)
				if voltage > max_voltage:
					max_voltage = voltage
				else:
					max_voltage = max_voltage
				
				print(f'[INFO] Voltage: {voltage}V')
				print(f'[INFO] Max Voltage: {max_voltage}V')

				if (max_voltage > 11 and max_voltage < 12):
					measure = False
					print('[INFO] Battery charging test passed')
					return True
				
				timeout += 1
				if timeout > 16:
					print('[ERROR] Battery charging test failed')
					measure = False
					return False
		except Exception as e:
			print(f'[ERROR] while testing battery charging: {e}')
			return False
		
	def test_power_consuption(self):
		try:
			measure = True
			current = 0
			max_current = 0
			max_current = float(max_current)
			timeout = 0

			while measure:
				time.sleep(1)
				current = self.get_current(1)
				if current > max_current:
					max_current = current
				print('Max current: ', max_current)
				
				if (max_current * 1000) > 200:
					measure = False
					print('[ERROR] Max power consumption test failed')
					return False
				timeout += 1
				if timeout > 5:
					measure = False
					print('[INFO] Max power consumption test passed')
					return True

		except Exception as e:
			print(f'[ERROR] while testing power consumption: {e}')
			return False
		
	def final_reset(self):
		try:
			self.power_on_off(1,0)
			self.power_on_off(2,0)
			time.sleep(1)
			if self.set_volt_curr(1, 14, 0.5):
				print('[INFO] Final reset done')
				return True
			else:
				print('[ERROR] Final reset failed')
				return False
		except Exception as e:
			print(f'[ERROR] while final reset: {e}')
			return False





