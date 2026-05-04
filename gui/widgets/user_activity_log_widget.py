# aurorafimpro/aurorafimpro/gui/widgets/user_activity_log_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QFont
from datetime import datetime
import os
import sys
import json

# Initialize logger for this widget
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def debug(self, msg): sys.stderr.write(f"DEBUG: {msg}\n")
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
    logger = SimpleLogger()

# Adjust import path for action_logger and config
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    logger.debug("Attempting to import config")
    import config  # For APP_NAME, theming potentially
    logger.debug("Imported config successfully")

    logger.debug("Attempting to import action_logger")
    from core.action_logger import action_logger  # Use the global instance
    logger.debug("Imported action_logger successfully")

except ImportError as e:
    logger.error(f"Error importing modules in user_activity_log_widget.py: {e}")
    # Fallback mocks if direct execution or critical import failure
    if 'config' not in globals():  # Check if config failed specifically
        config = type('MockConfig', (), {
                      'APP_NAME': 'FIM Activity', 'MAX_EVENTS_IN_DASHBOARD': 100})()
        logger.debug("Using MockConfig due to import error.")
    if 'action_logger' not in globals():  # Check if action_logger failed
        class MockActionLogger:
            def get_recent_actions(self, limit=100):
                logger.debug("MockActionLogger.get_recent_actions called")
                return [{"activity_timestamp": datetime.now().timestamp(), "username": "MockUser", "action_type": "MOCK_ACTION", "status": "MOCK", "details": "{}"}]
        action_logger = MockActionLogger()
        logger.debug("Using MockActionLogger due to import error.")
    # It's often better to re-raise if critical components for the class are missing
    # raise # Uncomment if these are absolutely critical for class definition itself

logger.debug("Helper imports successful. About to define UserActivityLogWidget class")


class UserActivityLogWidget(QWidget):
    def __init__(self, parent=None):
        logger.debug("UserActivityLogWidget.__init__ called")
        super().__init__(parent)
        self.setObjectName("UserActivityLogWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_label = QLabel("User Activity Log")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        self.refresh_button = QPushButton("Refresh Log")
        self.refresh_button.clicked.connect(self.load_activity_log)
        controls_layout.addWidget(self.refresh_button)
        main_layout.addLayout(controls_layout)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(5)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "Username", "Action Type", "Status", "Details"
        ])
        self.activity_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.verticalHeader().setVisible(False)

        self.activity_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        main_layout.addWidget(self.activity_table)
        self.load_activity_log()
        logger.debug("UserActivityLogWidget.__init__ finished")

    @Slot()
    def load_activity_log(self):
        logger.debug("UserActivityLogWidget.load_activity_log called")
        if not action_logger:  # Should not happen if fallback is in place
            logger.critical("action_logger is None in load_activity_log.")
            return

        log_entries = action_logger.get_recent_actions(
            limit=getattr(config, "MAX_EVENTS_IN_DASHBOARD", 100))
        logger.debug(
            f"UserActivityLogWidget - Fetched {len(log_entries)} activity log entries.")

        self.activity_table.setSortingEnabled(False)
        self.activity_table.setRowCount(0)

        for entry in log_entries:
            row_pos = self.activity_table.rowCount()
            self.activity_table.insertRow(row_pos)

            ts_float = entry.get("activity_timestamp", 0.0)
            ts_str = datetime.fromtimestamp(ts_float).strftime(
                '%Y-%m-%d %H:%M:%S') if ts_float else "N/A"

            details_str_raw = entry.get("details", "")
            details_display = ""
            if isinstance(details_str_raw, str):
                try:
                    details_dict = json.loads(details_str_raw)
                    details_display = json.dumps(
                        details_dict, indent=2) if details_dict else ""
                except json.JSONDecodeError:
                    details_display = details_str_raw
            elif isinstance(details_str_raw, dict):
                details_display = json.dumps(details_str_raw, indent=2)
            else:
                details_display = str(details_str_raw)

            self.activity_table.setItem(row_pos, 0, QTableWidgetItem(ts_str))
            self.activity_table.setItem(
                row_pos, 1, QTableWidgetItem(entry.get("username", "System")))
            self.activity_table.setItem(
                row_pos, 2, QTableWidgetItem(entry.get("action_type", "N/A")))
            self.activity_table.setItem(
                row_pos, 3, QTableWidgetItem(entry.get("status", "N/A")))
            self.activity_table.setItem(
                row_pos, 4, QTableWidgetItem(details_display))

            status_item = self.activity_table.item(row_pos, 3)
            if status_item:
                status_text = status_item.text().upper()
                if status_text == "FAILURE":
                    status_item.setForeground(QColor("red"))
                elif status_text == "SUCCESS":
                    status_item.setForeground(QColor("green"))

        self.activity_table.setSortingEnabled(True)
        self.activity_table.resizeRowsToContents()
        logger.debug(
            f"UserActivityLogWidget - Table populated. Row count: {self.activity_table.rowCount()}")


logger.debug("UserActivityLogWidget class has been defined")

if __name__ == '__main__':
    logger.debug("user_activity_log_widget.py running as __main__")
    # Import QApplication for direct test
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Backup and use mock for direct testing to avoid DB dependency here
    _original_action_logger = action_logger

    class MockActionLoggerForTest:
        def get_recent_actions(self, limit=100):
            logger.debug("MockActionLoggerForTest.get_recent_actions called")
            return [
                {"activity_timestamp": datetime.now().timestamp() - 60, "username": "admin",
                 "action_type": "LOGIN_SUCCESS", "status": "SUCCESS", "details": json.dumps({"role": "admin"})},
                {"activity_timestamp": datetime.now().timestamp() - 120, "username": "test_user", "action_type": "LOGIN_FAILURE",
                 "status": "FAILURE", "details": json.dumps({"reason": "Bad password"})},
            ]
    action_logger = MockActionLoggerForTest()

    widget = UserActivityLogWidget()
    widget.setWindowTitle("User Activity Log Test")
    widget.resize(800, 500)
    widget.show()

    exit_code = app.exec()
    action_logger = _original_action_logger  # Restore
    sys.exit(exit_code)

logger.debug("user_activity_log_widget.py - End of file reached")
