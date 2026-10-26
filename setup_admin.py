import getpass
from werkzeug.security import generate_password_hash
from database import connect, initialize_database

initialize_database()
username = input('Choose admin username: ').strip()
if not username:
    raise SystemExit('Username required.')
password = getpass.getpass('Choose admin password (at least 12 characters): ')
confirmation = getpass.getpass('Confirm password: ')
if len(password) < 12 or password != confirmation:
    raise SystemExit('Password must be at least 12 characters and match confirmation.')
with connect() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS admin_users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)')
    conn.execute('INSERT INTO admin_users(username,password_hash) VALUES (?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash', (username, generate_password_hash(password)))
print('Admin account saved.')
