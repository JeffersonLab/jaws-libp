#!/usr/bin/env python3

"""
    Lists the alarm actions (class of alarm).

    **Note**: With the ``--export`` option you can export a file that can be imported by ``set_action --file``.
"""

import click
from click import Choice

from ...console import CategoryConsoleConsumer, ActionConsoleConsumer


# pylint: disable=too-few-public-methods
class CategoryFilter:
    """
        Filter category messages
    """
    def __init__(self, category):
        self._category = category

    # pylint: disable=unused-argument
    def filter_if(self, key, value):
        """
            Filter out messages unless the category matches the provided category
        """
        return self._category is None or (value is not None and self._category == value.category)


# pylint: disable=missing-function-docstring,no-value-for-parameter
@click.command()
@click.option('--monitor', is_flag=True, help="Monitor indefinitely")
@click.option('--nometa', is_flag=True, help="Exclude audit headers and timestamp")
@click.option('--export', is_flag=True, help="Dump records in AVRO JSON format")
@click.option('--category', type=click.Choice([]),
              help="Only show registered alarms in the specified category (Options queried on-demand from "
                   "alarm-categories topic)")
def list_actions(monitor, nometa, export, category) -> None:
    consumer = ActionConsoleConsumer('list_actions.py')

    filter_obj = CategoryFilter(category)

    consumer.consume_then_done(monitor, nometa, export, filter_obj.filter_if)


def click_main() -> None:
    cat_consumer = CategoryConsoleConsumer('list_actions.py')
    categories = cat_consumer.get_keys_then_done()

    list_actions.params[3].type = Choice(categories)

    list_actions()


if __name__ == "__main__":
    click_main()
