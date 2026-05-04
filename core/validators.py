"""
Input validation utilities for AuroraFIM.
Provides sanitization and validation functions for user inputs.
"""

import re
import os
from typing import Tuple


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_username(username: str, min_length: int = 3, max_length: int = 32) -> Tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username: Username string to validate
        min_length: Minimum length
        max_length: Maximum length
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username must be a non-empty string."
    
    if len(username) < min_length or len(username) > max_length:
        return False, f"Username must be between {min_length} and {max_length} characters."
    
    # Allow alphanumeric, underscore, and hyphen only
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens."
    
    return True, ""


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password string to validate
        min_length: Minimum length
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string."
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    
    # Check for variety
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numeric characters."
    
    return True, ""


def validate_role(role: str) -> Tuple[bool, str]:
    """
    Validate user role.
    
    Args:
        role: Role string to validate
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    valid_roles = ['admin', 'auditor', 'viewer']
    
    if role not in valid_roles:
        return False, f"Role must be one of: {', '.join(valid_roles)}"
    
    return True, ""


def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    Validate file path format and optionally existence.
    
    Args:
        file_path: File path string to validate
        must_exist: Whether file must exist
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not file_path or not isinstance(file_path, str):
        return False, "File path must be a non-empty string."
    
    # Normalize path
    normalized_path = os.path.normpath(file_path)
    
    # Check for path traversal attempts
    if '..' in normalized_path:
        return False, "Path traversal attacks are not allowed."
    
    # Check if path exists if required
    if must_exist and not os.path.exists(normalized_path):
        return False, f"Path does not exist: {file_path}"
    
    return True, ""


def validate_directory_path(dir_path: str, must_exist: bool = True) -> Tuple[bool, str]:
    """
    Validate directory path format and optionally existence.
    
    Args:
        dir_path: Directory path string to validate
        must_exist: Whether directory must exist
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    is_valid, error = validate_file_path(dir_path, must_exist=False)
    if not is_valid:
        return is_valid, error
    
    # Check if it's a directory
    if must_exist and not os.path.isdir(dir_path):
        return False, f"Path is not a directory: {dir_path}"
    
    return True, ""


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially harmful characters.
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Truncate to max length
    result = input_string[:max_length]
    
    # Remove null bytes
    result = result.replace('\x00', '')
    
    return result.strip()


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format (basic validation).
    
    Args:
        email: Email string to validate
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string."
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format."
    
    return True, ""
