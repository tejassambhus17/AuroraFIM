# aurorafimpro/aurorafimpro/gui/widgets/login_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QFormLayout, QComboBox
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
    from core.validators import validate_username, validate_password, validate_role
    from core.logger import logger
    import config
except ImportError as e:
    class SimpleLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
        def debug(self, msg): pass
    logger = SimpleLogger()
    AuthHandler = None
    config = None
    validate_username = None
    validate_password = None
    validate_role = None
    logger = None


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
        self.setObjectName("LoginDialog")

        self.setWindowTitle(f"Login - {config.APP_NAME}")
        self.setMinimumWidth(350)
        self.setModal(True)
        main_layout = QVBoxLayout(self)
        title_label = QLabel("Welcome Back")
        title_label.setObjectName("LoginTitle")
        subtitle_label = QLabel("Sign in to continue to AuroraFIM Pro")
        subtitle_label.setObjectName("LoginSubtitle")
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(8)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        self.username_label = QLabel("Username:")
        self.username_label.setObjectName("FormLabel")
        self.username_input = QLineEdit()
        self.username_input.setObjectName("DialogInput")
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow(self.username_label, self.username_input)
        self.password_label = QLabel("Password:")
        self.password_label.setObjectName("FormLabel")
        self.password_input = QLineEdit()
        self.password_input.setObjectName("DialogInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow(self.password_label, self.password_input)
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(15)
        self.button_box = QDialogButtonBox()
        self.login_button = self.button_box.addButton(
            "Login", QDialogButtonBox.AcceptRole)
        self.login_button.setObjectName("PrimaryActionButton")
        self.create_user_button = self.button_box.addButton(
            "Create User", QDialogButtonBox.ApplyRole)
        self.create_user_button.setObjectName("SecondaryActionButton")
        self.cancel_button = self.button_box.addButton(
            "Cancel", QDialogButtonBox.RejectRole)
        self.cancel_button.setObjectName("SecondaryActionButton")
        main_layout.addWidget(self.button_box)
        self.login_button.clicked.connect(self.handle_login)
        self.create_user_button.clicked.connect(self.handle_create_user)
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

    @Slot()
    def handle_create_user(self):
        """Open dialog to create a new user."""
        create_dialog = CreateUserDialog(self.auth_handler, self)
        if create_dialog.exec() == QDialog.Accepted:
            QMessageBox.information(
                self, "Success", 
                f"User '{create_dialog.created_username}' created successfully!\n\n"
                "You can now log in with the new account."
            )
            # Clear fields and keep dialog open for login
            self.username_input.clear()
            self.password_input.clear()
            self.username_input.setFocus()


class CreateUserDialog(QDialog):
    """Dialog for creating a new user account."""
    
    def __init__(self, auth_handler: AuthHandler, parent=None):
        super().__init__(parent)
        self.auth_handler = auth_handler
        self.created_username = None
        self.setObjectName("CreateUserDialog")
        
        self.setWindowTitle(f"Create User - {config.APP_NAME}")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        main_layout = QVBoxLayout(self)
        title_label = QLabel("Create New User")
        title_label.setObjectName("CreateUserTitle")
        subtitle_label = QLabel("Define credentials and role for the new account")
        subtitle_label.setObjectName("CreateUserSubtitle")
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(8)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Username field
        self.username_label = QLabel("Username:")
        self.username_label.setObjectName("FormLabel")
        self.username_input = QLineEdit()
        self.username_input.setObjectName("DialogInput")
        self.username_input.setPlaceholderText("Enter new username (3-20 chars, alphanumeric, -, _)")
        form_layout.addRow(self.username_label, self.username_input)
        
        # Password field
        self.password_label = QLabel("Password:")
        self.password_label.setObjectName("FormLabel")
        self.password_input = QLineEdit()
        self.password_input.setObjectName("DialogInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Uppercase, lowercase, number, 8+ chars")
        form_layout.addRow(self.password_label, self.password_input)
        
        # Confirm password field
        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_label.setObjectName("FormLabel")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("DialogInput")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter password")
        form_layout.addRow(self.confirm_password_label, self.confirm_password_input)
        
        # Role field
        self.role_label = QLabel("Role:")
        self.role_label.setObjectName("FormLabel")
        self.role_combo = QComboBox()
        self.role_combo.setObjectName("DialogInput")
        self.role_combo.addItems(["auditor", "viewer", "admin"])
        form_layout.addRow(self.role_label, self.role_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(15)
        
        # Buttons
        button_box = QDialogButtonBox()
        self.create_btn = button_box.addButton(
            "Create", QDialogButtonBox.AcceptRole)
        self.create_btn.setObjectName("PrimaryActionButton")
        self.cancel_btn = button_box.addButton(
            "Cancel", QDialogButtonBox.RejectRole)
        self.cancel_btn.setObjectName("SecondaryActionButton")
        main_layout.addWidget(button_box)
        
        self.create_btn.clicked.connect(self.handle_create)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.username_input.setFocus()
    
    @Slot()
    def handle_create(self):
        """Handle user creation with validation."""
        username_val = self.username_input.text().strip()
        password_val = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role_val = self.role_combo.currentText()
        
        # Validate username
        is_valid, error = validate_username(username_val)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Username", f"Username error: {error}")
            self.username_input.setFocus()
            return
        
        # Validate password
        is_valid, error = validate_password(password_val)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Password", f"Password error: {error}")
            self.password_input.setFocus()
            return
        
        # Check password confirmation
        if password_val != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return
        
        # Validate role
        is_valid, error = validate_role(role_val)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Role", f"Role error: {error}")
            return
        
        # Try to create user
        try:
            if self.auth_handler.create_user(username_val, password_val, role_val):
                logger.info(f"User '{username_val}' created successfully with role '{role_val}'")
                self.created_username = username_val
                self.accept()
            else:
                QMessageBox.critical(
                    self, "Creation Failed", 
                    "Failed to create user. Username may already exist."
                )
                self.username_input.clear()
                self.username_input.setFocus()
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            QMessageBox.critical(
                self, "Error", 
                f"An error occurred while creating the user: {str(e)}"
            )


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    try:
        from core.auth import AuthHandler  # Re-import for test scope
        import config  # Re-import for test scope
        from database.db_setup import initialize_database
    except ModuleNotFoundError as e:
        logger.error(f"Module not found for LoginDialog test: {e}")
        sys.exit(1)
    app = QApplication(sys.argv)
    logger.info(f"Initializing DB for LoginDialog test: {os.path.join(config.BASE_DIR, config.DATABASE_NAME)}")
    initialize_database()
    test_auth_handler = AuthHandler()
    if test_auth_handler.get_user_count() == 0:
        logger.info("Creating default admin for LoginDialog test.")
        test_auth_handler.create_user(
            "admin", "admin", "admin")  # Use "admin" if changed
    dialog = LoginDialog(test_auth_handler)
    if dialog.exec() == QDialog.Accepted:
        logger.info(f"Login OK. User:{dialog.username}, Role:{dialog.user_role}, ID:{dialog.user_id_val}")
    else:
        logger.info("Login cancelled/failed.")
    sys.exit(app.exec())
