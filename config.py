# aurorafimpro/aurorafimpro/config.py
import os
import json
import sys

# Initialize logger for config module (used during early initialization)
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def warning(self, msg): sys.stderr.write(f"WARNING: {msg}\n")
        def info(self, msg): pass
    logger = SimpleLogger()

# --- Application Settings ---
APP_NAME = "AuroraFIM Pro"
APP_VERSION = "0.1.0"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- UI Settings ---
DEFAULT_UI_MODE = "dark"  # Make dark mode the default

# Modern Dark Theme Palette
DARK_THEME_PALETTE = {
    "window": "#0B1220",
    "windowText": "#E6EDF7",
    "base": "#111C2E",
    "alternateBase": "#1A2940",
    "toolTipBase": "#111C2E",
    "toolTipText": "#E6EDF7",
    "text": "#E6EDF7",
    "button": "#1A2940",
    "buttonText": "#E6EDF7",
    "brightText": "#ff4757",               # Bright red for critical alerts/text
    "highlight": "#1D9BF0",
    "highlightedText": "#ffffff",           # Text on highlighted items
    "disabledText": "#7A8AA5",
    "disabledButtonText": "#7A8AA5",
    "disabledWindowText": "#7A8AA5",
    "accent": "#49B3F5",
    "borderColor": "#233651",
    "tableHeaderBg": "#1A2940",
    "tableGrid": "#2C4362",
    "disabledButtonBackground": "#15233A",
    "disabledBorderColor": "#233651",
    "statusBarBg": "#111C2E",
    "menuBarBg": "#111C2E",
    "successGreen": "#22C55E",
    "warningOrange": "#f39c12",            # Orange for "VERIFYING" or warnings
    "dangerRed": "#e74c3c",                # Red for "COMPROMISED" badge
    "unknownGrey": "#8090AA"
}

# Light Theme Palette (can also be refined if needed)
LIGHT_THEME_PALETTE = {
    "window": "#F3F6FB", "windowText": "#0F172A", "base": "#FFFFFF", "alternateBase": "#EAF0F8",
    "toolTipBase": "#FFFFFF", "toolTipText": "#0F172A", "text": "#0F172A", "button": "#EAF0F8",
    "buttonText": "#0F172A", "brightText": "#DC2626", "highlight": "#0F6CBD", "highlightedText": "#FFFFFF",
    "disabledText": "#8FA1BA", "disabledButtonText": "#8FA1BA", "disabledWindowText": "#8FA1BA",
    "accent": "#1D87E0", "borderColor": "#D5E0EE", "tableHeaderBg": "#EAF0F8", "tableGrid": "#C0D0E5",
    "disabledButtonBackground": "#E3EAF5", "disabledBorderColor": "#CFDCEC",
    "statusBarBg": "#FFFFFF", "menuBarBg": "#FFFFFF",
    "successGreen": "#15803D", "warningOrange": "#B45309", "dangerRed": "#B91C1C", "unknownGrey": "#64748B"
}

