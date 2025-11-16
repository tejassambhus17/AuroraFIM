# aurorafimpro/aurorafimpro/gui/widgets/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QSizePolicy, QMessageBox, QProgressDialog, QApplication, QStyle
)
from PySide6.QtCore import (Qt, Slot, QThreadPool, QObject, Signal,
                            QTimer, QSize, QMetaObject, Q_ARG) 
from PySide6.QtGui import QIcon, QColor, QFont, QPalette
import time
import os
import subprocess
import sys
from datetime import datetime
import json

# Ensure the package root is in sys.path
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    import config
    from core.fim import FIMEngine
    from core.reporting import ReportGenerator
    from gui.widgets.worker import Worker
    from core.auth import AuthHandler
    from core.simulator import Simulator
    from core.action_logger import action_logger
except ImportError as e:
    print(f"ERROR: Error importing modules in dashboard_widget.py: {e}")
    # Fallback mocks
    config = type('MockConfig', (), {
        'MONITORED_DIRECTORIES': [],
        'MAX_EVENTS_IN_DASHBOARD': 50,
        'DASHBOARD_EVENT_REFRESH_INTERVAL': 300000,
        'APP_NAME': 'MockApp FIM',
        'LIGHT_THEME_PALETTE': {"accent": "#308cc6", "text": "#000000", "window": "#f0f0f0", "base": "#ffffff", "button": "#e0e0e0", "buttonText": "#000", "borderColor": "#ccc", "tableHeaderBg": "#eee", "tableGrid": "#ddd", "statusBarBg": "#e0e0e0", "menuBarBg": "#f0f0f0", "alternateBase": "#f5f5f5", "disabledButtonBackground": "#d0d0d0", "disabledBorderColor": "#b0b0b0", "disabledButtonText": "#a0a0a0", "successGreen": "#27ae60", "warningOrange": "#e67e22", "dangerRed": "#c0392b", "unknownGrey": "#95a5a6", "highlightedText": "#ffffff"},
        'DARK_THEME_PALETTE': {"accent": "#00aeff", "text": "#d0d0d0", "window": "#2b2b2b", "base": "#1e1e1e", "button": "#3c3f41", "buttonText": "#e0e0e0", "borderColor": "#4a4a4a", "tableHeaderBg": "#383838", "tableGrid": "#404040", "statusBarBg": "#232323", "menuBarBg": "#282828", "alternateBase": "#333333", "disabledButtonBackground": "#2c2c2c", "disabledBorderColor": "#3a3a3a", "disabledButtonText": "#777777", "successGreen": "#2ecc71", "warningOrange": "#f39c12", "dangerRed": "#e74c3c", "unknownGrey": "#7f8c8d", "highlightedText": "#000000"},
        'CURRENT_UI_MODE': 'dark',
        'GENERAL_STYLESHEET_TEMPLATE': "QWidget{{}}"
    })()
    FIMEngine = type('MockFIMEngine', (), {'__init__': lambda s, a=None: setattr(s, 'baseline_data', {}), 'verify_integrity': lambda s, sched=False: (
        [], {'message': 'mock'}), 'create_new_baseline': lambda s: (False, {'message': 'mock'}), 'get_recent_events_from_db': lambda s, l=None: []})()
    ReportGenerator = None
    class MockWorker:
        def __init__(self, fn, *args, **kwargs):
            self.fn = fn
            self.args = args
            self.kwargs = kwargs
            from PySide6.QtCore import QObject, Signal
            class MockWorkerSignals(QObject):
                finished = Signal()
                error = Signal(tuple)
                result = Signal(object)
            self.signals = MockWorkerSignals()

        @Slot()
        def run(self):
            try:
                result = self.fn(*self.args, **self.kwargs)
                self.signals.result.emit(result)
            except Exception as e:
                self.signals.error.emit((type(e), e, str(e)))
            finally:
                self.signals.finished.emit()
                
    Worker = MockWorker
    AuthHandler = None
    class MockSimulator:
        def __init__(self, *args): pass
        def run_anomaly_scenario(self): return "Mock Simulation: Anomaly simulated."
    Simulator = MockSimulator
    class MockActionLogger:
        def log_action(self, *args, **kwargs): pass
    action_logger = MockActionLogger()


