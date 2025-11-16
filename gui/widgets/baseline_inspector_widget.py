# aurorafimpro/aurorafimpro/gui/widgets/baseline_inspector_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit,
    QMessageBox, QApplication  # Added QApplication for processEvents
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QFont
from datetime import datetime
import os
import sys

# Adjust import path for core.fim and config
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    import config
    from core.fim import FIMEngine
    from core.hashing import FileHasher  # For potentially showing live hash
except ImportError as e:
    print(f"Error importing modules in baseline_inspector_widget.py: {e}")
    # Fallback for direct execution or if imports fail during app run
    config = type('MockConfig', (), {})()  # Basic mock
    FIMEngine = None
    FileHasher = None


class BaselineInspectorWidget(QWidget):
    def __init__(self, fim_engine: FIMEngine, parent=None):
        super().__init__(parent)

        if not FIMEngine or not config or not FileHasher:
            main_layout = QVBoxLayout(self)
            error_label = QLabel("Error: Critical components (FIMEngine, Config, or FileHasher) failed to load.\n"
                                 "Baseline Inspector cannot operate.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 16px;")
            main_layout.addWidget(error_label)
            # It's important that even in this error state, the __init__ completes
            # without further errors, or it could mask this one.
            self.fim_engine = None  # Ensure attributes are initialized to prevent further errors
            self.file_hasher = None
            self.baseline_table = None  # Or a dummy QTableWidget
            return

        self.fim_engine = fim_engine
        self.file_hasher = FileHasher()

        self.setObjectName("BaselineInspectorWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_label = QLabel("Baseline File Inspector")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by file path...")
        self.search_input.textChanged.connect(self.filter_table)
        controls_layout.addWidget(self.search_input, 1)

        self.refresh_button = QPushButton("Refresh Baseline Data")
        self.refresh_button.clicked.connect(self.load_and_display_baseline)
        controls_layout.addWidget(self.refresh_button)
        main_layout.addLayout(controls_layout)

        self.baseline_table = QTableWidget()
        self.baseline_table.setColumnCount(6)
        self.baseline_table.setHorizontalHeaderLabels([
            "File Path", "Stored Hash", "Size (Bytes)",
            "Baseline MTime", "Mode", "Live Hash Status"
        ])
        self.baseline_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.baseline_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.baseline_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.baseline_table.setAlternatingRowColors(True)
        self.baseline_table.verticalHeader().setVisible(False)

        self.baseline_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents)
        self.baseline_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeToContents)

        self.baseline_table.itemDoubleClicked.connect(
            self.on_item_double_clicked)
        main_layout.addWidget(self.baseline_table)
        self.load_and_display_baseline()

    @Slot()
    def load_and_display_baseline(self):
        if not self.fim_engine:  # Check if FIMEngine was initialized
            QMessageBox.critical(
                self, "Error", "FIM Engine not available to Baseline Inspector.")
            return

        if not self.fim_engine.baseline_data:
            self.fim_engine.load_baseline()

        if not self.fim_engine.baseline_data:
            if self.baseline_table:
                self.baseline_table.setRowCount(0)
            QMessageBox.information(self, "Baseline Information",
                                    "No baseline data is currently loaded or the baseline file is empty/missing/tampered.\n"
                                    "Please set a new baseline from the Dashboard if needed.")
            return

        baseline_data = self.fim_engine.baseline_data
        if not self.baseline_table:
            return  # Should not happen if __init__ completed

        self.baseline_table.setRowCount(0)
        self.baseline_table.setSortingEnabled(False)

        for file_path, properties in baseline_data.items():
            row_position = self.baseline_table.rowCount()
            self.baseline_table.insertRow(row_position)

            self.baseline_table.setItem(
                row_position, 0, QTableWidgetItem(file_path))
            self.baseline_table.setItem(
                row_position, 1, QTableWidgetItem(properties.get("hash", "N/A")))
            self.baseline_table.setItem(row_position, 2, QTableWidgetItem(
                str(properties.get("size", "N/A"))))

            mtime_baseline = properties.get("mtime", 0)
            mtime_str = "N/A"
            if mtime_baseline and mtime_baseline != "N/A":
                try:
                    mtime_str = datetime.fromtimestamp(
                        float(mtime_baseline)).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    mtime_str = str(mtime_baseline)
            self.baseline_table.setItem(
                row_position, 3, QTableWidgetItem(mtime_str))

            mode_baseline = properties.get("mode")
            mode_str = str(
                mode_baseline) if mode_baseline is not None else "N/A"
            if mode_baseline is not None:
                try:
                    mode_str = oct(mode_baseline)
                except TypeError:
                    pass
            self.baseline_table.setItem(
                row_position, 4, QTableWidgetItem(mode_str))

            live_hash_status_item = QTableWidgetItem("Double-click to compare")
            live_hash_status_item.setForeground(QColor("blue"))
            self.baseline_table.setItem(row_position, 5, live_hash_status_item)

        self.baseline_table.setSortingEnabled(True)
        self.baseline_table.resizeColumnsToContents()
        self.baseline_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    @Slot(QTableWidgetItem)
    def on_item_double_clicked(self, item: QTableWidgetItem):
        if not self.file_hasher or not self.baseline_table:  # Check if initialized
            return

        # Line 180 according to original traceback context
        if item.column() != 5:
            return  # This is the crucial fix for the IndentationError.
            # The 'if' block now has a body.

        # The following code is now correctly processed only if item.column() == 5
        row = item.row()  # This was line 185 in the traceback context
        path_item = self.baseline_table.item(row, 0)
        baseline_hash_item = self.baseline_table.item(row, 1)

        if not path_item or not baseline_hash_item:
            return

        file_path = path_item.text()
        baseline_hash = baseline_hash_item.text()

        status_item = self.baseline_table.item(row, 5)
        if not status_item:
            return  # Should not happen

        status_item.setText("Comparing...")
        status_item.setForeground(QColor("orange"))
        QApplication.processEvents()

        live_hash = self.file_hasher.calculate_hash(file_path)

        if live_hash is None:
            status_item.setText("Error/Not Found")
            status_item.setForeground(QColor("red"))
        elif live_hash == baseline_hash:
            status_item.setText("Match ✓")
            status_item.setForeground(QColor("green"))
        else:
            status_item.setText(f"Mismatch ✗ ({live_hash[:12]}...)")
            status_item.setForeground(QColor("red"))

    @Slot(str)
    def filter_table(self, text: str):
        if not self.baseline_table:
            return  # Check if initialized
        for i in range(self.baseline_table.rowCount()):
            item = self.baseline_table.item(i, 0)
            if item:
                match = text.lower() in item.text().lower()
                self.baseline_table.setRowHidden(i, not match)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Mock FIMEngine for direct testing
    class MockFIMEngineForInspectorTest:
        def __init__(self, auth_handler=None):
            self.baseline_data = {
                os.path.abspath("/test/file1.txt"): {"hash": "abc", "size": 100, "mtime": 1678886400.0, "mode": 0o644},
                os.path.abspath("/test/dir/file2.log"): {"hash": "def", "size": 250, "mtime": 1678886500.0, "mode": 0o600},
            }

        def load_baseline(self): return True

    # Mock FileHasher for direct testing
    class MockFileHasherForInspectorTest:
        def calculate_hash(self, file_path):
            if "file1.txt" in file_path:
                return "abc"
            if "file2.log" in file_path:
                return "xyz"
            return None

    # Use mocks if actual classes failed to import at the top
    CurrentFIMEngine = FIMEngine if FIMEngine is not None else MockFIMEngineForInspectorTest
    CurrentFileHasher = FileHasher if FileHasher is not None else MockFileHasherForInspectorTest

    # Replace FileHasher in the global scope of this test block if it was None
    if 'FileHasher' in globals() and globals()['FileHasher'] is None:
        globals()['FileHasher'] = CurrentFileHasher

    mock_fim = CurrentFIMEngine()
    # We need to ensure that the BaselineInspectorWidget uses the CurrentFileHasher if the global one was None
    # This is a bit tricky because the widget instantiates its own FileHasher.
    # For this test, we'll assume FileHasher global import worked or the fallback is sufficient.
    # If FileHasher was None at the top, the widget's __init__ would have returned early.

    if FIMEngine is not None and FileHasher is not None:  # Only run test if main imports likely succeeded
        inspector_widget = BaselineInspectorWidget(fim_engine=mock_fim)
        inspector_widget.setWindowTitle("Baseline Inspector Test (Corrected)")
        inspector_widget.resize(900, 600)
        inspector_widget.show()
    else:
        print("Skipping BaselineInspectorWidget test due to failed main imports.")
        # Show a simple message window if imports failed
        error_win = QWidget()
        QVBoxLayout(error_win).addWidget(
            QLabel("Critical imports failed, cannot run inspector test."))
        error_win.show()

    sys.exit(app.exec())
