"""
AuroraFIM - File Integrity Monitoring System
Professional initialization module for package setup.
"""

__version__ = "0.1.0"
__author__ = "Tejas Sambhus"

# Initialize logging on package import
try:
    from core.logger import logger
except ImportError:
    import sys
    sys.stderr.write("Warning: Could not initialize logger\n")
    # Create a fallback logger if import fails
    class FallbackLogger:
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
        def warning(self, msg): sys.stderr.write(f"WARNING: {msg}\n")
        def info(self, msg): pass
    logger = FallbackLogger()

# Initialize database pool after config is loaded
def init_db_pool():
    """Call this after config is loaded to initialize the database connection pool."""
    try:
        import config
        from core.db_pool import init_database_pool
        init_database_pool(
            db_path=f"{config.BASE_DIR}/{config.DATABASE_NAME}",
            pool_size=5
        )
        logger.info("Database connection pool initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize database pool: {e}")
    
# Export performance monitoring
try:
    from core.performance_monitor import performance_monitor
    from core.metrics_api import (
        get_performance_report,
        get_pool_status,
        get_logging_status,
        get_alerts,
        export_metrics,
        print_performance_report
    )
except ImportError:
    pass  # Performance monitoring is optional