class DashboardWidgetSignals(QObject):
    configurePathsRequested = Signal()
    monitorSingleFileRequested = Signal()


class DashboardWidget(QWidget):
    configurePathsRequested = Signal()
    monitorSingleFileRequested = Signal()

    def __init__(self, current_user: str, current_role: str,
                 fim_engine: FIMEngine, parent=None):
        super().__init__(parent)
        self.current_user, self.current_role = current_user, current_role
        
        # Initialize Simulator
        self.simulator = None
        if fim_engine and fim_engine.auth_handler and Simulator:
            try:
                self.simulator = Simulator(fim_engine, fim_engine.auth_handler)
                print("INFO: Simulator initialized.")
            except Exception as e:
                print(f"WARNING: Simulator failed to initialize: {e}")
        elif self.current_role == "admin":
             print("WARNING: Simulator not initialized. Missing dependencies or mock.")

        if FIMEngine is None or Worker is None:
            critical_error = "DashboardWidget cannot operate due to missing critical components (FIMEngine or Worker)."
            print(f"CRITICAL ERROR: {critical_error}")
            raise RuntimeError(critical_error)
        if ReportGenerator is None:
            print(
                "Warning: ReportGenerator module not loaded. Reporting will be disabled.")

        self.fim_engine = fim_engine
        self.threadpool = QThreadPool.globalInstance()
        self.setObjectName("DashboardWidget")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(20)

        self.integrity_badge_frame = QFrame()
        self.integrity_badge_frame.setObjectName("IntegrityBadgeFrame")
        self.integrity_badge_frame.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        badge_layout = QVBoxLayout(self.integrity_badge_frame)
        badge_layout.setAlignment(Qt.AlignCenter)

        self.integrity_status_label = QLabel("SYSTEM STATUS")
        self.integrity_status_label.setObjectName("IntegrityStatusLabel")
        sf = self.integrity_status_label.font()
        sf.setPointSize(10)
        self.integrity_status_label.setFont(sf)
        self.integrity_status_label.setAlignment(Qt.AlignCenter)

        self.integrity_badge_indicator = QLabel("UNKNOWN")
        bf = self.integrity_badge_indicator.font()
        bf.setPointSize(22)
        bf.setBold(True)
        self.integrity_badge_indicator.setFont(bf)
        self.integrity_badge_indicator.setAlignment(Qt.AlignCenter)
        self.integrity_badge_indicator.setStyleSheet(
            "padding: 15px 20px; border-radius: 8px; min-width: 150px;")
        
        self.last_audit_label = QLabel("Last Audit: Never")
        laf = self.last_audit_label.font()
        laf.setPointSize(8)
        self.last_audit_label.setFont(laf)
        self.last_audit_label.setAlignment(Qt.AlignCenter)
        
        badge_layout.addWidget(self.integrity_status_label)
        badge_layout.addWidget(self.integrity_badge_indicator)
        badge_layout.addWidget(self.last_audit_label)
        
        if self.fim_engine and hasattr(self.fim_engine, 'baseline_data') and self.fim_engine.baseline_data:
            self.update_integrity_badge("unknown", "Baseline Loaded")
        else:
            self.update_integrity_badge("unknown", "No Baseline")
        top_section_layout.addWidget(self.integrity_badge_frame, 1)

        self.quick_actions_frame = QFrame()
        self.quick_actions_frame.setObjectName("QuickActionsFrame")
        al = QVBoxLayout(self.quick_actions_frame)
        al.setSpacing(10)
        al.setAlignment(Qt.AlignTop)

        at = QLabel("Quick Actions")
        at.setObjectName("QuickActionsTitle")
        atf = at.font()
        atf.setPointSize(12)
        at.setFont(atf)
        al.addWidget(at)

        icon_size = QSize(18, 18)
        verify_icon = self.style().standardIcon(QStyle.SP_DialogApplyButton)
        baseline_icon = self.style().standardIcon(QStyle.SP_DriveHDIcon)
        report_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        configure_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        add_file_icon = self.style().standardIcon(QStyle.SP_FileLinkIcon)
        
        self.verify_baseline_button = QPushButton(" Verify Integrity")
        self.verify_baseline_button.setIcon(verify_icon)
        self.verify_baseline_button.setIconSize(icon_size)
        self.set_new_baseline_button = QPushButton(
            " Set New Baseline (All Monitored)")
        self.set_new_baseline_button.setIcon(baseline_icon)
        self.set_new_baseline_button.setIconSize(icon_size)
        self.monitor_single_file_button = QPushButton(
            " Monitor & Baseline Single File")
        self.monitor_single_file_button.setIcon(add_file_icon)
        self.monitor_single_file_button.setIconSize(icon_size)
        self.generate_report_button = QPushButton(" Generate Report")
        self.generate_report_button.setIcon(report_icon)
        self.generate_report_button.setIconSize(icon_size)
        
        # Simulator Button
        self.simulation_button = QPushButton(" UBA: Run Anomaly Simulation")
        self.simulation_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
        self.simulation_button.setIconSize(icon_size)
        self.simulation_button.clicked.connect(self.on_run_simulation_clicked)
        
        # Admin: Configure Paths Button
        self.configure_paths_button = QPushButton(" Admin: Configure Paths")
        self.configure_paths_button.setIcon(configure_icon)
        self.configure_paths_button.setIconSize(icon_size)
        self.configure_paths_button.clicked.connect(
            self.on_configure_paths_clicked)
        
        # Conditional Visibility for Simulation Button
        if self.current_role != "admin":
            self.simulation_button.setVisible(False)


        quick_action_buttons = [self.verify_baseline_button, self.set_new_baseline_button,
                                self.monitor_single_file_button, self.generate_report_button, self.simulation_button, self.configure_paths_button]
        
        for btn in quick_action_buttons:
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            al.addWidget(btn)

        al.addStretch()
        top_section_layout.addWidget(self.quick_actions_frame, 2)
        main_layout.addLayout(top_section_layout)

        ehl = QHBoxLayout()
        self.recent_events_title_label = QLabel("Recent Integrity Events")
        self.recent_events_title_label.setObjectName("RecentEventsTitleLabel")
        etf = self.recent_events_title_label.font()
        etf.setPointSize(12)
        self.recent_events_title_label.setFont(etf) # FIX: Set font on QLabel object
        ehl.addWidget(self.recent_events_title_label)
        ehl.addStretch()
        self.refresh_events_button = QPushButton("Refresh Events")
        self.refresh_events_button.clicked.connect(
            self.refresh_events_table_from_db)
        ehl.addWidget(self.refresh_events_button)
        main_layout.addLayout(ehl)

        self.recent_events_table = QTableWidget()
        self.recent_events_table.setColumnCount(3)
        self.recent_events_table.setHorizontalHeaderLabels(
            ["Timestamp", "File Path", "Event Type"])
        self.recent_events_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.recent_events_table.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.recent_events_table.setAlternatingRowColors(True)
        self.recent_events_table.verticalHeader().setVisible(False)
        self.recent_events_table.horizontalHeader().setStretchLastSection(True)
        self.recent_events_table.horizontalHeader().setSectionResizeMode(0,
                                                                         QHeaderView.ResizeToContents)
        self.recent_events_table.horizontalHeader(
        ).setSectionResizeMode(1, QHeaderView.Stretch)
        self.recent_events_table.horizontalHeader().setSectionResizeMode(2,
                                                                         QHeaderView.ResizeToContents)
        main_layout.addWidget(self.recent_events_table)

        self.verify_baseline_button.clicked.connect(
            self.on_verify_integrity_clicked)
        self.set_new_baseline_button.clicked.connect(
            self.on_set_new_baseline_clicked)
        self.generate_report_button.clicked.connect(
            self.on_generate_report_clicked)
        self.progress_dialog = None
        self.refresh_events_table_from_db()
        self.event_refresh_timer = QTimer(self)
        ri = getattr(config, "DASHBOARD_EVENT_REFRESH_INTERVAL", 300000)
        self.event_refresh_timer.timeout.connect(
            self.refresh_events_table_from_db)
        self.event_refresh_timer.start(ri)
        self.last_audit_summary_for_report = {}
        self.original_event_title_stylesheet = self.recent_events_title_label.styleSheet()

    def _show_progress_dialog(self, t: str, txt: str):
        if self.progress_dialog is None:
            self.progress_dialog = QProgressDialog(txt, None, 0, 0, self)
            self.progress_dialog.setWindowTitle(t)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
        else:
            self.progress_dialog.setWindowTitle(t)
            self.progress_dialog.setLabelText(txt)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        QApplication.processEvents()

    def _hide_progress_dialog(self):
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.close()

    def update_integrity_badge(self, status: str, last_audit_time: str = "Never"):
        if hasattr(self, 'last_audit_label'):
            self.last_audit_label.setText(f"Last Audit: {last_audit_time}")
        current_palette = config.DARK_THEME_PALETTE if config.CURRENT_UI_MODE == "dark" else config.LIGHT_THEME_PALETTE
        color_map = {
            "secure": ("SECURE", current_palette.get("successGreen", "#4CAF50"), current_palette.get("highlightedText", "white")),
            "compromised": ("COMPROMISED", current_palette.get("dangerRed", "#F44336"), current_palette.get("highlightedText", "white")),
            "verifying": ("VERIFYING...", current_palette.get("warningOrange", "#FFC107"), current_palette.get("text", "black")),
            "unknown": ("UNKNOWN", current_palette.get("unknownGrey", "#9E9E9E"), current_palette.get("highlightedText", "white")),
            "error": ("ERROR", current_palette.get("warningOrange", "#FF9800"), current_palette.get("text", "black")),
            "no_baseline": ("NO BASELINE", current_palette.get("unknownGrey", "#757575"), current_palette.get("highlightedText", "white"))
        }
        t, bg, fg = color_map.get(status.lower(), ("UNKNOWN", current_palette.get(
            "unknownGrey", "#9E9E9E"), current_palette.get("highlightedText", "white")))
        self.integrity_badge_indicator.setText(t)
        self.integrity_badge_indicator.setStyleSheet(
            f"background-color:{bg};color:{fg};padding:15px 20px;border-radius:8px;min-width:150px;")

    @Slot()
    def refresh_events_table_from_db(self):
        if not self.fim_engine:
            return
        print("DEBUG Dashboard: Refreshing events table from DB...")
        events_data = self.fim_engine.get_recent_events_from_db()
        print(
            f"DEBUG Dashboard: Fetched {len(events_data)} events from DB for refresh.")
        self._populate_events_table_ui(events_data)

    def _populate_events_table_ui(self, events_data: list):
        print(
            f"DEBUG Dashboard: _populate_events_table_ui called with {len(events_data)} events.")
        self.recent_events_table.setSortingEnabled(False)
        self.recent_events_table.setRowCount(0)
        for i, ev in enumerate(events_data):
            self.recent_events_table.insertRow(
                self.recent_events_table.rowCount())
            ts_f = ev.get("event_timestamp", 0.0)
            ts_s = datetime.fromtimestamp(ts_f).strftime(
                '%Y-%m-%d %H:%M:%S')if ts_f else "N/A"
            self.recent_events_table.setItem(i, 0, QTableWidgetItem(ts_s))
            self.recent_events_table.setItem(
                i, 1, QTableWidgetItem(ev.get("file_path", "N/A")))
            self.recent_events_table.setItem(
                i, 2, QTableWidgetItem(ev.get("event_type", "N/A")))
        self.recent_events_table.setSortingEnabled(True)
        self.recent_events_table.resizeColumnsToContents()
        print(
            f"DEBUG Dashboard: Table populated. Row count: {self.recent_events_table.rowCount()}")

    @Slot(str)
    def add_live_event_to_table(self, event_details_str: str):
        try:
            event_details = json.loads(event_details_str)
        except json.JSONDecodeError as e:
            print(
                f"ERROR Dashboard: Could not decode live event JSON: {e}. Data: {event_details_str}")
            return
        print(
            f"DEBUG Dashboard: add_live_event_to_table called with: {event_details}")
        print(
            f"DEBUG Dashboard: Table row count BEFORE live event insert: {self.recent_events_table.rowCount()}")
        self.recent_events_table.setSortingEnabled(False)
        self.recent_events_table.insertRow(0)
        ts_s = datetime.fromtimestamp(event_details.get(
            "timestamp", time.time())).strftime('%Y-%m-%d %H:%M:%S')
        self.recent_events_table.setItem(0, 0, QTableWidgetItem(ts_s))
        self.recent_events_table.setItem(
            0, 1, QTableWidgetItem(event_details.get("path", "N/A")))
        self.recent_events_table.setItem(0, 2, QTableWidgetItem(
            event_details.get("change_type", "N/A")))
        max_rows = getattr(config, "MAX_EVENTS_IN_DASHBOARD", 100)
        if self.recent_events_table.rowCount() > max_rows:
            self.recent_events_table.removeRow(
                self.recent_events_table.rowCount()-1)
        self.recent_events_table.setSortingEnabled(True)
        self.update_integrity_badge("unknown", "Live Event Occurred")
        print(
            f"DEBUG Dashboard: Table row count AFTER live event insert: {self.recent_events_table.rowCount()}")
        if hasattr(self, 'recent_events_title_label'):
            current_palette = config.DARK_THEME_PALETTE if config.CURRENT_UI_MODE == "dark" else config.LIGHT_THEME_PALETTE
            accent_color = current_palette.get("accent", "#007bff")
            original_text_color = current_palette.get("text", "#000000")
            self.recent_events_title_label.setStyleSheet(
                f"color: {accent_color}; font-weight: bold;")
            QTimer.singleShot(1500, lambda: self.recent_events_title_label.setStyleSheet(
                f"color: {original_text_color}; font-weight: bold;"))

    @Slot(str)
    def refresh_after_audit(self, summary_str: str):
        try:
            summary = json.loads(summary_str)
        except json.JSONDecodeError as e:
            print(
                f"ERROR Dashboard: Could not decode audit summary JSON: {e}. Data: {summary_str}")
            self.update_integrity_badge("error", "Audit Data Error")
            return
        print(f"DEBUG Dashboard: Refreshing after audit. Summary: {summary}")
        self.last_audit_summary_for_report = summary
        audit_time_str = datetime.fromisoformat(summary.get(
            "timestamp", datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M:%S')
        badge_status = "unknown"
        if summary.get("scan_errors", 0) > 0:
            badge_status = "error"
        elif summary.get("mismatches_found", 0) > 0 or summary.get("new_files_detected", 0) > 0:
            badge_status = "compromised"
        else:
            badge_status = "secure"
        self.update_integrity_badge(badge_status, audit_time_str)
        self.refresh_events_table_from_db()

    @Slot()
    def on_verify_integrity_clicked(self):
        if not self.fim_engine or (not self.fim_engine.baseline_data and not os.path.exists(self.fim_engine.baseline_file if hasattr(self.fim_engine, 'baseline_file') else '')):
            QMessageBox.warning(self, "Err", "No baseline.")
            self.update_integrity_badge("no_baseline", "Never")
            return
        self._show_progress_dialog("Integrity Check", "Verifying...")
        self.update_integrity_badge("verifying", "In Progress...")
        worker = Worker(self.fim_engine.verify_integrity, False)
        worker.signals.result.connect(self._handle_verification_result)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.finished.connect(self._hide_progress_dialog)
        self.threadpool.start(worker)

    @Slot()
    def on_set_new_baseline_clicked(self):
        print(
            f"Dashboard: Set New Baseline (All Monitored) clicked by {self.current_user} ({self.current_role})")
        if self.current_role != "admin":
            QMessageBox.warning(
                self, "Permission Denied", "Only administrators can set a new baseline for all monitored items.")
            return
        monitored_dirs = getattr(config, "MONITORED_DIRECTORIES", [])
        if not monitored_dirs:
            QMessageBox.warning(self, "Configuration Missing",
                                "No directories are configured for monitoring. Please configure paths first via the 'Admin: Configure Paths' button.")
            return
        reply = QMessageBox.question(
            self, "Confirm Baseline Reset", "This will overwrite the existing baseline with the current state of ALL currently monitored files and directories. Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._show_progress_dialog(
                "Baselining (All)", "Creating new baseline for all monitored items...")
            self.update_integrity_badge("verifying", "Baselining (All)...")
            worker = Worker(self.fim_engine.create_new_baseline)
            worker.signals.result.connect(self._handle_rebaseline_result)
            worker.signals.error.connect(self._handle_worker_error)
            worker.signals.finished.connect(self._hide_progress_dialog)
            self.threadpool.start(worker)

    @Slot(object)
    def _handle_verification_result(self, result_tuple):
        discrepancies, summary = result_tuple
        print(
            f"DEBUG Dashboard: Verification result received. Discrepancies: {len(discrepancies)}")
        # Pass the summary dict as a JSON string to refresh_after_audit
        QMetaObject.invokeMethod(
            self, "refresh_after_audit", Qt.QueuedConnection, Q_ARG(str, json.dumps(summary)))
        msg_title = "Verification Complete"
        if summary.get("scan_errors", 0) > 0:
            msg_text = f"Errors.\nMismatches:{summary.get('mismatches_found', 0)}\nNew:{summary.get('new_files_detected', 0)}\nErrors:{summary.get('scan_errors', 0)}"
        elif discrepancies:
            msg_text = f"Discrepancies!\nMismatches:{summary.get('mismatches_found', 0)}\nNew:{summary.get('new_files_detected', 0)}"
        else:
            msg_text = "No discrepancies."
        QMessageBox.information(self, msg_title, msg_text)
        print("Verify summary:", summary)

    @Slot(object)
    def _handle_rebaseline_result(self, result_tuple):
        success, summary = result_tuple
        audit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if success:
            QMessageBox.information(
                self, "Baseline Set", f"New baseline for all monitored items created.\nFiles:{summary.get('files_scanned', 0)}\nErrors:{summary.get('scan_errors', 0)}")
            self.update_integrity_badge("secure", audit_time)
            self.refresh_events_table_from_db()
        else:
            QMessageBox.critical(
                self, "Baseline Error", f"Failed to create new baseline.\nDetails:{summary.get('message', 'Error')}")
            self.update_integrity_badge("error", audit_time)
        print("Re-baseline summary:", summary)

    @Slot(tuple)
    def _handle_worker_error(self, error_tuple):
        exctype, value, tb = error_tuple
        print(f"Worker Error:{exctype},{value}\n{tb}")
        self._hide_progress_dialog()
        self.update_integrity_badge("error", "Op Failed")
        QMessageBox.critical(self, "Op Error", f"Error:\n{value}\nCheck logs.")

    @Slot()
    def on_configure_paths_clicked(self):
        print("Dashboard: Configure Paths button clicked, emitting request.")
        self.configurePathsRequested.emit()

    @Slot()
    def on_monitor_single_file_clicked(self):
        print("Dashboard: Monitor Single File button clicked, emitting request.")
        self.monitorSingleFileRequested.emit()
        
    @Slot()
    def on_run_simulation_clicked(self):
        if self.current_role != "admin":
             QMessageBox.critical(self, "Permission Denied", "Only administrators can run simulations.")
             return
        if not self.simulator:
             QMessageBox.critical(self, "Error", "Simulator module not initialized.")
             return
             
        reply = QMessageBox.question(
            self, "Confirm Simulation", "This will generate a burst of simulated activity (25+ file changes and a login) for a user named 'sim_attacker'. Are you sure?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            self._show_progress_dialog("UBA Simulation", "Running anomaly simulation...")
            
            # Use Worker to run the synchronous simulation function
            worker = Worker(self.simulator.run_anomaly_scenario)
            worker.signals.result.connect(self._handle_simulation_result)
            worker.signals.error.connect(self._handle_worker_error) # Use existing error handler
            worker.signals.finished.connect(self._hide_progress_dialog)
            self.threadpool.start(worker)

    @Slot(str)
    def _handle_simulation_result(self, message: str):
        QMessageBox.information(self, "Simulation Complete", message)
        
        # Ensure the UBA/Risk check runs shortly after the simulation completes
        # Use QMetaObject.invokeMethod to call the parent window's slot safely
        if self.parent() and hasattr(self.parent(), 'run_risk_assessment'):
            QMetaObject.invokeMethod(self.parent(), "run_risk_assessment", Qt.QueuedConnection)
        
        action_logger.log_action(action_type="UBA_SIMULATION_RUN", username=self.current_user, status="SUCCESS")

    @Slot()
    def on_generate_report_clicked(self):
        if ReportGenerator is None:
            QMessageBox.critical(
                self, "Error", "ReportGenerator module not loaded.")
            return
        if not self.fim_engine:
            return
        print(f"Dashboard: Generate Report by {self.current_user}")
        all_events = self.fim_engine.get_recent_events_from_db(limit=None)
        if not all_events and not self.last_audit_summary_for_report:
            QMessageBox.information(
                self, "No Data", "No audit data/events for report.")
            return
        report_data = {'discrepancies': all_events}
        self._show_progress_dialog("Report Generation", "Generating PDF...")

        def gen_task():
            if ReportGenerator is None:
                return None
            gen = ReportGenerator(
                report_data=report_data, audit_summary=self.last_audit_summary_for_report)
            return gen.build_pdf()
        worker = Worker(gen_task)
        worker.signals.result.connect(self._handle_report_generation_result)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.finished.connect(self._hide_progress_dialog)
        self.threadpool.start(worker)

    @Slot(object)
    def _handle_report_generation_result(self, report_filename: str | None):
        if report_filename:
            if QMessageBox.information(self, "Report Generated", f"Report saved:\n{report_filename}\n\nOpen it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
                self._open_file_externally(report_filename)
        else:
            QMessageBox.critical(self, "Report Error",
                                 "Failed to generate report.")

    def _open_file_externally(self, filepath):
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
        except Exception as e:
            print(f"Error opening file {filepath}:{e}")
            QMessageBox.warning(
                self, "Open Error", f"Could not open report.\nFind it at:\n{filepath}")

    def update_styles_for_theme(self, theme_name: str):
        print(
            f"DashboardWidget: Theme changed to {theme_name}, styles could be updated here.")
        self.setStyleSheet(self.styleSheet())
        self.integrity_badge_frame.setStyleSheet(
            self.integrity_badge_frame.styleSheet())
        self.quick_actions_frame.setStyleSheet(
            self.quick_actions_frame.styleSheet())