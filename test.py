import serial
import serial.tools.list_ports

def get_ports():
	ports = serial.tools.list_ports.comports()
	print('Available ports: ', ports)
	for port, desc, hwid in sorted(ports):
		if "USB Serial Port" in desc:
			print('Port found')
			return port
	print("No matching ports found")

get_ports()
#COM15: USB Serial Port (COM15) [USB VID:PID=0403:6001 SER=A50285BIA]