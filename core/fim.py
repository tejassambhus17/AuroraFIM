# aurorafimpro/aurorafimpro/core/fim.py
import os
import json
import time
import hmac
import hashlib
import sqlite3
import sys
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, FileMovedEvent
from PySide6.QtCore import QObject, Signal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize logger
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
        def info(self, msg): pass
        def debug(self, msg): pass
        def warning(self, msg): sys.stderr.write(f"WARNING: {msg}\n")
    logger = SimpleLogger()

try:
    import config
    from core.hashing import FileHasher
    from core.db_pool import get_db_pool, init_database_pool
except ImportError as e:
    logger.error(f"Error importing modules in core/fim.py: {e}")
    # Fallback mocks (ensure all necessary config attributes are present)

    class MockConfig:
        MONITORED_DIRECTORIES = []
        BASELINE_FILE_NAME = "b.json"
        BASELINE_SIGNATURE_FILE_NAME = "b.sig"
        HMAC_SIGNING_KEY = b"mk"
        HASH_ALGORITHM = "sha256"
        SNAPSHOT_DIR_NAME = "snaps"
        BASE_DIR = "."
        WATCHDOG_DEBOUNCE_DELAY = 1.5
        DATABASE_NAME = "mock_fim.db"
        MAX_EVENTS_IN_DASHBOARD = 100
        DEFAULT_AUDIT_SCHEDULE_TIME = "02:00"
        SCHEDULED_AUDIT_CHECK_INTERVAL = 60000
        def update_monitored_directories(
            self, paths): self.MONITORED_DIRECTORIES = paths
    config = MockConfig()
    FileHasher = type('MockFileHasher', (), {
                      '__init__': lambda s, a=None: None, 'calculate_hash': lambda s, p: "mh"})


class FIMChangeEventHandler(FileSystemEventHandler):  # (No changes to this class)
    def __init__(self, fim_engine_instance):
        super().__init__()
        self.fim_engine = fim_engine_instance
        self.debounce_timers = {}
        self.debounce_delay = getattr(config, "WATCHDOG_DEBOUNCE_DELAY", 1.5)

    def _debounce_event(self, ek, cb, *a):
        if ek in self.debounce_timers:
            self.debounce_timers[ek].cancel()
        from threading import Timer
        t = Timer(self.debounce_delay, cb, args=a)
        self.debounce_timers[ek] = t
        t.start()

    def _process_event(self, et: str, sp: str, dp: str = None):
        asp = os.path.abspath(sp)
        is_monitored = False
        for monitored_root in self.fim_engine.monitored_paths:
            if asp == monitored_root or asp.startswith(os.path.join(monitored_root, '')):
                is_monitored = True
                break
        if not is_monitored and dp:
            adp = os.path.abspath(dp)
            for monitored_root in self.fim_engine.monitored_paths:
                if adp == monitored_root or adp.startswith(os.path.join(monitored_root, '')):
                    is_monitored = True
                    break
        if not is_monitored:
            return
        self.fim_engine.handle_filesystem_change(
            et, asp, os.path.abspath(dp)if dp else None)

    def on_modified(self, e: FileModifiedEvent):
        if not e.is_directory:
            self._debounce_event(
                e.src_path, self._process_event, "MODIFIED", e.src_path)

    def on_created(self, e: FileCreatedEvent): self._debounce_event(
        e.src_path, self._process_event, "CREATED", e.src_path)

    def on_deleted(self, e: FileDeletedEvent): self._debounce_event(
        e.src_path, self._process_event, "DELETED", e.src_path)

    def on_moved(self, e: FileMovedEvent): self._debounce_event(
        e.src_path, self._process_event, "MOVED", e.src_path, e.dest_path)


class FIMEngineSignals(QObject):
    scheduledAuditCompleted = Signal(list, dict)
    liveFimEventDetected = Signal(dict)


