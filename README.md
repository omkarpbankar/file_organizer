# File Organizer 📁

A robust, modular, and simple Python application that organizes files in a folder into categorized subdirectories based on their file extensions, with built-in **MD5 checksum duplicate detection**.

## ✨ Features

- **Modular Architecture**: Clean separation of concerns into dedicated modules ([`detector.py`](file:///d:/euron/assignments/file_organizer/organizer/detector.py), [`mover.py`](file:///d:/euron/assignments/file_organizer/organizer/mover.py), [`logger.py`](file:///d:/euron/assignments/file_organizer/organizer/logger.py), [`exceptions.py`](file:///d:/euron/assignments/file_organizer/organizer/exceptions.py)).
- **MD5 Checksum Duplicate Management**:
  - Calculates memory-efficient MD5 hash digests for files.
  - Automatically verifies collisions and routes duplicates into a dedicated `Duplicates/` folder (`move_to_duplicates` default).
  - Also supports `rename` (e.g. `photo (1).jpg`), `overwrite`, `skip`, or `raise`.
- **Comprehensive Extension Mapping**:
  - `Images/`: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp`, etc.
  - `Text/`: `.txt`, `.md`, `.rtf`, `.log`
  - `Documents/`: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.pptx`, etc.
  - `Data/`: `.csv`, `.json`, `.xml`, `.sql`, `.yaml`, `.parquet`, etc.
  - `Audio/`: `.mp3`, `.wav`, `.aac`, `.flac`, etc.
  - `Video/`: `.mp4`, `.mkv`, `.mov`, `.avi`, etc.
  - `Archives/`: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, etc.
  - `Code/`: `.py`, `.js`, `.ts`, `.html`, `.css`, `.java`, `.cpp`, etc.
- **Robust Exception Handling**:
  - Handles non-existent source paths (`FileNotFoundError`).
  - Handles missing destination folders by automatically creating them, or raising `DestinationFolderError` if permissions fail.
  - Handles permission and filesystem errors (`PermissionError`, `FileMovementError`).
  - Custom exception `UnsupportedFileError(Exception)` for unrecognized file types.
- **Auditable Logging**: Records every successful and failed operation to both console and a log file (`file_organizer.log`) with precise timestamps and log levels (`INFO`, `WARNING`, `ERROR`).
- **Dual Interface**: Supports both command-line arguments and an interactive terminal menu.

---

## 📂 Project Structure

```
file_organizer/
│
├── organizer/
│   ├── __init__.py          # Package initialization & exports
│   ├── exceptions.py        # Custom exceptions (UnsupportedFileError, FileOrganizerError, etc.)
│   ├── logger.py            # Centralized logging setup (console + file)
│   ├── detector.py          # Extension detection & category mapping
│   └── mover.py             # MD5 checksum, file movement, folder creation & duplicate routing
│
├── tests/
│   ├── __init__.py
│   └── test_organizer.py    # Complete unit test suite
│
├── main.py                  # CLI & Interactive entry point
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (standard library only, no external dependencies required!)

### 1. Interactive Mode
Run without arguments to enter guided interactive mode:
```powershell
python main.py
```

### 2. Command-Line Interface (CLI)
You can specify arguments directly:

```powershell
# Organize a specific folder (routes duplicates into Duplicates/ by default)
python main.py --source "C:/Users/username/Downloads"

# Move duplicates into a dedicated Duplicates/ folder explicitly
python main.py --source "./my_files" --duplicates move_to_duplicates

# Organize files into a separate destination folder
python main.py --source "./my_files" --destination "./organized_files"

# Preview actions without moving files (Dry Run)
python main.py --source "./my_files" --dry-run

# Handle unsupported files by moving them into an "Others/" folder
python main.py --source "./my_files" --unsupported move_to_others

# Handle duplicates by renaming (photo (1).jpg)
python main.py --source "./my_files" --duplicates rename
```

#### CLI Options:
| Option | Shorthand | Description | Default |
|---|---|---|---|
| `--source` | `-s` | Source folder to organize | Prompted if omitted |
| `--destination` | `-d` | Target folder for subdirectories | Source folder |
| `--duplicates` | | `move_to_duplicates`, `rename`, `overwrite`, `skip`, or `raise` | `move_to_duplicates` |
| `--unsupported` | `-u` | `skip`, `move_to_others`, or `raise` | `skip` |
| `--dry-run` | | Simulate without moving files | `False` |
| `--log-file` | | Path to log file | `file_organizer.log` |
| `--interactive` | `-i` | Force interactive wizard | `False` |

---

## 🐍 Python API Usage

```python
from organizer import organize_directory, calculate_md5, FileDetector

# Check MD5 of a file
file_hash = calculate_md5("photo.jpg")
print(f"MD5 Checksum: {file_hash}")

# Organize folder and quarantine duplicate files
stats = organize_directory(
    source_dir="path/to/folder",
    duplicate_strategy="move_to_duplicates"
)
print(f"Moved: {stats['moved']}, Duplicates: {stats['duplicates']}")
```

---

## 🧪 Running Tests

```powershell
python -m unittest discover -s tests -v
```
All 18 tests verify category detection, MD5 checksum calculation, duplicate routing, folder auto-creation, dry-run simulation, and log file generation.
