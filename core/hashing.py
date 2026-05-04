# aurorafimpro/aurorafimpro/core/hashing.py
import hashlib
import os
import sys

# Adjust path to import config from the parent 'aurorafimpro' package directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize logger
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
        def warning(self, msg): sys.stderr.write(f"WARNING: {msg}\n")
        def info(self, msg): pass
    logger = SimpleLogger()

try:
    import config  # For HASH_ALGORITHM
except ImportError as e:
    logger.error(f"Error importing config in core/hashing.py: {e}")
    # Fallback or default if config is not available, though it's preferred

    class MockConfig:
        HASH_ALGORITHM = "sha256"  # Default if config fails
    config = MockConfig()


class FileHasher:
    """
    Utility class for generating file hashes.
    """

    def __init__(self, algorithm: str = None):
        """
        Initializes the hasher with a specific algorithm.
        Args:
            algorithm (str): The hashing algorithm to use (e.g., 'sha256', 'md5').
                             Defaults to the algorithm specified in config.py.
        """
        self.algorithm = algorithm or config.HASH_ALGORITHM
        if not hasattr(hashlib, self.algorithm):
            raise ValueError(
                f"Unsupported hash algorithm: {self.algorithm}. Supported: {hashlib.algorithms_available}")

    def calculate_hash(self, file_path: str) -> str | None:
        """
        Calculates the hash of a given file.

        Args:
            file_path (str): The absolute path to the file.

        Returns:
            str: The hexadecimal representation of the file's hash,
                 or None if the file cannot be read or an error occurs.
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.error(f"File not found or is not a file: {file_path}")
            return None

        try:
            hasher = hashlib.new(self.algorithm)
            with open(file_path, 'rb') as f:
                while True:
                    # Read in chunks to handle large files efficiently
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except IOError as e:
            logger.error(f"IOError reading file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error hashing file {file_path}: {e}")
            return None


if __name__ == '__main__':
    # --- Test Hashing ---
    # Create a dummy file for testing
    dummy_file_content = b"This is a test file for AuroraFIM Pro hashing."
    dummy_file_path = "dummy_test_file.txt"

    try:
        with open(dummy_file_path, "wb") as f:
            f.write(dummy_file_content)
        logger.info(f"Created dummy file: {dummy_file_path}")

        # Test with default algorithm (from config or fallback)
        default_hasher = FileHasher()
        logger.info(f"Using algorithm: {default_hasher.algorithm}")
        hash_value_default = default_hasher.calculate_hash(dummy_file_path)
        if hash_value_default:
            logger.info(
                f"Hash ({default_hasher.algorithm}) for '{dummy_file_path}': {hash_value_default}")
        else:
            logger.warning(
                f"Failed to calculate hash for '{dummy_file_path}' with {default_hasher.algorithm}.")

        # Test with a specific algorithm (e.g., md5)
        md5_hasher = FileHasher(algorithm="md5")
        logger.info(f"Using algorithm: {md5_hasher.algorithm}")
        hash_value_md5 = md5_hasher.calculate_hash(dummy_file_path)
        if hash_value_md5:
            logger.info(f"Hash (md5) for '{dummy_file_path}': {hash_value_md5}")
        else:
            logger.warning(
                f"Failed to calculate hash for '{dummy_file_path}' with md5.")

        # Test with a non-existent file
        logger.info("Testing non-existent file:")
        non_existent_hash = default_hasher.calculate_hash(
            "non_existent_file.txt")
        if non_existent_hash is None:
            logger.info("Correctly handled non-existent file (returned None).")

    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
            logger.info(f"Removed dummy file: {dummy_file_path}")
