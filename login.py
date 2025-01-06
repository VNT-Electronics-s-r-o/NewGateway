import sys

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from add_user_sqlite import find_user, add_user, check_user

class RegistrationForm(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle('Registrační formulář')

		username_label = QLabel('Uživatelské jméno:')
		self.username = QLineEdit()

		self.show_password = QCheckBox()
		self.show_password.setIcon(QIcon('icons/hidden.png'))
		self.show_password.setIconSize(QSize(20, 20))

		password_label = QLabel('Heslo:')
		password_label.setFixedWidth(300)

		self.password = QLineEdit()
		self.password.setEchoMode(QLineEdit.EchoMode.Password)

		confirm_password_label = QLabel('Potvrzení hesla:')
		self.confirm_password = QLineEdit()
		self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

		role_label = QLabel('Role:')

		self.role = QComboBox()
		self.role.addItems(['admin', 'user'])

		register_button = QPushButton('Registrovat')

		self.warning_label = QLabel()

		overall_layout = QHBoxLayout()
		overall_layout.addStretch(1)
		layout = QVBoxLayout()
		layout.addStretch(1)
		layout.addWidget(self.warning_label)
		layout.addWidget(username_label)
		layout.addWidget(self.username)

		password_layout = QHBoxLayout()
		password_layout.addWidget(password_label)
		password_layout.addWidget(self.show_password)

		layout.addLayout(password_layout)
		layout.addWidget(self.password)
		layout.addWidget(confirm_password_label)
		layout.addWidget(self.confirm_password)
		layout.addWidget(role_label)
		layout.addWidget(self.role)
		layout.addWidget(register_button)
		layout.addStretch(1)

		overall_layout.addLayout(layout)
		overall_layout.addStretch(1)

		stylesheet = '''
		QPushButton {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		QLabel {
			font-size: 25px;
			font-family: Calibri;
			height: 50px;
		}
		QLineEdit {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		QComboBox {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		'''
		self.setStyleSheet(stylesheet)

		self.setLayout(overall_layout)

		register_button.clicked.connect(self.register)
		self.show_password.stateChanged.connect(self.show_password_function)
	
	def register(self):
		username = self.username.text()
		password = self.password.text()
		confirm_password = self.confirm_password.text()
		role = self.role.currentText()

		if not username or not password or not role:
			print('[ERROR] - Empty fields')
			self.warning_label.setStyleSheet('color: red;')
			self.warning_label.setText('Vyplňte prosím všechna pole!')
			return

		if password != confirm_password:
			print('[ERROR] - Passwords do not match')
			self.warning_label.setStyleSheet('color: red;')
			self.warning_label.setText('Hesla se neshodují!')
			return
	
		if len(password) < 6:
			print('[ERROR] - Password too short')
			self.warning_label.setStyleSheet('color: red;')
			self.warning_label.setText('Heslo je příliš krátké!')
			return
		
		user = check_user(username)
		if user:
			print('[ERROR] - User already exists')
			self.warning_label.setStyleSheet('color: red;')
			self.warning_label.setText('Uživatel již existuje!')
			return
		
		if add_user(username, password, role):
			print('[INFO] - User added successfully')
			self.warning_label.setStyleSheet('color: green;')
			self.warning_label.setText('Uživatel registrován úspěšně')
		else:
			print('[ERROR] - User not added')
			self.warning_label.setStyleSheet('color: red;')
			self.warning_label.setText('Uživatele se nepodařilo registrovat')

	def show_password_function(self):
		if self.show_password.isChecked():
			self.password.setEchoMode(QLineEdit.EchoMode.Normal)
			self.confirm_password.setEchoMode(QLineEdit.EchoMode.Normal)
		else:
			self.password.setEchoMode(QLineEdit.EchoMode.Password)
			self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

class LoginWindow(QWidget):
	login_signal = pyqtSignal(str, str, str)

	def __init__(self):
		super().__init__()

		self.setWindowTitle('Přihlašovací okno')

		username_label = QLabel('Uživatelské jméno:')
		self.username = QLineEdit('admin')

		password_label = QLabel('Heslo:')
		password_label.setFixedWidth(300)

		self.password = QLineEdit('123456')
		self.password.setEchoMode(QLineEdit.EchoMode.Password)

		self.show_password = QCheckBox()
		self.show_password.setIcon(QIcon('icons/hidden.png'))
		self.show_password.setIconSize(QSize(20, 20))

		device_type_label = QLabel('Typ zařízení:')
		self.device_type = QComboBox()
		self.device_type.addItems(['GW100', 'FM20', 'Agrifence', 'Zap'])

		login_button = QPushButton('Přihlásit')

		register_button = QPushButton('Registrovat')

		close_button = QPushButton('Zavřít')

		self.error_label = QLabel()

		overall_layout = QHBoxLayout()
		overall_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
		overall_layout.addStretch(1)

		layout = QVBoxLayout()
		layout.addStretch(0)

		layout.addWidget(self.error_label, alignment=Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(username_label)
		layout.addWidget(self.username)

		password_layout = QHBoxLayout()
		password_layout.addWidget(password_label)
		password_layout.addStretch(1)
		password_layout.addWidget(self.show_password, alignment=Qt.AlignmentFlag.AlignLeft)

		layout.addLayout(password_layout)
		layout.addWidget(self.password)
		layout.addWidget(device_type_label)
		layout.addWidget(self.device_type)
		layout.addWidget(login_button)
		layout.addWidget(register_button)
		layout.addWidget(close_button)
		layout.addStretch(0)

		overall_layout.addLayout(layout)

		overall_layout.addStretch(1)

		stylesheet = '''
		QPushButton {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		QLabel {
			font-size: 25px;
			font-family: Calibri;
			height: 50px;

		}
		QLineEdit {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		QComboBox {
			font-size: 25px;
			font-family: Calibri;
			max-width: 500px;
			height: 50px;
		}
		'''
		self.setStyleSheet(stylesheet)
		self.setLayout(overall_layout)


		login_button.clicked.connect(self.login)
		register_button.clicked.connect(self.show_register_window)
		close_button.clicked.connect(self.close_window)

		self.show_password.stateChanged.connect(self.show_password_function)

	def login(self):
		
		username = self.username.text()
		password = self.password.text()

		user, role = find_user(username, password)
		# if None, None is returned, the user is not in the database
		# if False, False is returned, the password is incorrect
		if user is None:
			self.error_label.setText('Uživatel nenalezen')
			self.error_label.setStyleSheet('color: red;')
			return
		elif user is False:
			self.error_label.setText('Špatné heslo')
			self.error_label.setStyleSheet('color: red;')
			return
		else:
			self.error_label.setText('Přihlášení proběhlo úspěšně')
			self.error_label.setStyleSheet('color: green;')

		device = self.device_type.currentText()	
		self.login_signal.emit(username, role, device)
	
	def show_register_window(self):
		# You need to use self to store the form as an instance attribute, otherwise it will be garbage collected
		self.register_form = RegistrationForm()  # Store it as an instance attribute
		self.register_form.show()
	
	def show_password_function(self):
		if self.show_password.isChecked():
			self.password.setEchoMode(QLineEdit.EchoMode.Normal)
		else:
			self.password.setEchoMode(QLineEdit.EchoMode.Password)
	
	def close_window(self):
		QCoreApplication.instance().quit()


if __name__ == '__main__':
	sys.argv += ['-platform', 'windows:darkmode=1']
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	login_window = LoginWindow()
	login_window.showMaximized()
	sys.exit(app.exec())