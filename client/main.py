"""Module to create a GUI application for Software Licensing System"""

import json
import os
import sys
from datetime import datetime

import requests
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import QTimer

SERVER_URL = "http://127.0.0.1:8000"
LICENSE_FILE = "license.json"


def load_license():
    """Load the license details from the file"""
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_license(user_id, license_key, last_checked):
    """Save the license details and user_id to the file"""
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "user_id": user_id,
                "license_key": license_key,
                "last_checked": last_checked,
            },
            f,
        )


class LoginPage(QWidget):
    """Login Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.check_login)

        signup_btn = QPushButton("Don't have an account?")
        signup_btn.clicked.connect(self.goto_signup)

        layout.addWidget(QLabel("Login Page"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_btn)
        layout.addWidget(signup_btn)

        self.setLayout(layout)

    def check_login(self):
        """Check the login credentials"""
        username = self.username.text()
        password = self.password.text()

        response = requests.post(
            f"{SERVER_URL}/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code != 200:
            QMessageBox.warning(self, "Error", "Invalid credentials")
            return

        data = response.json()
        user_id = data.get("user_id")

        save_license(user_id, None, None)

        license_key = data.get("license_key")

        if not license_key:
            self.goto_license_generation_page()

        response = requests.post(
            f"{SERVER_URL}/verify-license/",
            json={"user_id": user_id, "license_key": license_key},
            timeout=10,
        )

        if response.status_code == 200:
            save_license(
                user_id, license_key, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            QMessageBox.information(self, "Status", "License verified.")
            self.stacked_widget.setCurrentIndex(5)  # Redirect to Main Application Page
        else:
            self.goto_license_verification_page()

    def goto_signup(self):
        """Redirect to the Signup Page"""
        self.stacked_widget.setCurrentIndex(2)

    def goto_license_verification_page(self):
        """Redirect to the License Verification Page"""
        self.stacked_widget.setCurrentIndex(4)

    def goto_license_generation_page(self):
        """Redirect to the License Generation Page"""
        self.stacked_widget.setCurrentIndex(3)


class SignupPage(QWidget):
    """Signup Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Choose a Username")

        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Choose a Password")
        self.password.setEchoMode(QLineEdit.Password)

        signup_btn = QPushButton("Sign Up")
        signup_btn.clicked.connect(self.create_account)

        back_btn = QPushButton("Back to Login")
        back_btn.clicked.connect(self.goto_login)

        layout.addWidget(QLabel("Signup Page"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(signup_btn)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def create_account(self):
        """Create a new account"""
        username = self.username.text()
        password = self.password.text()

        response = requests.post(
            f"{SERVER_URL}/signup",
            json={"username": username, "password": password},
            timeout=10,
        )
        data = response.json()
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Account Created!")
        save_license(user_id=data["user_id"], license_key=None, last_checked=None)
        self.goto_license_generation_page()

    def goto_license_generation_page(self):
        """Redirect to the License Generation Page"""
        self.stacked_widget.setCurrentIndex(3)

    def goto_login(self):
        """Redirect to the Login Page"""
        self.stacked_widget.setCurrentIndex(1)


class LicenseGenerationPage(QWidget):
    """License Generation Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        generate_btn = QPushButton("Generate License")
        generate_btn.clicked.connect(self.generate_license)

        layout.addWidget(QLabel("License Generation"))
        layout.addWidget(generate_btn)
        self.setLayout(layout)

    def generate_license(self):
        """Generate a new license"""
        expiry_days = 30
        user_id = load_license().get("user_id")
        response = requests.post(
            f"{SERVER_URL}/generate-license/",
            json={"expiry_days": expiry_days, "user_id": user_id},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            save_license(
                user_id,
                data["license_key"],
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            )
            QMessageBox.information(
                self, "Success", f"License Generated: {data['license_key']}"
            )
            self.stacked_widget.setCurrentIndex(5)  # Redirect to Main Page
        else:
            QMessageBox.warning(self, "Error", "Failed to Generate License")


class LicenseVerificationPage(QWidget):
    """License Verification Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        self.license_key = QLineEdit(self)
        self.license_key.setPlaceholderText("Enter License Key")

        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.verify_license)

        layout.addWidget(QLabel("License Verification"))
        layout.addWidget(self.license_key)
        layout.addWidget(submit_btn)
        self.setLayout(layout)

    def verify_license(self):
        """Verify the license key"""
        license_key = self.license_key.text()
        user_id = load_license().get("user_id")
        response = requests.post(
            f"{SERVER_URL}/verify-license/",
            json={"license_key": license_key, "user_id": user_id},
            timeout=10,
        )
        if response.status_code == 200:
            save_license(
                user_id, license_key, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            QMessageBox.information(self, "Success", "License Verified!")
            self.stacked_widget.setCurrentIndex(5)  # Redirect to Main Page
        else:
            QMessageBox.warning(self, "Error", "Invalid License Key")


class MainApplicationPage(QWidget):
    """Main Application Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Main Application Page"))
        self.setLayout(layout)


class Prechecks(QWidget):
    """Prechecks Page Widget"""

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Checking license..."))
        self.setLayout(layout)

        # Run prechecks after a short delay to allow UI to render
        QTimer.singleShot(100, self.run_prechecks)

    def run_prechecks(self):
        """Check if a valid license exists locally"""
        data = load_license()
        if not data:
            self.stacked_widget.setCurrentIndex(1)
            return

        license_key = data.get("license_key")
        user_id = data.get("user_id")

        if not user_id:
            self.stacked_widget.setCurrentIndex(1)
            return

        if not license_key:
            self.stacked_widget.setCurrentIndex(3)
            return

        response = requests.post(
            f"{SERVER_URL}/verify-license/",
            json={"license_key": license_key, "user_id": user_id},
            timeout=10,
        )
        if response.status_code == 200:
            save_license(
                user_id, license_key, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            QMessageBox.warning(self, "Error", "Invalid License Key")
            self.stacked_widget.setCurrentIndex(4)
            return

        self.stacked_widget.setCurrentIndex(5)


class App(QWidget):
    """Main Application Window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Software Licensing System")
        self.stacked_widget = QStackedWidget()

        self.prechecks_page = Prechecks(self.stacked_widget)
        self.login_page = LoginPage(self.stacked_widget)
        self.signup_page = SignupPage(self.stacked_widget)
        self.licesne_generation_page = LicenseGenerationPage(self.stacked_widget)
        self.license_verification_page = LicenseVerificationPage(self.stacked_widget)
        self.main_application_page = MainApplicationPage(self.stacked_widget)

        self.stacked_widget.addWidget(self.prechecks_page)
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        self.stacked_widget.addWidget(self.licesne_generation_page)
        self.stacked_widget.addWidget(self.license_verification_page)
        self.stacked_widget.addWidget(self.main_application_page)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        self.setGeometry(100, 100, 300, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
