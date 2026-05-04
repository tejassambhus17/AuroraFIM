"""
Initial application setup utilities for AuroraFIM.
Handles first-time setup, admin user creation, and configuration.
"""

import sys
import getpass
from typing import Tuple, Optional
from . import logger
from .validators import validate_username, validate_password, validate_role


def prompt_for_admin_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Prompt user to create admin credentials (interactive).
    
    Returns:
        Tuple[username, password] or (None, None) if cancelled
    """
    logger.info("=" * 50)
    logger.info("Initial Setup Required: Create Admin User")
    logger.info("=" * 50)
    
    while True:
        username = input("\nEnter admin username: ").strip()
        is_valid, error = validate_username(username)
        if not is_valid:
            logger.warning(f"Invalid username: {error}")
            continue
        break
    
    while True:
        password = getpass.getpass("Enter admin password: ")
        is_valid, error = validate_password(password)
        if not is_valid:
            logger.warning(f"Invalid password: {error}")
            continue
        
        password_confirm = getpass.getpass("Confirm admin password: ")
        if password != password_confirm:
            logger.warning("Passwords do not match.")
            continue
        
        break
    
    logger.info(f"Admin user '{username}' configured.")
    return username, password


def setup_admin_user_interactive(auth_handler) -> bool:
    """
    Prompt user to create first admin user (interactive mode).
    
    Args:
        auth_handler: AuthHandler instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if users already exist
        if auth_handler.get_user_count() > 0:
            logger.info("Users already exist in the database.")
            return True
        
        logger.info("No users found. Creating first admin user...")
        
        # Prompt user for credentials
        username, password = prompt_for_admin_credentials()
        
        if not username or not password:
            logger.error("Setup cancelled.")
            return False
        
        # Create the user
        if auth_handler.create_user(username, password, "admin"):
            logger.info(f"Admin user '{username}' created successfully.")
            return True
        else:
            logger.error("Failed to create admin user.")
            return False
    
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled by user.")
        return False
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False


def setup_admin_user_headless(auth_handler, username: str, password: str) -> bool:
    """
    Create first admin user (programmatic mode, no interaction).
    
    Args:
        auth_handler: AuthHandler instance
        username: Admin username
        password: Admin password
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate inputs
        is_valid, error = validate_username(username)
        if not is_valid:
            logger.error(f"Invalid username: {error}")
            return False
        
        is_valid, error = validate_password(password)
        if not is_valid:
            logger.error(f"Invalid password: {error}")
            return False
        
        # Check if users already exist
        if auth_handler.get_user_count() > 0:
            logger.info("Users already exist in the database.")
            return True
        
        # Create the user
        if auth_handler.create_user(username, password, "admin"):
            logger.info(f"Admin user '{username}' created successfully.")
            return True
        else:
            logger.error("Failed to create admin user.")
            return False
    
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False
