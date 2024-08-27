from typing import Dict, Any, List

from confluent_kafka import Message

from jaws_libp.clients import SystemProducer, SystemConsumer
from jaws_libp.eventsource import EventSourceListener
from jaws_libp.entities import AlarmSystem

class SystemListener(EventSourceListener):
    _systems: Dict[Any, Message]

    def on_highwater(self, cache: Dict[Any, Message]) -> None:
        self._systems = cache

    def on_batch(self, msgs: List[Message], highwater_reached: bool) -> None:
        pass

    def get_categories(self) -> Dict[Any, Message]:
        return self._systems


def test_category_client():
    producer = SystemProducer('category-test')
    consumer = SystemConsumer('category-test')

    expected_key = "TESTING"
    expected_value = AlarmSystem("Tester")

    try:
        producer.send(expected_key, expected_value)

        listener = SystemListener()

        consumer.add_listener(listener)

        consumer.start()

        consumer.await_highwater()

        categories = listener.get_categories()

        assert len(categories) == 1

        message = list(categories.values())[0]

        assert message.key() == expected_key
        assert message.value() == expected_value

    finally:
        consumer.stop()
        producer.send(expected_key, None)
