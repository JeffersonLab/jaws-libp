"""
   Console consumer clients.
"""
# This module should probably go in the jaws_scripts pypi package, but that package includes modules that are also
# scripts so imports are wonky

import time
from typing import Callable, List, Any, Dict, Tuple

from confluent_kafka import Message
from tabulate import tabulate
from .clients import JAWSConsumer, SystemConsumer, ActivationConsumer, LocationConsumer, OverrideConsumer, \
    AlarmConsumer, EffectiveRegistrationConsumer, EffectiveAlarmConsumer, EffectiveNotificationConsumer, \
    ActionConsumer
from .eventsource import EventSourceListener


class ConsoleConsumer:
    """
        This class wraps a JAWSConsumer and provides utilities to output messages to the console.

    """

    def __init__(self, consumer: JAWSConsumer, headers: List[str], torow: Callable[[Message], List[str]]):
        """
            Create a new JAWSConsoleConsumer with the provided JAWSConsumer.
        """
        self._consumer = consumer
        self._headers = headers if headers is not None else ["Key", "Value"]
        self._torow = torow if torow is not None else self._default_torow

    def print_table(self, nometa: bool = False,
                    filter_if: Callable[[Any, Any], bool] = lambda key, value: True) -> None:
        """
            Prints the compacted cache of records as a table to standard output.

            Note: Blocks until the highwater mark has been reached.

            :param nometa: If True, exclude timestamp, producer app name, host, and username from table
            :param filter_if: Callback applied to each Message to indicate if Message should be included
            :raises: TimeoutException if unable to obtain initial list of records up to highwater before timeout
        """
        head = self._headers

        records = self._consumer.await_highwater_get()

        table = []

        if not nometa:
            head = ["Timestamp", "User", "Host", "Produced By"] + head

        for record in records.values():
            row = self.__filtered_row_with_header(record, filter_if, nometa)
            if row is not None:
                table.append(row)

        # Truncate long cells
        table = [[(c if len(str(c)) < 30 else str(c)[:27] + "...") for c in row] for row in table]

        print(tabulate(table, head))

    # check breaks inheritance
    @staticmethod
    def _default_torow(msg: Message) -> List[str]:
        """
            Function to convert Message to table row (List of strings).

            Note: This function assumes the Message.value() is never None as
            this function should be called against a compacted Dict of Messages.

            :param msg: The Message
            :return: The table row (List of strings)
        """
        return [msg.key(), msg.value()]

    def get_keys_then_done(self) -> List[Any]:
        """
            Convenience function to get the list of keys.  This function blocks until the highwater mark is reached.

            WARNING: No other functions should be called on this JAWSConsumer afterwards as start() and stop() are
            called.

            :return: List of keys
        """
        with self._consumer:
            msgs = self._consumer.await_highwater_get()

        return msgs.keys()

    def consume_then_done(self, monitor: bool = False, nometa: bool = False, export: bool = False,
                          filter_if: Callable[[Any, Any], bool] = lambda key, value: True) -> None:
        """
            Convenience function for taking exactly one action given a set of hints.  If more than one action is
            indicated the first one in parameter order wins.  If Neither monitor nor export is indicated then
            print_table is called.

            WARNING: No other functions should be called on this JAWSConsumer afterwards as start() and stop() are
            called.

            :param monitor: If True print records as they arrive (uncompressed) indefinitely (kill with Ctrl-C)
            :param nometa: If True do not include timestamp, producer app, host, and username in output
            :param export: If True call export_records()
            :param filter_if: Callback applied to each Message to indicate if Message should be included
        """
        if monitor:
            self._consumer.add_listener(_MonitorListener())
            self._consumer.start()
        elif export:
            with self._consumer:
                self._consumer.export_records(filter_if)
        else:
            with self._consumer:
                self.print_table(nometa, filter_if)

    def __filtered_row_with_header(self, msg: Message, filter_if: Callable[[Any, Any], bool], nometa: bool):
        timestamp = msg.timestamp()
        headers = msg.headers()

        row = self._torow(msg)

        if filter_if(msg.key(), msg.value()):
            if not nometa:
                row_header = self.__get_row_meta_header(headers, timestamp)
                row = row_header + row
        else:
            row = None

        return row

    @staticmethod
    def __get_row_meta_header(headers: List[Tuple[str, str]], timestamp: Tuple[int, int]) -> List[str]:
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


