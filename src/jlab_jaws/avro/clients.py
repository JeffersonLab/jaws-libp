"""
    Clients for interacting with JAWS entities.
"""
import logging
import os
import pwd
import signal
import time
from typing import Dict, Any

from confluent_kafka import Message, SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from tabulate import tabulate

from jlab_jaws.avro.serde import LocationSerde, OverrideKeySerde, OverrideSerde, EffectiveRegistrationSerde
from jlab_jaws.eventsource import CachedTable, EventSourceListener, log_exception

logger = logging.getLogger(__name__)


def set_log_level_from_env():
    level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(threadName)-16s %(name)s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')


def get_registry_client():
    sr_conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
    return SchemaRegistryClient(sr_conf)


class MonitorListener(EventSourceListener):

    def on_highwater_timeout(self) -> None:
        pass

    def on_batch(self, msgs: Dict[Any, Message]) -> None:
        for msg in msgs.values():
            print("{}={}".format(msg.key(), msg.value()))

    def on_highwater(self) -> None:
        pass


class JAWSConsumer(CachedTable):

    def __init__(self, topic, consumer_name, key_serde, value_serde):
        self._topic = topic
        self._consumer_name = consumer_name
        self._key_serde = key_serde
        self._value_serde = value_serde

        set_log_level_from_env()

        signal.signal(signal.SIGINT, self.__signal_handler)

        ts = time.time()

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        config = {'topic': topic,
                  'bootstrap.servers': bootstrap_servers,
                  'key.deserializer': key_serde.deserializer(),
                  'value.deserializer': value_serde.deserializer(),
                  'group.id': consumer_name + str(ts)}

        super().__init__(config)

    def print_records_continuous(self):
        self.add_listener(MonitorListener())
        self.start(log_exception)

    def print_table(self, msg_to_list, head=[], nometa=False, filter_if=lambda key, value: True):
        records = self.get_records()

        table = []

        if not nometa:
            head = ["Timestamp", "User", "Host", "Produced By"] + head

        for record in records.values():
            row = self.__get_row(record, msg_to_list, filter_if, nometa)
            if row is not None:
                table.append(row)

        # Truncate long cells
        table = [[(c if len(str(c)) < 30 else str(c)[:27] + "...") for c in row] for row in table]

        print(tabulate(table, head))

    def export_records(self, filter_if=lambda key, value: True):
        records = self.get_records()

        sortedtuples = sorted(records.items())

        for item in sortedtuples:
            key = item[1].key()
            value = item[1].value()

            if filter_if(key, value):
                key_json = self._key_serde.to_json(key)
                value_json = self._value_serde.to_json(value)

                print(key_json + '=' + value_json)

    def get_records(self) -> Dict[Any, Message]:
        self.start(log_exception)
        records = self.await_get(5)
        self.stop()
        return records

    def __get_row(self, msg: Message, msg_to_list, filter_if, nometa):
        timestamp = msg.timestamp()
        headers = msg.headers()

        row = msg_to_list(msg)

        if not nometa:
            row_header = self.__get_row_header(headers, timestamp)
            row = row_header + row

        if filter_if(msg.key(), msg.value()):
            if not nometa:
                row = row_header + row
        else:
            row = None

        return row

    def __get_row_header(self, headers, timestamp):
        ts = time.ctime(timestamp[1] / 1000)

        user = ''
        producer = ''
        host = ''

        if headers is not None:
            lookup = dict(headers)
            bytez = lookup.get('user', b'')
            user = bytez.decode()
            bytez = lookup.get('producer', b'')
            producer = bytez.decode()
            bytez = lookup.get('host', b'')
            host = bytez.decode()

        return [ts, user, host, producer]

    def __signal_handler(self, sig, frame):
        print('Stopping from Ctrl+C!')
        self.stop()


class JAWSProducer:
    """
        This class produces messages with the JAWS expected header.

        Sensible defaults are used to determine BOOTSTRAP_SERVERS (look in env)
        and to handle errors (log them).

        This producer also knows how to import records from a file using the JAWS expected file format.
    """

    def __init__(self, topic, producer_name, key_serializer, value_serializer):
        set_log_level_from_env()

        self._topic = topic
        self._producer_name = producer_name

        bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
        producer_conf = {'bootstrap.servers': bootstrap_servers,
                         'key.serializer': key_serializer,
                         'value.serializer': value_serializer}

        self._producer = SerializingProducer(producer_conf)
        self._headers = self.__get_headers()

    def send(self, key, value):
        logger.debug("{}={}".format(key, value))
        self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                               on_delivery=self.__on_delivery)
        self._producer.flush()

    def import_records(self, file, line_to_kv):
        logger.debug("Loading file", file)
        handle = open(file, 'r')
        lines = handle.readlines()

        for line in lines:
            key, value = line_to_kv(line)

            logger.debug("{}={}".format(key, value))
            self._producer.produce(topic=self._topic, headers=self._headers, key=key, value=value,
                                   on_delivery=self.__on_delivery)

        self._producer.flush()

    def __get_headers(self):
        return [('user', pwd.getpwuid(os.getuid()).pw_name),
                ('producer', self._producer_name),
                ('host', os.uname().nodename)]

    @staticmethod
    def __on_delivery(err, msg):
        if err is not None:
            logger.error('Failed: {}'.format(err))
        else:
            logger.debug('Delivered')


class EffectiveRegistrationProducer(JAWSProducer):
    def __init__(self, client_name: str):
        schema_registry_client = get_registry_client()
        value_serde = EffectiveRegistrationSerde(schema_registry_client)

        key_serializer = StringSerializer()
        value_serializer = value_serde.serializer()

        super().__init__('effective-registrations', client_name, key_serializer, value_serializer)


class InstanceProducer(JAWSProducer):
    def __init__(self, client_name: str):
        schema_registry_client = get_registry_client()
        value_serde = LocationSerde(schema_registry_client)

        key_serializer = StringSerializer()
        value_serializer = value_serde.serializer()

        super().__init__('alarm-instances', client_name, key_serializer, value_serializer)


class LocationProducer(JAWSProducer):
    def __init__(self, client_name: str):
        schema_registry_client = get_registry_client()
        value_serde = LocationSerde(schema_registry_client)

        key_serializer = StringSerializer()
        value_serializer = value_serde.serializer()

        super().__init__('alarm-locations', client_name, key_serializer, value_serializer)


class OverrideProducer(JAWSProducer):
    def __init__(self, client_name: str):
        schema_registry_client = get_registry_client()
        key_serde = OverrideKeySerde(schema_registry_client)
        value_serde = OverrideSerde(schema_registry_client)

        key_serializer = key_serde.serializer()
        value_serializer = value_serde.serializer()

        super().__init__('alarm-overrides', client_name, key_serializer, value_serializer)
