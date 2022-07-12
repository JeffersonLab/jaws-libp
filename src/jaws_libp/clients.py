"""
   Clients for producing and consuming messages on the various Kafka topics in JAWS.
"""
import logging
import os
import signal
import socket
import time

from typing import Any, List, Tuple, Dict

import requests

from confluent_kafka import Message, SerializingProducer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from psutil import Process

from .avro.serde import LocationSerde, OverrideKeySerde, OverrideSerde, EffectiveRegistrationSerde, \
    StringSerde, Serde, EffectiveAlarmSerde, EffectiveNotificationSerde, ClassSerde, ActivationSerde, InstanceSerde
from .entities import UnionEncoding
from .eventsource import EventSourceListener, EventSourceTable

logger = logging.getLogger(__name__)


def set_log_level_from_env() -> None:
    """
        Simple utility for setting the loglevel via the environment variable LOGLEVEL, and also
        setting a sensible logging format.
    """
    level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(threadName)-16s %(name)s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')


def get_registry_client() -> SchemaRegistryClient:
    """
        Simple utility function for creating a SchemaRegistryClient using the environment
        variable SCHEMA_REGISTRY to determine URL.

        :return: A new SchemaRegistryClient
    """
    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    return SchemaRegistryClient(sr_conf)


class JAWSConsumer(EventSourceTable):
    """
        This class consumes messages from JAWS.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).

        This consumer also knows how to export records into a file using the JAWS expected file format.
    """

    def __init__(self, config):
        """
            Create a new JAWSConsumer with the provided attributes.

         Note:
             The configuration options include all those for EventSourceTable and DeserializingConsumer plus:

            +-------------------------+---------------------+-----------------------------------------------------+
            | Property Name           | Type                | Description                                         |
            +=========================+=====================+=====================================================+
            | ``client.name``         | str                 | Name of client app                                  |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Key Serde                                           |
            | ``key.serde``           | Serde               |                                                     |
            |                         |                     |                                                     |
            +-------------------------+---------------------+-----------------------------------------------------+
            |                         |                     | Value Serde                                         |
            | ``value.serde``         | Serde               |                                                     |
            |                         |                     |                                                     |
            +-------------------------+---------------------+-----------------------------------------------------+

            :param config: The Consumer config
        """
        set_log_level_from_env()

        signal.signal(signal.SIGINT, self.__signal_handler)

        ts = time.time()
        config['client.name'] = config['client.name'] if config['client.name'] is not None else 'JAWSConsumer'
        self._key_serde = config['key.serde']
        self._value_serde = config['value.serde']
        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        defaults = {'bootstrap.servers': bootstrap_servers,
                    'group.id': config['client.name'] + str(ts),
                    'key.deserializer': self._key_serde.deserializer(),
                    'value.deserializer': self._value_serde.deserializer(),
                    'enable.auto.commit': False,
                    'auto.offset.reset': 'earliest'}

        conf_copy = defaults.copy()
        conf_copy.update(config)

        # Remove all JAWSConsumer specific configs as Consumer will complain if unrecognized configs found
        del conf_copy['client.name']
        del conf_copy['key.serde']
        del conf_copy['value.serde']

        super().__init__(conf_copy)

        caching_enabled = self._config.get('compacted.cache') \
            if self._config.get('compacted.cache') is not None else True
        if caching_enabled:
            self._cache_listener = _CacheListener()
            self.add_listener(self._cache_listener)

    def await_highwater_get(self) -> Dict[Any, Message]:
        """
            Block the calling thread and wait for topic highwater to be reached, then return cache of compacted
            messages.

            See: The 'highwater.timeout' option passed to the config Dict in constructor

            :return: The cache of compacted messages
            :raises TimeoutException: If highwater is not reached before timeout
        """
        self.await_highwater()
        return self._cache_listener.get_cache()

    def __to_line(self, key: Any, value: Any) -> str:
        """
            Function to convert key and value pair to line for file.

            :param key: The topic key entity
            :param value: The topic value entity
            :return: The line (string)
        """
        key_json = self._key_serde.to_json(key)
        value_json = self._value_serde.to_json(value)

        return key_json + '=' + value_json

    def export_records(self, filter_if=lambda key, value: True) -> None:
        """
            Prints the compacted cache of records in the JAWS file format to standard output.

            Note: Blocks until the highwater mark has been reached.

            :param filter_if: Callback applied to each Message to indicate if Message should be included
            :raises: TimeoutException if unable to obtain initial list of records up to highwater before timeout
        """
        records = self.await_highwater_get()

        sortedtuples = sorted(records.items())

        for item in sortedtuples:
            key = item[1].key()
            value = item[1].value()

            if filter_if(key, value):
                print(self.__to_line(key, value))

    # pylint: disable=unused-argument
    def __signal_handler(self, sig, frame):
        print('Stopping from Ctrl+C!')
        self.stop()