class FIMEngine(QObject):
    def __init__(self, auth_handler=None, current_user_id: int = None):
        super().__init__()
        self.signals = FIMEngineSignals()
        self.current_user_id = current_user_id
        self.monitored_paths = list(config.MONITORED_DIRECTORIES)
        self.baseline_file = os.path.join(
            config.BASE_DIR, config.BASELINE_FILE_NAME)
        self.signature_file = os.path.join(
            config.BASE_DIR, config.BASELINE_SIGNATURE_FILE_NAME)
        self.snapshot_dir = os.path.join(
            config.BASE_DIR, config.SNAPSHOT_DIR_NAME)
        self.db_path = os.path.join(config.BASE_DIR, config.DATABASE_NAME)
        self.hasher = FileHasher(algorithm=config.HASH_ALGORITHM)
        self.auth_handler = auth_handler
        if not os.path.exists(self.snapshot_dir):
            try:
                os.makedirs(self.snapshot_dir, exist_ok=True)
            except OSError as e:
                logger.error(f"Error creating snapshot dir {self.snapshot_dir}: {e}")
        self.baseline_data = {}
        self.load_baseline()
        self.observer = None
        self.event_handler = FIMChangeEventHandler(self)
        # Initialize database connection pool
        try:
            init_database_pool(
                db_path=self.db_path,
                pool_size=5
            )
            logger.info("Database connection pool initialized for FIM engine")
        except Exception as e:
            logger.warning(f"Could not initialize database pool: {e}. Will use fallback connections.")
            self._use_pool = False
        else:
            self._use_pool = True

    # Removed direct SQLite connection method - use pool instead
    def _get_db_connection_from_pool(self) -> sqlite3.Connection | None:
        """Get a connection from the pool or fallback to direct connection."""
        pool = get_db_pool()
        if pool and self._use_pool:
            try:
                conn = pool.connections.get(timeout=2)
                return conn
            except Exception as e:
                logger.warning(f"Could not get connection from pool: {e}")
        # Fallback to direct connection
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error to {self.db_path}: {e}")
            return None

    def _return_connection_to_pool(self, conn: sqlite3.Connection):
        """Return connection to pool or close it."""
        pool = get_db_pool()
        if pool and self._use_pool:
            try:
                pool.connections.put(conn, timeout=2)
                return
            except Exception as e:
                logger.warning(f"Could not return connection to pool: {e}")
        # Fallback to closing
        try:
            if conn:
                conn.close()
        except:
            pass

    def _log_event_to_db(self, ed: dict, user_id: int = None):
        conn = self._get_db_connection_from_pool()
        if not conn:  # Check if connection failed
            logger.error(
                f"Cannot log event to DB, no connection. Event: {ed}")
            return
        
        # Determine user ID to log
        event_user_id = user_id if user_id is not None else self.current_user_id
        
        try:
            cursor = conn.cursor()
            # MODIFIED: Insert 'user_id' column
            cursor.execute("INSERT INTO fim_events (event_timestamp,file_path,event_type,baseline_hash,actual_hash,expected_props,actual_props,details,source,user_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (ed.get("timestamp", time.time()), ed.get("path", "N/A"), ed.get("change_type", "UNKNOWN"), ed.get("expected_hash"), ed.get("actual_hash"),
                            json.dumps(ed.get("expected_props"))if ed.get("expected_props")else None, json.dumps(
                               ed.get("actual_props"))if ed.get("actual_props")else None,
                               ed.get("details"), ed.get("source", "UNKNOWN"), event_user_id))
            conn.commit()
            logger.debug(f"DB Event: {ed.get('change_type')} on {ed.get('path')}")
        except sqlite3.Error as e:
            logger.error(f"DB log error: {e}")
        finally:
            if conn:  # Ensure conn exists before returning
                self._return_connection_to_pool(conn)

    def get_recent_events_from_db(self, limit: int = None) -> list[dict]:
        l = limit or getattr(config, "MAX_EVENTS_IN_DASHBOARD", 100)
        conn = self._get_db_connection_from_pool()
        if not conn:  # Check if connection failed
            return []  # Return empty list if no connection

        evs = []
        try:
            cursor = conn.cursor()
            # MODIFIED: Included user_id in SELECT
            cursor.execute(
                "SELECT event_timestamp,file_path,event_type,baseline_hash,actual_hash,details,source,user_id FROM fim_events ORDER BY event_timestamp DESC LIMIT ?", (l,))
            for r in cursor.fetchall():
                evs.append(dict(r))
            return evs
        except sqlite3.Error as e:
            logger.error(f"DB fetch error: {e}")
            return []  # Return empty list on query error
        finally:
            if conn:  # Ensure conn exists before returning
                self._return_connection_to_pool(conn)

    def update_monitored_paths_and_restart_observer(self, new_paths: list[str]):
        logger.info("FIMEngine: Updating monitored paths and restarting observer...")
        self.stop_monitoring()
        normalized_paths = []
        for path in new_paths:
            abs_path = os.path.abspath(path)
            if abs_path not in normalized_paths:
                normalized_paths.append(abs_path)
        self.monitored_paths = normalized_paths
        config.MONITORED_DIRECTORIES = list(self.monitored_paths)
        self.start_monitoring()
        logger.info(
            f"FIMEngine: Observer restarted with paths: {self.monitored_paths}")

    def start_monitoring(self):
        if not self.monitored_paths:
            logger.warning("FIM: No paths to monitor.")
            return
        if self.observer and self.observer.is_alive():
            logger.debug("FIM: Monitoring active.")
            return
        self.observer = Observer()
        for path in self.monitored_paths:
            if os.path.exists(path):
                self.observer.schedule(
                    self.event_handler, path, recursive=os.path.isdir(path))
                logger.info(
                    f"FIM: Monitoring {'dir' if os.path.isdir(path) else 'file'}: {path}")
            else:
                logger.warning(f"FIM: Path '{path}' not found for monitoring.")
        if self.observer.emitters:
            self.observer.start()
            logger.info("FIM: Live monitoring started.")
        else:
            logger.warning("FIM: No valid paths scheduled. Observer not started.")
            self.observer = None

    def stop_monitoring(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("FIM: Live monitoring stopped.")
        self.observer = None

    def handle_filesystem_change(self, et: str, sp: str, dp: str = None):
        logger.debug(f"FIM Processing Live: {et} on {sp}" + (f" -> {dp}" if dp else ""))
        # user_id is implicit via self.current_user_id, used as fallback in _log_event_to_db
        cd = {"path": sp, "change_type": f"LIVE_{et.upper()}",
              "timestamp": time.time(), "source": "LIVE"}
        if et == "CREATED":
            props = self._scan_file_properties(sp)
            cd["actual_props"] = props
            cd["actual_hash"] = props.get("hash")if props else None
        elif et == "DELETED":
            if sp in self.baseline_data:
                cd["expected_props"] = self.baseline_data[sp]
        elif et == "MODIFIED":
            props = self._scan_file_properties(sp)
            cd["actual_props"] = props
            cd["actual_hash"] = props.get("hash")if props else None
            if sp in self.baseline_data:
                cd["expected_props"] = self.baseline_data[sp]
                cd["baseline_hash"] = self.baseline_data[sp].get("hash")
        elif et == "MOVED":
            cd["details"] = f"Moved to:{dp}"
            if sp in self.baseline_data:
                cd["original_baseline_props"] = self.baseline_data[sp]
            if dp:
                dp_props = self._scan_file_properties(dp)
                dest_ev = {"path": dp, "change_type": "LIVE_MOVED_DESTINATION", "timestamp": time.time(
                ), "source": "LIVE", "actual_props": dp_props, "actual_hash": dp_props.get("hash")if dp_props else None, "details": f"Moved from:{sp}"}
                self._log_event_to_db(dest_ev)
                self.signals.liveFimEventDetected.emit(dest_ev)
        self._log_event_to_db(cd)
        self.signals.liveFimEventDetected.emit(cd)

    def _sign_data(self, d: bytes) -> str: k = config.HMAC_SIGNING_KEY; k = k.encode()if isinstance(k,
                                                                                                    str)else k; db = d.encode()if isinstance(d, str)else d; return hmac.new(k, db, hashlib.sha256).hexdigest()

    def _verify_signature(
        self, d: bytes, s_hex: str) -> bool: return hmac.compare_digest(self._sign_data(d), s_hex)

    def load_baseline(self) -> bool:
        if not os.path.exists(self.baseline_file):
            self.baseline_data = {}
            return False
        try:
            with open(self.baseline_file, 'r')as f:
                bc = f.read()
            if not os.path.exists(self.signature_file):
                logger.warning("Baseline signature file missing")
                self.baseline_data = {}
                return False
            with open(self.signature_file, 'r')as f_s:
                sig = f_s.read().strip()
            if self._verify_signature(bc.encode('utf-8'), sig):
                self.baseline_data = json.loads(bc)
                logger.info("Baseline loaded and verified")
                return True
            else:
                logger.error("Baseline signature verification FAILED!")
                self.baseline_data = {}
                return False
        except Exception as e:
            logger.error(f"Error loading baseline: {e}")
            self.baseline_data = {}
            return False

    def save_baseline(self) -> bool:
        try:
            bc = json.dumps(self.baseline_data, indent=4)
            sig = self._sign_data(bc.encode('utf-8'))
            with open(self.baseline_file, 'w')as f:
                f.write(bc)
            with open(self.signature_file, 'w')as f_s:
                f_s.write(sig)
            logger.info("Baseline saved and signed")
            return True
        except Exception as e:
            logger.error(f"Error saving baseline: {e}")
            return False

    def _scan_file_properties(self, fp: str) -> dict | None:
        try:
            h = self.hasher.calculate_hash(fp)
            if h is None:
                return None
            si = os.stat(fp)
            return {"hash": h, "size": si.st_size, "mtime": si.st_mtime, "mode": si.st_mode, "last_scanned": time.time()}
        except Exception as e:
            logger.error(f"Error scanning file properties for {fp}: {e}")
            return None

    def add_and_baseline_single_file(self, file_path: str) -> tuple[bool, str]:
        abs_file_path = os.path.abspath(file_path)
        if not os.path.exists(abs_file_path) or not os.path.isfile(abs_file_path):
            return False, f"File not found or is not a regular file: {abs_file_path}"
        logger.info(f"Adding and baselining single file: {abs_file_path}")
        properties = self._scan_file_properties(abs_file_path)
        if not properties:
            return False, f"Could not scan properties for file: {abs_file_path}"
        self.baseline_data[abs_file_path] = properties
        if not self.save_baseline():
            return False, f"Updated in-memory baseline for {abs_file_path}, but failed to save baseline file."
        is_already_effectively_monitored = False
        for monitored_root in self.monitored_paths:
            if abs_file_path == monitored_root or abs_file_path.startswith(os.path.join(monitored_root, '')):
                is_already_effectively_monitored = True
                break
        if not is_already_effectively_monitored:
            self.monitored_paths.append(abs_file_path)
        return True, f"Successfully added and baselined file: {abs_file_path}"

    def create_new_baseline(self, paths_to_monitor: list[str] = None) -> tuple[bool, dict]:
        logger.info("Creating new baseline for all monitored items")
        nb = {}
        fs = 0
        se = 0
        tp = paths_to_monitor if paths_to_monitor is not None else self.monitored_paths
        if not tp:
            return False, {"message": "No paths.", "files_scanned": 0, "scan_errors": 0}
        for rp in tp:
            if not os.path.exists(rp):
                se += 1
                continue
            if os.path.isfile(rp):
                p = self._scan_file_properties(rp)
                if p:
                    nb[os.path.abspath(rp)] = p
                    fs += 1
                else:
                    se += 1
            elif os.path.isdir(rp):
                for dp, _, fns in os.walk(rp):
                    for fn in fns:
                        fp = os.path.join(dp, fn)
                        afp = os.path.abspath(fp)
                        p = self._scan_file_properties(afp)
                        if p:
                            nb[afp] = p
                            fs += 1
                        else:
                            se += 1
        self.baseline_data = nb
        s = self.save_baseline()
        smry = {"message": "Baseline created."if s else "Save fail.",
                "files_scanned": fs, "scan_errors": se, "save_successful": s}
        logger.info(f"Baseline creation summary: {smry}")
        return s, smry

    def verify_integrity(self, is_scheduled_audit: bool = False) -> tuple[list[dict], dict]:
        logger.info(f"Starting integrity verification (scheduled audit: {is_scheduled_audit})")
        if not self.baseline_data:
            return [], {"message": "No baseline.", "checked": 0, "mismatches": 0, "errors": 0, "new_files": 0, "removed_files": 0}
        df = []
        cf = 0
        mc = 0
        ec = 0
        nfd = 0
        cfs = {}

        for bp, bprops in self.baseline_data.items():
            cf += 1
            cfs[bp] = True
            ed = {"path": bp, "timestamp": time.time(), "source": "SCAN",
                  "expected_props": bprops}
            if not os.path.exists(bp):
                ed.update({"change_type": "REMOVED",
                          "actual_props": {"status": "Not found"}})
                mc += 1
            else:
                cp = self._scan_file_properties(bp)
                ed["actual_props"] = cp
                if not cp:
                    ed["change_type"] = "ERROR_SCANNING"
                    ec += 1
                elif cp["hash"] != bprops["hash"]:
                    ed.update({"change_type": "MODIFIED_HASH",
                              "baseline_hash": bprops["hash"], "actual_hash": cp["hash"]})
                    mc += 1
                elif cp["size"] != bprops["size"]:
                    ed.update({"change_type": "MODIFIED_SIZE",
                              "baseline_hash": bprops["hash"], "actual_hash": cp["hash"]})
                    mc += 1
                else:
                    ed = None
            if ed and ed.get("change_type"):
                self._log_event_to_db(ed)
                df.append(ed)

        if is_scheduled_audit:
            logger.debug("Scheduled audit: scanning for new files in monitored directories")
            for rp in self.monitored_paths:
                if not os.path.exists(rp):
                    continue
                paths_to_check = []
                if os.path.isfile(rp):
                    paths_to_check.append(os.path.abspath(rp))
                elif os.path.isdir(rp):
                    for dp, _, fns in os.walk(rp):
                        for fn in fns:
                            paths_to_check.append(
                                os.path.abspath(os.path.join(dp, fn)))
                for afp in paths_to_check:
                    if afp not in self.baseline_data and afp not in cfs:
                        cp = self._scan_file_properties(afp)
                        ed = {"path": afp, "change_type": "NEW_FILE", "actual_props": cp, "actual_hash": cp.get(
                            "hash")if cp else None, "timestamp": time.time(), "source": "SCAN"}
                        self._log_event_to_db(ed)
                        df.append(ed)
                        nfd += 1
                        cfs[afp] = True
        else:
            logger.debug("Manual verification: skipping scan for new files in monitored directories")

        smry = {"message": "Integrity scan complete.", "files_in_baseline": len(
            self.baseline_data), "files_checked_from_baseline": cf-ec, "mismatches_found": mc, "new_files_detected": nfd, "scan_errors": ec, "timestamp": datetime.now().isoformat()}
        logger.info(f"Integrity verification summary: {smry}")
        if is_scheduled_audit:
            self.signals.scheduledAuditCompleted.emit(df, smry)
        return df, smry

    # NEW METHOD for UBA integration: trigger_risk_assessment
    def trigger_risk_assessment(self) -> list:
        """Triggers the profiler to generate the daily risk report."""
        try:
            # Dynamic import to avoid circular dependency
            from core.user_profiler import user_profiler
            return user_profiler.generate_daily_risk_report()
        except ImportError:
            logger.error("user_profiler module not found for risk assessment")
            return []

    # NEW METHOD for UBA integration: update_user_profiles
    def update_user_profiles(self) -> bool:
        """Triggers the profiler to recalculate all user baselines."""
        try:
            from core.user_profiler import user_profiler
            return user_profiler.save_profiles()
        except ImportError:
            logger.error("user_profiler module not found for profile update")
            return False

if __name__ == '__main__':
    pass