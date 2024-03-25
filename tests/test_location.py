import pytest

from click.testing import CliRunner
from jaws_libp.avro.serde import LocationSerde
from jaws_libp.entities import AlarmLocation
from jaws_libp.scripts.client.list_locations import list_locations
from jaws_libp.scripts.client.set_location import set_location


@pytest.mark.integration
def test_location():
    location1_name = "LOCATION1"
    location1 = AlarmLocation(None)

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_location, [location1_name])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_locations, ['--export'])
        assert result.exit_code == 0

        location_serde = LocationSerde(None)
        assert result.output == location1_name + '=' + location_serde.to_json(location1) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_location, [location1_name, '--unset'])
        assert result.exit_code == 0


@pytest.mark.integration
def test_location_with_parent():
    location1_name = "LOCATION1"
    parent = "LOCATION2"
    location1 = AlarmLocation(parent)

    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_location, [location1_name, '--parent', parent])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_locations, ['--export'])
        assert result.exit_code == 0

        location_serde = LocationSerde(None)
        assert result.output == location1_name + '=' + location_serde.to_json(location1) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_location, [location1_name, '--unset'])
        assert result.exit_code == 0
