# aurorafimpro/aurorafimpro/database/db_setup.py
import sqlite3
import os
import sys

# Adjust path to import config from the parent 'aurorafimpro' package directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize logger for db_setup
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
    logger = SimpleLogger()

try:
    import config
except ImportError as e:
    logger.error(f"Error importing config in db_setup.py: {e}")

    class MockConfig:
        BASE_DIR = "."
        DATABASE_NAME = "aurorafim_fallback.db"
    config = MockConfig()
    project_root_from_db = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root_from_db not in sys.path:
        sys.path.insert(0, project_root_from_db)
    # Try to re-import with adjusted path
    from aurorafimpro import config as actual_config
    config = actual_config


DATABASE_FILE = os.path.join(config.BASE_DIR, config.DATABASE_NAME)


def initialize_database():
    """
    Initializes the SQLite database and creates necessary tables if they don't exist.
    """
    db_dir = os.path.dirname(DATABASE_FILE)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        except OSError as e:
            logger.error(f"Error creating database directory {db_dir}: {e}")
            return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # --- Users Table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'auditor', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("Users table checked/created successfully.")

        # --- FIM Events Table ---
        # Note: Added user_id to this table in FIMEngine for UBA tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fim_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_timestamp REAL NOT NULL, 
                file_path TEXT NOT NULL,
                event_type TEXT NOT NULL, 
                baseline_hash TEXT,      
                actual_hash TEXT,        
                expected_props TEXT,     
                actual_props TEXT,       
                details TEXT,            
                source TEXT NOT NULL,    
                acknowledged INTEGER DEFAULT 0, 
                user_id INTEGER,          
                FOREIGN KEY (user_id) REFERENCES users(id) 
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_fim_events_timestamp ON fim_events (event_timestamp DESC)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_fim_events_file_path ON fim_events (file_path)")
        logger.info("FIM Events table checked/created successfully with indexes.")

        # --- User Activity Log Table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_timestamp REAL NOT NULL,
                user_id INTEGER,          -- Can be NULL if action is system-initiated before login
                username TEXT,            -- Store username for easier display, even if user is deleted
                action_type TEXT NOT NULL, -- e.g., 'LOGIN_SUCCESS', 'LOGIN_FAIL', 'SET_BASELINE_ALL', 
                                          -- 'SET_BASELINE_SINGLE', 'VERIFY_INTEGRITY', 'CONFIG_PATHS_UPDATE', 
                                          -- 'GENERATE_REPORT', 'USER_CREATED', 'USER_ROLE_CHANGED'
                details TEXT,             -- JSON string for additional context specific to the action
                ip_address TEXT,          -- Optional: for web apps, less relevant for desktop
                status TEXT               -- e.g., 'SUCCESS', 'FAILURE'
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_activity_log_timestamp ON user_activity_log (activity_timestamp DESC)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_activity_log_user ON user_activity_log (user_id, username)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_activity_log_action ON user_activity_log (action_type)")
        logger.info("User Activity Log table checked/created successfully with indexes.")
        
        # --- UBA User Profiles Table (NEW) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,        
                username TEXT UNIQUE NOT NULL,
                profile_data_json TEXT NOT NULL,    -- JSON string containing avg_logins_per_day, normal_login_hour, etc.
                profiled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("User Profiles table checked/created successfully.")

        conn.commit()
        logger.info(f"Database '{DATABASE_FILE}' initialized successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database error during initialization: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    logger.info(f"Attempting to initialize database at: {DATABASE_FILE}")
    logger.info(f"Configured BASE_DIR from config.py: {config.BASE_DIR}")
    if not os.path.exists(config.BASE_DIR):
        logger.warning(f"BASE_DIR '{config.BASE_DIR}' does not exist.")
    initialize_database()