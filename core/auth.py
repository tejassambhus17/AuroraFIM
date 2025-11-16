# aurorafimpro/aurorafimpro/core/auth.py
import sqlite3
import os
import sys
import json  # For logging details

# Adjust path to import config and action_logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
    from core.action_logger import action_logger  # Import the global logger instance
except ImportError as e:
    print(f"Error importing in core/auth.py: {e}")
    config = type('MockConfig', (), {
                  'BASE_DIR': '.', 'DATABASE_NAME': 'auth_fallback.db'})()
    # Mock action_logger if it fails to import, so auth can still function minimally

    class MockActionLogger:
        def log_action(
            self, *args, **kwargs): print(f"MockLog (auth): {args} {kwargs}")
    action_logger = MockActionLogger()

# --- Third-Party Imports that might fail (bcrypt) ---
try:
    import bcrypt
except ImportError:
    print("WARNING: bcrypt module not found. Using INSECURE password stub for college demonstration.")
    
    # --- Mock Implementation ---
    MOCK_HASH_PREFIX = b'MOCK_INSECURE_HASH_'

    class MockBcrypt:
        @staticmethod
        def gensalt(): return b'stub_salt'
        
        @staticmethod
        def hashpw(password: bytes, salt) -> bytes: 
            # Returns a BYTES object. This is what fixed the previous error.
            return MOCK_HASH_PREFIX + password
        
        @staticmethod
        def checkpw(plain_password: bytes, hashed_password: bytes) -> bool: 
            if not isinstance(hashed_password, bytes):
                return False
                
            if not hashed_password.startswith(MOCK_HASH_PREFIX):
                return False 
            
            stored_plaintext_mock = hashed_password.removeprefix(MOCK_HASH_PREFIX)
            
            return plain_password == stored_plaintext_mock

    bcrypt = MockBcrypt
# ----------------------------------------------------


DATABASE_FILE = os.path.join(config.BASE_DIR, config.DATABASE_NAME)


class AuthHandler:
    def __init__(self):
        self.db_path = DATABASE_FILE

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # FIX: Ensure hashed_password is a bytes object before decoding.
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
            
        return hashed_password.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            print(f"Error during password verification: {e}")
            return False

    def create_user(self, username: str, password: str, role: str) -> bool:
        if role not in ['admin', 'auditor', 'viewer']:
            print(f"Invalid role: {role}.")
            action_logger.log_action(
                action_type="USER_CREATE_ATTEMPT", username="System/Admin",
                details={"target_user": username, "role": role, "error": "Invalid role"}, status="FAILURE"
            )
            return False
        if not os.path.exists(self.db_path):
            print(f"DB {self.db_path} does not exist. Cannot create user.")
            action_logger.log_action(
                action_type="USER_CREATE_ATTEMPT", username="System/Admin",
                details={"target_user": username, "error": "Database not found"}, status="FAILURE"
            )
            return False

        password_hash = self.hash_password(password)
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            print(
                f"User '{username}' created successfully with role '{role}'.")
            action_logger.log_action(
                # Or by current admin user if UI exists
                action_type="USER_CREATED", username="System/Admin",
                details={"new_user": username, "role": role}, status="SUCCESS"
            )
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Username '{username}' already exists.")
            action_logger.log_action(
                action_type="USER_CREATE_ATTEMPT", username="System/Admin",
                details={"target_user": username, "error": "Username exists"}, status="FAILURE"
            )
            return False
        except sqlite3.Error as e:
            print(f"Database error during user creation: {e}")
            action_logger.log_action(
                action_type="USER_CREATE_ATTEMPT", username="System/Admin",
                details={"target_user": username, "error": str(e)}, status="FAILURE"
            )
            return False
        finally:
            if conn:
                conn.close()

    # Added user_id
    def authenticate_user(self, username: str, password: str) -> tuple[bool, str | None, str | None, int | None]:
        """
        Authenticates a user.
        Returns a tuple: (isAuthenticated, username, role, user_id)
        If authentication fails, returns (False, None, None, None).
        """
        user = self.get_user(username)
        log_details = {"attempted_username": username}

        if user and self.verify_password(password, user['password_hash']):
            print(
                f"User '{username}' authenticated successfully. Role: {user['role']}")
            action_logger.log_action(
                action_type="LOGIN_SUCCESS",
                user_id=user['id'],
                username=user['username'],
                details={"role": user['role']},
                status="SUCCESS"
            )
            return True, user['username'], user['role'], user['id']

        print(f"Authentication failed for user '{username}'.")
        action_logger.log_action(
            action_type="LOGIN_FAILURE",
            username=username,  # Log attempted username even on failure
            details=log_details,
            status="FAILURE"
        )
        return False, None, None, None

    def get_user(self, username: str) -> sqlite3.Row | None:
        if not os.path.exists(self.db_path):
            return None
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()
            return user_data
        except sqlite3.Error as e:
            print(f"Database error while fetching user '{username}': {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_count(self) -> int:
        if not os.path.exists(self.db_path):
            return 0
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Database error while getting user count: {e}")
            return 0
        finally:
            if conn:
                conn.close()