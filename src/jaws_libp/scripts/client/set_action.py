#!/usr/bin/env python3

"""
    Set alarm action (class of alarm) .

    **Note**: bulk imports with ``--file`` expect alarm action records formatted in
    `AVRO JSON Encoding <https://avro.apache.org/docs/current/spec.html#json_encoding>`_
    See `Example file <https://github.com/JeffersonLab/jaws/blob/main/examples/data/actions>`_.
"""

import click
from click import Choice

from ...clients import ActionProducer
from ...console import SystemConsoleConsumer
from ...entities import AlarmAction, AlarmPriority


# pylint: disable=duplicate-code,missing-function-docstring,no-value-for-parameter,too-many-arguments
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-actions-value schema")
@click.option('--unset', is_flag=True, help="Remove the class")
@click.option('--system', type=click.Choice([]),
              help="The alarm system (Options queried on-demand from alarm-systems topic)")
@click.option('--priority', type=click.Choice(list(map(lambda c: c.name, AlarmPriority))), help="The alarm priority")
@click.option('--filterable/--not-filterable', is_flag=True, default=True,
              help="True if alarm can be filtered out of view")
@click.option('--latchable/--not-latchable', is_flag=True, default=True,
              help="Indicate that the alarm latches and requires acknowledgement to clear")
@click.option('--rationale', help="The alarm rationale")
@click.option('--correctiveaction', help="The corrective action")
@click.option('--ondelayseconds', type=int, default=None, help="Number of on delay seconds")
@click.option('--offdelayseconds', type=int, default=None, help="Number of off delay seconds")
@click.argument('name')
def set_action(file, unset, system,
              priority, filterable, latchable, rationale,
              correctiveaction, ondelayseconds, offdelayseconds, name) -> None:
    producer = ActionProducer('set_action.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            if system is None:
                raise click.ClickException("--system required")

            if priority is None:
                raise click.ClickException("--priority required")

            if rationale is None:
                raise click.ClickException("--rationale required")

            if correctiveaction is None:
                raise click.ClickException("--correctiveaction required")

            value = AlarmAction(system,
                                AlarmPriority[priority],
                                rationale,
                                correctiveaction,
                                latchable,
                                filterable,
                                ondelayseconds,
                                offdelayseconds)

        producer.send(key, value)


def click_main() -> None:
    cat_consumer = SystemConsoleConsumer('set_action.py')
    systems = cat_consumer.get_keys_then_done()

    set_action.params[2].type = Choice(systems)

    set_action()


if __name__ == "__main__":
    click_main()
