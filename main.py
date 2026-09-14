"""Main entry point for File Organizer application.

Provides both a Command-Line Interface (CLI) and an interactive prompt with MD5 duplicate management.
"""

import argparse
from pathlib import Path
import sys

from organizer import (
    DestinationFolderError,
    FileOrganizerError,
    UnsupportedFileError,
    get_logger,
    organize_directory,
)


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Organize files in a directory into subfolders based on file extensions and MD5 duplicate handling.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-s",
        "--source",
        type=str,
        help="Source directory containing files to organize.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default=None,
        help="Destination directory for organized folders (defaults to source folder).",
    )
    parser.add_argument(
        "--unsupported",
        choices=["skip", "move_to_others", "raise"],
        default="skip",
        help="Strategy for files with unrecognized extensions.",
    )
    parser.add_argument(
        "--duplicates",
        choices=["move_to_duplicates", "rename", "overwrite", "skip", "raise"],
        default="move_to_duplicates",
        help="Strategy for handling duplicate files (uses MD5 checksum detection).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the organization without moving any files.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="file_organizer.log",
        help="Path to log file for recording operations.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode.",
    )

    return parser.parse_args()


def interactive_mode() -> tuple[str, str | None, str, str, bool, str]:
    """Guides the user through setting up the file organizer interactively."""
    print("=" * 60, flush=True)
    print("           FILE ORGANIZER - INTERACTIVE MODE", flush=True)
    print("=" * 60, flush=True)

    while True:
        source_input = input("Enter path of the folder to organize: ").strip().strip('"').strip("'")
        if not source_input:
            print("Path cannot be empty. Please enter a valid directory path.", flush=True)
            continue
        source_path = Path(source_input)
        if not source_path.exists():
            print(f"Directory not found: '{source_input}'. Please try again.", flush=True)
            continue
        if not source_path.is_dir():
            print(f"Path is not a directory: '{source_input}'. Please try again.", flush=True)
            continue
        break

    dest_input = input(
        f"Enter destination path (press Enter to organize inside '{source_input}'): "
    ).strip().strip('"').strip("'")
    destination = dest_input if dest_input else None

    print("\nHow should unsupported file extensions be handled?", flush=True)
    print("  1. Skip them (leave in source directory) [Default]", flush=True)
    print("  2. Move to an 'Others/' folder", flush=True)
    print("  3. Raise an error and stop", flush=True)
    unsupported_choice = input("Select option (1/2/3): ").strip()
    unsupported_map = {"1": "skip", "2": "move_to_others", "3": "raise"}
    unsupported_strategy = unsupported_map.get(unsupported_choice, "skip")

    print("\nHow should duplicate files be handled (MD5 checksum verified)?", flush=True)
    print("  1. Move duplicates to a 'Duplicates/' folder [Default]", flush=True)
    print("  2. Automatically rename (e.g. photo (1).jpg)", flush=True)
    print("  3. Overwrite existing file", flush=True)
    print("  4. Skip duplicate file", flush=True)
    print("  5. Raise an error and stop", flush=True)
    dup_choice = input("Select option (1/2/3/4/5): ").strip()
    dup_map = {
        "1": "move_to_duplicates",
        "2": "rename",
        "3": "overwrite",
        "4": "skip",
        "5": "raise",
    }
    duplicate_strategy = dup_map.get(dup_choice, "move_to_duplicates")

    dry_run_input = input("\nPerform a dry-run first without moving files? (y/N): ").strip().lower()
    dry_run = dry_run_input in ("y", "yes")

    log_file = "file_organizer.log"

    return source_input, destination, unsupported_strategy, duplicate_strategy, dry_run, log_file


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    # If no source provided or interactive flag passed, use interactive mode
    if not args.source or args.interactive:
        source, destination, unsupported_strategy, duplicate_strategy, dry_run, log_file = (
            interactive_mode()
        )
    else:
        source = args.source
        destination = args.destination
        unsupported_strategy = args.unsupported
        duplicate_strategy = args.duplicates
        dry_run = args.dry_run
        log_file = args.log_file

    logger = get_logger(log_file=log_file)

    print("\n" + "-" * 60, flush=True)
    print("Running File Organizer...", flush=True)
    print(f" Source Directory       : {Path(source).resolve()}", flush=True)
    print(f" Destination Directory  : {Path(destination).resolve() if destination else Path(source).resolve()}", flush=True)
    print(f" Unsupported Strategy   : {unsupported_strategy}", flush=True)
    print(f" Duplicate Strategy     : {duplicate_strategy} (MD5 checksum)", flush=True)
    print(f" Dry Run Mode           : {'ON (No files will be moved)' if dry_run else 'OFF'}", flush=True)
    print(f" Log File               : {Path(log_file).resolve()}", flush=True)
    print("-" * 60 + "\n", flush=True)

    try:
        stats = organize_directory(
            source_dir=source,
            target_dir=destination,
            logger=logger,
            duplicate_strategy=duplicate_strategy,
            unsupported_strategy=unsupported_strategy,
            dry_run=dry_run,
        )

        print("\n" + "=" * 60, flush=True)
        print("                 ORGANIZATION SUMMARY", flush=True)
        print("=" * 60, flush=True)
        print(f" Total files processed  : {stats['processed']}", flush=True)
        print(f" Files moved            : {stats['moved']}", flush=True)
        print(f" Duplicates detected    : {stats['duplicates']}", flush=True)
        print(f" Files skipped          : {stats['skipped']}", flush=True)
        print(f" Errors/Failures        : {stats['failed']}", flush=True)
        print(f" Full log recorded in   : {Path(log_file).resolve()}", flush=True)
        print("=" * 60, flush=True)

    except FileNotFoundError as e:
        print(f"\n[ERROR] File/Folder not found: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except UnsupportedFileError as e:
        print(f"\n[ERROR] Unsupported File Type: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except DestinationFolderError as e:
        print(f"\n[ERROR] Destination Folder Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except FileOrganizerError as e:
        print(f"\n[ERROR] Organizer Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
