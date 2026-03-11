"""Tests for FileSystemWatcher and related components."""

import pytest

pytest.importorskip("watchdog", reason="watchdog not installed")

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.events import DomainEvent, FileDetectedEvent
from src.infrastructure.file_watcher import FileSystemWatcher, _FileCreatedHandler


class TestFileDetectedEvent:
    """Tests for FileDetectedEvent domain event."""

    def test_create_file_detected_event(self):
        event = FileDetectedEvent(
            file_path="/tmp/uploads/report.pdf",
            filename="report.pdf",
        )

        assert event.file_path == "/tmp/uploads/report.pdf"
        assert event.filename == "report.pdf"
        assert isinstance(event.occurred_at, datetime)

    def test_file_detected_event_inherits_from_domain_event(self):
        event = FileDetectedEvent(
            file_path="/tmp/uploads/report.pdf",
            filename="report.pdf",
        )

        assert isinstance(event, DomainEvent)

    def test_file_detected_event_is_immutable(self):
        event = FileDetectedEvent(
            file_path="/tmp/uploads/report.pdf",
            filename="report.pdf",
        )

        with pytest.raises(AttributeError):
            event.file_path = "modified"

        with pytest.raises(AttributeError):
            event.filename = "modified.pdf"

    def test_file_detected_event_default_values(self):
        event = FileDetectedEvent()

        assert event.file_path == ""
        assert event.filename == ""

    def test_file_detected_event_auto_sets_occurred_at(self):
        before = datetime.utcnow()
        event = FileDetectedEvent(file_path="/tmp/test.txt", filename="test.txt")
        after = datetime.utcnow()

        assert before <= event.occurred_at <= after


class TestFileSystemWatcherInit:
    """Tests for FileSystemWatcher initialization."""

    def test_init_with_string_path(self, tmp_path):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher(str(tmp_path), dispatcher)

        assert watcher._watch_dir == tmp_path
        assert watcher._event_dispatcher is dispatcher
        assert watcher._observer is None

    def test_init_with_path_object(self, tmp_path):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher(tmp_path, dispatcher)

        assert watcher._watch_dir == tmp_path
        assert watcher._event_dispatcher is dispatcher


class TestFileSystemWatcherStart:
    """Tests for FileSystemWatcher.start()."""

    def test_start_creates_directory_if_not_exists(self, tmp_path):
        watch_dir = tmp_path / "new_subdir" / "uploads"
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher(watch_dir, dispatcher)

        with (
            patch("src.infrastructure.file_watcher.Observer") as mock_observer_cls,
            patch("src.infrastructure.file_watcher.asyncio.get_event_loop", return_value=MagicMock()),
        ):
            mock_observer = MagicMock()
            mock_observer_cls.return_value = mock_observer
            watcher.start()

        assert watch_dir.exists()

    def test_start_initializes_observer(self, tmp_path):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher(tmp_path, dispatcher)

        with (
            patch("src.infrastructure.file_watcher.Observer") as mock_observer_cls,
            patch("src.infrastructure.file_watcher.asyncio.get_event_loop", return_value=MagicMock()),
        ):
            mock_observer = MagicMock()
            mock_observer_cls.return_value = mock_observer
            watcher.start()

        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()
        assert watcher._observer is mock_observer


class TestFileSystemWatcherStop:
    """Tests for FileSystemWatcher.stop()."""

    def test_stop_when_observer_is_none(self):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher("/tmp/fake", dispatcher)

        # Should not raise any exception
        watcher.stop()

    def test_stop_stops_and_joins_observer(self, tmp_path):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher(tmp_path, dispatcher)
        mock_observer = MagicMock()
        watcher._observer = mock_observer

        watcher.stop()

        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()


class TestOnFileCreated:
    """Tests for FileSystemWatcher._on_file_created dispatch logic."""

    @pytest.mark.asyncio
    async def test_on_file_created_dispatches_file_detected_event(self):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher("/tmp/uploads", dispatcher)

        await watcher._on_file_created("/tmp/uploads/report.pdf")

        dispatcher.dispatch.assert_called_once()
        dispatched_event = dispatcher.dispatch.call_args[0][0]
        assert isinstance(dispatched_event, FileDetectedEvent)
        assert dispatched_event.file_path == "/tmp/uploads/report.pdf"
        assert dispatched_event.filename == "report.pdf"

    @pytest.mark.asyncio
    async def test_on_file_created_sets_correct_filename_from_nested_path(self):
        dispatcher = AsyncMock()
        watcher = FileSystemWatcher("/tmp/uploads", dispatcher)

        await watcher._on_file_created("/tmp/uploads/subdir/data.csv")

        dispatched_event = dispatcher.dispatch.call_args[0][0]
        assert dispatched_event.filename == "data.csv"
        assert dispatched_event.file_path == "/tmp/uploads/subdir/data.csv"


class TestFileCreatedHandler:
    """Tests for _FileCreatedHandler watchdog event handler."""

    def test_ignores_directory_events(self):
        loop = MagicMock()
        callback = MagicMock()
        handler = _FileCreatedHandler(loop, callback)

        dir_event = MagicMock()
        dir_event.is_directory = True
        dir_event.src_path = "/tmp/uploads/new_dir"

        handler.on_created(dir_event)

        loop.call_soon_threadsafe.assert_not_called()

    def test_processes_file_events(self):
        loop = MagicMock()
        callback = MagicMock()
        handler = _FileCreatedHandler(loop, callback)

        file_event = MagicMock()
        file_event.is_directory = False
        file_event.src_path = "/tmp/uploads/report.pdf"

        handler.on_created(file_event)

        loop.call_soon_threadsafe.assert_called_once()
        call_args = loop.call_soon_threadsafe.call_args[0]
        # First arg should be asyncio.ensure_future
        assert call_args[0] is __import__("asyncio").ensure_future
        # Second arg should be the coroutine from callback
        callback.assert_called_once_with("/tmp/uploads/report.pdf")
