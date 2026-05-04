# aurorafimpro/aurorafimpro/gui/widgets/configure_paths_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QDialogButtonBox, QStyle  # Added QStyle here
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QIcon  # QStyle removed from here
import os
import sys

# Ensure config can be imported if this dialog is tested directly
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
try:
    import config  # For APP_NAME
    from core.logger import logger
except ImportError:
    config = type('MockConfig', (), {'APP_NAME': 'FIM'})()
    class SimpleLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
        def debug(self, msg): pass
    logger = SimpleLogger()


class ConfigurePathsDialog(QDialog):
    def __init__(self, current_paths: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure Monitored Paths - {config.APP_NAME}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)

        self.current_paths = list(current_paths)  # Work with a copy

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Manage Monitored Files and Directories")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.paths_list_widget = QListWidget()
        self.paths_list_widget.setAlternatingRowColors(True)
        for path in self.current_paths:
            self.paths_list_widget.addItem(QListWidgetItem(path))
        main_layout.addWidget(self.paths_list_widget)

        # --- Buttons for Add/Remove ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        icon_size = QSize(18, 18)
        # Use QStyle correctly
        add_file_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        add_dir_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        remove_icon = self.style().standardIcon(QStyle.SP_DialogCloseButton)

        self.add_file_button = QPushButton(" Add File...")
        self.add_file_button.setIcon(add_file_icon)
        self.add_file_button.setIconSize(icon_size)
        self.add_file_button.clicked.connect(self.add_file)
        buttons_layout.addWidget(self.add_file_button)

        self.add_dir_button = QPushButton(" Add Directory...")
        self.add_dir_button.setIcon(add_dir_icon)
        self.add_dir_button.setIconSize(icon_size)
        self.add_dir_button.clicked.connect(self.add_directory)
        buttons_layout.addWidget(self.add_dir_button)

        buttons_layout.addStretch()  # Push remove button to the right

        self.remove_path_button = QPushButton(" Remove Selected")
        self.remove_path_button.setIcon(remove_icon)
        self.remove_path_button.setIconSize(icon_size)
        self.remove_path_button.clicked.connect(self.remove_selected_path)
        buttons_layout.addWidget(self.remove_path_button)

        main_layout.addLayout(buttons_layout)

        # --- Dialog Buttons (Save/Cancel) ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    @Slot()
    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Monitor",
            os.path.expanduser("~"),
            "All Files (*.*)"
        )
        if file_path:
            abs_file_path = os.path.abspath(file_path)
            if not self._is_path_already_added(abs_file_path):
                self.paths_list_widget.addItem(QListWidgetItem(abs_file_path))
                # self.current_paths.append(abs_file_path) # No longer need to sync this manually
            else:
                QMessageBox.information(
                    self, "Path Exists", f"The path '{abs_file_path}' is already in the list.")

    @Slot()
    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Monitor",
            os.path.expanduser("~")
        )
        if dir_path:
            abs_dir_path = os.path.abspath(dir_path)
            if not self._is_path_already_added(abs_dir_path):
                self.paths_list_widget.addItem(QListWidgetItem(abs_dir_path))
                # self.current_paths.append(abs_dir_path) # No longer need to sync this manually
            else:
                QMessageBox.information(
                    self, "Path Exists", f"The path '{abs_dir_path}' is already in the list.")

    def _is_path_already_added(self, new_path: str) -> bool:
        for i in range(self.paths_list_widget.count()):
            if self.paths_list_widget.item(i).text() == new_path:
                return True
        return False

    @Slot()
    def remove_selected_path(self):
        selected_items = self.paths_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection",
                                "Please select a path to remove.")
            return

        for item in selected_items:
            # path_to_remove = item.text() # Not strictly needed if not syncing self.current_paths
            self.paths_list_widget.takeItem(self.paths_list_widget.row(item))
            # if path_to_remove in self.current_paths:
            #     self.current_paths.remove(path_to_remove)

    def get_updated_paths(self) -> list[str]:
        updated_paths = []
        for i in range(self.paths_list_widget.count()):
            updated_paths.append(self.paths_list_widget.item(i).text())
        return updated_paths


if __name__ == '__main__':
    # QApplication needs to be imported for the test
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    initial_paths = [
        os.path.abspath("C:/Windows/System32/drivers/etc/hosts"),
        os.path.abspath(os.path.expanduser("~/Documents"))
    ]

    dialog = ConfigurePathsDialog(current_paths=initial_paths)
    if dialog.exec() == QDialog.Accepted:  # Use QDialog.Accepted for standard dialogs
        new_paths = dialog.get_updated_paths()
        logger.info("Paths saved:")
        for path in new_paths:
            logger.info(f"- {path}")
    else:
        logger.info("Configuration cancelled.")
    # sys.exit() # Not needed if app.exec() is not called for this simple test