class _CacheListener(EventSourceListener):
    """
        Internal listener implementation for the JAWSConsumer await highwater feature.
    """

    def __init__(self):
        self._cache = {}

    def on_batch(self, msgs: List[Message], highwater_reached: bool) -> None:
        pass

    def on_highwater(self, cache: Dict[Any, Message]) -> None:
        self._cache = cache

    def get_cache(self):
        """
            Get the cache.  Assumes caller waited on the EventSourceTable.awaitHighwater() first.

            :return: The cached messages Dict
        """
        return self._cache


class JAWSProducer:
    """
        This class produces messages to JAWS.

        The JAWS expected header is included in all messages.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).

        This producer also knows how to import records from a file using the JAWS expected file format.
    """

    def __init__(self, topic: str, client_name: str, key_serde: Serde, value_serde: Serde) -> None:
        """
            Create a new JAWSProducer with the provided attributes.

            :param topic: The Kafka topic name
            :param client_name: The name of the client application
            :param key_serde: The appropriate Kafka message key Serde for the given topic
            :param value_serde: The appropriate Kafka message value Serde for the given topic
        """
        set_log_level_from_env()

        self._topic = topic
        self._client_name = client_name
        self._key_serde = key_serde
        self._value_serde = value_serde

        key_serializer = key_serde.serializer()
        value_serializer = value_serde.serializer()

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        producer_conf = {'bootstrap.servers': bootstrap_servers,
                         'key.serializer': key_serializer,
                         'value.serializer': value_serializer}

        self._producer = SerializingProducer(producer_conf)
        self._headers = self.__get_headers()

    def send(self, key: Any, value: Any) -> None:
        """
            Send a single message to a Kafka topic.

            :param key: The message key
            :param value: The message value
        """
        logger.debug("%s=%s", key, value)
        self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                               on_delivery=self.__on_delivery)
        self._producer.flush()

    def __from_line(self, line: str) -> Tuple[Any, Any]:
        """
            Function to convert line from file to key and value pair
            :param line: The line (string)
            :return: A Tuple containing the key and value pair
        """
        tokens = line.split("=", 1)
        key_str = tokens[0]
        value_str = tokens[1]

        key = self._key_serde.from_json(key_str)
        value = self._value_serde.from_json(value_str)

        return key, value

    def __import_lines(self, lines):
        for line in lines:
            if line:  # url streaming may contain empty keep-alive lines
                key, value = self.__from_line(line)

                logger.debug("%s=%s", key, value)
                self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                                       on_delivery=self.__on_delivery)

        self._producer.flush()

    def __import_from_url(self, url: str) -> None:
        """
            Send a batch of messages stored in a JAWS formatted file at a URL to a Kafka topic.

            :param url: URL path to a file to import
        """
        with requests.get(url, stream=True) as r:
            if r.encoding is None:
                r.encoding = 'utf-8'

            lines = r.iter_lines(decode_unicode=True)
            self.__import_lines(lines)

    def __import_from_file(self, file: str) -> None:
        """
            Send a batch of messages stored in a JAWS formatted file to a Kafka topic.

            :param file: Path to file to import
        """
        logger.debug("Loading file %s", file)
        with open(file, "r", encoding="utf8") as handle:
            lines = handle.readlines()
            self.__import_lines(lines)

    def import_records(self, path: str) -> None:
        """
            Send a batch of messages stored in a JAWS formatted file/url to a Kafka topic.

            :param path: Path to file/url to import
        """
        if path.startswith("http"):
            self.__import_from_url(path)
        else:
            self.__import_from_file(path)

    def __get_headers(self) -> List[Tuple[str, str]]:
        return [('user', Process().username()),
                ('producer', self._client_name),
                ('host', socket.gethostname())]

    # pylint: disable=unused-argument
    @staticmethod
    def __on_delivery(err: KafkaError, msg: Message) -> None:
        if err is not None:
            logger.error('Failed: %s', err)
        else:
            logger.debug('Delivered')


