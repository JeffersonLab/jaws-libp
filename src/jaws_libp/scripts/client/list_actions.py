#!/usr/bin/env python3

"""
    Lists the alarm actions (class of alarm).

    **Note**: With the ``--export`` option you can export a file that can be imported by ``set_action --file``.
"""

import click
from click import Choice

from ...console import SystemConsoleConsumer, ActionConsoleConsumer


# pylint: disable=too-few-public-methods
class SystemFilter:
    """
        Filter system messages
    """
    def __init__(self, system):
        self._system = system

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the system matches the provided system
        """
        return self._system is None or (value is not None and self._system == value.system)


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--system', type=click.Choice([]),
              help="Only show registered alarms in the specified system (Options queried on-demand from "
                   "alarm-systems topic)")
def list_actions(monitor, nometa, export, system) -> None:
    consumer = ActionConsoleConsumer('list_actions.py')

    filter_obj = SystemFilter(system)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    cat_consumer = SystemConsoleConsumer('list_actions.py')
    systems = cat_consumer.get_keys_then_done()

    list_actions.params[3].type = Choice(systems)

    list_actions()


if __name__ == "__main__":
    click_main()
