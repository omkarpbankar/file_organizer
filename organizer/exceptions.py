"""Custom exceptions for the File Organizer application."""


class FileOrganizerError(Exception):
    """Base exception for all file organizer errors."""
    pass


class UnsupportedFileError(FileOrganizerError):
    """Raised when a file has an unrecognized or unsupported extension."""
    def __init__(self, filename: str, extension: str, message: str | None = None):
        self.filename = filename
        self.extension = extension
        if message is None:
            message = f"Unsupported file type: '{filename}' with extension '{extension}'"
        super().__init__(message)


class DestinationFolderError(FileOrganizerError):
    """Raised when destination folder cannot be created or accessed."""
    pass


class DuplicateFileError(FileOrganizerError):
    """Raised when a duplicate file exists and cannot be resolved."""
    pass


class FileMovementError(FileOrganizerError):
    """Raised when a file cannot be moved due to filesystem or permission errors."""
    pass
