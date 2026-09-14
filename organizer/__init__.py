"""File Organizer Package.

A modular Python package to organize files based on their extensions.
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
from organizer.mover import FileMover, organize_directory

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
    "FileMover",
    "organize_directory",
]
