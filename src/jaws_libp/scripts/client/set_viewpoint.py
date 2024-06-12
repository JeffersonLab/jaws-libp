#!/usr/bin/env python3

"""
    Set alarm viewpoint.
"""

import click

from ...clients import ViewpointProducer
from ...entities import AlarmViewpoint


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is viewpoint name and value is "
                   "AlarmViewpoint JSON")
@click.option('--unset', is_flag=True, help="Remove the viewpoint")
@click.argument('name')
@click.option('--location', '-l', help="Name of location", multiple=True)
@click.option('--category', '-c', help="Name of category", multiple=True)
@click.option('--alarmclass', '-a', help="Name of alarmclass", multiple=True)
def set_viewpoint(file, unset, name, location, category, alarmclass) -> None:
    producer = ViewpointProducer('set_viewpoint.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            value = AlarmViewpoint(location, category, alarmclass)

        producer.send(key, value)


def click_main() -> None:
    set_viewpoint()


if __name__ == "__main__":
    click_main()
