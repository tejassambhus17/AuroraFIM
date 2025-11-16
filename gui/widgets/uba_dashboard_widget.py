# aurorafimpro/aurorafimpro/gui/widgets/uba_dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame,
    QStyle, QMessageBox, QApplication # Added QApplication for processEvents
)
from PySide6.QtCore import Qt, Slot, QTimer, QSize, QThreadPool
from PySide6.QtGui import QColor, QIcon, QFont, QPalette
from datetime import datetime
import os
import sys
import json

# Adjust import path for core components
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    import config
    from core.fim import FIMEngine
    from core.user_profiler import user_profiler
    from gui.widgets.worker import Worker # NEW: Import Worker
except ImportError as e:
    print(f"ERROR: Error importing modules in uba_dashboard_widget.py: {e}")
    # Fallback mocks
    config = type('MockConfig', (), {
        'APP_NAME': 'UBA Dashboard',
        'DARK_THEME_PALETTE': {"successGreen": "#2ecc71", "warningOrange": "#f39c12", "dangerRed": "#e74c3c", "text": "#d0d0d0", "alternateBase": "#333333"},
        'LIGHT_THEME_PALETTE': {"successGreen": "#27ae60", "warningOrange": "#e67e22", "dangerRed": "#c0392b", "text": "#000000", "alternateBase": "#f5f5f5"},
        'CURRENT_UI_MODE': 'dark',
    })()
    FIMEngine = None
    user_profiler = type('MockProfiler', (), {'get_all_user_profiles': lambda s: [], 'get_latest_risk_report': lambda s: [
        {'username': 'MockUser', 'risk_score': 85, 'classification': 'High Risk', 'report_time': 'N/A'}]})()
    Worker = type('MockWorker', (), {'__init__': lambda s, fn, *a, **k: setattr(s, 'signals', type('s', (), {'result': Signal(object), 'error': Signal(tuple), 'finished': Signal()}))})


