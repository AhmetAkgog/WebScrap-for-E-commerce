import sys
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QMessageBox
from Main import ScraperGUI  # Import the main GUI


class LoginPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return

        if self.validate_login(username, password):
            self.open_main_gui(username, password)
        else:
            QMessageBox.warning(self, "Login Error", "Invalid username or password.")

    def validate_login(self, username, password):
        # Database connection parameters
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'password',
            'database': 'dbname'
        }

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Query to validate the username and password
            query = "SELECT * FROM logininfo WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))

            result = cursor.fetchone()
            conn.close()

            # Check if the query returned a result
            return result is not None
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Database Error", f"Error: {err}")
            return False

    def open_main_gui(self, username, password):
        self.scraper_gui = ScraperGUI(username, password)
        self.scraper_gui.show()
        self.close()  # Close the login window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginPage()
    login_window.show()
    sys.exit(app.exec_())
