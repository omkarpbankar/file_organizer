"""File movement and organization module with MD5 checksum duplicate detection."""

import hashlib
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


def calculate_md5(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Calculates the MD5 checksum hash of a file using memory-efficient chunked reading.

    Args:
        file_path: Path to the file.
        chunk_size: Byte size of chunks to read into memory (default: 64 KB).

    Returns:
        Hexadecimal MD5 digest string.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


class FileMover:
    """Handles moving files to categorized folders with MD5 checksum duplicate detection."""

    def __init__(
        self,
        detector: FileDetector | None = None,
        logger: logging.Logger | None = None,
        duplicate_strategy: str = "move_to_duplicates",
        unsupported_strategy: str = "skip",
        others_folder_name: str = "Others",
        duplicates_folder_name: str = "Duplicates",
    ) -> None:
        """Initializes the FileMover.

        Args:
            detector: Instance of FileDetector. If None, default detector is used.
            logger: Configured logger instance.
            duplicate_strategy: How to handle duplicate files:
                - 'move_to_duplicates': Moves duplicate files to a separate Duplicates/ folder (default)
                - 'rename': Automatically appends (1), (2), etc.
                - 'overwrite': Overwrites existing destination file
                - 'skip': Skips moving the duplicate file
                - 'raise': Raises DuplicateFileError
            unsupported_strategy: How to handle unsupported file extensions:
                - 'skip': Skip the file and log a warning (default)
                - 'move_to_others': Move the file into an 'Others' folder
                - 'raise': Raise UnsupportedFileError
            others_folder_name: Folder name used when unsupported_strategy is 'move_to_others'.
            duplicates_folder_name: Folder name used when duplicate_strategy is 'move_to_duplicates'.
        """
        self.detector = detector or FileDetector()
        self.logger = logger or get_logger()
        self.duplicate_strategy = duplicate_strategy.lower()
        self.unsupported_strategy = unsupported_strategy.lower()
        self.others_folder_name = others_folder_name
        self.duplicates_folder_name = duplicates_folder_name

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
    ) -> tuple[Path | None, bool]:
        """Moves a single file into the appropriate category folder within destination_dir.

        Args:
            source_file: Path to the source file.
            destination_dir: Base directory where categorized subfolders live.
            dry_run: If True, simulates the move without modifying files.

        Returns:
            A tuple of (final_destination_path, is_duplicate):
                - final_destination_path: Path if moved successfully, None if skipped.
                - is_duplicate: True if file was handled as a duplicate, False otherwise.

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
            return None, False

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
                return None, False

        # 3. Check for duplicates in category destination
        category_dir = dest_base / category
        target_path = category_dir / src.name
        is_duplicate = False

        # If source is already in the target position, nothing to do
        if src == target_path:
            self.logger.info(f"File '{src.name}' is already in destination '{category_dir}'.")
            return target_path, False

        if target_path.exists():
            is_duplicate = True
            src_md5 = calculate_md5(src)
            dest_md5 = calculate_md5(target_path)
            content_match = (src_md5 == dest_md5)

            match_info = f"exact MD5 match: {src_md5}" if content_match else f"different MD5: src={src_md5}, dest={dest_md5}"
            self.logger.info(f"Duplicate filename collision on '{src.name}' ({match_info}).")

            if self.duplicate_strategy == "raise":
                msg = f"Duplicate file exists at destination: '{target_path}' (MD5: {src_md5})"
                self.logger.error(msg)
                raise DuplicateFileError(msg)

            elif self.duplicate_strategy == "skip":
                self.logger.warning(
                    f"Skipping duplicate file: '{src.name}' already exists in '{category}'."
                )
                return None, True

            elif self.duplicate_strategy == "overwrite":
                self.logger.info(f"Overwriting existing file '{target_path}' with '{src}'.")

            elif self.duplicate_strategy == "move_to_duplicates":
                # Route file to dedicated Duplicates/ directory
                dup_dir = dest_base / self.duplicates_folder_name
                try:
                    if not dry_run:
                        dup_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    msg = f"Failed to create duplicates folder '{dup_dir}': {e}"
                    self.logger.error(msg)
                    raise DestinationFolderError(msg) from e

                target_path = self.get_unique_destination(dup_dir / src.name)
                category = self.duplicates_folder_name
                self.logger.info(
                    f"Duplicate detected (MD5: {src_md5}). Routing '{src.name}' -> '{self.duplicates_folder_name}/{target_path.name}'."
                )

            else:  # 'rename'
                target_path = self.get_unique_destination(target_path)
                self.logger.info(
                    f"Duplicate filename. Renaming '{src.name}' -> '{target_path.name}' (MD5: {src_md5})."
                )

        # 4. Ensure destination category folder exists (if not already handled)
        if not is_duplicate or self.duplicate_strategy != "move_to_duplicates":
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

        # 5. Execute file movement
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Would move: '{src.name}' -> '{category}/{target_path.name}'")
                return target_path, is_duplicate

            shutil.move(str(src), str(target_path))
            self.logger.info(f"Successfully moved: '{src.name}' -> '{category}/{target_path.name}'")
            return target_path, is_duplicate

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
    duplicate_strategy: str = "move_to_duplicates",
    unsupported_strategy: str = "skip",
    dry_run: bool = False,
) -> dict[str, int]:
    """Organizes all files in source_dir into categorized subfolders with MD5 duplicate handling.

    Args:
        source_dir: Directory containing files to organize.
        target_dir: Destination directory (defaults to source_dir if not specified).
        detector: Custom FileDetector instance.
        logger: Logger instance.
        duplicate_strategy: 'move_to_duplicates', 'rename', 'overwrite', 'skip', or 'raise'.
        unsupported_strategy: 'skip', 'move_to_others', or 'raise'.
        dry_run: If True, simulates without moving files.

    Returns:
        Summary dict containing counts:
        {'processed': N, 'moved': N, 'duplicates': N, 'skipped': N, 'failed': N}
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

    log.info(
        f"Starting organization of folder: '{src_path}' -> '{dest_path}' "
        f"(Duplicates: {duplicate_strategy}, Dry run: {dry_run})"
    )

    stats = {"processed": 0, "moved": 0, "duplicates": 0, "skipped": 0, "failed": 0}

    # Gather all immediate files in source directory (skip subdirectories to avoid recursive loops)
    for item in list(src_path.iterdir()):
        if item.is_file():
            stats["processed"] += 1
            try:
                dest_result, is_dup = mover.move_file(item, dest_path, dry_run=dry_run)
                if is_dup:
                    stats["duplicates"] += 1
                if dest_result is not None:
                    stats["moved"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                log.error(f"Error organizing file '{item.name}': {e}")
                if (
                    isinstance(e, UnsupportedFileError) and unsupported_strategy == "raise"
                ) or (
                    isinstance(e, DuplicateFileError) and duplicate_strategy == "raise"
                ):
                    raise

    log.info(
        f"Finished organizing. Summary: Processed={stats['processed']}, "
        f"Moved={stats['moved']}, Duplicates={stats['duplicates']}, "
        f"Skipped={stats['skipped']}, Failed={stats['failed']}"
    )
    return stats
