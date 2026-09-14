"""Unit tests for the File Organizer application."""

from pathlib import Path
import tempfile
import unittest

from organizer.detector import FileDetector
from organizer.exceptions import (
    DuplicateFileError,
    UnsupportedFileError,
)
from organizer.logger import close_logger_handlers, get_logger
from organizer.mover import organize_directory


class TestFileDetector(unittest.TestCase):
    """Test suite for FileDetector."""

    def setUp(self) -> None:
        self.detector = FileDetector()

    def test_example_mappings(self) -> None:
        """Verify prompt specific example mappings."""
        self.assertEqual(self.detector.get_category("photo.jpg"), "Images")
        self.assertEqual(self.detector.get_category("notes.txt"), "Text")
        self.assertEqual(self.detector.get_category("report.pdf"), "Documents")
        self.assertEqual(self.detector.get_category("data.csv"), "Data")

    def test_case_insensitivity(self) -> None:
        """Verify that uppercase extensions are categorized properly."""
        self.assertEqual(self.detector.get_category("PHOTO.JPG"), "Images")
        self.assertEqual(self.detector.get_category("REPORT.PDF"), "Documents")
        self.assertEqual(self.detector.get_category("DATA.CSV"), "Data")

    def test_unsupported_file_error(self) -> None:
        """Verify that an unknown extension raises UnsupportedFileError."""
        with self.assertRaises(UnsupportedFileError) as ctx:
            self.detector.get_category("unknown_file.custom_weird_ext")
        self.assertEqual(ctx.exception.extension, ".custom_weird_ext")
        self.assertEqual(ctx.exception.filename, "unknown_file.custom_weird_ext")

    def test_file_without_extension(self) -> None:
        """Verify that a file with no extension raises UnsupportedFileError."""
        with self.assertRaises(UnsupportedFileError):
            self.detector.get_category("no_extension_file")

    def test_custom_category(self) -> None:
        """Verify adding a custom category works as expected."""
        self.detector.add_category("3DModels", [".obj", ".stl"])
        self.assertEqual(self.detector.get_category("model.obj"), "3DModels")
        self.assertEqual(self.detector.get_category("part.stl"), "3DModels")


