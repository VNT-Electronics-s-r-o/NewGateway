import sqlite3
import bcrypt
import datetime

DB_USERS = "C:/NewGateway/data/users.db"

# Add user to the database with username, password, role
def add_user(username, password, role):
	try:
		# Get the current date and time
		date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

		# The password is hashed with bcrypt before adding to the database
		hashed_pswd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

		conn = sqlite3.connect(DB_USERS)
		c = conn.cursor()

		c.execute('''
			CREATE TABLE IF NOT EXISTS users (
				username TEXT PRIMARY KEY,
				password TEXT,
				role TEXT,
				reg_date TEXT
			)
		''')

		c.execute('INSERT INTO users (username, password, role, reg_date) VALUES (?, ?, ?, ?)', (username, hashed_pswd, role, date))
		conn.commit()
		conn.close()

		print('[INFO] Added user:', username, 'with role:', role, 'on:', date, 'to the database')
		return True
	except Exception as e:
		print('[ERROR] while adding user to database:', username, e)
		return False
# Delete user by username
def delete_user(username):
	try:
		conn = sqlite3.connect(DB_USERS)
		c = conn.cursor()

		c.execute('''
			CREATE TABLE IF NOT EXISTS users (
				username TEXT PRIMARY KEY,
				password TEXT,
				role TEXT,
				reg_date TEXT
			)
		''')

		c.execute('DELETE FROM users WHERE username = ?', (username,))
		conn.commit()
		conn.close()

		print('[INFO] Deleted user:', username, 'from the database')
	except Exception as e:
		print('[ERROR] while deleting user:', username, e)
		return e
	
def check_user(username):
	try:
		conn = sqlite3.connect(DB_USERS)
		c = conn.cursor()

		c.execute('''
			CREATE TABLE IF NOT EXISTS users (
				username TEXT PRIMARY KEY,
				password TEXT,
				role TEXT,
				reg_date TEXT
			)
		''')

		c.execute('SELECT * FROM users WHERE username = ?', (username,))
		user = c.fetchone()
		conn.close()

		if user:
			return True
		else:
			return False
	except Exception as e:
		print('[ERROR] while finding user:', username, e)
		return e

# Find user by username if it is in the database
def find_user(username, password):
	try:
		conn = sqlite3.connect(DB_USERS)
		c = conn.cursor()

		c.execute('''
			CREATE TABLE IF NOT EXISTS users (
				username TEXT PRIMARY KEY,
				password TEXT,
				role TEXT,
				reg_date TEXT
			)
		''')

		c.execute('SELECT * FROM users WHERE username = ?', (username,))
		user = c.fetchone()
		conn.close()

		if user:
			if bcrypt.checkpw(password.encode('utf-8'), user[1]):
				# Return the user and role if the password is correct
				return user[0], user[2]
			else:
				return False, False
		else:
			return None, None
	except Exception as e:
		print('[ERROR] while finding user:', username, e)
		return None, None