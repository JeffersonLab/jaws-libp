#!/usr/bin/env python3

"""
    Lists the alarm registration alarms.
"""

import click

from ...console import AlarmConsoleConsumer


# pylint: disable=too-few-public-methods
class ActionFilter:
    """
        Filter action (class of alarm) messages
    """
    def __init__(self, action):
        self._action = action

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the action name matches the provided action name
        """
        return self._action is None or (value is not None and self._action == value.action)


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--action', help="Only show alarms with the specified action (class of alarm)")
def list_alarms(monitor, nometa, export, action) -> None:
    consumer = AlarmConsoleConsumer('list_alarms.py')

    filter_obj = ActionFilter(action)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_alarms()


if __name__ == "__main__":
    click_main()
