"""
Database connection pooling for AuroraFIM.
Manages SQLite connections efficiently to avoid resource exhaustion.
"""

import sqlite3
import threading
import time
from queue import Queue
from contextlib import contextmanager
from typing import Optional


class DatabaseConnectionPool:
    """Thread-safe connection pool for SQLite database."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str, pool_size: int = 5):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str, pool_size: int = 5):
        if self._initialized:
            return
        
        self._initialized = True
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Pre-populate pool with connections
        for _ in range(pool_size):
            try:
                conn = self._create_connection()
                self.connections.put(conn)
            except sqlite3.Error as e:
                import logging
                logging.error(f"Failed to create pooled connection: {e}")
        
        # Initialize performance monitoring
        try:
            from core.performance_monitor import performance_monitor
            # Record initial pool creation
            for _ in range(pool_size):
                performance_monitor.record_connection_acquired()
        except ImportError:
            pass  # Performance monitoring optional
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_connection(self):
        """
        Context manager to get a connection from the pool.
        Automatically returns connection to pool when done.
        """
        conn = None
        start_time = time.time()
        
        try:
            conn = self.connections.get(timeout=5)
            wait_time = time.time() - start_time
            
            # Update performance metrics
            try:
                from core.performance_monitor import performance_monitor
                performance_monitor.record_connection_acquired(wait_time)
                active_conns = self.pool_size - self.connections.qsize()
                performance_monitor.update_pool_utilization(active_conns, self.pool_size)
            except ImportError:
                pass
            
            yield conn
        except Exception as e:
            import logging
            logging.error(f"Error getting connection from pool: {e}")
            
            # Track error
            try:
                from core.performance_monitor import performance_monitor
                performance_monitor.record_connection_error()
            except ImportError:
                pass
            
            yield None
        finally:
            if conn:
                try:
                    self.connections.put(conn, timeout=5)
                    
                    # Update performance metrics
                    try:
                        from core.performance_monitor import performance_monitor
                        performance_monitor.record_connection_released()
                    except ImportError:
                        pass
                except Exception as e:
                    import logging
                    logging.error(f"Error returning connection to pool: {e}")
                    try:
                        conn.close()
                    except:
                        pass
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
            except:
                pass
        self._initialized = False


# Global pool instance will be initialized after config is loaded
_pool = None


def init_database_pool(db_path: str, pool_size: int = 5) -> DatabaseConnectionPool:
    """Initialize the global database connection pool."""
    global _pool
    _pool = DatabaseConnectionPool(db_path, pool_size)
    return _pool


def get_db_pool() -> Optional[DatabaseConnectionPool]:
    """Get the global database connection pool."""
    if _pool is None:
        import logging
        logging.error("Database pool not initialized. Call init_database_pool first.")
    return _pool
