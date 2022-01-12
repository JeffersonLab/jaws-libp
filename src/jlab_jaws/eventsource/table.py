"""A module for Event Sourcing
"""
from concurrent.futures import ThreadPoolExecutor
from typing import List

from confluent_kafka import DeserializingConsumer, OFFSET_BEGINNING, Message
from threading import Timer, Event

from src.jlab_jaws.eventsource.listener import EventSourceListener


class TimeoutException(Exception):
    pass


class EventSourceTable:
    """This class provides an Event Source Table abstraction.
    """

    __slots__ = ['_hash', '_config', '_listeners', '_state', '_consumer', '_executor',
                 '_end_reached', '_high', '_low', '_run', 'is_highwater_timeout']

    _listeners: List[EventSourceListener] = []

    def __init__(self, config):
        """Create an EventSourceTable instance.

         Args:
             config (dict): Configuration
             on_initial_state (callable(dict): Callback providing initial state of EventSourceTable
             on_state_update (callable(dict)): Callback providing updated state

         Note:
             The configuration options include:

            +-------------------------+---------------------+-----------------------------------------------------+
            | Property Name           | Type                | Description                                         |
            +=========================+=====================+=====================================================+
            | ``bootstrap.servers``   | str                 | Comma-separated list of brokers.                    |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Client group id string.                             |
            | ``group.id``            | str                 | All clients sharing the same group.id belong to the |
            |                         |                     | same group.                                         |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Callable(SerializationContext, bytes) -> obj        |
            | ``key.deserializer``    | callable            |                                                     |
            |                         |                     | Deserializer used for message keys.                 |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Callable(SerializationContext, bytes) -> obj        |
            | ``value.deserializer``  | callable            |                                                     |
            |                         |                     | Deserializer used for message values.               |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Kafka topic name to consume messages from           |
            | ``topic``               | str                 |                                                     |
            |                         |                     |                                                     |
            +-------------------------+---------------------+-----------------------------------------------------+

            Note:
                Keys must be hashable so your key deserializer generally must generate immutable types.

         """
        self._config = config

        self._run = True
        self._low = None
        self._high = None
        self._state = {}

        self._is_highwater_timeout = False
        self._end_reached = False
        self._consumer = None
        self._executor = None
        self._highwater_signal = Event()

    def add_listener(self, listener: EventSourceListener):
        self._listeners.append(listener)

    def remove_listener(self, listener: EventSourceListener):
        self._listeners.remove(listener)

    def await_highwater(self, timeout_seconds: float) -> None:
        flag = self._highwater_signal.wait(timeout_seconds)
        if not flag:
            raise TimeoutException

    def start(self):
        """
            Start monitoring for state updates.
        """

        self._executor = ThreadPoolExecutor(max_workers=1)

        self._executor.submit(self.__monitor)

    def __do_highwater_timeout(self):
        self._is_highwater_timeout = True

    def __update_state(self, msg: Message):
        if msg.value() is None:
            if msg.key() in self._state:
                del self._state[msg.key()]
        else:
            self._state[msg.key()] = msg

    def __notify_changes(self):
        for listener in self._listeners:
            listener.on_batch(self._state.copy())

        self._state.clear()

    def __monitor(self):
        self.__monitor_initial()
        self.__monitor_continue()
        self._consumer.close()
        self._executor.shutdown()

    def __monitor_initial(self):
        consumer_conf = {'bootstrap.servers': self._config['bootstrap.servers'],
                         'key.deserializer': self._config['key.deserializer'],
                         'value.deserializer': self._config['value.deserializer'],
                         'group.id': self._config['group.id']}

        self._consumer = DeserializingConsumer(consumer_conf)
        self._consumer.subscribe([self._config['topic']], on_assign=self._my_on_assign)

        t = Timer(30, self.__do_highwater_timeout())
        t.start()

        while not end_reached and not self._is_highwater_timeout:
            msgs = self._consumer.consume(500, timeout=1)

            if msgs is not None:
                for msg in msgs:
                    self.__update_state(msg)

                    if msg.offset() + 1 == self._high:
                        end_reached = True

                self.__notify_changes()

        t.cancel()

        if self._is_highwater_timeout:
            for listener in self._listeners:
                listener.on_highwater_timeout()
        else:
            for listener in self._listeners:
                listener.on_highwater()

    def __monitor_continue(self):
        while self._run:
            msgs = self._consumer.consume(500, timeout=1)

            if msgs is not None:
                for msg in msgs:
                    self.__update_state(msg)

                self.__notify_changes()

    def stop(self) -> None:
        """
            Stop monitoring for state updates.
        """

        self._run = False

    def _my_on_assign(self, consumer, partitions) -> None:

        for p in partitions:
            p.offset = OFFSET_BEGINNING
            self._low, self._high = consumer.get_watermark_offsets(p)

            if self._high == 0:
                self._end_reached = True

        consumer.assign(partitions)
