import time
import serial
import serial.tools.list_ports
import binascii
import threading


# RF USB CONTROL SETTINGS
SNYC_PACKAGE = 0x2DD4
NAME = 'Silicon Labs'

# SERIAL PORT SETTINGS
BAUD_RATE = 9600
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
BYTE_SIZE = serial.EIGHTBITS

#PINS 
RED_LED = 1
GREEN_LED = 2
PROGRAMMING_MODE = 3
ESP_ON_OFF = 4

SYNC_HEADER = b'\x2D\xD4'
PACKET_LENGTH = 9


class Crc8:
	"""CRC8 calculation utility class"""
	def __init__(self, polynomial=0xD5):
		self.table = self.generate_table(polynomial)
	
	def generate_table(self, polynomial):
		table = [0] * 256
		for i in range(256):
			crc = i
			for _ in range(8):
				if crc & 0x80:
					crc = (crc << 1) ^ polynomial
				else:
					crc <<= 1
			table[i] = crc & 0xFF
		return table
		
	def calculate_crc(self, data):
		crc = 0
		for byte in data:
			crc = self.table[crc ^ byte]
		return crc
	
class SerialConnection:
	"""Serial connection utility class"""
	def __init__(self, device_name='Silicon Labs'):
		self.device_name = device_name
		self.serial_connection = None
		self.port_open = False
		self.lock = threading.Lock()
	
	def find_port(self):
		"""Find the port for the device"""
		for port in serial.tools.list_ports.comports():
			if port.manufacturer == self.device_name:
				return port.device
		return None

	def open_port(self):
		"""Open the serial port"""
		try:
			port = self.find_port()
			if port:
				if self.port_open == True:
					print('[DEBUG] Tester already connected')
					return True
				self.serial_connection = serial.Serial(port, baudrate=BAUD_RATE, timeout=1, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
				self.port_open = True
				print(f'[INFO] Opened port: {port}')
				return True
			else:
				print(f'[ERROR] Device {self.device_name} not found')
				return False
		except Exception as e:
			print(f'[ERROR] Error while opening port: {e}')
			return False
		
	def close_port(self):
		"""Close the serial port"""
		while self.lock:
			if self.serial_connection and self.serial_connection.is_open:
				# Reset buffers and close the port
				self.serial_connection.reset_input_buffer()
				self.serial_connection.reset_output_buffer()
				self.serial_connection.flush()

				self.serial_connection.close()
				self.port_open = False
				print(f'[INFO] Port has been closed')
				return True
			else:
				print(f'[ERROR] Port is not open')
				return False

	def send_data(self, data):
		"""Send data over the serial port"""
		if self.port_open and self.serial_connection:
			self.serial_connection.write(data)
			print(f'[INFO] Sent data: {data}')
				
		else:
			print(f'[ERROR] Port is not open')
	
	def read_data(self, size):
		"""Read data from the serial port"""
		if self.port_open and self.serial_connection:
			with self.lock:
				return self.serial_connection.read(size)
		else:
			print(f'[ERROR] Port is not open')
			return None
		
	def check_port(self):
		if not self.port_open:
			return False
		return True
	
class RfUSBControl:
	"""RF USB Control for handling packets and auxiliary pins."""
	def __init__(self):
		self.serial_connection_class = SerialConnection(device_name="Silicon Labs")
		self.crc8 = Crc8()
		self.stop_listening = False

	def start_listening(self):
		if not self.serial_connection_class.open_port():
			print('[ERROR] Connection to testing device failed!')
			return False
		else:
			self.listen_thread = threading.Thread(target=self.listen)
			self.listen_thread.start()
			return True

	def send_packet(self, payload):
		"""Constructs and sends a packet with the given payload."""
		header = bytearray([len(payload), 0, 0])
		crc_header = self.crc8.calculate_crc(header)
		header.append(crc_header)

		packet = bytearray(SYNC_HEADER + header + payload)
		crc_packet = self.crc8.calculate_crc(packet)
		packet.append(crc_packet)

		self.serial_connection_class.send_data(packet)

	def set_aux_pin(self, pin, state):
		"""Sets the state of the given auxiliary pin."""
		payload = bytearray([pin, state])
		self.send_packet(payload)
		return True
	
	def set_aux_blinking(self, pin, blink_time):
		payload = bytearray(5)
		payload[0] = (pin + 0x07)
		payload[1:5] = blink_time.to_bytes(4, byteorder = 'little')
		self.send_packet(payload)
		return True

	def reset_pin(self, pin, state, delay):
		"""Sets the state of the given auxiliary pin for a specified duration."""
		self.set_aux_pin(pin, not state)
		time.sleep(delay)
		self.set_aux_pin(pin, state)

	def listen(self):
		"""Listens for incoming data on the serial port."""
		buffer = bytearray()
		print("[INFO] Starting listener")

		while not self.stop_listening:
			data = self.serial_connection_class.read_data(PACKET_LENGTH)
			if data:
				buffer.extend(data)

				while len(buffer) >= PACKET_LENGTH:
					packet = buffer[:PACKET_LENGTH]
					sync_header = packet[:2]

					if sync_header == SYNC_HEADER:
						crc_calculated = self.crc8.calculate_crc(packet[:-1])
						if crc_calculated == packet[-1]:
							print(f"[INFO] Valid packet received: {packet}")
							self._process_packet(packet)
						else:
							print("[ERROR] Invalid CRC, discarding packet")
						buffer = buffer[PACKET_LENGTH:]
					else:
						print("[WARNING] Sync header not found, shifting buffer")
						buffer.pop(0)

		print("[INFO] Listener stopped")

	def _process_packet(self, packet):
		"""Processes a received packet."""
		payload = packet[5:-1]
		if payload == b'\x06\xD3':
			print("[INFO] Start work signal detected")
		elif payload == b'\x07\x05y':
			print("[INFO] New device signal detected")

	def closing_app(self):
		try:
			if not self.serial_connection_class.check_port():
				return True
			self.set_aux_pin(1,0)
			self.set_aux_pin(2,0)
			self.set_aux_pin(3, 0)
			self.set_aux_pin(4, 0)
			self.stop_listening = True

			# stop listening thread:
			self.serial_connection_class.close_port()
			return True
		except Exception as e:
			print('Error when closing ports: ', e)
			return False

# example usage
'''
# Open serial port
serial_conn = SerialConnection(device_name="Silicon Labs")
if serial_conn.open_port():
    rf_control = RfUSBControl(serial_conn)
    rf_control.listen()

# Set auxiliary pins
rf_control.set_aux_pin(1, True)  # Turn on pin 1
rf_control.set_aux_blinking(2, 5000)  # Blink pin 2 for 5000 ms
rf_control.reset_pin(1, True, 2)  # Reset pin 1 after 2 seconds

# Close serial port
serial_conn.close_port()

'''