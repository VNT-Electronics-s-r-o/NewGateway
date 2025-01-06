import os
import json
import serial
import subprocess
import configparser
import serial.tools.list_ports

class UploadSTM:

	def __init__(self, device):
		self.device = device

	def upload_stm(self):
		# 1. load config
		# 2. find + connect to STM
		# 3. erase STM
		# 4. upload startloader
		# 5. upload bootloader
		# 6. upload application
		# 7. write EEPROM (in data/)
		
		self.load_config()
		if not self.find_and_connect_st():
			print('No STM found')
			return False, 'Error while searching for STM'
		
		if not self.erase_st():
			print('Error erasing STM')
			return False, 'Error while erasing STM'
		
		if not self.upload_startloader():
			print('Error uploading startloader')
			return False, 'Error while uploading startloader'
		
		if not self.upload_bootloader():
			print('Error uploading bootloader')
			return False, 'Error while uploading bootloader'
		
		if not self.upload_application():
			print('Error uploading application')
			return False
		
		if not self.write_to_eeprom():
			print('Error writing to EEPROM')
			return False, 'Error while writing to eeprom'
		
		return True, 'Process finished successfully'

	def find_and_connect_st(self):
		found = self.run_command('-List')
		if not found:			
			return False
		

		connected = self.run_command('-c', 'ID=0', 'SWD', 'UR', f'freq={self.frequency}', 'V', '-NoPrompt')
		if not connected:
			return False

		print('Connected to STM with result: ' + str(connected))
		return True
	
	def erase_st(self):
		# check if read out protection is enabled
		read_out_protection = self.run_command('-c', 'ID=0', 'SWD', 'UR', f'freq={self.frequency}', '-OB', 'RDP=0', '-V', '-NoPrompt', '-Run')
		if not read_out_protection:
			return False

		print('Erased STM with result: ' + str(read_out_protection))


		erased_eeprom = self.run_command('-c', 'ID=0', 'SWD', f'freq={self.frequency}', '-SE', 'ed1', '-V', '-NoPrompt', '-Run')
		if not erased_eeprom:
			return False
		
		erased_chip = self.run_command('-c', 'ID=0', 'SWD', f'freq={self.frequency}', '-ME', '-V', '-NoPrompt', '-Run')
		if not erased_chip:
			return False
		
		return True
	
	def upload_startloader(self):
		# first check if file exists
		if not os.path.exists(self.startloader):
			return False
		
		uploaded = self.run_command('-c', 'ID=0', 'SWD', 'UR', f'freq={self.frequency}', '-P', self.startloader, f'0x{self.start_address}', '-V', '-NoPrompt', '-Run')
		if not uploaded:
			return False

		return True

	def upload_bootloader(self):
		# first check if file exists
		if not os.path.exists(self.bootloader):
			return False
		
		uploaded = self.run_command('-c', 'ID=0', 'SWD', 'UR', f'freq={self.frequency}', '-P', self.bootloader, f'0x{self.boot_address}', '-V', '-NoPrompt', '-Run')
		if not uploaded:
			return False

		return True
	
	def upload_application(self):
		# first check if file exists
		if not os.path.exists(self.application):
			return False
		
		uploaded = self.run_command('-c', 'ID=0', 'SWD', 'UR', f'freq={self.frequency}', '-P', self.application, f'0x{self.app_address}', '-V', '-NoPrompt', '-Run')
		if not uploaded:
			return False

		return True
	
	def write_to_eeprom(self):
		# first check if file exists
		if not os.path.exists(self.eeprom_file):
			return False
		
		# read eeprom file
		with open(self.eeprom_file, 'r') as file:
			eeprom_data = json.load(file)

		for item in eeprom_data:
			address = item.get('address')
			value = item.get('value')
			if value:
				if value.isdigit():
					value = int(value)
					if value < 256:
						value = f'0x{value:02x}'
					else:
						value = f'0x{value:X}'
				else:
					byte_value = value.encode('utf-8')
					value = ''.join(f'{byte:02X}' for byte in byte_value)
					value = f'0x{value}'
				
				result = self.write_value(address, value)
				if not result:
					return False
				else:
					print(f'Wrote value {value} at address {address}')
					print('Result: ' + str(result))
			else:
				print('No value found in EEPROM file, continuing...')
				continue
		
		return True
	
	def write_value(self, address, value):
		clean_value = value.lower().replace('0x', '')
		if len(clean_value) % 2 != 0:
			clean_value = '0' + clean_value

		byte_data = bytes.fromhex(clean_value)
		reversed_byte_data = byte_data[::-1]

		print(f"Numeric address: {int(address, 16)}")
		print(f"Original Hex Value: {value}")
		print(f"Byte Data (original): {byte_data}")
		print(f"Reversed Byte Data: {reversed_byte_data}")

		if len(byte_data) <= 1: # 8-bit value
			return self.run_command('-c', 'ID=0', 'SWD', f'freq={self.frequency}', '-w8', address, value)
		elif len(byte_data) <= 4: # 32-bit value
			return self.run_command('-c', 'ID=0', 'SWD', f'freq={self.frequency}', '-w32', address, value)
		else:
			return self.write_byte_by_byte(address, reversed_byte_data, byte_data)
	
	def write_byte_by_byte(self, address, reversed_byte_data, byte_data):
		num_address = int(address, 16)
		if address == '0x08080008':
			byte_data = reversed_byte_data

		for i, byte in enumerate(byte_data):
			byte_address = f'0x{num_address + i:08X}'
			byte_hex = f'0x{byte:02X}'
			print(f'Writing byte {i} at address {byte_address} with value {byte_hex}')
			result = self.run_command('-c', 'ID=0', 'SWD', f'freq={self.frequency}', '-w8', byte_address, byte_hex)
			if not result:
				return False
		return True

	def run_command(self, *args):
		print('Running command: ', args)
		cmd = [self.stlink_path] + list(args)
		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

		print('run_cmd result: ', result)

		if 'No ST-LINK detected!' in result.stdout:
			return False
		elif 'Elf Loader could not be transfered to device.' in result.stdout:
			return False
		elif 'Read out protection is activated.' in result.stdout:
			return False
		elif 'Error occured during program operation!' in result.stdout:
			return False
		elif 'Unexpected error' in result.stdout:
			return False
		
		if result.returncode == 0:
			return True
	
		return True
		

	def load_config(self):
		# load configuration from file only from the STM section
		config = configparser.ConfigParser()
		config.read('config.ini')
		self.stm_dir = config['STM']['STM_Directory']
		self.bootloader = config['STM']['Bootloader_Path']
		self.startloader = config['STM']['Startloader_Path']
		self.app_address = config['STM']['Flash_App_Address']
		self.boot_address = config['STM']['Flash_Boot_Address']
		self.start_address = config['STM']['Flash_Start_Address']
		self.frequency = config['STM']['Frequency']
		self.stlink_path = config['STM']['STLink_Path']

		if self.device == 'GW100':
			self.application = config['STM']['App_Path_GW100']
			self.eeprom_file = 'data/data_gw_100.json'
		elif self.device == 'FM20':
			self.application = config['STM']['App_Path_FM20']
			self.eeprom_file = 'data/data_fm_20.json'
		elif self.device == 'Agrifence':
			self.application = config['STM']['App_Path_Agrifence']
			self.eeprom_file = 'data/data_gw_agrifence.json'
		elif self.device == 'Zap!':
			self.application = config['STM']['App_Path_Zap']
			self.eeprom_file = 'data/data_gw_zap.json'
		else:
			self.application = config['STM']['App_Path_Default']
			self.eeprom_file = 'data/data_gw_100.json'



	
