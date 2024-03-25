import pytest

from jaws_libp.scripts.broker.list_topics import list_topics
from jaws_libp.scripts.broker.create_topics import create_topics
from jaws_libp.scripts.registry.list_schemas import list_schemas
from jaws_libp.scripts.registry.create_schemas import create_schemas

@pytest.fixture(scope="module", autouse=True)
def setupKafkaTopicsIfNotExists(request):
    if request.node.get_closest_marker("integration") is not None:
        list_topics()
        create_topics()

@pytest.fixture(scope="module", autouse=True)
def setupRegistrySchemasIfNotExists(request):
    if request.node.get_closest_marker("integration") is not None:
        list_schemas()
        create_schemas()
