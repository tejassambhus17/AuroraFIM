# aurorafimpro/aurorafimpro/gui/widgets/login_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QPixmap

import sys
import os
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    # AuthHandler.authenticate_user now returns user_id
    from core.auth import AuthHandler
    import config
except ImportError as e:
    print(f"Error importing in login_dialog.py: {e}")
    AuthHandler = None
    config = None


class LoginDialog(QDialog):
    def __init__(self, auth_handler: AuthHandler, parent=None):
        super().__init__(parent)
        if not AuthHandler or not config:
            QMessageBox.critical(self, "Error", "Critical components missing.")
            # self.reject() # Let main handle exit if this is critical
            raise RuntimeError(
                "LoginDialog cannot operate without AuthHandler or Config.")

        self.auth_handler = auth_handler
        self.user_role = None
        self.username = None
        self.user_id_val = None  # To store the user_id

        self.setWindowTitle(f"Login - {config.APP_NAME}")
        self.setMinimumWidth(350)
        self.setModal(True)
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow(self.username_label, self.username_input)
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow(self.password_label, self.password_input)
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(15)
        self.button_box = QDialogButtonBox()
        self.login_button = self.button_box.addButton(
            "Login", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton(
            "Cancel", QDialogButtonBox.RejectRole)
        main_layout.addWidget(self.button_box)
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.setFocus()

    @Slot()
    def handle_login(self):
        username_val = self.username_input.text().strip()
        password_val = self.password_input.text()
        if not username_val or not password_val:
            QMessageBox.warning(self, "Login Failed",
                                "Username and password cannot be empty.")
            return

        # AuthHandler.authenticate_user returns: (isAuthenticated, username, role, user_id)
        is_authenticated, auth_username, user_role, user_id = self.auth_handler.authenticate_user(
            username_val, password_val)

        if is_authenticated:
            self.username = auth_username
            self.user_role = user_role
            self.user_id_val = user_id  # Store the user_id
            # QMessageBox.information(self, "Login Successful", f"Welcome, {self.username}! Role: {self.user_role.capitalize()}") # Message shown by main.py
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed",
                                "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    try:
        from core.auth import AuthHandler  # Re-import for test scope
        import config  # Re-import for test scope
        from database.db_setup import initialize_database
    except ModuleNotFoundError as e:
        print(f"Module not found for LoginDialog test: {e}")
        sys.exit(1)
    app = QApplication(sys.argv)
    print(
        f"Initializing DB for LoginDialog test: {os.path.join(config.BASE_DIR, config.DATABASE_NAME)}")
    initialize_database()
    test_auth_handler = AuthHandler()
    if test_auth_handler.get_user_count() == 0:
        print("Creating default admin for LoginDialog test.")
        test_auth_handler.create_user(
            "admin", "admin", "admin")  # Use "admin" if changed
    dialog = LoginDialog(test_auth_handler)
    if dialog.exec() == QDialog.Accepted:
        print(
            f"Login OK. User:{dialog.username}, Role:{dialog.user_role}, ID:{dialog.user_id_val}")
    else:
        print("Login cancelled/failed.")
    sys.exit(app.exec())
