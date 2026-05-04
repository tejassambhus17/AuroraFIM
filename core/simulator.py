# aurorafimpro/aurorafimpro/core/simulator.py
import os
import time
from datetime import datetime
from PySide6.QtCore import QObject, Signal

# Adjust path to import core/fim and core/auth
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
    from core.fim import FIMEngine
    from core.auth import AuthHandler
    from core.action_logger import action_logger
    from core.user_profiler import user_profiler # NEW: Import global profiler instance
except ImportError as e:
    logger.error(f"Error importing modules in core/simulator.py: {e}")
    FIMEngine = None
    AuthHandler = None
    # Mock logger to prevent errors if running standalone
    class MockLogger:
        def log_action(self, *args, **kwargs): pass
    action_logger = MockLogger()
    # Mock profiler
    class MockProfiler:
        def save_profiles(self): return True
    user_profiler = MockProfiler()


class Simulator:
    """Utility to run scenario-based tests against the FIM/UBA system."""

    def __init__(self, fim_engine: FIMEngine, auth_handler: AuthHandler):
        self.fim_engine = fim_engine
        self.auth_handler = auth_handler
        self.target_user_id = None
        self.target_username = "sim_attacker"

    def _ensure_target_user(self):
        """Ensures a dedicated user exists for simulation."""
        user = self.auth_handler.get_user(self.target_username)
        if user:
            self.target_user_id = user['id']
            return True

        # Create user if not found (using default password for testing)
        if self.auth_handler.create_user(self.target_username, "SimulateP@ss", "auditor"):
            user = self.auth_handler.get_user(self.target_username)
            if user:
                self.target_user_id = user['id']
                action_logger.log_action(
                    action_type="UBA_SIM_USER_CREATED", username="System", 
                    details={"user": self.target_username}, status="SUCCESS"
                )
                return True
        
        logger.error(f"Could not ensure simulation user {self.target_username} exists.")
        return False

    def run_anomaly_scenario(self) -> str:
        """
        Simulates behavior designed to trigger anomaly alerts:
        1. Accessing multiple files (High File Change Count).
        2. Accessing restricted file types (Restricted File Access).
        3. Logging in (to contribute to the unusual time anomaly).
        """
        if not self._ensure_target_user():
            return "Simulation failed: Cannot create or find simulation user."
        
        # 1. Simulate an unusual login (just log the action)
        action_logger.log_action(
            action_type="LOGIN_SUCCESS", 
            user_id=self.target_user_id, 
            username=self.target_username,
            details={"note": "Simulated login at an off-hour (e.g., 3:00 AM)"}, 
            status="SUCCESS"
        )
        
        # 2. Simulate High File Change Count (25 changes) and Restricted Access
        test_files = [
            "/etc/hosts", 
            "/tmp/temp_config.conf", 
            "/var/log/secure",
            "/bin/restricted.exe", # Restricted file type
        ]
        
        num_changes = 25 
        
        for i in range(num_changes):
            file_to_change = test_files[i % (len(test_files) - 1)] # Avoid the .exe file in the high count loop
            
            # Simulate MODIFIED event (requires user_id)
            event = {
                "path": os.path.abspath(file_to_change),
                "change_type": "LIVE_MODIFIED",
                "timestamp": time.time() - (i * 10), 
                "source": "SIMULATOR",
                "details": f"Simulated change {i+1}",
                "expected_hash": "OLD",
                "actual_hash": f"NEW_{i}",
            }
            # Manually call FIMEngine's logger with the specific user_id
            self.fim_engine._log_event_to_db(event, user_id=self.target_user_id)
        
        # 3. Simulate Restricted Access on the .exe file (should trigger the highest risk)
        restricted_event = {
            "path": os.path.abspath("/bin/restricted.exe"),
            "change_type": "LIVE_MODIFIED",
            "timestamp": time.time() - 5,
            "source": "SIMULATOR",
            "details": "Simulated restricted file modification (high risk)",
            "actual_hash": "RESTRICTED_HASH",
        }
        self.fim_engine._log_event_to_db(restricted_event, user_id=self.target_user_id)
        
        # NEW FIX: Force the profile calculation immediately after logging anomalies.
        # This sets a "low" baseline against which the just-logged anomalies will be checked.
        user_profiler.save_profiles() 
        
        return f"Anomaly simulation successfully logged {num_changes + 1} events for user '{self.target_username}' (ID: {self.target_user_id}). The next periodic UBA check will generate an alert."