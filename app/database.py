"""Database operations for user and license management"""

import sqlite3
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_FILE = "licenses.db"

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        license_key TEXT UNIQUE,
        expiry_date TEXT,
        last_checked TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
conn.commit()


def save_user(username, password):
    """Save user credentials with hashed password"""
    hashed_password = pwd_context.hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password),
    )
    conn.commit()


def get_user(username):
    """Retrieve user credentials"""
    cursor.execute(
        "SELECT id, username, password FROM users WHERE username = ?", (username,)
    )
    return cursor.fetchone()


def save_license(user_id, license_key, expiry_date):
    """Save the license key by encoding the details; expiry_date and last_checked"""
    cursor.execute(
        "INSERT INTO licenses (user_id, license_key, expiry_date, last_checked) VALUES (?, ?, ?, ?)",
        (
            user_id,
            license_key,
            expiry_date,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()


def get_license_by_user(user_id):
    """Get the license related details (expiry_date and last checked)"""
    cursor.execute(
        "SELECT license_key, expiry_date, last_checked FROM licenses WHERE user_id = ?",
        (user_id,),
    )
    return cursor.fetchone()


def update_last_checked(license_key):
    """Update the last checked date of the license so that
    applications could check if the license is still valid or has expired"""
    cursor.execute(
        "UPDATE licenses SET last_checked = ? WHERE license_key = ?",
        (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), license_key),
    )
    conn.commit()


def user_has_license(user_id):
    """Check if the user has a license"""
    cursor.execute("SELECT 1 FROM licenses WHERE user_id = ?", (user_id,))
    return cursor.fetchone()
