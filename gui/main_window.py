# aurorafimpro/aurorafimpro/gui/main_window.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu,
    QToolBar, QLabel, QStyleFactory, QTabWidget, QMessageBox, QStyle,
    QDialog, QFileDialog, QToolButton, QSizePolicy
)
from PySide6.QtGui import QAction, QPalette, QColor, QIcon
from PySide6.QtCore import Qt, Slot, QMetaObject, Q_ARG, QTimer, QTime, QDate, QSize, QThreadPool
from datetime import datetime, time as dt_time
import os
import json  # Ensure json is imported for serialization

print(
    f"DEBUG: gui.main_window.py - Top of file, __name__ is {__name__} at {datetime.now()}")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
    from gui.widgets.dashboard_widget import DashboardWidget
    from gui.widgets.baseline_inspector_widget import BaselineInspectorWidget
    from gui.widgets.configure_paths_dialog import ConfigurePathsDialog
    from gui.widgets.user_activity_log_widget import UserActivityLogWidget
    from gui.widgets.uba_dashboard_widget import UbaDashboardWidget # NEW: UBA Dashboard
    from core.auth import AuthHandler
    from core.fim import FIMEngine
    from core.action_logger import action_logger
    from gui.widgets.worker import Worker
    from core.user_profiler import user_profiler # NEW: Import global profiler instance
except ImportError as e:
    import traceback
    print(
        f"CRITICAL DEBUG: Error during imports in main_window.py (or its dependencies): {e} at {datetime.now()}")
    traceback.print_exc()
    raise
print(
    f"DEBUG: gui.main_window.py - All helper imports successful. About to define MainWindow class at {datetime.now()}")


