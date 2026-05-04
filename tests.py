"""
Unit tests for AuroraFIM core modules.
Tests authentication, validation, and logging functionality.
"""

import unittest
import tempfile
import os
import sqlite3
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.validators import (
    validate_username, validate_password, validate_role,
    validate_file_path, sanitize_input, validate_email
)


class TestValidators(unittest.TestCase):
    """Test input validation functions."""
    
    def test_valid_username(self):
        """Test valid username validation."""
        is_valid, error = validate_username("testuser")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_invalid_username_too_short(self):
        """Test username too short."""
        is_valid, error = validate_username("ab")
        self.assertFalse(is_valid)
        self.assertIn("between", error.lower())
    
    def test_invalid_username_special_chars(self):
        """Test username with invalid characters."""
        is_valid, error = validate_username("user@name!")
        self.assertFalse(is_valid)
        self.assertIn("letters", error.lower())
    
    def test_valid_password(self):
        """Test valid password."""
        is_valid, error = validate_password("SecurePass123")
        self.assertTrue(is_valid)
    
    def test_invalid_password_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, error = validate_password("lowercase123")
        self.assertFalse(is_valid)
    
    def test_invalid_password_too_short(self):
        """Test password too short."""
        is_valid, error = validate_password("Short1")
        self.assertFalse(is_valid)
    
    def test_valid_role(self):
        """Test valid roles."""
        for role in ['admin', 'auditor', 'viewer']:
            is_valid, error = validate_role(role)
            self.assertTrue(is_valid)
    
    def test_invalid_role(self):
        """Test invalid role."""
        is_valid, error = validate_role("superuser")
        self.assertFalse(is_valid)
        self.assertIn("admin", error.lower())
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test null byte removal
        result = sanitize_input("test\x00string")
        self.assertEqual(result, "teststring")
        
        # Test whitespace trimming
        result = sanitize_input("  test  ")
        self.assertEqual(result, "test")
    
    def test_valid_email(self):
        """Test valid email format."""
        is_valid, error = validate_email("user@example.com")
        self.assertTrue(is_valid)
    
    def test_invalid_email(self):
        """Test invalid email format."""
        is_valid, error = validate_email("notanemail")
        self.assertFalse(is_valid)


class TestAuthHandler(unittest.TestCase):
    """Test authentication handler."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_dir = tempfile.mkdtemp()
        cls.db_file = os.path.join(cls.test_dir, "test_auth.db")
        
        # Create test database with users table
        conn = sqlite3.connect(cls.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'auditor', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)
        os.rmdir(cls.test_dir)


class TestLoggerInitialization(unittest.TestCase):
    """Test logger module."""
    
    def test_logger_singleton(self):
        """Test that logger is a singleton."""
        from core.logger import logger as logger1
        from core.logger import logger as logger2
        self.assertIs(logger1, logger2)
    
    def test_logger_methods(self):
        """Test logger has required methods."""
        from core.logger import logger
        self.assertTrue(callable(logger.info))
        self.assertTrue(callable(logger.warning))
        self.assertTrue(callable(logger.error))
        self.assertTrue(callable(logger.debug))
        self.assertTrue(callable(logger.critical))


if __name__ == '__main__':
    unittest.main()
