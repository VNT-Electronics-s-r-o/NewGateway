import os
import sqlite3

#SAVE_PATH = r'\\192.168.1.95\\Vyroba\\zal\\GWTest'
MAIN_TABLE = 'main_data'
DEVICE_TABLE = 'device_data'
SAVE_PATH = r'\\192.168.1.95\\Vyroba\\fencee\\GW_Data'

class DataSaver:
	def __init__(self):
		print('Data Saver initialised')

	def save_data(self, data):
		#protocol_number = data["protocol_number"]
		device = data['device']
		desk_id = data['desk_id']
		if desk_id == '':
			desk_id = 'test_123'

		values = (
				data['device'], 
				data['username'], 
				data['role'], 
				data['protocol'], 
				data['desk_id'], 
				data['box_id'], 
				data['mac'], 
				data['result'],
				data['date'],    # Optional field with default value if missing
		)
		db_path = os.path.join(SAVE_PATH, device, f'data_{device}.db')

		device_folder_path = os.path.join(SAVE_PATH, device, desk_id)
		os.makedirs(device_folder_path, exist_ok=True)

		device_db_path = os.path.join(device_folder_path, f'data_{desk_id}.db')

		if self.save_to_db(values, db_path, MAIN_TABLE) and self.save_to_db(values, device_db_path, DEVICE_TABLE):
			return True, 'Saved'
		else:
			return False, 'Error'
	
	def save_to_db(self, data, db_path, table):

		with sqlite3.connect(db_path) as conn:
			print('Saving data to database: ', db_path)

			cursor = conn.cursor()
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {table} (
					Device TEXT,
					Username TEXT,
					Role TEXT,
					Protocol TEXT,
					DeskID TEXT PRIMARY KEY,
					BoxID TEXT,
					DeviceMAC TEXT,
					Result TEXT,
					Date TEXT
				)''')
			
			# Extract values from the dictionary in the order of the columns

			cursor.execute(f'''REPLACE INTO {table} (Device, Username, Role, Protocol, DeskID, BoxID, DeviceMAC, Result, Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', data)
			conn.commit()
			return True