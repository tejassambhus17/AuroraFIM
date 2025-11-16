# aurorafimpro/aurorafimpro/core/action_logger.py
import sqlite3
import os
import sys
import json
import time
from datetime import datetime

# Adjust path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
except ImportError as e:
    print(f"Error importing config in core/action_logger.py: {e}")
    # Basic fallback for direct script execution if needed

    class MockConfig:
        BASE_DIR = "."
        DATABASE_NAME = "aurorafim_fallback_logger.db"
    config = MockConfig()


class ActionLogger:
    def __init__(self):
        self.db_path = os.path.join(config.BASE_DIR, config.DATABASE_NAME)

    def _get_db_connection(self) -> sqlite3.Connection | None:
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            print(
                f"ActionLogger: Database connection error to {self.db_path}: {e}")
            return None

    def log_action(self, action_type: str, user_id: int = None, username: str = None,
                   details: dict = None, status: str = "SUCCESS", ip_address: str = None):
        """
        Logs a user or system action to the user_activity_log table.

        Args:
            action_type (str): A string code representing the type of action.
            user_id (int, optional): The ID of the user performing the action.
            username (str, optional): The username of the user.
            details (dict, optional): A dictionary of additional details about the action.
                                      Will be stored as a JSON string.
            status (str, optional): 'SUCCESS' or 'FAILURE' or other relevant status.
            ip_address (str, optional): IP address if relevant.
        """
        conn = self._get_db_connection()
        if not conn:
            print(
                f"ActionLogger: Cannot log action, no DB connection. Action: {action_type}, User: {username}")
            return

        details_json = json.dumps(details) if details is not None else None
        current_timestamp = time.time()

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity_log 
                (activity_timestamp, user_id, username, action_type, details, status, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (current_timestamp, user_id, username, action_type, details_json, status, ip_address))
            conn.commit()
            print(
                f"Action Logged: Type='{action_type}', User='{username or 'System'}', Status='{status}'")
        except sqlite3.Error as e:
            print(
                f"ActionLogger: Database error logging action '{action_type}': {e}")
        finally:
            if conn:
                conn.close()

    def get_recent_actions(self, limit: int = 100) -> list[dict]:
        """Retrieves recent user actions from the log."""
        conn = self._get_db_connection()
        if not conn:
            return []

        actions = []
        try:
            cursor = conn.cursor()
            # Fetch all columns for display flexibility
            cursor.execute("""
                SELECT id, activity_timestamp, user_id, username, action_type, details, status, ip_address
                FROM user_activity_log
                ORDER BY activity_timestamp DESC
                LIMIT ?
            """, (limit,))

            # Convert sqlite3.Row objects to dictionaries
            for row in cursor.fetchall():
                action_dict = {}
                for idx, col in enumerate(cursor.description):
                    action_dict[col[0]] = row[idx]
                actions.append(action_dict)
            return actions
        except sqlite3.Error as e:
            print(f"ActionLogger: Database error fetching recent actions: {e}")
            return []
        finally:
            if conn:
                conn.close()


# Global instance for easy access
action_logger = ActionLogger()

if __name__ == '__main__':
    # Example Usage (requires database to be initialized with the new table)
    print("Testing ActionLogger...")
    # You would need to run db_setup.py first if the DB/table doesn't exist
    # from ..database.db_setup import initialize_database
    # initialize_database()

    action_logger.log_action("TEST_ACTION_SUCCESS", user_id=1, username="testuser", details={
                             "info": "This is a test"}, status="SUCCESS")
    action_logger.log_action("TEST_ACTION_FAIL", username="anotheruser", details={
                             "error_code": 123}, status="FAILURE")
    action_logger.log_action("SYSTEM_STARTUP", details={"version": "0.1.0"})

    recent = action_logger.get_recent_actions(5)
    print("\nRecent Actions:")
    for item in recent:
        ts = datetime.fromtimestamp(
            item['activity_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(
            f"- {ts} | User: {item.get('username', 'N/A')} | Action: {item['action_type']} | Status: {item['status']} | Details: {item['details']}")