class UbaDashboardWidget(QWidget):
    def __init__(self, fim_engine: FIMEngine, parent=None):
        super().__init__(parent)
        self.fim_engine = fim_engine
        self.current_theme = config.CURRENT_UI_MODE
        self.setObjectName("UbaDashboardWidget")
        self.threadpool = QThreadPool.globalInstance() # NEW: Threadpool reference
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("User Behavior Analytics (UBA) Dashboard")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        
        # Top Section: Risk Report and Summary
        top_h_layout = QHBoxLayout()

        # 1. Suspicious Activity Summary (Risk Report Table)
        risk_frame = QFrame()
        risk_layout = QVBoxLayout(risk_frame)
        risk_frame.setObjectName("RiskSummaryFrame")
        risk_frame.setFrameShape(QFrame.StyledPanel)
        risk_frame.setFrameShadow(QFrame.Raised)
        
        risk_title = QLabel("Suspicious Activity Summary (Last Check)")
        risk_title.setObjectName("RiskSummaryTitle")
        risk_title.setFont(QFont('Arial', 12, QFont.Bold))
        risk_layout.addWidget(risk_title)

        self.risk_table = QTableWidget()
        self.risk_table.setColumnCount(4)
        self.risk_table.setHorizontalHeaderLabels([
            "User", "Risk Score", "Classification", "Time"
        ])
        self.risk_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.risk_table.verticalHeader().setVisible(False)
        self.risk_table.horizontalHeader().setStretchLastSection(True)
        self.risk_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.risk_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        risk_layout.addWidget(self.risk_table)
        top_h_layout.addWidget(risk_frame, 1)

        # Placeholder for future visualizations (or other summary frames)
        viz_frame = QFrame()
        viz_layout = QVBoxLayout(viz_frame)
        viz_title = QLabel("Behavior Visualization (Future Chart Area)")
        viz_title.setFont(QFont('Arial', 12, QFont.Bold))
        viz_layout.addWidget(viz_title)
        viz_layout.addWidget(QLabel("Charts for login times, file mods per day, etc., will be displayed here."))
        top_h_layout.addWidget(viz_frame, 1)


        main_layout.addLayout(top_h_layout)

        # User Profiles Baseline Table
        baseline_controls_layout = QHBoxLayout() # NEW Layout for title + button

        self.baseline_title = QLabel("User Behavior Baseline (30-Day Average)")
        self.baseline_title.setFont(QFont('Arial', 12, QFont.Bold))
        baseline_controls_layout.addWidget(self.baseline_title)
        
        self.recalculate_button = QPushButton("Manual Recalculate Profiles") # NEW Button
        self.recalculate_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.recalculate_button.clicked.connect(self.on_recalculate_profiles)
        baseline_controls_layout.addWidget(self.recalculate_button, alignment=Qt.AlignRight)

        main_layout.addLayout(baseline_controls_layout) # Use the new layout
        
        self.baseline_table = QTableWidget()
        self.baseline_table.setColumnCount(4)
        self.baseline_table.setHorizontalHeaderLabels([
            "User", "Avg. Logins/Day", "Avg. File Changes/Day", "Normal File Types"
        ])
        self.baseline_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.baseline_table.verticalHeader().setVisible(False)
        self.baseline_table.horizontalHeader().setStretchLastSection(True)
        
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)

        main_layout.addWidget(self.baseline_table)
        
        # Periodic refresh for visualization/dashboard data
        self.refresh_button = QPushButton("Refresh UBA Data Tables")
        self.refresh_button.clicked.connect(self.refresh_uba_data)
        main_layout.addWidget(self.refresh_button, alignment=Qt.AlignRight)

        # Initial Load
        QTimer.singleShot(100, self.refresh_uba_data)
        self.update_styles_for_theme(self.current_theme)

    @Slot()
    def on_recalculate_profiles(self):
        """
        Triggers the profile recalculation on a separate worker thread.
        This is an expensive operation and should not block the UI.
        """
        if not self.fim_engine:
            QMessageBox.critical(self, "Error", "FIM Engine not available for profile calculation.")
            return

        reply = QMessageBox.question(
            self, "Confirm Recalculation", 
            "This will analyze the last 30 days of activity for ALL users and overwrite the existing baseline. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.recalculate_button.setEnabled(False)
            self.recalculate_button.setText("Calculating...")
            QApplication.processEvents() # Update button text immediately
            
            worker = Worker(self.fim_engine.update_user_profiles)
            worker.signals.result.connect(self._handle_recalculate_result)
            worker.signals.error.connect(self._handle_recalculate_error)
            worker.signals.finished.connect(self._handle_recalculate_finished)
            self.threadpool.start(worker)

    @Slot(object)
    def _handle_recalculate_result(self, success: bool):
        if success:
            QMessageBox.information(self, "Success", "User profiles successfully recalculated and saved.")
        else:
            QMessageBox.critical(self, "Error", "Failed to recalculate user profiles. Check logs.")
        self.load_user_profiles() # Refresh the baseline table immediately

    @Slot(tuple)
    def _handle_recalculate_error(self, error_tuple):
        exctype, value, tb = error_tuple
        QMessageBox.critical(self, "Worker Error", f"Profile calculation failed:\n{value}")
        
    @Slot()
    def _handle_recalculate_finished(self):
        self.recalculate_button.setEnabled(True)
        self.recalculate_button.setText("Manual Recalculate Profiles")
        
    @Slot()
    def refresh_uba_data(self):
        """Loads both the latest risk report and all user profiles."""
        self.load_risk_report()
        self.load_user_profiles()
        
    @Slot()
    def load_risk_report(self):
        """Populates the Risk Report table from the last calculated report."""
        # Use the result stored in the user_profiler instance
        report_data = user_profiler.get_latest_risk_report()
        self.risk_table.setSortingEnabled(False)
        self.risk_table.setRowCount(0)
        
        current_palette = config.DARK_THEME_PALETTE if self.current_theme == "dark" else config.LIGHT_THEME_PALETTE
        
        for i, entry in enumerate(report_data):
            self.risk_table.insertRow(i)
            
            username_item = QTableWidgetItem(entry.get("username", "N/A"))
            score_item = QTableWidgetItem(str(entry.get("risk_score", 0)))
            class_item = QTableWidgetItem(entry.get("classification", "Normal"))
            time_item = QTableWidgetItem(entry.get("report_time", "N/A"))

            # Color code the classification
            color_map = {
                "High Risk": QColor(current_palette.get("dangerRed")),
                "Suspicious": QColor(current_palette.get("warningOrange")),
                "Normal": QColor(current_palette.get("successGreen")),
                "No Profile": QColor(current_palette.get("text")),
            }
            color = color_map.get(entry.get("classification", "Normal"), QColor(current_palette.get("text")))
            class_item.setForeground(color)
            score_item.setForeground(color)
            
            self.risk_table.setItem(i, 0, username_item)
            self.risk_table.setItem(i, 1, score_item)
            self.risk_table.setItem(i, 2, class_item)
            self.risk_table.setItem(i, 3, time_item)

        self.risk_table.setSortingEnabled(True)
        self.risk_table.resizeColumnsToContents()
        
    @Slot()
    def load_user_profiles(self):
        """Populates the User Profiles table."""
        profiles = user_profiler.get_all_user_profiles()
        self.baseline_table.setSortingEnabled(False)
        self.baseline_table.setRowCount(0)
        
        for i, profile in enumerate(profiles):
            self.baseline_table.insertRow(i)
            
            # Format file types list
            file_types_str = ", ".join(profile.get("normal_file_types", []))
            
            # Use normal_login_hour in tooltip if present, otherwise omit
            username_item = QTableWidgetItem(profile.get("username", "N/A"))
            login_hour = profile.get("normal_login_hour")
            if login_hour is not None:
                username_item.setToolTip(f"Normal Login Hour: {login_hour:02d}:00")

            self.baseline_table.setItem(i, 0, username_item)
            self.baseline_table.setItem(i, 1, QTableWidgetItem(str(profile.get("avg_logins_per_day", "N/A"))))
            self.baseline_table.setItem(i, 2, QTableWidgetItem(str(profile.get("avg_file_changes_per_day", "N/A"))))
            self.baseline_table.setItem(i, 3, QTableWidgetItem(file_types_str))

        self.baseline_table.setSortingEnabled(True)
        self.baseline_table.resizeColumnsToContents()

    def update_styles_for_theme(self, theme_name: str):
        self.current_theme = theme_name
        # Trigger re-coloring for tables since colors are hardcoded based on theme palette
        self.load_risk_report()
        # Ensure title colors match the theme (as QSS cannot target non-text content like QColor foregrounds)
        current_palette = config.DARK_THEME_PALETTE if theme_name == "dark" else config.LIGHT_THEME_PALETTE
        text_color = current_palette.get("text")
        # Apply foreground color directly to titles if needed (QSS usually handles this)
        self.baseline_title.setStyleSheet(f"color: {text_color};")
        risk_title_label = self.findChild(QLabel, "RiskSummaryTitle")
        if risk_title_label:
            risk_title_label.setStyleSheet(f"color: {text_color};")
        # Ensure the overall widget styles update
        if hasattr(self, 'styleSheet'):
            self.setStyleSheet(self.styleSheet())