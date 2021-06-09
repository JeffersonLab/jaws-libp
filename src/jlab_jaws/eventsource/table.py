"""A module for Event Sourcing
"""
from confluent_kafka import DeserializingConsumer, OFFSET_BEGINNING
from confluent_kafka.serialization import SerializationError


class EventSourceTable:
    """This class provides an Event Source Table abstraction.
    """

    __slots__ = ['_hash', '_config', '_on_initial_state', '_on_state_update', '_state', '_default_conf',
                 '_empty', '_high', '_low', '_run']

    def __init__(self, config, on_initial_state, on_state_update):
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
            |                         |                     | True to monitor continuously, False to stop after   |
            | ``monitor``             | bool                | determining initial state.  Defaults to False.      |
            |                         |                     |                                                     |
            +-------------------------+---------------------+-----------------------------------------------------+

            Note:
                Keys must be hashable so your key deserializer generally must generate immutable types.

         """
        self._config = config
        self._on_initial_state = on_initial_state
        self._on_state_update = on_state_update

        self._run = True
        self._low = None
        self._high = None
        self._empty = False
        self._default_conf = {}
        self._state = {}

    def start(self):
        """
            Start monitoring for state updates.
        """
        consumer_conf = {'bootstrap.servers': self._config['bootstrap.servers'],
                         'key.deserializer': self._config['key.deserializer'],
                         'value.deserializer': self._config['value.deserializer'],
                         'group.id': self._config['group.id']}

        c = DeserializingConsumer(consumer_conf)
        c.subscribe([self._config['topic']], on_assign=self._my_on_assign)

        while True:
            try:
                msg = c.poll(1.0)

            except SerializationError as e:
                print("Message deserialization failed for {}: {}".format(msg, e))
                break

            if self._empty:
                break

            if msg is None:
                continue

            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue

            if msg.value() is None:
                if msg.key() in self._state:
                    del self._state[msg.key()]
            else:
                self._state[msg.key()] = msg

            if msg.offset() + 1 == self._high:
                break

        self._on_initial_state(self._state)

        if not self._config['monitor']:
            self._run = False

        while self._run:
            try:
                msg = c.poll(1.0)

            except SerializationError as e:
                print("Message deserialization failed for {}: {}".format(msg, e))
                break

            if msg is None:
                continue

            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue

            self._on_state_update(msg)

        c.close()

    def stop(self):
        """
            Stop monitoring for state updates.
        """

        self._run = False

    def _my_on_assign(self, consumer, partitions):

        for p in partitions:
            p.offset = OFFSET_BEGINNING
            self._low, self._high = consumer.get_watermark_offsets(p)

            if self._high == 0:
                self._empty = True

        consumer.assign(partitions)