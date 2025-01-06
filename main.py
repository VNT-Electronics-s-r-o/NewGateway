import sys
import time
import json
import serial
import datetime
import serial.tools.list_ports

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


from login import LoginWindow
from rf import SerialConnection, RfUSBControl
from psu import PSUControll
from esp import UploadESP
from stm import UploadSTM
from git_clone import GitClone
from data_saver import DataSaver

PSU_IP = '192.168.20.126'
CLONING_PATH = 'C:\\GatewayGit\\'
WORKING_PATH = 'C:\\GatewayGit\\assemblyline\\'
REPO_URL = 'http://192.168.1.127/assemblyline/gw100_gw10_assemblyline'
DEV_MODE = False
#ICONS_PATH = 'C:/Users/Jesse/Desktop/Work/NewGateway/icons/'
ICONS_PATH = 'C:/NewGateway/icons/'

LIGHT_GREEN = '#b4e495'

class Signals(QObject):
	progress_signal = pyqtSignal(int)
	result = pyqtSignal(bool)
	

class Worker(QRunnable):
	def __init__(self, fn, *args, **kwargs):
		super().__init__()
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = Signals()

	@pyqtSlot()
	def run(self):
		function_result = self.fn(*self.args, **self.kwargs)
		self.signals.result.emit(function_result)

class ServiceWidget(QWidget):
	log_signal = pyqtSignal(str, str)
	db_signal = pyqtSignal()
	config_signal = pyqtSignal()
	change_signal = pyqtSignal()
	save_signal = pyqtSignal()
	close_signal = pyqtSignal()

	def __init__(self, username, role, device):
		super().__init__()

		self.username = username
		self.role = role
		self.device = device

		self.log_signal.connect(self.log_msg)
		self.db_signal.connect(self.open_database)
		self.config_signal.connect(self.open_config)
		self.change_signal.connect(self.change_device)
		self.save_signal.connect(self.save_data)
		self.close_signal.connect(self.close_app)

		self.psu = PSUControll()
		self.rf_control = RfUSBControl() # init the class at the beginning

# -------------------- FONT SETUP --------------------
		font = QFont()
		font.setFamily('Calibri')
		font.setPointSize(18)
		self.setFont(font)

# -------------------- WIDGETS --------------------
# - - - - - - - - - INFO GROUP - - - - - - - - -
		info_group = QGroupBox('Info')

		self.device_label = QLabel(self.device)
		self.device_label.setStyleSheet('font-weight: bold; font-size: 25px; font-family: Calibri;')

# - - - - - - - - - LOG GROUP - - - - - - - - -
		log_group = QGroupBox('Log')

		self.log = QTextEdit()
		self.log.setReadOnly(True)
		self.log.setStyleSheet('border: 1px solid lightgrey; border-radius: 5px;')
		self.log.setFixedHeight(200)
		self.log.setMinimumWidth(500)
		self.log.setFont(QFont('Consolas', 13))

		self.progress_bar = QProgressBar()
		self.progress_bar.setFixedHeight(20)
		self.progress_bar.setRange(0, 100)
		self.progress_bar.setValue(0)

# - - - - - - - - - BUTTONS GROUP - - - - - - - - -
		btns_group = QGroupBox('Actions')

		self.start_continue_btn = QPushButton(' START')
		self.start_continue_btn.setFixedHeight(50)
		self.start_continue_btn.setIcon(QIcon(ICONS_PATH + 'start.png'))
		self.start_continue_btn.setIconSize(QSize(24, 24))
		self.start_continue_btn.setStyleSheet('font-weight: bold; font-size: 25px;')

		self.new_protocol_btn = QPushButton(' Nová průvodka')
		self.new_protocol_btn.setFixedHeight(40)
		self.new_protocol_btn.setIcon(QIcon(ICONS_PATH + 'add.png'))
		self.new_protocol_btn.setIconSize(QSize(20, 20))

		self.change_device_btn = QPushButton(' Změnit zařízení')
		self.change_device_btn.setFixedHeight(40)
		self.change_device_btn.setIcon(QIcon(ICONS_PATH + 'change.png'))
		self.change_device_btn.setIconSize(QSize(20, 20))

		self.try_again_btn = QPushButton(' Znovu')
		self.try_again_btn.setFixedHeight(40)
		self.try_again_btn.setIcon(QIcon(ICONS_PATH + 'again.png'))
		self.try_again_btn.setIconSize(QSize(20, 20))

