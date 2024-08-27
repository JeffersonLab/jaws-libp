#!/usr/bin/env python3

"""
    Set alarm system.
"""

import click

from ...clients import SystemProducer
from ...entities import AlarmSystem

# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is system name and value is "
                   "AlarmSystem JSON")
@click.option('--unset', is_flag=True, help="Remove the category")
@click.argument('name')
@click.option('--team', '-t', help="Name of team")
def set_system(file, unset, name, team) -> None:
    producer = SystemProducer('set_system.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            if team is None:
                raise click.ClickException("--team required")

            value = AlarmSystem(team)

        producer.send(key, value)


def click_main() -> None:
    set_system()


if __name__ == "__main__":
    click_main()
