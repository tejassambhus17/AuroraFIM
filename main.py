# aurorafimpro/aurorafimpro/main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory, QDialog, QSystemTrayIcon
from PySide6.QtCore import QTimer

# --- Path Setup ---
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)
project_root = os.path.dirname(package_dir)

try:
    import config
    from gui.main_window import MainWindow
    from gui.modern_style import ModernStylesheet
    from gui.widgets.login_dialog import LoginDialog
    from core.auth import AuthHandler
    from core.fim import FIMEngine
    from core.action_logger import action_logger
    from core.logger import logger
    from core.setup import setup_admin_user_interactive
    from database.db_setup import initialize_database
except ImportError as e:
    import sys
    sys.stderr.write(f"Critical Error importing modules in main.py: {e}\n")
    sys.exit(1)

fim_engine_global_instance = None


def setup_application_data_paths():
    """Create necessary application data directories."""
    paths_to_create = [
        os.path.join(config.BASE_DIR, config.SNAPSHOT_DIR_NAME),
        os.path.join(config.BASE_DIR, config.REPORTS_DIR_NAME),
        os.path.dirname(os.path.join(config.BASE_DIR, config.DATABASE_NAME)),
        os.path.dirname(os.path.join(config.BASE_DIR, config.LOG_FILE))
    ]
    for p in paths_to_create:
        if not os.path.exists(p):
            try:
                os.makedirs(p, exist_ok=True)
                logger.info(f"Created directory: {p}")
            except OSError as ex:
                logger.error(f"Error creating directory {p}: {ex}")

# No hard-coded credentials - setup is handled interactively
def ensure_admin_exists(auth_handler: AuthHandler) -> bool:
    """
    Ensure at least one admin user exists.
    If no users exist, prompt to create admin interactively.
    """
    if auth_handler.get_user_count() > 0:
        return True
    
    logger.info("No users found in database.")
    if not setup_admin_user_interactive(auth_handler):
        logger.critical("Failed to create admin user. Exiting.")
        QApplication.instance().quit()
        return False
    return True


def main():
    global fim_engine_global_instance
    app = QApplication(sys.argv)
    app.setOrganizationName("AuroraFIMSolutions")
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))

    app_settings = config.load_app_settings()
    if not os.path.exists(config.APP_SETTINGS_FILE):
        app_settings["current_ui_mode"] = config.DEFAULT_UI_MODE
        config.save_app_settings(app_settings)

    # Always load and apply persisted theme before any dialog opens.
    app_settings = config.load_app_settings()
    config.CURRENT_UI_MODE = app_settings.get(
        "current_ui_mode", config.DEFAULT_UI_MODE)
    ModernStylesheet.apply_modern_theme(
        app, dark_mode=(config.CURRENT_UI_MODE == "dark"))

    action_logger.log_action(action_type="APP_START", details={
                             "version": config.APP_VERSION})  # Log app start

    setup_application_data_paths()
    initialize_database()
    auth_handler = AuthHandler()
    
    if not ensure_admin_exists(auth_handler):
        sys.exit(1)
    
    fim_engine_global_instance = FIMEngine(auth_handler=auth_handler)
    if not fim_engine_global_instance.baseline_data and not os.path.exists(fim_engine_global_instance.baseline_file):
        logger.warning("No baseline found. Live monitoring limited.")
        if not config.MONITORED_DIRECTORIES:
            logger.info("MONITORED_DIRECTORIES is empty.")

    # Main loop for login/logout flow
    while True:
        login_dialog = LoginDialog(auth_handler)
        if login_dialog.exec() == QDialog.Accepted:
            # Assuming LoginDialog stores user_id_val
            current_user, current_role, current_user_id = login_dialog.username, login_dialog.user_role, login_dialog.user_id_val

            if current_user_id is None:
                logger.warning("User ID not retrieved from login dialog. Attempting re-fetch.")
                user_data_for_id = auth_handler.get_user(current_user)
                if user_data_for_id:
                    current_user_id = user_data_for_id['id']
                else:
                    logger.critical("Could not retrieve user ID after login. Exiting.")
                    sys.exit(1)

            logger.info(f"Login successful. User: {current_user}, Role: {current_role}, ID: {current_user_id}")

            main_window = MainWindow(
                current_user, current_role, current_user_id, auth_handler, fim_engine_global_instance)
            main_window.show()
            QTimer.singleShot(100, fim_engine_global_instance.start_monitoring)
            if hasattr(main_window, 'tray_icon') and main_window.tray_icon and main_window.tray_icon.isVisible():
                status_msg = "Monitoring active." if fim_engine_global_instance.observer and fim_engine_global_instance.observer.is_alive(
                ) else "Monitoring not active."
                main_window.tray_icon.showMessage(
                    f"{config.APP_NAME}", status_msg, QSystemTrayIcon.Information, 2000)
            app.exec()
            
            # Check if user logged out or quit
            if hasattr(main_window, 'logout_requested') and main_window.logout_requested:
                # User logged out, show login dialog again
                logger.info(f"User {current_user} logged out. Returning to login screen.")
                continue
            else:
                # User quit the application
                action_logger.log_action(
                    action_type="APP_SHUTDOWN", user_id=current_user_id, username=current_user)
                logger.info("Application exiting...")
                if fim_engine_global_instance:
                    fim_engine_global_instance.stop_monitoring()
                break
        else:
            action_logger.log_action(action_type="LOGIN_CANCELLED_OR_APP_EXIT")
            logger.info("Login cancelled or failed. Exiting.")
            break
    
    sys.exit(0)


if __name__ == "__main__":
    main()