# - - - - - - - - - DATA GROUP - - - - - - - - -
		data_group = QGroupBox('Data')

		psu_label = QLabel('IP Zdroje: ')
		self.psu_input = QLabel(PSU_IP)

		protocol_label = QLabel('Průvodka: ')
		self.protocol_number = QLabel()

		desk_label = QLabel('ID Desky: ')
		self.desk_id = QLabel()

		mac_label = QLabel('MAC: ')
		self.mac = QLabel()

		esp_mac_label = QLabel('ESP MAC: ')
		self.esp_mac = QLabel()

		

# - - - - - - - - - CHECKS GROUP - - - - - - - - -
		check_group = QGroupBox('Checklist')

		self.git_cloned_check = QCheckBox('Data stažena')
		self.protocol_loaded_check = QCheckBox('Průvodka načtena')
		self.desk_id_check = QCheckBox('ID desky zadáno')
		self.mac_generated_check = QCheckBox('MAC vygenerována')
		self.ready_to_upload_check = QCheckBox('Připraveno k nahrávání')

		self.psu_connected_check = QCheckBox('Zdroj připojen')
		self.esp_uploaded_check = QCheckBox('ESP nahráno')
		self.stm_uploaded_check = QCheckBox('STM nahráno')
		self.measuring_done_check = QCheckBox('Měření dokončeno')
		self.data_saved_check = QCheckBox('Data uložena')
		self.final_check = QCheckBox('Dokončeno')

		# adding signal for every checkbox, if it's checked, the background color will change to green, if it's unchecked, it will not have any background
		for checkbox in [self.git_cloned_check, self.protocol_loaded_check, self.desk_id_check,
							self.mac_generated_check, self.ready_to_upload_check, self.psu_connected_check,
							self.esp_uploaded_check, self.stm_uploaded_check, self.measuring_done_check,
							self.data_saved_check, self.final_check]:
			checkbox.stateChanged.connect(self.check_state_changed)

		final_result_label = QLabel('Výsledek: ')
		self.final_result = QLabel()

		result_layout = QHBoxLayout()
		result_layout.addWidget(final_result_label)
		result_layout.addWidget(self.final_result)

# -------------------- LAYOUTS --------------------

		data_layout = QHBoxLayout()
		left_data_layout = QVBoxLayout()
		data_form= QFormLayout()

		data_form.addRow(protocol_label, self.protocol_number)
		data_form.addRow(desk_label, self.desk_id)
		data_form.addRow(mac_label, self.mac)
		data_form.addRow(esp_mac_label, self.esp_mac)
		data_form.addRow(psu_label, self.psu_input)

		left_data_layout.addLayout(data_form)

		data_layout.addLayout(left_data_layout)

		check_layout = QVBoxLayout()

		check_layout.addWidget(self.git_cloned_check)
		check_layout.addWidget(self.protocol_loaded_check)
		check_layout.addWidget(self.desk_id_check)
		check_layout.addWidget(self.mac_generated_check)
		check_layout.addWidget(self.ready_to_upload_check)

		check_layout.addWidget(self.psu_connected_check)
		check_layout.addWidget(self.esp_uploaded_check)
		check_layout.addWidget(self.stm_uploaded_check)
		check_layout.addWidget(self.measuring_done_check)
		check_layout.addWidget(self.data_saved_check)
		check_layout.addWidget(self.final_check)
		check_layout.addStretch(0)

		check_layout.addLayout(result_layout)

		btn_layout = QVBoxLayout()
		btn_layout.addWidget(self.start_continue_btn)
		row_btn_layout = QHBoxLayout()
		row_btn_layout.addWidget(self.new_protocol_btn)
		row_btn_layout.addWidget(self.change_device_btn)
		row_btn_layout.addWidget(self.try_again_btn)
		btn_layout.addLayout(row_btn_layout)

		log_layout = QVBoxLayout()
		log_layout.addWidget(self.log)
		log_layout.addWidget(self.progress_bar)
		
		info_layout = QVBoxLayout()
		info_layout.addWidget(self.device_label, alignment=Qt.AlignmentFlag.AlignLeft)

		info_group.setLayout(info_layout)
		log_group.setLayout(log_layout)
		btns_group.setLayout(btn_layout)
		data_group.setLayout(data_layout)
		check_group.setLayout(check_layout)

		outer_layout = QVBoxLayout()
		main_layout = QHBoxLayout()
		
		right_layout = QVBoxLayout()
		left_layout = QVBoxLayout()

		right_layout.addWidget(info_group)
		right_layout.addWidget(log_group)
		right_layout.addWidget(btns_group)
		right_layout.addWidget(data_group)

		left_layout.addWidget(check_group)

		main_layout.addStretch(0)
		main_layout.addLayout(left_layout)
		main_layout.addLayout(right_layout)
		main_layout.addStretch(0)
		outer_layout.addLayout(main_layout)
		outer_layout.addStretch(0)

		self.setLayout(outer_layout)

		stylesheet = '''
		QCheckBox {
			padding: 5px;
		}
		QPushButton {
			background-color: white;
			border: 1px solid lightgrey;
			border-radius: 5px;
			padding: 5px;
		}
		QPushButton:hover {
			background-color: lightblue;
			border: 1px solid blue;
		}
		QLabel {
			font-size: 16px;
			font-family: Calibri;
		}

		'''
		self.setStyleSheet(stylesheet)

