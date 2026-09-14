"""File movement and organization module."""

import logging
from pathlib import Path
import shutil

from organizer.detector import FileDetector
from organizer.exceptions import (
    DestinationFolderError,
    DuplicateFileError,
    FileMovementError,
    UnsupportedFileError,
)
from organizer.logger import get_logger


class FileMover:
    """Handles moving files to categorized folders with robust error and collision handling."""

    def __init__(
        self,
        detector: FileDetector | None = None,
        logger: logging.Logger | None = None,
        duplicate_strategy: str = "rename",
        unsupported_strategy: str = "skip",
        others_folder_name: str = "Others",
    ) -> None:
        """Initializes the FileMover.

        Args:
            detector: Instance of FileDetector. If None, default detector is used.
            logger: Configured logger instance.
            duplicate_strategy: How to handle duplicate file names:
                - 'rename': Automatically appends (1), (2), etc. (default)
                - 'overwrite': Overwrites existing destination file
                - 'skip': Skips moving the duplicate file
                - 'raise': Raises DuplicateFileError
            unsupported_strategy: How to handle unsupported file extensions:
                - 'skip': Skip the file and log a warning (default)
                - 'move_to_others': Move the file into an 'Others' folder
                - 'raise': Raise UnsupportedFileError
            others_folder_name: Folder name used when unsupported_strategy is 'move_to_others'.
        """
        self.detector = detector or FileDetector()
        self.logger = logger or get_logger()
        self.duplicate_strategy = duplicate_strategy.lower()
        self.unsupported_strategy = unsupported_strategy.lower()
        self.others_folder_name = others_folder_name

    def get_unique_destination(self, dest_file: Path) -> Path:
        """Generates a unique destination path if a file with the same name already exists.

        Example: 'photo.jpg' -> 'photo (1).jpg' -> 'photo (2).jpg'
        """
        if not dest_file.exists():
            return dest_file

        stem = dest_file.stem
        suffix = dest_file.suffix
        parent = dest_file.parent
        counter = 1

        while True:
            new_dest = parent / f"{stem} ({counter}){suffix}"
            if not new_dest.exists():
                return new_dest
            counter += 1

    def move_file(
        self,
        source_file: str | Path,
        destination_dir: str | Path,
        dry_run: bool = False,
    ) -> Path | None:
        """Moves a single file into the appropriate category folder within destination_dir.

        Args:
            source_file: Path to the source file.
            destination_dir: Base directory where categorized subfolders live.
            dry_run: If True, simulates the move without modifying files.

        Returns:
            The final destination Path if moved successfully, None if skipped.

        Raises:
            FileNotFoundError: If source_file does not exist.
            DestinationFolderError: If destination directory cannot be accessed/created.
            UnsupportedFileError: If unsupported_strategy is 'raise' and file is not supported.
            DuplicateFileError: If duplicate_strategy is 'raise' and destination exists.
            FileMovementError: If file movement fails due to permissions or OS errors.
        """
        src = Path(source_file).resolve()
        dest_base = Path(destination_dir).resolve()

        # 1. Validate source file existence
        if not src.exists():
            msg = f"Failed to move: Source file does not exist '{src}'"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        if not src.is_file():
            msg = f"Failed to move: Source path is a directory, not a file '{src}'"
            self.logger.warning(msg)
            return None

        # 2. Determine target category
        try:
            category = self.detector.get_category(src)
        except UnsupportedFileError as err:
            if self.unsupported_strategy == "raise":
                self.logger.error(f"Failed operation on '{src.name}': {err}")
                raise
            elif self.unsupported_strategy == "move_to_others":
                category = self.others_folder_name
                self.logger.info(
                    f"Unsupported extension for '{src.name}'. Routing to '{self.others_folder_name}/'."
                )
            else:  # 'skip'
                self.logger.warning(
                    f"Skipping unsupported file '{src.name}' (extension: '{err.extension}')."
                )
                return None

        # 3. Ensure destination category folder exists
        category_dir = dest_base / category
        try:
            if not dry_run:
                category_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            msg = f"Permission denied while creating folder '{category_dir}': {e}"
            self.logger.error(msg)
            raise DestinationFolderError(msg) from e
        except OSError as e:
            msg = f"Failed to create destination folder '{category_dir}': {e}"
            self.logger.error(msg)
            raise DestinationFolderError(msg) from e

        # 4. Handle target file naming and collisions
        target_path = category_dir / src.name

        # If source is already in the target position, nothing to do
        if src == target_path:
            self.logger.info(f"File '{src.name}' is already in destination '{category_dir}'.")
            return target_path

        if target_path.exists():
            if self.duplicate_strategy == "raise":
                msg = f"Duplicate file exists at destination: '{target_path}'"
                self.logger.error(msg)
                raise DuplicateFileError(msg)
            elif self.duplicate_strategy == "skip":
                self.logger.warning(f"Skipping duplicate file: '{src.name}' already exists in '{category}'.")
                return None
            elif self.duplicate_strategy == "overwrite":
                self.logger.info(f"Overwriting existing file '{target_path}' with '{src}'.")
            else:  # default: 'rename'
                target_path = self.get_unique_destination(target_path)
                self.logger.info(f"Duplicate detected. Renaming '{src.name}' -> '{target_path.name}'.")

        # 5. Execute file movement
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Would move: '{src.name}' -> '{category}/{target_path.name}'")
                return target_path

            shutil.move(str(src), str(target_path))
            self.logger.info(f"Successfully moved: '{src.name}' -> '{category}/{target_path.name}'")
            return target_path

        except PermissionError as e:
            msg = f"Permission denied moving '{src}' to '{target_path}': {e}"
            self.logger.error(msg)
            raise FileMovementError(msg) from e
        except OSError as e:
            msg = f"OS error occurred moving '{src}' to '{target_path}': {e}"
            self.logger.error(msg)
            raise FileMovementError(msg) from e


