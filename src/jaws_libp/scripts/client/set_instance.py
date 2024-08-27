#!/usr/bin/env python3

"""
    Set alarm registration instance.

    **Note**: bulk imports with ``--file`` expect alarm instance records formatted in
    `AVRO JSON Encoding <https://avro.apache.org/docs/current/spec.html#json_encoding>`_.
    See `Example file <https://github.com/JeffersonLab/jaws/blob/main/examples/data/instances>`_.
"""

import click
from click import Choice

from ...clients import InstanceProducer
from ...console import LocationConsoleConsumer
from ...entities import AlarmInstance, \
    Source, EPICSSource, CALCSource


# pylint: disable=duplicate-code,missing-function-docstring,too-many-arguments,no-value-for-parameter,invalid-name
@click.command()
@click.option('--file', is_flag=True,
              help="Imports a file of key=value pairs (one per line) where the key is alarm name and value is JSON "
                   "encoded AVRO formatted per the alarm-instances-value schema")
@click.option('--unset', is_flag=True, help="Remove the alarm")
@click.option('--action', help="The alarm action (class of alarm)")
@click.option('--pv', help="The name of the EPICS CA PV that directly powers this alarm")
@click.option('--expression', help="The CALC expression used to generate this alarm")
@click.option('--location', '-l', type=click.Choice([]), multiple=True,
              help="The alarm location (Options queried on-demand from alarm-locations topic).  Multiple locations "
                   "allowed.")
@click.option('--screencommand', help="The command to open the related control system screen")
@click.option('--managedby', help="Whom manages this alarm (optional)")
@click.option('--maskedby', help="The optional parent alarm that masks this one")
@click.argument('name')
def set_instance(file, unset, action, pv, expression, location,
                 screencommand, managedby, maskedby, name) -> None:
    producer = InstanceProducer('set_instance.py')

    key = name

    if file:
        producer.import_records(name)
    else:
        if unset:
            value = None
        else:
            if pv:
                source = EPICSSource(pv)
            elif expression:
                source = CALCSource(expression)
            else:
                source = Source()

            if action is None:
                action = "base"

            value = AlarmInstance(action,
                                  source,
                                  location,
                                  managedby,
                                  maskedby,
                                  screencommand)

        producer.send(key, value)


def click_main() -> None:
    consumer = LocationConsoleConsumer('set_instance.py')
    locations = consumer.get_keys_then_done()

    set_instance.params[5].type = Choice(locations)

    set_instance()


if __name__ == "__main__":
    click_main()