# -------------------- BTN CONNECTIONS --------------------
		self.start_continue_btn.clicked.connect(self.start_work)
		self.new_protocol_btn.clicked.connect(self.load_new_protocol)
		self.change_device_btn.clicked.connect(self.change_device)
		self.try_again_btn.clicked.connect(self.try_again)

		self.clone_repository()

# -------------------- FUNCTIONS --------------------

	def open_database(self):
		print('Opening database')

	def open_config(self):
		print('Opening config')

	def update_psu(self):
		print('Updating psu ip')

	def check_state_changed(self):
		# sender object to get whichc check was checked/unchecked
		self.sender_check = self.sender()
		if self.sender_check.isChecked():
			self.sender_check.setStyleSheet('background-color: #b4e495; border-radius: 5px; border: 0px solid #b4e495;')
		else:
			self.sender_check.setStyleSheet('background-color: transparent; border: none;')

	# initialise connection with the tester to be able to control led etc
	def init_uploader(self):
		# init of rf control and listenning process
		
		if not self.rf_control.start_listening():
			return False
		#self.rf_control.listen()
		print('[INFO] - Init of the uploader, cloning repofor device: ', self.device)
		return True

# - - - - - - - - - START OF THE ACTUAL WORK - - - - - - - - -

	def start_work(self):
		connected = self.init_uploader()

		if not connected:
			self.log_signal.emit('<b>Nepodařilo se připojit k testeru, zkontrolujte, zda je vše zapojeno a zkuste to znovu!</b>', 'E')
			return
		
		self.erase_gui()
		
		mac = self.generate_mac()
		if not mac:
			self.switch_leds(False)
			self.log_signal.emit('Chyba při generování MAC adresy!', 'E')
			return False
		
		if not self.update_eeprom_file(mac, self.device):
			self.switch_leds(False)
			self.log_signal.emit('Chyba při aktualizaci EEPROM souboru!', 'E')
			return False

		if self.start_continue_btn.text() == 'START':
			if not self.load_new_protocol():
				self.switch_leds(False)
				return False
		# If the button is 'POKRAČOVAT', protocol number is the same so we continue as default with loading device

		if not self.load_device_id():
			self.switch_leds(False)
			self.log_signal.emit('ID desky nebylo načteno nebo neodpovídá požadovanému formátu!', 'W')
			return False

		result = self.confirmation_msg('Informace', 'Je deska v testeru?')
		print('Result: ', result)
		if not result:
			self.switch_leds(False)
			return
		
		self.ready_to_upload_check.setChecked(True)

		self.start_background_worker()
		# 6. Start background process

	def try_again(self):
		
		if not self.mac.text() or not self.protocol_number or not self.desk_id():
			self.log_signal.emit('<b>Některe parametry chybí, použijte tlačítko START. </b>', 'E')
			return

		self.log_signal.emit('Proces bude zopakován', 'I')
		self.start_background_worker()

	def start_background_worker(self):
		self.log_signal.emit('------------------------------------------')
		self.log_signal.emit('<b>ZAČÍNÁ NAHRÁVÁNÍ</b',)
		self.log_signal.emit('------------------------------------------')

		self.rf_control.set_aux_blinking(2, 100)
		self.rf_control.set_aux_blinking(1, 100)

		'''
		- always check if the specific checkbox is checked before starting the actual process
		- if the check is checked, continue checking another check
		- if it ends without errors, check the check
		- if everything is checked and there are no errors, check the last chceck and finish the work
		- uncheck all checks when starting again
		- when finished set the start_continue btn to POKRAČOVAT:
			self.start_continue_btn.setText('POKRAČOVAT') -- if the process finished successfully, you will set it to CONTINUE otherwise it will stay START
		'''

		if not self.psu_connected_check.isChecked():
			self.init_psu()
		elif not self.esp_uploaded_check.isChecked():
			self.upload_esp()
		elif not self.stm_uploaded_check.isChecked():
			self.upload_stm()
		elif not self.measuring_done_check.isChecked():
			self.psu_measuring()
		else:
			print('Work finished')
			self.work_finished()

	# 1
	def init_psu(self):
		self.log_signal.emit('1 z 5 - <b>Inicializace zdroje</b>', 'I')
		print('Init PSU')
		self.rf_control.set_aux_pin(4,0) # vypnuti ESP
		worker = Worker(self.init_psu_worker)
		worker.signals.result.connect(self.init_psu_done)
		QThreadPool.globalInstance().start(worker)

	def init_psu_worker(self):
		
		print('Init PSU Worker')
		if not self.psu.start_psu(PSU_IP):
			return False
		if not self.rf_control.set_aux_pin(1,0):
			return False
		time.sleep(0.1)
		if not self.rf_control.set_aux_pin(3,1):
			return False
		time.sleep(0.1)
	
		return True

	def init_psu_done(self, result):
		if not result:
			self.switch_leds(False)
			self.log_signal.emit('Došlo k chybě během inicializace zdroje!', 'E')
			return False

		self.psu_connected_check.setChecked(True)
		self.start_background_worker()

	# 2 
	def upload_esp(self):
		print('Upload ESP')
		self.log_signal.emit('2 z 5 - <b>Nahrávání ESP čipu</b>', 'I')
		# turn on ESP pin
		
		worker = Worker(self.upload_esp_worker)
		worker.signals.result.connect(self.upload_esp_done)
		QThreadPool.globalInstance().start(worker)

	def upload_esp_worker(self):
		try:
			# init ESP class to be able to call upload_esp_process
			if not self.rf_control.set_aux_pin(4, 1):
				return False
			esp = UploadESP(log_signal=self.log_signal, device=self.device)
			result, info = esp.upload_esp_process() # process that loads config, connects to esp, reases esp and programs esp
			# reset pins after done, no matter the result
			self.rf_control.reset_pin(4, 1, 2)
			time.sleep(0.5)
			if result:
				return True
			else:
				print('[ERROR] - ESP upload failed:', info)
				self.log_signal.emit(f'Nahrávání ESP se nezdařilo: <b>{info}</b>', 'E')
				# restart PSU if it failed (maybe)
				#self.psu.reset_desk()
				return False
		except Exception as e:
			print('Error in upload_esp_worker: ', e)
			return False

		finally:
		# always reset set these pins at the end
			self.rf_control.set_aux_pin(4, 0)
			time.sleep(2)
			self.rf_control.set_aux_pin(3, 0)
			time.sleep(2)
			self.rf_control.set_aux_pin(4, 1)

	def upload_esp_done(self, result):
		if not result:
			self.switch_leds(False)
			self.psu_connected_check.setChecked(False)
			self.log_signal.emit('Nepodařilo se nahrát čip ESP!', 'W')
			return False

		self.esp_uploaded_check.setChecked(True)
		self.start_background_worker()

	# 3
	def upload_stm(self):
		# first set corespondig voltage and current (basically turn on the psu)
		self.log_signal.emit('3 z 5 - <b>Nahrávání ST čipu</b>', 'I')
		self.psu.set_volt_curr(1, 14, 0.5)
		self.psu.set_volt_curr(2, 8.3, 0.5)

		worker = Worker(self.upload_stm_worker)
		worker.signals.result.connect(self.upload_stm_done)
		QThreadPool.globalInstance().start(worker)

	def upload_stm_worker(self):
		self.stm = UploadSTM(self.device)
		result, info = self.stm.upload_stm()
		if not result:
			print('Result: ', result, 'Info: ', info)
			self.log_signal.emit(f'Nahrávání STM se nezdařilo: <b>{info}</b>', 'E')
			return False
		return True

	def upload_stm_done(self, result):
		if not result:
			self.switch_leds(False)
			self.log_signal.emit('Nepodařilo se nahrát čip ST!', 'W')
			return False

		self.stm_uploaded_check.setChecked(True)
		self.start_background_worker()

	# 4
	def psu_measuring(self):
		self.log_signal.emit('4 z 5 - <b>Měření desky</b>', 'I')
		print('Starting measuring process')
		self.log_signal.emit('Probíhá měření desky, prosím čekejte ...', 'I')
		worker = Worker(self.psu_measuring_worker)
		worker.signals.result.connect(self.psu_measuring_done)
		QThreadPool.globalInstance().start(worker)
	
	def psu_measuring_worker(self):
		result, info = self.psu.start_measuring()
		if not result:
			print(f'Error while measuring {info}')
			self.log_signal.emit(f'Deska neprošla měřením, chybné testy: <b>{info}</b>', 'E')
			return False
		return True

	def psu_measuring_done(self, result):
		if not result:
			self.switch_leds(False)
			return False
		
		self.log_signal.emit('Měření proběhlo úspěšně.', 'O')
		self.measuring_done_check.setChecked(True)
		self.start_background_worker()

	# 5
	def work_finished(self):
		self.log_signal.emit('5 z 5 - <b>Rozsvícení desky</b>', 'I')
		result = self.confirmation_msg('Potvrzení', 'Svítí display a je vidět text?')
		if not result:
			self.log_signal.emit('Během nahrávání došlo k chybě, zkuste výrobek nahrát znovu nebo kontaktujte podporu.', 'E')
			self.final_result.setText('CHYBA')
			self.final_result.setStyleSheet('color: red; font-weight: bold')
			self.switch_leds(False)
			return
		self.start_continue_btn.setText('POKRAČOVAT') #-- if the process finished successfully, you will set it to CONTINUE otherwise it will stay START
		self.switch_leds(True)
		self.save_data()

	def save_data(self):
		self.log_signal.emit('Nahrávání bylo dokončeno úspěšně, ukládám data', 'I')
		worker = Worker(self.save_data_worker)
		worker.signals.result.connect(self.save_data_done)
		QThreadPool.globalInstance().start(worker)

	def save_data_worker(self):
		data = self.create_data_object()
		if not data:
			return False
		
		saver = DataSaver()
		result, info = saver.save_data(data)
		if not result:
			print('Error while saving data: ', info)
			return False
		else:
			return True

	def save_data_done(self, result):
		if not result:
			print('[ERROR] - Error occured while saving the data!')
			self.log_signal.emit('Vyskytla se chyba během ukládání dat!', 'W')
			self.final_result.setText('CHYBA')
			self.final_result.setStyleSheet('color: red; font-weight: bold')
			self.switch_leds(False)
			return

		self.data_saved_check.setChecked(True)

		self.final_result.setText('OK')
		self.final_result.setStyleSheet('color: green; font-weight: bold')

		self.log_signal.emit('', '')
		self.log_signal.emit('<b>Data byla úspěšně uložena, můžete pokračovat v nahrávání</b>', 'O')
		self.log_signal.emit('', '')
		

	def create_data_object(self):
		try:
		# instead of creating tuple (data = (username, role, ...)) lets create a dictionary
		# to access specific values from dictionary use: protocol_number = data["protocol_number"]
			current_date = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
			data = {
				'device': self.device,
				'username': self.username,
				'role': self.role,
				'protocol': self.protocol_number.text(),
				'desk_id': self.desk_id.text(),
				'box_id': 'none',
				'mac': self.mac.text(),
				'result': self.final_result.text(),
				'date': current_date
			}
			return data
		except Exception as e:
			print('Error while creating data object: ', e)
			return False

