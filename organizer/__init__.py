"""File Organizer Package.

A modular Python package to organize files based on their extensions with MD5 duplicate detection.
"""

from organizer.detector import DEFAULT_CATEGORIES, FileDetector
from organizer.exceptions import (
    DestinationFolderError,
    DuplicateFileError,
    FileMovementError,
    FileOrganizerError,
    UnsupportedFileError,
)
from organizer.logger import close_logger_handlers, get_logger
from organizer.mover import FileMover, calculate_md5, organize_directory

__all__ = [
    "DEFAULT_CATEGORIES",
    "FileDetector",
    "FileOrganizerError",
    "UnsupportedFileError",
    "DestinationFolderError",
    "DuplicateFileError",
    "FileMovementError",
    "get_logger",
    "close_logger_handlers",
    "calculate_md5",
    "FileMover",
    "organize_directory",
]
