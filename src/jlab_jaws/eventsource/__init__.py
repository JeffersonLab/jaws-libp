"""
   Code to facilitate Event Sourcing.

   See Also:
       - `Storing Data in Kafka <https://www.confluent.io/blog/okay-store-data-apache-kafka/>`_
       - `Fowler on Event Sourcing <ttps://martinfowler.com/eaaDev/EventSourcing.html>`_
"""
import logging

from .listener import EventSourceListener
from .table import EventSourceTable
from .cached_table import CachedTable

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


def log_exception(e):
    logger.exception(e)
