#!/usr/bin/env python3

"""
    Lists the alarm overrides.
"""

import click

from ...entities import OverriddenAlarmType
from ...console import OverrideConsoleConsumer


# pylint: disable=too-few-public-methods
class TypeFilter:
    """
        Filter override type messages
    """
    def __init__(self, override_type):
        self._override_type = override_type

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the override type matches the provided type
        """
        return self._override_type is None or (value is not None and self._override_type == key.type.name)


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--override', type=click.Choice(list(map(lambda c: c.name, OverriddenAlarmType))),
              help="The type of override")
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
def list_overrides(override, monitor, nometa, export) -> None:
    consumer = OverrideConsoleConsumer('list_overrides.py')

    filter_obj = TypeFilter(override)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    list_overrides()


if __name__ == "__main__":
    click_main()