class _MonitorListener(EventSourceListener):
    """
        Internal listener implementation for the JAWSConsumer monitor feature.
    """

    def on_batch(self, msgs: List[Message], highwater_reached: bool) -> None:
        for msg in msgs:
            print(f"{msg.key()}={msg.value()}")

    def on_highwater(self, cache: Dict[Any, Message]) -> None:
        pass


class ActivationConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS Activation messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = ActivationConsumer(client_name)

        super().__init__(consumer, None, None)


class SystemConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS System messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = SystemConsumer(client_name)

        super().__init__(consumer, ["System Name", "Team"], lambda msg: [msg.key(), msg.value().team])


class ActionConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS Class messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = ActionConsumer(client_name)

        super().__init__(consumer, ["Action Name", "Category", "Priority", "Rationale", "Corrective Action",
                                   "Latchable", "Filterable", "On Delay", "Off Delay"],
                         lambda msg: [msg.key(),
                                      msg.value().category,
                                      msg.value().priority.name if msg.value().priority is not None else None,
                                      msg.value().rationale.replace("\n", "\\n ")
                                      if msg.value().rationale is not None else None,
                                      msg.value().corrective_action.replace("\n", "\\n")
                                      if msg.value().corrective_action is not None else None,
                                      msg.value().latchable,
                                      msg.value().filterable,
                                      msg.value().on_delay_seconds,
                                      msg.value().off_delay_seconds])


class EffectiveNotificationConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS notification messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = EffectiveNotificationConsumer(client_name)

        super().__init__(consumer, ["Alarm Name", "State", "Overrides"], lambda msg: [msg.key(),
                                                                                      msg.value().state.name,
                                                                                      msg.value().overrides])


class EffectiveAlarmConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS alarm messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = EffectiveAlarmConsumer(client_name)

        super().__init__(consumer, ["Alarm Name", "State", "Overrides", "Instance", "Class"],
                         lambda msg: [msg.key(),
                                      msg.value().notification.state.name,
                                      msg.value().notification.overrides,
                                      msg.value().registration.instance,
                                      msg.value().registration.alarm_class])


class EffectiveRegistrationConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS registration messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = EffectiveRegistrationConsumer(client_name)

        super().__init__(consumer, ["Alarm Name", "Instance", "Class"], lambda msg: [msg.key(),
                                                                                     msg.value().instance,
                                                                                     msg.value().alarm_class])


class AlarmConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS Alarm registration instance messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = AlarmConsumer(client_name)

        super().__init__(consumer, ["Alarm Name", "Action", "Source", "Location", "Managed By", "Masked By",
                                    "Screen Command"],
                         lambda msg: [msg.key(),
                                      msg.value().action,
                                      msg.value().source,
                                      msg.value().location,
                                      msg.value().managed_by,
                                      msg.value().masked_by,
                                      msg.value().screen_command])


class LocationConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS AlarmLocation messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = LocationConsumer(client_name)

        super().__init__(consumer, ["Location Name", "Parent"], lambda msg: [msg.key(), msg.value().parent])


class OverrideConsoleConsumer(ConsoleConsumer):
    """
        ConsoleConsumer for JAWS AlarmOverride messages.
    """
    def __init__(self, client_name: str):
        """
            Create a new Consumer.

            :param client_name: The name of the client application
        """
        consumer = OverrideConsumer(client_name)

        super().__init__(consumer, ["Alarm Name", "Override Type", "Value"], lambda msg: [msg.key().name,
                                                                                          msg.key().type.name,
                                                                                          msg.value()])
