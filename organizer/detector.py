"""File detection and extension mapping module."""

from pathlib import Path
from organizer.exceptions import UnsupportedFileError


DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"],
    "Text": [".txt", ".md", ".rtf", ".log"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".epub"],
    "Data": [".csv", ".json", ".xml", ".sql", ".yaml", ".yml", ".tsv", ".parquet"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"],
    "Video": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".cs", ".php", ".rb", ".go", ".rs", ".sh", ".bat"],
}


class FileDetector:
    """Detects the category of a file based on its file extension."""

    def __init__(self, categories: dict[str, list[str]] | None = None) -> None:
        """Initializes the detector with given categories or defaults.

        Args:
            categories: Optional custom mapping of category names to lists of extensions.
        """
        self.categories: dict[str, list[str]] = categories or DEFAULT_CATEGORIES
        self._extension_map: dict[str, str] = {}
        self._build_extension_map()

    def _build_extension_map(self) -> None:
        """Constructs a normalized lookup map of extension -> category."""
        self._extension_map.clear()
        for category, extensions in self.categories.items():
            for ext in extensions:
                normalized_ext = ext.lower()
                if not normalized_ext.startswith("."):
                    normalized_ext = f".{normalized_ext}"
                self._extension_map[normalized_ext] = category

    def add_category(self, category: str, extensions: list[str]) -> None:
        """Adds or updates a category with extensions.

        Args:
            category: Category name (e.g. '3DModels').
            extensions: List of extensions (e.g. ['.obj', '.stl']).
        """
        self.categories[category] = extensions
        self._build_extension_map()

    def get_category(self, file_path: str | Path) -> str:
        """Identifies category for a given file path based on its extension.

        Args:
            file_path: Path to the file.

        Returns:
            The category name (e.g., 'Images', 'Documents').

        Raises:
            UnsupportedFileError: If the file extension is not recognized.
        """
        path = Path(file_path)
        filename = path.name
        extension = path.suffix.lower()

        if not extension or extension not in self._extension_map:
            raise UnsupportedFileError(filename=filename, extension=extension or "none")

        return self._extension_map[extension]

    def is_supported(self, file_path: str | Path) -> bool:
        """Checks if a file extension is supported without raising an error.

        Args:
            file_path: Path to the file.

        Returns:
            True if supported, False otherwise.
        """
        path = Path(file_path)
        return path.suffix.lower() in self._extension_map
