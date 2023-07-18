import pytest

from jaws_libp.scripts.broker.list_topics import list_topics
from jaws_libp.scripts.broker.create_topics import create_topics
from jaws_libp.scripts.registry.list_schemas import list_schemas
from jaws_libp.scripts.registry.create_schemas import create_schemas

@pytest.fixture(scope="module", autouse=True)
def setupKafkaTopicsIfNotExists():
    list_topics()
    create_topics()

@pytest.fixture(scope="module", autouse=True)
def setupRegistrySchemasIfNotExists():
    list_schemas()
    create_schemas()