# - - - - - - - - - DEVICE ID RELATED - - - - - - - - -

	def change_device(self):
		device_type = self.open_dialog('Změna zařízení', 'Vyberte zařízení: ', '1')
		if device_type and self.device != device_type:
			self.device = device_type
			self.device_label.setText(self.device)
			print('Selected device: ', self.device)
			self.erase_gui()
			self.clone_repository()
			self.log_signal.emit('<b>Změna zařízení proběhla úspěšně, vyčkejte na stažení dat.</b>', 'O')
			self.start_continue_btn.setText('START')
		elif device_type:
			self.erase_gui()
			print('Same device was selected')
			self.start_continue_btn.setText('START')
		else:
			print('Device selection was cancelled')
	
	def load_device_id(self):
		device_id = self.open_dialog('ID desky', 'Načtěte číslo desky:', '0')
		print('[INFO] Device ID:', device_id)
		# open the input dialog value
		# load the device id
		if device_id:
			if not self.verify_device_id(device_id):
				self.log_signal.emit('Zadaný kód neodpovídá požadovanému formátu!', 'E')
				return False

			self.desk_id.setText(device_id)
			self.desk_id_check.setChecked(True)
			return device_id
		else:
			return False
	
	def verify_device_id(self, device_id):
		if device_id.startswith('03') and len(device_id) == 10:
			return True
		elif DEV_MODE:
			return True
		else:
			return False

