# File Organizer 📁

A robust, modular, and simple Python application that organizes files in a folder into categorized subdirectories based on their file extensions.

## ✨ Features

- **Modular Architecture**: Clean separation of concerns into dedicated modules (`detector.py`, `mover.py`, `logger.py`, `exceptions.py`).
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
  - Handles duplicate filenames safely with customizable collision strategies (`rename`, `overwrite`, `skip`, `raise`).
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
│   └── mover.py             # File movement, folder creation & collision resolution
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
# Organize a specific folder
python main.py --source "C:/Users/username/Downloads"

# Organize files into a separate destination folder
python main.py --source "./my_files" --destination "./organized_files"

# Preview actions without moving files (Dry Run)
python main.py --source "./my_files" --dry-run

# Handle unsupported files by moving them into an "Others/" folder
python main.py --source "./my_files" --unsupported move_to_others

# Handle duplicates by overwriting or raising an error
python main.py --source "./my_files" --duplicates overwrite
```

#### CLI Options:
| Option | Shorthand | Description | Default |
|---|---|---|---|
| `--source` | `-s` | Source folder to organize | Prompted if omitted |
| `--destination` | `-d` | Target folder for subdirectories | Source folder |
| `--unsupported` | `-u` | `skip`, `move_to_others`, or `raise` | `skip` |
| `--duplicates` | | `rename`, `overwrite`, `skip`, or `raise` | `rename` |
| `--dry-run` | | Simulate without moving files | `False` |
| `--log-file` | | Path to log file | `file_organizer.log` |
| `--interactive` | `-i` | Force interactive wizard | `False` |

---

## 🐍 Python API Usage

You can also use `file_organizer` directly in your Python code:

```python
from organizer import organize_directory, FileDetector, UnsupportedFileError

# Simple usage
stats = organize_directory("path/to/folder")
print(f"Moved {stats['moved']} files successfully!")

# Advanced usage with custom categories & error handling
custom_detector = FileDetector({
    "Images": [".jpg", ".png"],
    "Documents": [".pdf", ".docx"],
    "3DModels": [".obj", ".stl", ".fbx"]
})

try:
    stats = organize_directory(
        source_dir="path/to/folder",
        detector=custom_detector,
        duplicate_strategy="rename",
        unsupported_strategy="move_to_others"
    )
except UnsupportedFileError as e:
    print(f"Unsupported file: {e}")
```

---

## 🧪 Running Tests

Run the full automated unit test suite with:

```powershell
python -m unittest discover -s tests -v
```

All 16 tests verify category detection, custom exceptions, folder auto-creation, collision resolution, dry-run simulation, and log file generation.
