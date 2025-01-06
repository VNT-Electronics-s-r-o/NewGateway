

import re
import io
import sys
import time
import serial
import serial.tools.list_ports
import esptool
import subprocess
import configparser

CONDA_PYTHON = 'C:\\Users\\Pruvodky\\anaconda3\\envs\\newGWEnv\\python.exe'


class UploadESP:
	def __init__(self, log_signal, device):
		self.device = device
		self.log_signal = log_signal
		self.esptool = esptool
		print('ESPTool: ', self.esptool)

	def upload_esp_process(self):
		self.log_signal.emit('Nahrávání ESP zahájeno', 'I')
		if not self.load_config():
			return False, 'Nepodařilo se načíst konfiguraci'
		if not self.find_and_connect_esp():
			return False, f'ESP nebylo nalezeno na portu: {self.port}'
		if not self.erase_esp():
			return False, 'ESP se nepodařilo smazat!'
		time.sleep(5)
		if not self.program_esp():
			return False, 'Nahrávání ESP ne nezdařilo'

		# 1. load config
		# 2. find + connect to ESP 
		# 3. erase ESP
		# 4. program chip

		print('Uploading ESP finished sucessfully')
		return True, 'Uploading finished without an error'
	
	def get_ports(self):
		ports = serial.tools.list_ports.comports()
		for port, desc, hwid in sorted(ports):
			print(f'Port: {port}, Desc: {desc}, HWID: {hwid}')
			if "USB Serial Port" in desc:
				print('Port found: ', port)
				return port

		print("No matching ports found")
		return False

	def find_and_connect_esp(self):
		try:
			new_port = self.get_ports()
			if new_port:
				print('New port found: ', new_port)
				self.port = new_port

			cmd = [CONDA_PYTHON, '-m', 'esptool', '--port', self.port, 'read_mac']
			try:
				result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
			except Exception as e:
				print('Error while looking for ESP (subprocess.check_output): ', e)
				return False
				print('ESP found: ', result)

			# extracting the mac and bluetooth
			esp_mac = re.search(r'MAC: ([0-9a-fA-F:]+)', result)
			print('ESP MAC: ', esp_mac)
			if esp_mac:
				esp_mac = esp_mac.group(1)
			return True
		
		except subprocess.CalledProcessError as e:
			print(f'Error while searching for ESP: {e.output.decode()}')
			return False

		except Exception as e:
			print('Error while searching for ESP: ', e)
			return False


	def program_esp(self):
		try:
			#original_stderr = sys.stderr  # Save the original stderr
			#custom_stderr = io.StringIO()

			original_stdout = sys.stdout
			sys.stdout = self

			cmd = [
				'--port', self.port,
				'--baud', self.baudrate,
				'--before', 'default_reset',
				'--after', 'hard_reset',
				'--chip', 'esp32',
				'write_flash',
				'--flash_mode', 'dio',
				'--flash_freq', '40m',
				'--flash_size', 'detect',
				self.ptable_address, self.ptable_path,
				self.ota_address, self.ota_path,
				self.boot_address, self.boot_path,
				self.app_address, self.app_path,
			]

			esptool.main(cmd)
			#sys.stderr = original_stderr

			#error_output = custom_stderr.getvalue()
			return True
		except Exception as e:
			#sys.stderr = original_stderr
			print('Error while programming ESP', e)
			return False
		finally:
			sys.stdout = original_stdout

	def erase_esp(self):
		try:
			original_stdout = sys.stdout
			sys.stdout = self
			cmd = [
				'--baud', self.baudrate,
				'--port', self.port,
				'erase_flash'
			]
			

			esptool.main(cmd)
			
			return True
		except Exception as e:
			print(f'Error while erasing ESP: {e}')
			
			return False
		finally:
			sys.stdout = original_stdout
	
	def close_port(self):
		
			try:
				if hasattr(self, 'serial_connection') and self.serial_connection:
					self.serial_connection.close()
					print(f'Port {self.port} closed successfully')
				else:
					print('There is no active connection to close')
				
			except Exception as e:
				print(f'Error while closing port {self.port}: {e}')


	def load_config(self):
		config = configparser.ConfigParser()
		config.read('config.ini')

		self.esp_dir = config['ESP']['ESP_Directory']

		if self.device == 'GW100':
			self.app_path = config['ESP']['App_Path_GW100']
		elif self.device == 'FM20':
			self.app_path = config['ESP']['App_Path_FM20']
		elif self.device == 'Agrifence':
			self.app_path = config['ESP']['App_Path_Agrifence']
		elif self.device == 'Zap!':
			self.app_path = config['ESP']['App_Path_Zap']
		else:
			self.app_path = config['ESP']['App_Path_Default']

		self.boot_path = config['ESP']['Bootloader_Path']
		self.ota_path = config['ESP']['Ota_Path']
		self.ptable_path = config['ESP']['Partition_Table_Path']
		self.app_address = config['ESP']['Flash_App_Address']
		self.boot_address = config['ESP']['Flash_Boot_Address']
		self.ota_address = config['ESP']['Flash_Ota_Address']
		self.ptable_address = config['ESP']['Flash_Partition_Table_Address']
		self.port = config['ESP']['COM_Port']
		self.baudrate = config['ESP']['Baudrate']

		return True
	
	@staticmethod
	def remove_ansi(msg):
		try:
			ansi_escape = re.compile(r'\x18\[[0-9]*[ -/]*[@-~]')
			return ansi_escape.sub('', msg)
		except TypeError:
			return msg
	
	def write(self, msg):
		clear_msg = self.remove_ansi(msg)
		if 'Writing at' and '%' in clear_msg:
			self.log_signal.emit(clear_msg, 'I')

		sys.__stdout__.write(clear_msg)

	def isatty(self):
		return False
	
	def flush(self):
		pass