class ActivationConsumer(JAWSConsumer):
    """
        Consumer for JAWS Activation messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = ActivationSerde(schema_registry_client)

        config = {
            'topic': 'alarm-activations',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class CategoryConsumer(JAWSConsumer):
    """
        Consumer for JAWS Category messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        key_serde = StringSerde()
        value_serde = StringSerde()

        config = {
            'topic': 'alarm-categories',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class ClassConsumer(JAWSConsumer):
    """
        Consumer for JAWS Class messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = ClassSerde(schema_registry_client)

        config = {
            'topic': 'alarm-classes',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class EffectiveNotificationConsumer(JAWSConsumer):
    """
        Consumer for JAWS EffectiveNotification messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveNotificationSerde(schema_registry_client)

        config = {
            'topic': 'effective-notifications',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class EffectiveAlarmConsumer(JAWSConsumer):
    """
        Consumer for JAWS EffectiveAlarm messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveAlarmSerde(schema_registry_client)

        config = {
            'topic': 'effective-alarms',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class EffectiveRegistrationConsumer(JAWSConsumer):
    """
        Consumer for JAWS EffectiveRegistration messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveRegistrationSerde(schema_registry_client)

        config = {
            'topic': 'effective-registrations',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class InstanceConsumer(JAWSConsumer):
    """
        Consumer for JAWS Instance messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = InstanceSerde(schema_registry_client, UnionEncoding.DICT_WITH_TYPE)

        config = {
            'topic': 'alarm-instances',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class LocationConsumer(JAWSConsumer):
    """
        Consumer for JAWS Location messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = LocationSerde(schema_registry_client)

        config = {
            'topic': 'alarm-locations',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class OverrideConsumer(JAWSConsumer):
    """
        Consumer for JAWS Override messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = OverrideKeySerde(schema_registry_client)
        value_serde = OverrideSerde(schema_registry_client)

        config = {
            'topic': 'alarm-overrides',
            'client.name': client_name,
            'key.serde': key_serde,
            'value.serde': value_serde
        }

        super().__init__(config)


class ActivationProducer(JAWSProducer):
    """
        Producer for JAWS Activation messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = ActivationSerde(schema_registry_client)

        super().__init__('alarm-activations', client_name, key_serde, value_serde)


class CategoryProducer(JAWSProducer):
    """
        Producer for JAWS Category messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        key_serde = StringSerde()
        value_serde = StringSerde()

        super().__init__('alarm-categories', client_name, key_serde, value_serde)


class ClassProducer(JAWSProducer):
    """
        Producer for JAWS Class messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = ClassSerde(schema_registry_client)

        super().__init__('alarm-classes', client_name, key_serde, value_serde)


class EffectiveNotificationProducer(JAWSProducer):
    """
        Producer for JAWS EffectiveNotification messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveNotificationSerde(schema_registry_client)

        super().__init__('effective-notifications', client_name, key_serde, value_serde)


class EffectiveAlarmProducer(JAWSProducer):
    """
        Producer for JAWS EffectiveAlarm messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveAlarmSerde(schema_registry_client)

        super().__init__('effective-alarms', client_name, key_serde, value_serde)


class EffectiveRegistrationProducer(JAWSProducer):
    """
        Producer for JAWS EffectiveRegistration messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = EffectiveRegistrationSerde(schema_registry_client)

        super().__init__('effective-registrations', client_name, key_serde, value_serde)


class InstanceProducer(JAWSProducer):
    """
        Producer for JAWS Instance messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = InstanceSerde(schema_registry_client)

        super().__init__('alarm-instances', client_name, key_serde, value_serde)


class LocationProducer(JAWSProducer):
    """
        Producer for JAWS Location messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = StringSerde()
        value_serde = LocationSerde(schema_registry_client)

        super().__init__('alarm-locations', client_name, key_serde, value_serde)


class OverrideProducer(JAWSProducer):
    """
        Producer for JAWS Override messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Producer.

            :param client_name: The name of the client application
        """
        schema_registry_client = get_registry_client()
        key_serde = OverrideKeySerde(schema_registry_client)
        value_serde = OverrideSerde(schema_registry_client)

        super().__init__('alarm-overrides', client_name, key_serde, value_serde)
