"""Concrete implementation of IEventDispatcher.

Manages event handlers and dispatches domain events to registered handlers.
Supports both synchronous and asynchronous handler functions.
"""

import inspect
from typing import Callable, Type

from src.domain.events import DomainEvent
from src.application.interfaces import IEventDispatcher


class EventDispatcher(IEventDispatcher):
    """Concrete implementation of IEventDispatcher.

    Manages event handlers and dispatches domain events to registered handlers.
    Handlers can be either synchronous or asynchronous callables.
    """

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Callable]] = {}

    def register(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The type of domain event to listen for.
            handler: A callable (sync or async) to invoke when the event is dispatched.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch a domain event to all registered handlers for its exact type.

        Args:
            event: The domain event to dispatch.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
