"""Hashing utilities for document fingerprinting."""

import hashlib
from typing import BinaryIO


def compute_file_hash(file: BinaryIO, algorithm: str = "sha256") -> str:
    """Compute hash of a file for duplicate detection.

    Args:
        file: File-like object to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)

    # Read file in chunks to handle large files
    chunk_size = 8192
    file.seek(0)  # Ensure we're at the beginning

    while chunk := file.read(chunk_size):
        hasher.update(chunk)

    file.seek(0)  # Reset file position for subsequent reads
    return hasher.hexdigest()


def compute_content_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Compute hash of bytes content.

    Args:
        content: Bytes to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()
