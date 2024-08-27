#!/usr/bin/env python3

"""
    Set effective registration.

    **Note**: This is generally for testing only and should be done automatically via
    `jaws-effective-processor <https://github.com/JeffersonLab/jaws-effective-processor>`_
"""

import click
from ...clients import EffectiveRegistrationProducer
from ...entities import EffectiveRegistration, \
    Alarm, Source


# pylint: disable=duplicate-code
def __get_instance():
    return Alarm("base",
                 Source(),
                 ["INJ"],
                 None,
                 "alarm1",
                 "command1")


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--unset', is_flag=True, help="present to clear state, missing to set state")
@click.argument('name')
def set_effective_registration(unset, name):
    producer = EffectiveRegistrationProducer('set_effective_registration.py')

    key = name

    if unset:
        value = None
    else:
        action = None
        alarm = __get_instance()

        value = EffectiveRegistration(action, alarm)

    producer.send(key, value)


def click_main() -> None:
    set_effective_registration()


if __name__ == "__main__":
    click_main()
