"""
   Event Sourcing database abstraction layer for Apache Kafka.

   See Also:
       - `Storing Data in Kafka <https://www.confluent.io/blog/okay-store-data-apache-kafka/>`_
       - `Fowler on Event Sourcing <https://martinfowler.com/eaaDev/EventSourcing.html>`_
"""
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Timer, Event
from typing import List, Dict, Any, Callable

from confluent_kafka import DeserializingConsumer, OFFSET_BEGINNING, Message

logger = logging.getLogger(__name__)


class EventSourceListener(ABC):
    """
        Listener interface for EventSourceTable callbacks.
    """
    @abstractmethod
    def on_highwater(self, cache: Dict[Any, Message]) -> None:
        """
            Callback for notification of highwater reached.

            :param cache: The cache of initial messages, empty if compacted.cache = False
        """

    @abstractmethod
    def on_batch(self, msgs: List[Message], highwater_reached: bool) -> None:
        """
            Callback notification of a batch of messages received.

            This method is called regardless of highwater status.

            :param highwater_reached: true if highwater has already been reached
            :param msgs: Batch of one or more ordered messages
        """


def log_exception(e: Exception) -> None:
    """
        Simple default action of logging an exception.

        :param e: The Exception
    """
    logger.exception(e)


class TimeoutException(Exception):
    """
        Thrown on asynchronous task timeout
    """


class EventSourceTable:
    """
        This class provides an Event Source Table abstraction.
    """

    __slots__ = [
        '_config',
        '_consumer',
        '_listeners',
        '_executor',
        '_high',
        '_highwater_reached',
        '_highwater_signal',
        '_is_highwater_timeout',
        '_low',
        '_on_exception',
        '_run',
        '_state'
    ]

    def __init__(self, config: Dict[str, Any], on_exception: Callable[[Exception], None] = log_exception) -> None:
        """
            Create an EventSourceTable instance.

         Args:
             config (dict): Configuration

             on_exception (Callable): Function to call when an asynchronous exception occurs, including a Timeout.


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
            |                         |                     | Number of seconds to wait for highwater. Default 30.|
            | ``highwater.timeout``   | float               |                                                     |
            |                         |                     |                                                     |
            +-------------------------+---------------------+-----------------------------------------------------+
            | ``compacted.cache``     | bool                | If False, disables on_highwater cache. Default True.|
            +-------------------------+---------------------+-----------------------------------------------------+

        Warning:
                Keys must be hashable so your key deserializer generally must generate immutable types.

         """
        # Apply defaults
        defaults = {'highwater.timeout': 30,
                    'compacted.cache': True}

        conf_copy = defaults.copy()
        conf_copy.update(config)

        if conf_copy.get('topic') is None:
            raise KeyError('"topic" is required in config Dict')

        self._config: Dict[str, Any] = conf_copy
        self._on_exception = on_exception
        self._consumer: DeserializingConsumer = None
        self._listeners: List[EventSourceListener] = []
        self._executor: ThreadPoolExecutor = None
        self._high: int = None
        self._highwater_reached: bool = False
        self._highwater_signal: Event = Event()
        self._is_highwater_timeout: bool = False
        self._low: int = None
        self._run: bool = True
        self._state: List[Message] = []

    def add_listener(self, listener: EventSourceListener) -> None:
        """
            Add an EventSourceListener.

            :param listener: The EventSourceListener to register
        """

        self._listeners.append(listener)

    def remove_listener(self, listener: EventSourceListener) -> None:
        """
            Remove an EventSourceListener.

            :param listener: The EventSourceListener to unregister
        """
        self._listeners.remove(listener)

    def await_highwater(self) -> None:
        """
            Block the calling thread and wait for topic highwater to be reached.

            See: The 'highwater.timeout' option passed to the config Dict in constructor

            :raises TimeoutException: If highwater is not reached before timeout
        """
        logger.debug("await_highwater")
        self._highwater_signal.wait()
        if self._is_highwater_timeout:
            raise TimeoutException()

    def start(self):
        """
            Start monitoring for state updates.

            Note: start() should only be called once.  I'm too lazy to come up with some thread-safe locking check
            to ensure it, so just like Python doesn't actually have private members, I'm not actually going to stop you,
            but you've been warned.
        """
        logger.debug("start")

        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='TableThread')

        self._executor.submit(self.__monitor)

    def highwater_reached(self) -> bool:
        """
            Check whether initial highwater has been reached.

            :return: True if highwater reached
        """

        return self._highwater_reached

    def __do_highwater_timeout(self) -> None:
        logger.debug("__do_highwater_timeout")
        self._is_highwater_timeout = True

    def __notify_changes(self, highwater_reached) -> None:
        for listener in self._listeners:
            listener.on_batch(self._state.copy(), highwater_reached)

        self._state.clear()

    def __monitor(self) -> None:
        try:
            self.__monitor_initial()
            self.__monitor_continue()
        except Exception as e:
            self._on_exception(e)
        finally:
            self._consumer.close()
            self._executor.shutdown()

    def __monitor_initial(self) -> None:
        logger.debug("__monitor_initial")

        # Remove all EventSourceTable specific configs as Consumer will complain if unrecognized configs found
        conf_copy = self._config.copy()
        del conf_copy['topic']
        del conf_copy['highwater.timeout']
        del conf_copy['compacted.cache']

        self._consumer = DeserializingConsumer(conf_copy)
        self._consumer.subscribe([self._config['topic']], on_assign=self.__on_assign)

        timeout_seconds = self._config['highwater.timeout']

        t = Timer(timeout_seconds, self.__do_highwater_timeout)
        t.start()

        caching_enabled = self._config['compacted.cache']
        cache = {}

        while not (self._highwater_reached or self._is_highwater_timeout):
            msg = self._consumer.poll(1)

            logger.debug("__monitor_initial poll None: %s", msg is None)

            msgs = [msg] if msg is not None else None

            if msgs is not None:
                for msg in msgs:

                    if caching_enabled:
                        if msg.value() is None:
                            if msg.key() in cache:
                                del cache[msg.key()]
                        else:
                            cache[msg.key()] = msg

                    self._state.append(msg)

                    if msg.offset() + 1 == self._high:
                        self._highwater_reached = True

                self.__notify_changes(False)

        t.cancel()

        if self._is_highwater_timeout:
            self._highwater_signal.set()
            raise TimeoutException()

        for listener in self._listeners:
            listener.on_highwater(cache)

        self._highwater_signal.set()

    def __monitor_continue(self) -> None:
        logger.debug("__monitor_continue")
        while self._run:
            msg = self._consumer.poll(1)

            logger.debug("__monitor_continue poll None: %s", msg is None)

            msgs = [msg] if msg is not None else None

            if msgs is not None:
                for msg in msgs:
                    self._state.append(msg)

                self.__notify_changes(True)

    def stop(self) -> None:
        """
            Stop monitoring for state updates.
        """
        logger.debug("stop")
        self._run = False

    def __on_assign(self, consumer, partitions) -> None:

        for p in partitions:
            p.offset = OFFSET_BEGINNING
            self._low, self._high = consumer.get_watermark_offsets(p)

            if self._high == 0:
                self._highwater_reached = True

        consumer.assign(partitions)

    def __enter__(self):
        self.start()

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()