# --------------------LED SWITCHING BASED ON RESULTS -----------------------------    
	def switch_leds(self, result):
		try:
			# If true, green will be on, else red
			if result is True:
				self.rf_control.set_aux_pin(1, 0)
				self.rf_control.set_aux_pin(2, 1)
			else:
				self.rf_control.set_aux_pin(2, 0)
				self.rf_control.set_aux_pin(1, 1)
		except Exception as e:
			print('Error while switching leds: ', e)

# - - - - - - - - - PROTOCOL RELATED - - - - - - - - -

	def load_new_protocol(self):
		protocol_number = self.open_dialog('Číslo průvodky', 'Zadejte číslo průvodky:', '0')
		if not protocol_number:
			self.log_signal.emit('Načítání průvodky zrušeno uživatelem, nebo nebylo zadáno', 'W')
			return False
		
		if not self.verify_protocol_number(protocol_number):
			self.log_signal.emit('Průvodní list neodpovídá požadovanému formátu!','E')
			return False
		
		self.protocol_number.setText(protocol_number)
		self.protocol_loaded_check.setChecked(True)
	
		# open the file dialog
		# load the protocol
		# fill the form with the data
		self.start_continue_btn.setText('POKRAČOVAT')
		return True

	def verify_protocol_number(self, protocol_number):
		# example: 010H000000000580

		if protocol_number.startswith('010H') and len(protocol_number) == 16:
			return True
		elif DEV_MODE:
			return True
		else:
			print('[ERROR] Protocol number does not match the required format.')
			return False