# --- Enhanced QSS Templates ---
GENERAL_STYLESHEET_TEMPLATE = """
    QMainWindow, QDialog {{
        background-color: {window};
        color: {windowText};
    }}
    QToolBar {{
        background-color: {menuBarBg}; /* Use a distinct toolbar background */
        border-bottom: 1px solid {borderColor};
        padding: 6px;
        spacing: 8px;
    }}
    QToolButton {{
        background-color: transparent;
        color: {buttonText};
        padding: 8px 10px; /* Increased padding */
        margin: 1px;
        border-radius: 4px;
        font-size: 10pt; /* Slightly larger font for toolbar buttons */
    }}
    QToolButton:hover {{
        background-color: {highlight};
        color: {highlightedText};
    }}
    QToolButton:pressed {{
        background-color: {accent};
        color: {highlightedText};
    }}
    QToolButton:checked {{ /* For toggle buttons like theme switcher */
        background-color: {accent};
        color: {highlightedText};
        border: 1px solid {highlight};
    }}
    QPushButton {{
        background-color: {button};
        color: {buttonText};
        border: 1px solid {borderColor};
        padding: 10px 15px; /* Increased padding */
        border-radius: 5px; /* More rounded */
        font-size: 10pt;
        min-height: 24px; 
    }}
    QPushButton:hover {{
        background-color: {highlight};
        color: {highlightedText};
        border: 1px solid {accent};
    }}
    QPushButton:pressed {{
        background-color: {accent};
        color: {highlightedText};
    }}
    QPushButton:disabled {{
        background-color: {disabledButtonBackground};
        color: {disabledButtonText};
        border-color: {disabledBorderColor};
    }}
    QLabel {{
        color: {text};
        font-size: 10pt; /* Default label size */
    }}
    QLabel#IntegrityStatusLabel, QLabel#QuickActionsTitle, QLabel#RecentEventsTitleLabel {{ /* Specific labels */
        font-size: 11pt; /* Slightly larger for titles */
        font-weight: bold;
        color: {accent}; /* Use accent color for section titles */
        padding-bottom: 5px; /* Add some space below titles */
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {base};
        color: {text};
        border: 1px solid {borderColor};
        border-radius: 4px;
        padding: 6px;
        font-size: 10pt;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {accent};
    }}
    QTableView, QTableWidget {{
        background-color: {base};
        color: {text};
        gridline-color: {tableGrid};
        border: 1px solid {borderColor};
        border-radius: 4px; /* Rounded corners for the table itself */
        font-size: 9pt;
        selection-background-color: {highlight}; /* Color for selected rows/cells */
        selection-color: {highlightedText};
    }}
    QHeaderView::section {{
        background-color: {tableHeaderBg};
        color: {text};
        padding: 8px; /* Increased padding */
        border: none; /* Remove individual cell borders */
        border-bottom: 2px solid {accent}; 
        font-weight: bold;
        font-size: 10pt;
    }}
    QHeaderView {{
        border-top-left-radius: 3px; /* Match table's radius */
        border-top-right-radius: 3px;
    }}
    QTabWidget::pane {{
        border: 1px solid {borderColor};
        border-top: none; /* Remove top border as tab bar acts as separator */
        background-color: {window}; 
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    }}
    QTabBar::tab {{
        background: {button};
        color: {buttonText};
        border: 1px solid {borderColor};
        border-bottom: none; 
        border-top-left-radius: 5px; /* More rounded tabs */
        border-top-right-radius: 5px;
        padding: 10px 20px; /* Increased padding */
        margin-right: 1px;
        font-size: 10pt;
    }}
    QTabBar::tab:selected {{
        background: {window}; /* Selected tab matches window background */
        color: {accent}; /* Accent color for selected tab text */
        border-bottom: 2px solid {window}; /* Make it look like it's part of the pane */
        font-weight: bold;
    }}
    QTabBar::tab:!selected:hover {{
        background: {highlight};
        color: {highlightedText};
    }}
    QStatusBar {{
        background-color: {statusBarBg};
        color: {text};
        border-top: 1px solid {borderColor};
        padding: 3px;
    }}
    QFrame#IntegrityBadgeFrame, QFrame#QuickActionsFrame {{ 
        border: 1px solid {borderColor};
        border-radius: 6px; /* Slightly more rounded */
        padding: 15px; /* Increased padding */
        background-color: {alternateBase}; /* Distinct background for these frames */
    }}
    QListWidget {{
        background-color: {base};
        color: {text};
        border: 1px solid {borderColor};
        border-radius: 4px;
        padding: 5px;
    }}
    QListWidget::item:hover {{
        background-color: {highlight};
        color: {highlightedText};
    }}
    QListWidget::item:selected {{
        background-color: {accent};
        color: {highlightedText};
    }}
    QMessageBox {{ 
        background-color: {window};
    }}
    QMessageBox QLabel {{ /* Ensure text color in QMessageBox follows theme */
        color: {text}; 
    }}
    QProgressDialog {{
        background-color: {window};
        color: {text};
    }}
    QProgressDialog QLabel {{
        color: {text};
    }}
"""

# --- Application Settings File --- (No changes from here down for this step)
APP_SETTINGS_FILE = os.path.join(BASE_DIR, "app_settings.json")