def organize_directory(
    source_dir: str | Path,
    target_dir: str | Path | None = None,
    detector: FileDetector | None = None,
    logger: logging.Logger | None = None,
    duplicate_strategy: str = "rename",
    unsupported_strategy: str = "skip",
    dry_run: bool = False,
) -> dict[str, int]:
    """Organizes all files in source_dir into categorized subfolders.

    Args:
        source_dir: Directory containing files to organize.
        target_dir: Destination directory (defaults to source_dir if not specified).
        detector: Custom FileDetector instance.
        logger: Logger instance.
        duplicate_strategy: 'rename', 'overwrite', 'skip', or 'raise'.
        unsupported_strategy: 'skip', 'move_to_others', or 'raise'.
        dry_run: If True, simulates without moving files.

    Returns:
        Summary dict containing counts: {'processed': N, 'moved': N, 'skipped': N, 'failed': N}
    """
    src_path = Path(source_dir).resolve()
    dest_path = Path(target_dir).resolve() if target_dir else src_path
    log = logger or get_logger()

    mover = FileMover(
        detector=detector,
        logger=log,
        duplicate_strategy=duplicate_strategy,
        unsupported_strategy=unsupported_strategy,
    )

    if not src_path.exists() or not src_path.is_dir():
        msg = f"Source directory does not exist or is not a directory: '{src_path}'"
        log.error(msg)
        raise FileNotFoundError(msg)

    log.info(f"Starting organization of folder: '{src_path}' -> '{dest_path}' (Dry run: {dry_run})")

    stats = {"processed": 0, "moved": 0, "skipped": 0, "failed": 0}

    # Gather all immediate files in source directory (skip subdirectories to avoid recursive loops)
    for item in list(src_path.iterdir()):
        if item.is_file():
            stats["processed"] += 1
            try:
                result = mover.move_file(item, dest_path, dry_run=dry_run)
                if result is not None:
                    stats["moved"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                log.error(f"Error organizing file '{item.name}': {e}")
                # If unsupported_strategy is 'raise' or duplicate_strategy is 'raise', propagate if desired
                if (
                    isinstance(e, UnsupportedFileError) and unsupported_strategy == "raise"
                ) or (
                    isinstance(e, DuplicateFileError) and duplicate_strategy == "raise"
                ):
                    raise

    log.info(
        f"Finished organizing. Summary: Processed={stats['processed']}, "
        f"Moved={stats['moved']}, Skipped={stats['skipped']}, Failed={stats['failed']}"
    )
    return stats
