"""
Centralized logging module for AuroraFIM.
Replaces scattered print statements with proper structured logging.
"""

import logging
import os
import sys
from datetime import datetime


class AuroraFIMLogger:
    """Centralized logging handler for the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('AuroraFIM')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (if log directory exists)
        try:
            try:
                import config
                log_dir = os.path.dirname(os.path.join(config.BASE_DIR, config.LOG_FILE))
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(config.BASE_DIR, config.LOG_FILE)
            except (ImportError, AttributeError):
                # Fallback if config is not available or BASE_DIR is not set
                log_dir = os.path.join(os.getcwd(), "logs")
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "aurorafim.log")
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    def _record_metric(self, level: str):
        """Record a log message in performance metrics."""
        try:
            from core.performance_monitor import performance_monitor
            performance_monitor.record_log_message(level)
        except ImportError:
            pass  # Performance monitoring optional
    
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)
        self._record_metric('DEBUG')
    
    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
        self._record_metric('INFO')
    
    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
        self._record_metric('WARNING')
    
    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
        self._record_metric('ERROR')
    
    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)
        self._record_metric('CRITICAL')


# Global singleton instance
logger = AuroraFIMLogger()
