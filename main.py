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
    from gui.widgets.login_dialog import LoginDialog
    from core.auth import AuthHandler  # AuthHandler returns user_id now
    from core.fim import FIMEngine
    from core.action_logger import action_logger  # Import for initial app start log
    from database.db_setup import initialize_database
except ImportError as e:
    print(f"Critical Error importing modules in main.py: {e}")
    sys.exit(1)

fim_engine_global_instance = None


def setup_application_data_paths():  # (Same as before)
    paths_to_create = [os.path.join(config.BASE_DIR, config.SNAPSHOT_DIR_NAME), os.path.join(config.BASE_DIR, config.REPORTS_DIR_NAME), os.path.dirname(
        os.path.join(config.BASE_DIR, config.DATABASE_NAME)), os.path.dirname(os.path.join(config.BASE_DIR, config.LOG_FILE))]
    for p in paths_to_create:
        if not os.path.exists(p):
            try:
                os.makedirs(p, exist_ok=True)
                print(f"Ensured dir: {p}")
            except OSError as ex:
                print(f"Err creating dir {p}:{ex}")


# (Reverted to Original Logic)
def create_default_admin_if_needed(auth_handler: AuthHandler):
    if auth_handler.get_user_count() == 0:
        print("No users. Creating default admin...")
        if not auth_handler.create_user("admin", "admin", "admin"):
            print(f"Failed default admin.")
            QApplication.instance().quit()
            sys.exit("Crit err.")
        print(f"Default admin 'admin' created with pass 'admin'.")


def main():
    global fim_engine_global_instance
    app = QApplication(sys.argv)
    app.setOrganizationName("AuroraFIMSolutions")
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    if not os.path.exists(config.APP_SETTINGS_FILE):
        config.save_app_setting("current_ui_mode", config.DEFAULT_UI_MODE)
        config.CURRENT_UI_MODE = config.load_app_setting(
            "current_ui_mode", config.DEFAULT_UI_MODE)

    action_logger.log_action(action_type="APP_START", details={
                             "version": config.APP_VERSION})  # Log app start

    setup_application_data_paths()
    initialize_database()
    auth_handler = AuthHandler()
    create_default_admin_if_needed(auth_handler)
    fim_engine_global_instance = FIMEngine(auth_handler=auth_handler)
    if not fim_engine_global_instance.baseline_data and not os.path.exists(fim_engine_global_instance.baseline_file):
        print("WARN: No baseline. Live mon limited.")
        if not config.MONITORED_DIRECTORIES:
            print("INFO: MONITORED_DIRECTORIES empty.")

    login_dialog = LoginDialog(auth_handler)
    if login_dialog.exec() == QDialog.Accepted:
        # Assuming LoginDialog stores user_id_val
        current_user, current_role, current_user_id = login_dialog.username, login_dialog.user_role, login_dialog.user_id_val

        if current_user_id is None:  # Fallback if LoginDialog didn't provide it
            print(
                "Warning: User ID not retrieved from login dialog. Attempting re-fetch.")
            user_data_for_id = auth_handler.get_user(current_user)
            if user_data_for_id:
                current_user_id = user_data_for_id['id']
            else:
                print("CRITICAL: Could not retrieve user ID after login. Exiting.")
                sys.exit(1)

        print(
            f"Login successful. User: {current_user}, Role: {current_role}, ID: {current_user_id}")

        main_window = MainWindow(
            current_user, current_role, current_user_id, auth_handler, fim_engine_global_instance)
        main_window.show()
        QTimer.singleShot(100, fim_engine_global_instance.start_monitoring)
        if hasattr(main_window, 'tray_icon') and main_window.tray_icon and main_window.tray_icon.isVisible():
            status_msg = "Monitoring active." if fim_engine_global_instance.observer and fim_engine_global_instance.observer.is_alive(
            ) else "Monitoring not active."
            main_window.tray_icon.showMessage(
                f"{config.APP_NAME}", status_msg, QSystemTrayIcon.Information, 2000)
        exit_code = app.exec()
        action_logger.log_action(
            action_type="APP_SHUTDOWN", user_id=current_user_id, username=current_user)
        print("App exiting, stopping FIM mon...")
        if fim_engine_global_instance:
            fim_engine_global_instance.stop_monitoring()
        sys.exit(exit_code)
    else:
        action_logger.log_action(action_type="LOGIN_CANCELLED_OR_APP_EXIT")
        print("Login failed/cancelled. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()