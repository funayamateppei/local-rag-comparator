"""Tests for EventDispatcher - concrete implementation of IEventDispatcher."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.events import DomainEvent, DocumentUploadedEvent
from src.application.event_dispatcher import EventDispatcher


class TestEventDispatcherRegisterAndDispatch:
    """Tests for registering handlers and dispatching events."""

    @pytest.mark.asyncio
    async def test_registered_handler_is_called_on_matching_event(self):
        """A registered handler should be called when a matching event is dispatched."""
        dispatcher = EventDispatcher()
        handler = AsyncMock()
        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")

        dispatcher.register(DocumentUploadedEvent, handler)
        await dispatcher.dispatch(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_dispatch_with_no_handlers_does_not_raise(self):
        """Dispatching an event with no registered handlers should not raise an error."""
        dispatcher = EventDispatcher()
        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")

        # Should not raise any exception
        await dispatcher.dispatch(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called(self):
        """All registered handlers for an event type should be called."""
        dispatcher = EventDispatcher()
        handler_1 = AsyncMock()
        handler_2 = AsyncMock()
        handler_3 = AsyncMock()
        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")

        dispatcher.register(DocumentUploadedEvent, handler_1)
        dispatcher.register(DocumentUploadedEvent, handler_2)
        dispatcher.register(DocumentUploadedEvent, handler_3)
        await dispatcher.dispatch(event)

        handler_1.assert_called_once_with(event)
        handler_2.assert_called_once_with(event)
        handler_3.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_async_handler_is_awaited(self):
        """Async handler functions should be awaited correctly."""
        dispatcher = EventDispatcher()
        call_log = []

        async def async_handler(event: DomainEvent) -> None:
            call_log.append(("async", event))

        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")

        dispatcher.register(DocumentUploadedEvent, async_handler)
        await dispatcher.dispatch(event)

        assert len(call_log) == 1
        assert call_log[0][0] == "async"
        assert call_log[0][1] == event

    @pytest.mark.asyncio
    async def test_sync_handler_is_called(self):
        """Synchronous handler functions should be called correctly."""
        dispatcher = EventDispatcher()
        call_log = []

        def sync_handler(event: DomainEvent) -> None:
            call_log.append(("sync", event))

        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")

        dispatcher.register(DocumentUploadedEvent, sync_handler)
        await dispatcher.dispatch(event)

        assert len(call_log) == 1
        assert call_log[0][0] == "sync"
        assert call_log[0][1] == event

    @pytest.mark.asyncio
    async def test_handlers_only_fire_for_registered_event_type(self):
        """Handlers should only fire for their registered event type, not other types."""
        dispatcher = EventDispatcher()
        uploaded_handler = AsyncMock()
        domain_handler = AsyncMock()

        dispatcher.register(DocumentUploadedEvent, uploaded_handler)
        dispatcher.register(DomainEvent, domain_handler)

        # Dispatch a DocumentUploadedEvent - only uploaded_handler should fire
        event = DocumentUploadedEvent(document_id="doc-1", filename="test.pdf")
        await dispatcher.dispatch(event)

        uploaded_handler.assert_called_once_with(event)
        domain_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_domain_event_does_not_trigger_uploaded_handler(self):
        """A DomainEvent dispatch should not trigger DocumentUploadedEvent handlers."""
        dispatcher = EventDispatcher()
        uploaded_handler = AsyncMock()

        dispatcher.register(DocumentUploadedEvent, uploaded_handler)

        # Dispatch a base DomainEvent - uploaded_handler should NOT fire
        base_event = DomainEvent()
        await dispatcher.dispatch(base_event)

        uploaded_handler.assert_not_called()