class TestFileMoverAndOrganizer(unittest.TestCase):
    """Test suite for FileMover and organize_directory."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.log_file = self.root / "test.log"
        self.logger = get_logger(f"test_logger_{id(self)}", log_file=self.log_file, reset_handlers=True)

    def tearDown(self) -> None:
        close_logger_handlers(self.logger)
        self.temp_dir.cleanup()

    def test_basic_file_organization(self) -> None:
        """Test organizing standard files into their respective subfolders."""
        # Create test files
        (self.source / "photo.jpg").write_text("dummy photo")
        (self.source / "notes.txt").write_text("dummy notes")
        (self.source / "report.pdf").write_text("dummy report")
        (self.source / "data.csv").write_text("dummy data")

        stats = organize_directory(
            source_dir=self.source,
            logger=self.logger,
            unsupported_strategy="skip",
        )

        self.assertEqual(stats["processed"], 4)
        self.assertEqual(stats["moved"], 4)
        self.assertEqual(stats["failed"], 0)

        self.assertTrue((self.source / "Images" / "photo.jpg").exists())
        self.assertTrue((self.source / "Text" / "notes.txt").exists())
        self.assertTrue((self.source / "Documents" / "report.pdf").exists())
        self.assertTrue((self.source / "Data" / "data.csv").exists())

    def test_missing_source_directory(self) -> None:
        """Test that missing source directory raises FileNotFoundError."""
        non_existent = self.root / "does_not_exist"
        with self.assertRaises(FileNotFoundError):
            organize_directory(non_existent, logger=self.logger)

    def test_missing_destination_folder_creation(self) -> None:
        """Test that missing destination folder is automatically created."""
        dest_folder = self.root / "custom_dest"
        (self.source / "photo.jpg").write_text("photo data")

        organize_directory(
            source_dir=self.source,
            target_dir=dest_folder,
            logger=self.logger,
        )

        self.assertTrue((dest_folder / "Images" / "photo.jpg").exists())

    def test_duplicate_rename_strategy(self) -> None:
        """Test that duplicate files are automatically renamed safely."""
        images_dir = self.source / "Images"
        images_dir.mkdir()
        (images_dir / "photo.jpg").write_text("existing photo")

        # Source file with same name
        (self.source / "photo.jpg").write_text("new photo")

        organize_directory(
            source_dir=self.source,
            logger=self.logger,
            duplicate_strategy="rename",
        )

        self.assertTrue((images_dir / "photo.jpg").exists())
        self.assertTrue((images_dir / "photo (1).jpg").exists())

    def test_duplicate_skip_strategy(self) -> None:
        """Test that duplicate files are skipped when duplicate_strategy='skip'."""
        images_dir = self.source / "Images"
        images_dir.mkdir()
        (images_dir / "photo.jpg").write_text("existing photo")
        (self.source / "photo.jpg").write_text("new photo")

        stats = organize_directory(
            source_dir=self.source,
            logger=self.logger,
            duplicate_strategy="skip",
        )

        self.assertEqual(stats["skipped"], 1)
        self.assertTrue((self.source / "photo.jpg").exists())

    def test_duplicate_raise_strategy(self) -> None:
        """Test that duplicate files raise DuplicateFileError when requested."""
        images_dir = self.source / "Images"
        images_dir.mkdir()
        (images_dir / "photo.jpg").write_text("existing photo")
        (self.source / "photo.jpg").write_text("new photo")

        with self.assertRaises(DuplicateFileError):
            organize_directory(
                source_dir=self.source,
                logger=self.logger,
                duplicate_strategy="raise",
            )

    def test_unsupported_file_skip_strategy(self) -> None:
        """Test that unsupported files are skipped and left in place."""
        (self.source / "unknown.xyz").write_text("some content")

        stats = organize_directory(
            source_dir=self.source,
            logger=self.logger,
            unsupported_strategy="skip",
        )

        self.assertEqual(stats["skipped"], 1)
        self.assertTrue((self.source / "unknown.xyz").exists())

    def test_unsupported_file_others_strategy(self) -> None:
        """Test that unsupported files are moved to Others/ when strategy='move_to_others'."""
        (self.source / "unknown.xyz").write_text("some content")

        stats = organize_directory(
            source_dir=self.source,
            logger=self.logger,
            unsupported_strategy="move_to_others",
        )

        self.assertEqual(stats["moved"], 1)
        self.assertTrue((self.source / "Others" / "unknown.xyz").exists())

    def test_unsupported_file_raise_strategy(self) -> None:
        """Test that unsupported files raise UnsupportedFileError when strategy='raise'."""
        (self.source / "unknown.xyz").write_text("some content")

        with self.assertRaises(UnsupportedFileError):
            organize_directory(
                source_dir=self.source,
                logger=self.logger,
                unsupported_strategy="raise",
            )

    def test_dry_run_mode(self) -> None:
        """Test that dry run does not physically move files."""
        (self.source / "photo.jpg").write_text("photo data")

        stats = organize_directory(
            source_dir=self.source,
            logger=self.logger,
            dry_run=True,
        )

        self.assertEqual(stats["moved"], 1)
        self.assertTrue((self.source / "photo.jpg").exists())
        self.assertFalse((self.source / "Images" / "photo.jpg").exists())

    def test_logging_recorded_to_file(self) -> None:
        """Verify that operations write to the log file."""
        (self.source / "notes.txt").write_text("notes data")

        organize_directory(source_dir=self.source, logger=self.logger)

        self.assertTrue(self.log_file.exists())
        log_content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("Successfully moved", log_content)
        self.assertIn("notes.txt", log_content)


if __name__ == "__main__":
    unittest.main()
