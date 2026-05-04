# aurorafimpro/aurorafimpro/core/user_profiler.py
import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

# --- Mock imports for isolated execution/dependencies ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize logger
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
        def info(self, msg): pass
    logger = SimpleLogger()

try:
    import config
    from core.action_logger import ActionLogger
except ImportError as e:
    logger.error(f"Error importing config/ActionLogger in user_profiler.py: {e}")
    class MockConfig:
        BASE_DIR = "."
        DATABASE_NAME = "mock_uba.db"
    config = MockConfig()
    ActionLogger = None # Should be imported if main app runs

DATABASE_FILE = os.path.join(config.BASE_DIR, config.DATABASE_NAME)

# --- UBA Configuration/Thresholds ---
ANOMALY_THRESHOLD_MULTIPLIER = 2.5 # X times the average is considered anomalous
RISK_SCORES = {
    "UNUSUAL_LOGIN_TIME": 30,
    "HIGH_FILE_CHANGE_COUNT": 30,
    "RESTRICTED_FILE_ACCESS": 40,
}

class UserProfiler:
    def __init__(self):
        self.db_path = DATABASE_FILE
        self.risk_report = [] # Stores the last generated risk report

    def _get_db_connection(self) -> sqlite3.Connection | None:
        """Establishes a connection to the SQLite database. Returns None on failure."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"UserProfiler: Database connection error to {self.db_path}: {e}")
            return None

    def _get_user_base_stats(self, conn: sqlite3.Connection):
        """
        Calculates the 30-day rolling average for core metrics for all users.
        """
        end_time = time.time()
        start_time = end_time - timedelta(days=30).total_seconds()
        
        # 1. Core Action Log Metrics (Logins, Status Counts, Avg. Login Time)
        log_query = """
            SELECT user_id, username, activity_timestamp, action_type, status
            FROM user_activity_log
            WHERE activity_timestamp >= ? AND user_id IS NOT NULL;
        """
        
        # 2. FIM Event Metrics (Files Accessed/Modified/Deleted, File Types)
        fim_query = """
            SELECT user_id, file_path, event_timestamp, event_type
            FROM fim_events
            WHERE event_timestamp >= ? AND event_type LIKE 'LIVE_%' AND user_id IS NOT NULL;
        """
        
        user_metrics = defaultdict(lambda: {
            'username': None,
            'login_counts': [],
            'login_times': [],  # Store hours only
            'file_changes': 0,
            'file_types_modified': defaultdict(int),
            'action_counts': defaultdict(int)
        })
        
        cursor = conn.cursor()
        
        # Process User Activity Log
        cursor.execute(log_query, (start_time,))
        log_rows = cursor.fetchall()
        for row in log_rows:
            user_id = row['user_id']
            if user_id:
                username = row['username']
                
                # Update username if it's currently None for this user_id in the map
                if user_metrics[user_id].get('username') is None:
                    user_metrics[user_id]['username'] = username
                    
                if row['action_type'] == 'LOGIN_SUCCESS':
                    user_metrics[user_id]['login_counts'].append(1)
                    dt_obj = datetime.fromtimestamp(row['activity_timestamp'])
                    # Store login time as hour (0-23)
                    user_metrics[user_id]['login_times'].append(dt_obj.hour)
                
                user_metrics[user_id]['action_counts'][row['action_type']] += 1

        # Process FIM Events
        cursor.execute(fim_query, (start_time,))
        fim_rows = cursor.fetchall()
        for row in fim_rows:
            user_id = row['user_id']
            if user_id and 'MODIFIED' in row['event_type'].upper():
                user_metrics[user_id]['file_changes'] += 1
                
                # Track file types modified
                _, ext = os.path.splitext(row['file_path'])
                user_metrics[user_id]['file_types_modified'][ext.lower()] += 1

        # Calculate Averages and store in profile format
        profiles = {}
        for user_id, metrics in user_metrics.items():
            days = (end_time - start_time) / (60 * 60 * 24)
            total_logins = sum(metrics['login_counts'])
            
            # Calculate average login time (hour mode, simplified)
            if metrics['login_times']:
                avg_login_hour = round(sum(metrics['login_times']) / len(metrics['login_times'])) % 24
            else:
                avg_login_hour = None
            
            # Calculate top 5 most modified file extensions
            top_file_types = sorted(metrics['file_types_modified'].items(), key=lambda item: item[1], reverse=True)[:5]

            profiles[user_id] = {
                'username': metrics.get('username'),
                'avg_logins_per_day': round(total_logins / days, 2),
                'avg_file_changes_per_day': round(metrics['file_changes'] / days, 2),
                'normal_login_hour': avg_login_hour,
                'normal_file_types': [ext for ext, count in top_file_types],
                'profile_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        return profiles
    
    def save_profiles(self):
        """Calculates and overwrites all user profiles."""
        conn = self._get_db_connection()
        if not conn:
            return False

        try:
            profiles = self._get_user_base_stats(conn)
            cursor = conn.cursor()
            
            # Clear old profiles
            cursor.execute("DELETE FROM user_profiles")
            
            for user_id, profile_data in profiles.items():
                # Attempt to get an existing username if the base stats couldn't provide one (edge case)
                username = profile_data.pop('username') or 'N/A'
                
                # Insert new profile
                cursor.execute("""
                    INSERT INTO user_profiles (user_id, username, profile_data_json)
                    VALUES (?, ?, ?)
                """, (user_id, username, json.dumps(profile_data)))
            
            conn.commit()
            logger.info(f"User profiles updated for {len(profiles)} users.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving user profiles: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load_profile(self, user_id: int) -> dict | None:
        """Loads the profile for a specific user."""
        conn = self._get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_data_json FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row['profile_data_json'])
            return None
        except sqlite3.Error as e:
            logger.error(f"Error loading profile for user_id {user_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def check_for_anomaly(self, user_id: int) -> tuple[int, str]:
        """
        Runs anomaly detection and calculates risk score for a single user's last 24 hours of activity.
        Returns: (risk_score: int, classification: str)
        """
        profile = self.load_profile(user_id)
        if not profile:
            return 0, "No Profile"

        conn = self._get_db_connection()
        if not conn:
            return 0, "DB Error"

        risk_score = 0
        current_time = time.time()
        start_time_24h = current_time - timedelta(days=1).total_seconds()
        
        # 1. Get last 24h of activity
        activity_query = """
            SELECT activity_timestamp, action_type
            FROM user_activity_log
            WHERE user_id = ? AND activity_timestamp >= ?;
        """
        fim_query = """
            SELECT file_path, event_type, event_timestamp
            FROM fim_events
            WHERE user_id = ? AND event_timestamp >= ? AND event_type LIKE 'LIVE_%';
        """

        cursor = conn.cursor()
        
        # Check Login Time Anomaly
        cursor.execute(activity_query, (user_id, start_time_24h))
        log_rows = cursor.fetchall()
        
        login_times_24h = [datetime.fromtimestamp(row['activity_timestamp']).hour 
                           for row in log_rows if row['action_type'] == 'LOGIN_SUCCESS']
        
        # Simple Logic: Check if the majority of the day's logins were outside the normal hour (or +/- 3 hours)
        normal_hour = profile.get('normal_login_hour')
        if normal_hour is not None and login_times_24h:
            unusual_logins = 0
            for login_hour in login_times_24h:
                # Check if the hour is outside the normal window (e.g., normal_hour +/- 3 hours)
                if not (normal_hour - 3 <= login_hour <= normal_hour + 3):
                     unusual_logins += 1
            
            if unusual_logins / len(login_times_24h) > 0.5: # More than 50% logins are unusual
                risk_score += RISK_SCORES["UNUSUAL_LOGIN_TIME"]
                
        # Check File Change Count Anomaly
        cursor.execute(fim_query, (user_id, start_time_24h))
        fim_rows = cursor.fetchall()
        
        file_changes_24h = 0
        for row in fim_rows:
            if 'MODIFIED' in row['event_type'].upper():
                file_changes_24h += 1
        
        avg_changes = profile.get('avg_file_changes_per_day', 0.0)
        if file_changes_24h > (avg_changes * ANOMALY_THRESHOLD_MULTIPLIER) and file_changes_24h > 10: # Min 10 changes for significance
            risk_score += RISK_SCORES["HIGH_FILE_CHANGE_COUNT"]

        # Check File Type Anomaly (Restricted/Unusual File Access)
        normal_file_types = set(profile.get('normal_file_types', []))
        restricted_extensions = {'.exe', '.dll', '.sys', '.dat'} # Example restricted types
        
        for row in fim_rows:
            _, ext = os.path.splitext(row['file_path'])
            ext = ext.lower()
            
            # Anomaly 1: Accessing completely new/unusual file type
            if ext and ext not in normal_file_types:
                risk_score += (RISK_SCORES["RESTRICTED_FILE_ACCESS"] // 2) # Half risk for unusual type
                normal_file_types.add(ext) # Don't double count for the next iteration

            # Anomaly 2: Accessing highly restricted file type (higher risk)
            if ext in restricted_extensions:
                 risk_score += RISK_SCORES["RESTRICTED_FILE_ACCESS"]
                 break # High risk triggered, no need to check other files

        # Risk Classification
        risk_class = "Normal"
        if risk_score >= 70:
            risk_class = "High Risk"
        elif risk_score >= 40:
            risk_class = "Suspicious"
            
        return risk_score, risk_class

    def generate_daily_risk_report(self) -> list:
        """
        Identifies all users and runs anomaly check on each of them.
        Saves the resulting risk scores to self.risk_report and returns it.
        """
        conn = self._get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            # We need all user IDs who have logged at least once
            cursor.execute("SELECT DISTINCT user_id, username FROM user_activity_log WHERE user_id IS NOT NULL")
            user_data = cursor.fetchall()
            
            daily_report = []
            
            for user in user_data:
                user_id = user['user_id']
                username = user['username']
                
                # Check for anomaly
                score, classification = self.check_for_anomaly(user_id)
                
                if score > 0:
                    daily_report.append({
                        'user_id': user_id,
                        'username': username,
                        'risk_score': score,
                        'classification': classification,
                        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            self.risk_report = sorted(daily_report, key=lambda x: x['risk_score'], reverse=True)
            return self.risk_report
            
        except sqlite3.Error as e:
            logger.error(f"Error generating daily risk report: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_user_profiles(self) -> list[dict]:
        """
        (NEW) Retrieves all stored user profiles for display on the UBA Dashboard.
        """
        conn = self._get_db_connection()
        if not conn:
            return []
        
        profiles = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, profile_data_json FROM user_profiles")
            for row in cursor.fetchall():
                profile_data = json.loads(row['profile_data_json'])
                profiles.append({
                    'user_id': row['user_id'],
                    'username': row['username'],
                    **profile_data # Merge profile details
                })
            return profiles
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user profiles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_latest_risk_report(self) -> list[dict]:
        """
        (NEW) Returns the last calculated risk report.
        """
        # The list is updated by generate_daily_risk_report, which is called periodically by the MainWindow timer.
        return self.risk_report


# Global instance for use in FIMEngine and MainWindow
user_profiler = UserProfiler()