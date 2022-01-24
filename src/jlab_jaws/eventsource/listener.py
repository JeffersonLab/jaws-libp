from abc import ABC, abstractmethod
from typing import Dict, Any

from confluent_kafka import Message


class EventSourceListener(ABC):
    """
        Listener interface for EventSourcing callbacks.
    """
    @abstractmethod
    def on_highwater(self) -> None:
        """
            Callback for notification of highwater reached.
        """
        pass

    @abstractmethod
    def on_highwater_timeout(self) -> None:
        """
            Callback notification of timeout before highwater could be reached.
        """
        pass

    @abstractmethod
    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        """
            Callback notification of a batch of messages received.

            :param msgs: Batch of one or more messages, keyed by topic key object
        """
        pass