def load_app_settings() -> dict:
    if os.path.exists(APP_SETTINGS_FILE):
        try:
            with open(APP_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading app settings: {e}. Using defaults.")
    return {}


def save_app_settings(settings_dict: dict):
    try:
        with open(APP_SETTINGS_FILE, 'w') as f:
            json.dump(settings_dict, f, indent=4)
    except Exception as e:
        logger.warning(f"Error saving app settings: {e}")


_app_settings = load_app_settings()

MONITORED_DIRECTORIES = _app_settings.get(
    "monitored_directories", [])  # Default to empty
if not isinstance(MONITORED_DIRECTORIES, list):
    MONITORED_DIRECTORIES = []
WATCHDOG_DEBOUNCE_DELAY = 1.5
BASELINE_FILE_NAME = "baseline.json"
BASELINE_SIGNATURE_FILE_NAME = "baseline.sig"
SNAPSHOT_DIR_NAME = "file_snapshots"
HASH_ALGORITHM = "sha256"
HMAC_SIGNING_KEY = _app_settings.get(
    "hmac_signing_key", "your-default-secret-key-please-change-me").encode('utf-8')
DEFAULT_AUDIT_SCHEDULE_TIME = _app_settings.get(
    "default_audit_schedule_time", "02:00")
SCHEDULED_AUDIT_CHECK_INTERVAL = _app_settings.get(
    "scheduled_audit_check_interval", 60000)
REPORTS_DIR_NAME = "audit_reports"
MAX_EVENTS_IN_DASHBOARD = _app_settings.get("max_events_in_dashboard", 100)
DASHBOARD_EVENT_REFRESH_INTERVAL = _app_settings.get(
    "dashboard_event_refresh_interval", 300000)
ENABLE_EMAIL_ALERTS = _app_settings.get("enable_email_alerts", False)
SMTP_SERVER = _app_settings.get("smtp_server", "smtp.example.com")
SMTP_PORT = _app_settings.get("smtp_port", 587)
SMTP_USERNAME = _app_settings.get("smtp_username", "u")
SMTP_PASSWORD = _app_settings.get("smtp_password", "p")
SMTP_USE_TLS = _app_settings.get("smtp_use_tls", True)
EMAIL_SENDER = _app_settings.get("email_sender", "fim@example.com")
EMAIL_RECIPIENTS = _app_settings.get("email_recipients", ["admin@example.com"])
MINIMIZE_TO_TRAY_ON_CLOSE = _app_settings.get(
    "minimize_to_tray_on_close", True)
DATABASE_NAME = "aurorafim.db"
LOG_FILE = "aurorafim.log"
LOG_LEVEL = "INFO"
DEBUG_MODE = True
CURRENT_UI_MODE = _app_settings.get("current_ui_mode", DEFAULT_UI_MODE)


def set_current_ui_mode(mode: str):
    global CURRENT_UI_MODE, _app_settings
    if mode in ["light", "dark"]:
        CURRENT_UI_MODE = mode
        _app_settings["current_ui_mode"] = mode
        save_app_settings(_app_settings)


def update_monitored_directories(new_paths: list[str]):
    global MONITORED_DIRECTORIES, _app_settings
    normalized_paths = []
    for path in new_paths:
        abs_path = os.path.abspath(path)
        if abs_path not in normalized_paths:
            normalized_paths.append(abs_path)
    MONITORED_DIRECTORIES = normalized_paths
    _app_settings["monitored_directories"] = MONITORED_DIRECTORIES
    save_app_settings(_app_settings)
    logger.info(f"Monitored directories updated: {MONITORED_DIRECTORIES}")


def update_audit_schedule_time(new_time_str: str):
    global DEFAULT_AUDIT_SCHEDULE_TIME, _app_settings
    try:
        h, m = map(int, new_time_str.split(':'))
        if 0 <= h <= 23 and 0 <= m <= 59:
            DEFAULT_AUDIT_SCHEDULE_TIME = new_time_str
            _app_settings["default_audit_schedule_time"] = new_time_str
            save_app_settings(_app_settings)
            logger.info(
                f"Audit schedule updated to {DEFAULT_AUDIT_SCHEDULE_TIME}")
            return True
        else:
            logger.warning(f"Invalid time: {new_time_str}")
            return False
    except ValueError:
        logger.warning(
            f"Invalid time format: {new_time_str}. Expected HH:MM.")
        return False