class MainWindow(QMainWindow):
    def __init__(self, current_user: str, current_role: str, user_id: int,
                 auth_handler: AuthHandler, fim_engine: FIMEngine, parent=None):
        super().__init__(parent)
        self.current_user, self.current_role, self.current_user_id = current_user, current_role, user_id
        self.auth_handler, self.fim_engine = auth_handler, fim_engine
        self.setWindowTitle(f"{config.APP_NAME} - {config.APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # UBA Timers and properties
        self.uba_profile_timer = QTimer(self)
        self.uba_risk_check_timer = QTimer(self)
        self.daily_risk_report = []

        self.icon_paths = {
            "app": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "app_icon.png"),
            "theme_light": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "sun.svg"),
            "theme_dark": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "moon.svg"),
            "quit": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "power.svg"),
            "dashboard": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "layout-dashboard.svg"),
            "inspector": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "search-check.svg"),
            "activity_log": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "list-checks.svg"),
            "uba": os.path.join(config.BASE_DIR, "aurorafimpro", "gui", "assets", "icons", "fingerprint.svg"), # NEW Icon for UBA (Conceptual path)
        }
        os.makedirs(os.path.dirname(self.icon_paths["app"]), exist_ok=True)
        if not os.path.exists(self.icon_paths["app"]):
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (32, 32), color=(73, 109, 137))
                d = ImageDraw.Draw(img)
                d.text((10, 10), "AF", fill=(255, 255, 0))
                img.save(self.icon_paths["app"])
                print(f"Dummy icon {self.icon_paths['app']}")
            except:
                print("Pillow not installed or error creating dummy icon.")
        if os.path.exists(self.icon_paths["app"]):
            self.setWindowIcon(QIcon(self.icon_paths["app"]))

        self.setup_ui_elements()
        self.setup_tray_icon()
        self.statusBar().showMessage(
            f"Logged in as: {self.current_user} ({self.current_role.capitalize()})")
        self.current_theme = config.CURRENT_UI_MODE
        self._apply_theme(self.current_theme)
        self._update_theme_action_text_and_icon()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        if hasattr(self.fim_engine, 'signals'):
            self.fim_engine.signals.scheduledAuditCompleted.connect(
                self.handle_scheduled_audit_completed)
            self.fim_engine.signals.liveFimEventDetected.connect(
                self.handle_live_fim_event)
        if hasattr(self.dashboard_widget, 'configurePathsRequested'):
            self.dashboard_widget.configurePathsRequested.connect(
                self.configure_monitored_paths_dialog)
        if hasattr(self.dashboard_widget, 'monitorSingleFileRequested'):
            self.dashboard_widget.monitorSingleFileRequested.connect(
                self.on_monitor_single_file)

        self.setup_scheduled_audit_timer()
        self.setup_uba_timers()
        self.last_scheduled_audit_date = None
        self.threadpool = QThreadPool.globalInstance()
        print(f"DEBUG: MainWindow.__init__ finished at {datetime.now()}")

    def _get_icon(self, key: str, fallback_style_enum=None):
        if key in self.icon_paths and os.path.exists(self.icon_paths[key]):
            return QIcon(self.icon_paths[key])
        elif fallback_style_enum:
            std_icon = self.style().standardIcon(fallback_style_enum)
            if not std_icon.isNull():
                return std_icon
        return QIcon()

    def setup_ui_elements(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.dashboard_widget = DashboardWidget(
            self.current_user, self.current_role, self.fim_engine)
        self.tab_widget.addTab(self.dashboard_widget, self._get_icon(
            "dashboard", QStyle.SP_FileDialogToParent), "Dashboard")
        self.baseline_inspector_widget = BaselineInspectorWidget(
            self.fim_engine)
        self.tab_widget.addTab(self.baseline_inspector_widget, self._get_icon(
            "inspector", QStyle.SP_FileDialogDetailedView), "Baseline Inspector")
        
        # NEW: UBA Dashboard Tab
        self.uba_dashboard_widget = UbaDashboardWidget(
            self.fim_engine)
        self.tab_widget.addTab(self.uba_dashboard_widget, self._get_icon(
            "uba", QStyle.SP_MessageBoxWarning), "UBA Dashboard")
            
        self.user_activity_log_widget = UserActivityLogWidget()
        self.tab_widget.addTab(self.user_activity_log_widget, self._get_icon(
            "activity_log", QStyle.SP_FileDialogListView), "User Activity")

        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(self.toolbar)

        self.theme_tool_button = QToolButton(self)
        self.theme_tool_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.theme_tool_button.setAutoRaise(True)
        self.theme_tool_button.setPopupMode(QToolButton.InstantPopup)
        self.theme_tool_button.setFixedHeight(36)
        self.theme_tool_button.setStyleSheet(
            "QToolButton { padding: 5px 10px; margin-right: 10px; }")
        self.theme_tool_button.clicked.connect(self.toggle_theme)
        self.toolbar.addWidget(self.theme_tool_button)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)

        self.quit_tool_button = QToolButton(self)
        self.quit_tool_button.setText("Quit Application")
        self.quit_tool_button.setIcon(self._get_icon(
            "quit", QStyle.SP_DialogCloseButton))
        self.quit_tool_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.quit_tool_button.setAutoRaise(True)
        self.quit_tool_button.setFixedHeight(36)
        self.quit_tool_button.setStyleSheet(
            "QToolButton { padding: 5px 10px; margin-left: 10px; }")
        self.quit_tool_button.clicked.connect(self.close)
        self.toolbar.addWidget(self.quit_tool_button)

    def setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("No tray.")
            self.tray_icon = None
            return
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = self._get_icon("app", QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip(f"{config.APP_NAME}")
        menu = QMenu(self)
        sa = QAction("Show", self)
        sa.triggered.connect(self.show_window_from_tray)
        qa = QAction("Quit", self)
        qa.triggered.connect(self.close)
        menu.addAction(sa)
        menu.addSeparator()
        menu.addAction(qa)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def setup_scheduled_audit_timer(self):
        self.audit_check_timer = QTimer(self)
        self.audit_check_timer.timeout.connect(
            self.check_and_run_scheduled_audit)
        ci = getattr(config, "SCHEDULED_AUDIT_CHECK_INTERVAL", 60000)
        self.audit_check_timer.start(ci)
        print(
            f"Sched audit timer started. Interval:{ci/1000}s. Daily at {config.DEFAULT_AUDIT_SCHEDULE_TIME}.")
        QTimer.singleShot(5000, self.check_and_run_scheduled_audit)

    # UPDATED FUNCTION: Setup UBA Timers
    def setup_uba_timers(self):
        """
        Sets up timers for periodic risk assessment. 
        Profile update is now handled manually/on-demand from the UBA Dashboard.
        """
        # 1. Periodic Risk Check (Lightweight, runs more often)
        self.uba_risk_check_timer.timeout.connect(self.run_risk_assessment)
        # Run every 5 minutes (300,000 ms)
        self.uba_risk_check_timer.start(300000) 
        QTimer.singleShot(15000, self.run_risk_assessment) # Run once after 15s to check initial anomalies

    @Slot()
    def check_and_run_scheduled_audit(self):
        try:
            h, m = map(int, config.DEFAULT_AUDIT_SCHEDULE_TIME.split(':'))
            st = dt_time(h, m)
        except ValueError:
            print(
                f"Error: Invalid schedule time '{config.DEFAULT_AUDIT_SCHEDULE_TIME}'.")
            self.audit_check_timer.stop()
            return
        n = datetime.now()
        ct = n.time()
        cd = n.date()
        if ct >= st and (self.last_scheduled_audit_date is None or self.last_scheduled_audit_date < cd):
            print(f"INFO:Triggering sched audit at {ct}.")
            self.trigger_scheduled_audit_worker()
            self.last_scheduled_audit_date = cd

    def trigger_scheduled_audit_worker(self):
        print("MW:Triggering sched audit worker...")
        if self.dashboard_widget:
            QMetaObject.invokeMethod(self.dashboard_widget, "update_integrity_badge", Qt.QueuedConnection, Q_ARG(
                str, "verifying"), Q_ARG(str, "Scheduled Audit Running..."))
        if not hasattr(self, 'threadpool') or self.threadpool is None:
            self.threadpool = QThreadPool.globalInstance()
        w = Worker(self.fim_engine.verify_integrity, True)
        w.signals.error.connect(self._handle_scheduled_audit_worker_error)
        w.signals.finished.connect(
            self._handle_scheduled_audit_worker_finished)
        self.threadpool.start(w)

    @Slot(tuple)
    def _handle_scheduled_audit_worker_error(self, err_tuple):
        et, v, tb = err_tuple
        print(f"CRIT:Sched audit err:{et},{v}\n{tb}")
        if self.dashboard_widget:
            QMetaObject.invokeMethod(self.dashboard_widget, "update_integrity_badge", Qt.QueuedConnection, Q_ARG(
                str, "error"), Q_ARG(str, "Sched Audit Failed"))
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "FIM - Audit Error", f"Sched audit failed:{v}", QSystemTrayIcon.Critical, 5000)

    @Slot()
    def _handle_scheduled_audit_worker_finished(
        self): print("MW:Sched audit worker finished.")

    @Slot(list, dict)
    def handle_scheduled_audit_completed(self, discrepancies: list, summary: dict):
        print(f"MW:Sched audit completed. Discrepancies:{len(discrepancies)}")
        if self.dashboard_widget:
            try:
                # Serialize summary to JSON string
                summary_str = json.dumps(summary)
                QMetaObject.invokeMethod(
                    self.dashboard_widget,
                    "refresh_after_audit",
                    Qt.QueuedConnection,
                    Q_ARG(str, summary_str)  # Pass as string
                )
            except TypeError as e:
                print(
                    f"ERROR serializing summary for Q_ARG in handle_scheduled_audit_completed: {e}. Summary: {summary}")

        if self.tray_icon and self.tray_icon.isVisible():
            ats = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            t = "FIM - Sched Audit"
            m = f"Audit @{ats}.\n"
            i = QSystemTrayIcon.Information
            if summary.get("scan_errors", 0) > 0:
                m += f"Errors:{summary['scan_errors']}"
                i = QSystemTrayIcon.Critical
            elif summary.get("mismatches_found", 0) > 0 or summary.get("new_files_detected", 0) > 0:
                m += f"Changes:{summary.get('mismatches_found', 0)+summary.get('new_files_detected', 0)}"
                i = QSystemTrayIcon.Warning
            else:
                m += "Secure."
            self.tray_icon.showMessage(t, m, i, 5000)

    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_icon_activated(self, r):
        if r == QSystemTrayIcon.Trigger:
            self.show_window_from_tray()

    def show_window_from_tray(self): self.showNormal(
    ); self.activateWindow(); self.raise_()

    @Slot(int)
    def on_tab_changed(self, idx):
        widget = self.tab_widget.widget(idx)
        if widget == self.baseline_inspector_widget:
            if hasattr(self.baseline_inspector_widget, 'load_and_display_baseline'):
                self.baseline_inspector_widget.load_and_display_baseline()
        elif widget == self.user_activity_log_widget:
            if hasattr(self.user_activity_log_widget, 'load_activity_log'):
                self.user_activity_log_widget.load_activity_log()
        elif widget == self.uba_dashboard_widget: # NEW: Refresh UBA dashboard
            if hasattr(self.uba_dashboard_widget, 'refresh_uba_data'):
                self.uba_dashboard_widget.refresh_uba_data()


    @Slot()
    def configure_monitored_paths_dialog(self):
        dialog = ConfigurePathsDialog(
            list(self.fim_engine.monitored_paths), self)
        if dialog.exec() == QDialog.Accepted:
            new_paths = dialog.get_updated_paths()
            print(f"MainWindow: New paths from Configure Dialog: {new_paths}")
            action_details = {"old_paths": list(
                self.fim_engine.monitored_paths), "new_paths": new_paths}
            if hasattr(self.fim_engine, 'update_monitored_paths_and_restart_observer'):
                self.fim_engine.update_monitored_paths_and_restart_observer(
                    new_paths)
                action_logger.log_action(action_type="CONFIG_PATHS_UPDATE", user_id=self.current_user_id,
                                         username=self.current_user, details=action_details, status="SUCCESS")
                QMessageBox.information(
                    self, "Paths Updated", "Monitored paths updated and monitoring restarted.")
            else:
                action_logger.log_action(action_type="CONFIG_PATHS_UPDATE", user_id=self.current_user_id,
                                         username=self.current_user, details=action_details, status="FAILURE", ip_address="FIM engine error")
                QMessageBox.warning(
                    self, "Error", "FIM Engine cannot update paths dynamically.")
        else:
            action_logger.log_action(action_type="CONFIG_PATHS_UPDATE_CANCELLED",
                                     user_id=self.current_user_id, username=self.current_user)
            print("Path configuration (dialog) cancelled.")

    @Slot()
    def on_monitor_single_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Single File to Monitor & Baseline", os.path.expanduser("~"), "All Files (*.*)")
        if file_path:
            abs_file_path = os.path.abspath(file_path)
            print(f"MainWindow: User selected single file: {abs_file_path}")
            success, message = self.fim_engine.add_and_baseline_single_file(
                abs_file_path)
            log_details = {"file_path": abs_file_path, "message": message}
            if success:
                action_logger.log_action(action_type="SET_BASELINE_SINGLE", user_id=self.current_user_id,
                                         username=self.current_user, details=log_details, status="SUCCESS")
                QMessageBox.information(self, "File Monitored", message)
                current_monitored_paths = list(config.MONITORED_DIRECTORIES)
                is_newly_added_to_config = False
                if abs_file_path not in current_monitored_paths:
                    is_covered = False
                    for p_dir in current_monitored_paths:
                        if os.path.isdir(p_dir) and abs_file_path.startswith(os.path.abspath(p_dir) + os.sep):
                            is_covered = True
                            break
                    if not is_covered:
                        current_monitored_paths.append(abs_file_path)
                        is_newly_added_to_config = True

                if is_newly_added_to_config:
                    config.update_monitored_directories(
                        current_monitored_paths)
                    if hasattr(self.fim_engine, 'update_monitored_paths_and_restart_observer'):
                        self.fim_engine.update_monitored_paths_and_restart_observer(
                            config.MONITORED_DIRECTORIES)

                if self.tab_widget.currentWidget() == self.baseline_inspector_widget:
                    if hasattr(self.baseline_inspector_widget, 'load_and_display_baseline'):
                        self.baseline_inspector_widget.load_and_display_baseline()
            else:
                action_logger.log_action(action_type="SET_BASELINE_SINGLE", user_id=self.current_user_id,
                                         username=self.current_user, details=log_details, status="FAILURE")
                QMessageBox.critical(self, "Error Monitoring File", message)
        else:
            action_logger.log_action(action_type="SET_BASELINE_SINGLE_CANCELLED",
                                     user_id=self.current_user_id, username=self.current_user)
            print("MainWindow: Single file selection cancelled.")

    # NEW SLOT: Run Daily Profile Update (No longer checks time, runs immediately on trigger)
    @Slot()
    def run_profile_update(self):
        """Manually triggers the user profile update."""
        print("INFO: Manually triggering user profile update...")
        worker = Worker(self.fim_engine.update_user_profiles)
        worker.signals.result.connect(lambda r: print(f"INFO: Profile update worker finished. Success: {r}."))
        self.threadpool.start(worker)

    # NEW SLOT: Run Periodic Risk Assessment
    @Slot()
    def run_risk_assessment(self):
        """Runs the periodic risk assessment for all users in a worker thread."""
        print("INFO: Starting periodic risk assessment...")
        worker = Worker(self.fim_engine.trigger_risk_assessment)
        worker.signals.result.connect(self._handle_risk_report)
        self.threadpool.start(worker)

    # NEW SLOT: Handle Risk Report Result
    @Slot(list)
    def _handle_risk_report(self, risk_report: list):
        """Processes the risk report and updates the UI/sends alerts."""
        self.daily_risk_report = risk_report
        
        # Manually refresh the UBA dashboard widget on a successful risk report calculation
        QMetaObject.invokeMethod(self.uba_dashboard_widget, "load_risk_report", Qt.QueuedConnection)

        high_risk_users = [r for r in risk_report if r['classification'] == 'High Risk']
        
        if high_risk_users:
            msg = f"HIGH RISK ALERT: {len(high_risk_users)} user(s) detected with critical anomalies."
            self.statusBar().showMessage(msg, 5000)
            if self.tray_icon and self.tray_icon.isVisible():
                user_list = ', '.join([r['username'] for r in high_risk_users][:3])
                self.tray_icon.showMessage(
                    "UBA High Risk Alert", 
                    f"Anomaly detected for: {user_list}...", 
                    QSystemTrayIcon.Critical, 5000)
        
        # Log the generation of the report (as system action)
        risk_summary = {'total_risky_users': len(risk_report), 'high_risk_count': len(high_risk_users)}
        action_logger.log_action(action_type="UBA_RISK_REPORT", username="System/UBA", 
                                 details=risk_summary, status="SUCCESS")


    @Slot()
    def toggle_theme(self):
        self.current_theme = "dark"if self.current_theme == "light"else "light"
        self._apply_theme(self.current_theme)
        config.set_current_ui_mode(self.current_theme)
        self._update_theme_action_text_and_icon()
        self.statusBar().showMessage(
            f"Theme:{self.current_theme.capitalize()}.", 3000)

    def _update_theme_action_text_and_icon(self):
        if hasattr(self, 'theme_tool_button'):
            if self.current_theme == "light":
                self.theme_tool_button.setText(" Switch to Dark Mode")
                self.theme_tool_button.setIcon(self._get_icon(
                    "theme_dark", QStyle.SP_TitleBarMenuButton))
            else:
                self.theme_tool_button.setText(" Switch to Light Mode")
                self.theme_tool_button.setIcon(self._get_icon(
                    "theme_light", QStyle.SP_DialogHelpButton))

    def _apply_theme(self, theme_name: str):
        app = QApplication.instance()
        if not app:
            return
        if app.style().objectName().lower() != "fusion":
            app.setStyle(QStyleFactory.create("Fusion"))
        cp = config.DARK_THEME_PALETTE if theme_name == "dark"else config.LIGHT_THEME_PALETTE
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(cp["window"]))
        p.setColor(QPalette.ColorRole.WindowText, QColor(cp["windowText"]))
        p.setColor(QPalette.ColorRole.Base, QColor(cp["base"]))
        p.setColor(QPalette.ColorRole.AlternateBase,
                   QColor(cp["alternateBase"]))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor(cp["toolTipBase"]))
        p.setColor(QPalette.ColorRole.ToolTipText, QColor(cp["toolTipText"]))
        p.setColor(QPalette.ColorRole.Text, QColor(cp["text"]))
        p.setColor(QPalette.ColorRole.Button, QColor(cp["button"]))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(cp["buttonText"]))
        p.setColor(QPalette.ColorRole.BrightText, QColor(cp["brightText"]))
        p.setColor(QPalette.ColorRole.Link, QColor(cp["accent"]))
        p.setColor(QPalette.ColorRole.Highlight, QColor(cp["highlight"]))
        p.setColor(QPalette.ColorRole.HighlightedText,
                   QColor(cp["highlightedText"]))
        p.setColor(QPalette.ColorGroup.Disabled,
                   QPalette.ColorRole.Text, QColor(cp["disabledText"]))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(
            cp["disabledButtonText"]))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(
            cp["disabledWindowText"]))
        app.setPalette(p)
        qss_template = getattr(
            config, "GENERAL_STYLESHEET_TEMPLATE", "QWidget{}")
        qss = qss_template.format(**cp)
        app.setStyleSheet(qss)
        if hasattr(self, 'tab_widget') and self.tab_widget:
            self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
        if hasattr(self.dashboard_widget, 'update_styles_for_theme'):
            self.dashboard_widget.update_styles_for_theme(theme_name)
        if hasattr(self.baseline_inspector_widget, 'update_styles_for_theme'):
            self.baseline_inspector_widget.update_styles_for_theme(theme_name)
        if hasattr(self, 'user_activity_log_widget') and hasattr(self.user_activity_log_widget, 'update_styles_for_theme'):
            self.user_activity_log_widget.update_styles_for_theme(theme_name)
        if hasattr(self, 'uba_dashboard_widget') and hasattr(self.uba_dashboard_widget, 'update_styles_for_theme'): # NEW: UBA Dashboard theme update
            self.uba_dashboard_widget.update_styles_for_theme(theme_name)

    def handle_live_fim_event(self, event_details: dict):
        print(
            f"DEBUG:MW.handle_live_fim_event rcvd:{event_details} at {datetime.now()}")
        if self.dashboard_widget:
            try:
                # Serialize dict to JSON string
                event_details_str = json.dumps(event_details)
                QMetaObject.invokeMethod(
                    self.dashboard_widget,
                    "add_live_event_to_table",
                    Qt.QueuedConnection,
                    Q_ARG(str, event_details_str)  # Pass as string
                )
            except TypeError as e:
                print(
                    f"ERROR serializing event_details for Q_ARG:{e}. Event:{event_details}")
        et = event_details.get("change_type", "").upper()
        fp = event_details.get("path", "N/A")
        mi = QSystemTrayIcon.Information
        ti = "FIM Event"
        msg = f"{et}:{os.path.basename(fp)}"
        if "ERROR" in et:
            mi = QSystemTrayIcon.Critical
            ti = "FIM Error"
        elif any(s in et for s in ["MODIFIED", "REMOVED", "DELETED", "NEW", "CREATED", "MOVED"]):
            mi = QSystemTrayIcon.Warning
            ti = "FIM Alert"
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(ti, msg, mi, 3000)

    def closeEvent(self, event):
        if self.tray_icon and self.tray_icon.isVisible() and getattr(config, "MINIMIZE_TO_TRAY_ON_CLOSE", True):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                f"{config.APP_NAME}", "Minimized.", QSystemTrayIcon.Information, 1500)
        else:
            if QMessageBox.question(self, 'Quit', "Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
                # Stop UBA timers before quitting
                self.uba_profile_timer.stop()
                self.uba_risk_check_timer.stop()
                
                action_logger.log_action(
                    action_type="APP_QUIT", user_id=self.current_user_id, username=self.current_user)
                print("Closing...")
                QApplication.instance().quit()
                event.accept()
            else:
                event.ignore()


print(
    f"DEBUG: gui.main_window.py - MainWindow class defined at {datetime.now()}")
if __name__ == '__main__':
    print(f"DEBUG: gui.main_window.py running as __main__ at {datetime.now()}")
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))

    class MA:
        def get_user_count(s): return 1
        def create_user(s, u, p, r): return True

    class MF:
        def __init__(s, a=None): s.monitored_paths, s.baseline_data, s.baseline_file = ["/dummy"], {}, "mock_baseline.json"; s.signals = type(
            's', (), {'scheduledAuditCompleted': Signal(list, dict), 'liveFimEventDetected': Signal(dict)})()

        def add_monitored_path(s, p): pass; load_baseline = lambda s: True; start_monitoring = lambda s: print("MockFIM:SM"); stop_monitoring = lambda s: print("MockFIM:SM"); update_monitored_paths_and_restart_observer = lambda s, p: setattr(s, 'monitored_paths', p)

        def get_recent_events_from_db(s, l=None): return []; verify_integrity = lambda s, sched=False: (
            ([], {"message": "Mock Verify"}), s.signals.scheduledAuditCompleted.emit([], {"message": "Mock Verify Done"}) if sched else None)[0]

        def add_and_baseline_single_file(s, fp): print(
            f"MockFIM: Add & Baseline {fp}"); return (True, f"Mocked {fp}")
        
        # Mock UBA methods
        def update_user_profiles(s): return True
        def trigger_risk_assessment(s): return [{'username': 'TU', 'risk_score': 80, 'classification': 'High Risk'}]


    m_a, m_f = MA(), MF()
    if 'config' not in globals() or globals()['config'] is None:
        class TC:
            APP_NAME = "Test"
            APP_VERSION = "0"
            CURRENT_UI_MODE = "light"
            DARK_THEME_PALETTE = {"window": "#eee", "windowText": "#000", "base": "#fff", "borderColor": "#ccc", "button": "#ddd", "buttonText": "#000", "highlight": "#38f", "highlightedText": "#fff",
                                  "accent": "#007bff", "tableHeaderBg": "#eee", "tableGrid": "#ddd", "disabledButtonBackground": "#ccc", "disabledBorderColor": "#bbb", "disabledButtonText": "#888", "text": "#000", "successGreen": "#4CAF50", "warningOrange": "#FFC107", "dangerRed": "#F44336"}
            LIGHT_THEME_PALETTE = TC.DARK_THEME_PALETTE
            MINIMIZE_TO_TRAY_ON_CLOSE = False
            BASE_DIR = "."
            DEFAULT_AUDIT_SCHEDULE_TIME = "00:00"
            SCHEDULED_AUDIT_CHECK_INTERVAL = 60000
            GENERAL_STYLESHEET_TEMPLATE = "QWidget{{background-color:{window};}}"
            icon_paths = {}
            MONITORED_DIRECTORIES = []
            def update_monitored_directories(p): return None
        config = TC()
        print("DEBUG: MW __main__ using TempConfig")
    if not hasattr(config, 'GENERAL_STYLESHEET_TEMPLATE'):
        config.GENERAL_STYLESHEET_TEMPLATE = "QWidget{{}}"
    if not os.path.exists(getattr(config, 'APP_SETTINGS_FILE', "app_settings.json")):
        import json
        sf = getattr(config, 'APP_SETTINGS_FILE', "app_settings.json")
        f = open(sf, 'w')
        json.dump({"current_ui_mode": getattr(
            config, 'DEFAULT_UI_MODE', "light")}, f)
        f.close()
    mw = MainWindow("TU", "Tester", 0, m_a, m_f)
    mw.show()
    print(
        f"DEBUG: gui.main_window.py __main__ - Main window shown, starting exec loop at {datetime.now()}")
    sys.exit(app.exec())
print(f"DEBUG: gui.main_window.py - End of file at {datetime.now()}")