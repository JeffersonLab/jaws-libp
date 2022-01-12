import time

from confluent_kafka import Message
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.avro.serde import AlarmInstanceSerde
from jlab_jaws.eventsource.table import EventSourceTable
from jlab_jaws.eventsource.listener import EventSourceListener
from typing import List


class CacheListener(EventSourceListener):

    def __init__(self, parent: EventSourceTable):
        self._parent = parent

    def on_highwater(self):
        self._parent._highwater_signal.set()

    def on_highwater_timeout(self):
        pass

    def on_batch(self, msgs):
        self._parent.__update_cache(msgs)


class CachedTable(EventSourceTable):

    def __init__(self, config):
        self._cache = None

        super().__init__(config)

        self._listener = CacheListener(self)

        super().add_listener(self._listener)

    def __update_cache(self, msgs: List[Message]) -> None:
        for msg in msgs:
            if msg.value() is None:
                if msg.key() in self._state:
                    del self._state[msg.key()]
            else:
                self._state[msg.key()] = msg

    def await_get(self, timeout_seconds) -> List[Message]:
        """
        Synchronously get messages up to highwater mark.  Blocks with a timeout.

        :param timeout_seconds: Seconds to wait for highwater to be reached
        :return: List of Message
        :raises TimeoutException: If highwater is not reached before timeout
        """
        super().await_highwater(timeout_seconds)
        return self._cache


class CategoryCachedTable(CachedTable):
    def __init__(self, bootstrap_servers):
        key_deserializer = StringDeserializer('utf_8')
        value_deserializer = StringDeserializer('utf_8')

        ts = time.time()

        config = {'topic': 'alarm-categories',
                  'bootstrap.servers': bootstrap_servers,
                  'key.deserializer': key_deserializer,
                  'value.deserializer': value_deserializer,
                  'group.id': 'category-cached-table' + str(ts)}

        super().__init__(config)

        self.start()


class InstanceCachedTable(CachedTable):
    def __init__(self, bootstrap_servers, schema_registry_client):
        key_deserializer = StringDeserializer('utf_8')
        value_deserializer = AlarmInstanceSerde.deserializer(schema_registry_client)

        ts = time.time()

        config = {'topic': 'alarm-instances',
                  'bootstrap.servers': bootstrap_servers,
                  'key.deserializer': key_deserializer,
                  'value.deserializer': value_deserializer,
                  'group.id': 'instance-cached-table' + str(ts)}

        super().__init__(config)

        self.start()
