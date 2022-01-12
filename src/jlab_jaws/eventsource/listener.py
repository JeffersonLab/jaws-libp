from abc import ABC, abstractmethod


class EventSourceListener(ABC):
    @abstractmethod
    def on_highwater(self) -> None:
        pass

    @abstractmethod
    def on_highwater_timeout(self) -> None:
        pass

    @abstractmethod
    def on_batch(self, msgs) -> None:
        pass
