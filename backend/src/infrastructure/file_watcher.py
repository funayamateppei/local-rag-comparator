"""FileSystemWatcher - monitors directories for new file arrivals."""

import asyncio
import logging
from pathlib import Path

from src.domain.events import FileDetectedEvent
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class _FileCreatedHandler(FileSystemEventHandler):
    """Internal handler that queues file creation events."""

    def __init__(self, loop: asyncio.AbstractEventLoop, callback) -> None:
        self._loop = loop
        self._callback = callback

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        logger.info(f"File detected: {event.src_path}")
        self._loop.call_soon_threadsafe(
            asyncio.ensure_future,
            self._callback(event.src_path),
        )


class FileSystemWatcher:
    """Watches a directory for new files and dispatches FileDetectedEvent.

    Uses watchdog to monitor filesystem and dispatches domain events
    through IEventDispatcher when new files are detected.
    """

    def __init__(self, watch_dir: str | Path, event_dispatcher) -> None:
        self._watch_dir = Path(watch_dir)
        self._event_dispatcher = event_dispatcher
        self._observer: Observer | None = None

    async def _on_file_created(self, file_path: str) -> None:
        path = Path(file_path)
        event = FileDetectedEvent(
            file_path=str(path),
            filename=path.name,
        )
        await self._event_dispatcher.dispatch(event)

    def start(self) -> None:
        if not self._watch_dir.exists():
            self._watch_dir.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()
        handler = _FileCreatedHandler(loop, self._on_file_created)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._watch_dir), recursive=False)
        self._observer.start()
        logger.info(f"FileSystemWatcher started: {self._watch_dir}")

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("FileSystemWatcher stopped")
