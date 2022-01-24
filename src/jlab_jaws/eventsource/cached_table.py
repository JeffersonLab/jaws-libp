import logging

from confluent_kafka import Message
from jlab_jaws.eventsource.table import EventSourceTable
from jlab_jaws.eventsource.listener import EventSourceListener
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CachedTable(EventSourceTable):
    """
        Adds an in-memory cache to an EventSourceTable.   Caller should be aware of size of topic being consumed and
        this class should only be used for topics whose data will fit in caller's memory.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._cache: Dict[Any, Message] = {}

        super().__init__(config)

        self._listener = _CacheListener(self)

        self.add_listener(self._listener)

    def update_cache(self, msgs: Dict[Any, Message]) -> None:
        """
            Merge updated set of unique messages with existing cache, replacing existing keys if any.

            :param msgs: The new messages
        """
        for msg in msgs.values():
            if msg.value() is None:
                if msg.key() in self._cache:
                    del self._cache[msg.key()]
            else:
                self._cache[msg.key()] = msg

    def await_get(self, timeout_seconds) -> Dict[Any, Message]:
        """
            Synchronously get messages up to highwater mark.  Blocks with a timeout.

            :param timeout_seconds: Seconds to wait for highwater to be reached
            :raises TimeoutException: If highwater is not reached before timeout
        """
        self.await_highwater(timeout_seconds)
        return self._cache


class _CacheListener(EventSourceListener):
    """
        Internal listener implementation for the CacheTable
    """

    def __init__(self, parent: CachedTable) -> None:
        """
            Create a new _CacheListener with provided parent.

            :param parent: The parent CachedTable
        """
        self._parent = parent

    def on_highwater(self) -> None:
        self._parent.highwater_signal.set()

    def on_highwater_timeout(self) -> None:
        pass

    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        self._parent.update_cache(msgs)