# - - - - - - - - - GIT WORKER - - - - - - - - -
	def clone_repository(self):
		print('Cloning repo')
		self.log_signal.emit('Stahuji data.', 'I')
		self.disable_gui(True)
		worker = Worker(self.clone_repo_worker)
		worker.signals.result.connect(self.repository_cloned)
		QThreadPool.globalInstance().start(worker)
	
	def clone_repo_worker(self):
		git_clone = GitClone(REPO_URL, CLONING_PATH, WORKING_PATH)
		if git_clone.clone():
			return True
		else:
			return False
	
	def repository_cloned(self, result):
		if result:
			self.git_cloned_check.setChecked(True)
			self.log_signal.emit('<b>Data stažena. </b>', 'O')
			
		else:
			self.git_cloned_check.setChecked(False)
			self.log_signal.emit('Chyba při klonování repozitáře!', 'E')
		self.disable_gui(False)

# - - - - - - - - - - - - - - - - - - - - - - -
	# get avaliable ports to connect to STM and ESP processors
	def get_ports(self):
		ports = serial.tools.list_ports.comports()
		port_list = []
		for port, desc, hwid in sorted(ports):
			print(f'{port}: {desc} [{hwid}]')
			port_list.append(port)
		
		return port_list

	def update_eeprom_file(self, mac, device_name):
		try:
			# Determine the file to open
			eeprom_files = {
				'FM20': 'data/data_fm_20.json',
				'GW100': 'data/data_gw_100.json',
				'Agrifence': 'data/data_gw_agrifence.json',
				'Zap!': 'data/data_gw_zap.json'
			}

			eeprom_file = eeprom_files.get(device_name)
			if not eeprom_file:
				print('[ERROR] - Device name not found')
				return False

			# Open and modify the file
			with open(eeprom_file, 'r') as file:
				data = json.load(file)

			for item in data:
				if item['name'] == 'My TX EUI 1':
					item['value'] = mac

			# Save the changes
			with open(eeprom_file, 'w') as file:
				json.dump(data, file, indent=4)

			print('[INFO] EEPROM file updated successfully.')
			return True

		except FileNotFoundError:
			print('[ERROR] EEPROM file not found:', eeprom_file)
			return False

		except Exception as e:
			print('[ERROR] while updating EEPROM file:', e)
			return False
		
	def generate_mac(self):
		utc_time = int(datetime.datetime.now(datetime.UTC).timestamp())
		mac = str('0x{:X}'.format((utc_time * 0x100000000) + 0x08))
		self.mac.setText(mac)
		self.mac_generated_check.setChecked(True)
		return mac
	
	def confirmation_msg(self, title, label):
		msg_box = QMessageBox()
		msg_box.setWindowTitle(title)
		msg_box.setText(label)
		msg_box.setIcon(QMessageBox.Icon.Question)
		msg_box.setWindowIcon(QIcon(ICONS_PATH + 'g14.ico'))

		yes_btn = msg_box.addButton('Ano', QMessageBox.ButtonRole.YesRole)
		no_btn = msg_box.addButton('Ne', QMessageBox.ButtonRole.NoRole)

		msg_box.setStyleSheet("""
			QPushButton {
				height: 30px;
				width: 100px;
				font-size: 14px;
			}
			QinputDialog {
				min-height: 30px;
			}
		""")

		ok = msg_box.exec()
		print('OK: ', ok)
		if ok == 2:
			print('Yes')
			return True
		return False

	def open_dialog(self, title, label, dialog_type=0):
		# dialog_type = 0 is for regular dialog with input field, 1 is for having combobox with devices (could be added more in the future)
		dialog = QInputDialog()
		dialog.setLabelText(label)
		dialog.setWindowTitle(title)
		dialog.setWindowIcon(QIcon(ICONS_PATH + 'g14.ico'))

		if dialog_type == '1':
			dialog.setComboBoxItems(['GW100', 'FM20', 'Agrifence', 'Zap'])

		font = QFont()
		font.setPointSize(18)
		dialog.setFont(font)

		dialog.resize(500, 300)

		dialog.setStyleSheet("""
			QPushButton {
				height: 30px;
				width: 100px;
				font-size: 16px;
			}
			QinputDialog {
				min-height: 30px;
			}
			QinputDialog {
				min-height: 30px;
			}
		""")

		ok = dialog.exec()
		print('OK: ', ok)
		if ok == 1:
			if dialog.textValue() == '':
				return False
			return dialog.textValue()
		else:
			return False

	def disable_gui(self, disable=True):
		self.start_continue_btn.setDisabled(disable)
		self.new_protocol_btn.setDisabled(disable)
		self.change_device_btn.setDisabled(disable)

	def erase_gui(self):
		self.log.clear() # clear the log before starting the process
		self.desk_id.setText('')
		self.mac.setText('')
		self.esp_mac.setText('')

		self.git_cloned_check.setChecked(False)
		self.protocol_loaded_check.setChecked(False)
		self.desk_id_check.setChecked(False)
		self.psu_connected_check.setChecked(False)
		self.esp_uploaded_check.setChecked(False)
		self.stm_uploaded_check.setChecked(False)
		self.measuring_done_check.setChecked(False)
		self.data_saved_check.setChecked(False)
		self.final_check.setChecked(False)

	def update_progress(self, value):
		# slowly update the progress bar based on the value, don't just set it
		if value > self.progress_bar.value():
			for i in range(self.progress_bar.value(), value+1):
				self.progress_bar.setValue(i)
				QApplication.processEvents()
				QThread.msleep(50)
		else:
			self.progress_bar.setValue(value)
			QApplication.processEvents()

	def get_timestamp(self):
		return datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

	def log_msg(self, msg, type='I'):
		if len(msg)<= 1:
			return

		color_map = {
			'I': 'black',
			'O': 'green',
			'W': 'orange',
			'E': 'red',
			'D': 'blue',
			'': 'black'
		}
		time = self.get_timestamp()
		color = color_map.get(type, 'black')
		if type == 'I':
			self.log.append(f'<font color="{color}">[INFO] {time} - {msg}</font>')
		elif type == 'W':
			self.log.append(f'<font color="{color}">[WARNING] {time} - {msg}</font>')
		elif type == 'E':
			self.log.append(f'<font color="{color}">[ERROR] {time} - {msg}</font>')
		elif type == 'D':
			self.log.append(f'<font color="{color}">[DEBUG] {time} - {msg}</font>')
		elif type == 'O':
			self.log.append(f'<font color="{color}">[OK] {time} - {msg}</font>')
		else:
			self.log.append(f'{time} - {msg}')
	
	def close_app(self):
		#if DEV_MODE:
		#	self.close()
		if self.confirmation_msg('Ukončit', 'Opravdu chcete aplikaci ukončit?'):
			print('The app will be closed shortly')
			self.rf_control.closing_app()
			self.psu.disconnect_psu()
			self.close()
		else:
			print('User does not want to close the app')
			return False
		# first disconnect the port and turn off the leds

	def closeEvent(self, event):
		QApplication.quit()

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Gateway Uploader')
		self.setWindowIcon(QIcon(ICONS_PATH + 'g14.ico'))

		# defining toolbar
		toolbar = QToolBar('Main Toolbar')
		self.addToolBar(toolbar)

		config_action = QAction(' Konfigurace', self)
		config_action.setIcon(QIcon(ICONS_PATH + 'config.png'))

		database_action = QAction(' Databáze', self)
		database_action.setIcon(QIcon(ICONS_PATH + 'database.png'))

		# action buttons
		change_action = QAction(' Změnit zařízení', self)
		change_action.setIcon(QIcon(ICONS_PATH + 'change.png'))

		save_action = QAction(' Uložit', self)
		save_action.setIcon(QIcon(ICONS_PATH + 'save.png'))

		close_action = QAction(' ', self)
		close_action.setIcon(QIcon(ICONS_PATH + 'exit.png'))

		# add actions to toolbar
		toolbar.addAction(config_action)
		toolbar.addAction(database_action)
		toolbar.addAction(change_action)
		toolbar.addAction(save_action)

		# add a spacer to push the close action to the right
		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		toolbar.addWidget(spacer)

		toolbar.addAction(close_action)

		toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
		toolbar.setIconSize(QSize(30,30))

		# connect toolbar actions to functions
		config_action.triggered.connect(self.emit_open_config)
		database_action.triggered.connect(self.emit_open_db)
		change_action.triggered.connect(self.emit_change_device)
		save_action.triggered.connect(self.emit_save_data)
		close_action.triggered.connect(self.emit_close_app)

		if DEV_MODE:
			self.show_service_widget('admin', 'admin', 'GW100')
		else:
			self.login_window = LoginWindow()
			self.login_window.login_signal.connect(self.show_service_widget)
			
			self.setCentralWidget(self.login_window)

			# timer to have the window maximized, needed because it takes some time until the window is loaded so this way you ensure it is maximised
			QTimer.singleShot(0, self.showMaximized)

	def emit_open_db(self):
		self.service_widget.db_signal.emit()
	
	def emit_open_config(self):
		self.service_widget.config_signal.emit()

	def emit_change_device(self):
		self.service_widget.change_signal.emit()

	def emit_close_app(self, action):
		self.service_widget.close_signal.emit()
	
	def emit_save_data(self, action):
		self.service_widget.save_signal.emit()
	
	# If the main window is closed using
	def closeEvent(self, event):
		self.close()

	def show_service_widget(self, username, role, device):
		self.service_widget = ServiceWidget(username, role, device)
		self.setCentralWidget(self.service_widget)

if __name__ == '__main__':
	# you need to specify the darkmode in PyQt 6 to get the one that you want!
	sys.argv += ['-platform', 'windows:darkmode=1'] #darkmode=1 == light theme, darkmode=2  == dark theme
	app = QApplication(sys.argv)
	app.setStyle('windowsvista')
	window = MainWindow()
	window.setStyleSheet(
	"""
		font-family: Calibri;
		font-size: 18px;
	""")
	window.show()
	window.showMaximized()
	
	sys.exit(app.exec())