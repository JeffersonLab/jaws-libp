from click.testing import CliRunner
from jaws_libp.avro.serde import ViewpointSerde
from jaws_libp.entities import AlarmViewpoint
from jaws_libp.scripts.client.list_viewpoints import list_viewpoints
from jaws_libp.scripts.client.set_viewpoint import set_viewpoint


def test_viewpoint():
    viewpoint = 'EXAMPLE_VIEWPOINT'
    location = ["Loc1", "Loc2"]
    value = AlarmViewpoint(location, [], [])
    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_viewpoint, [viewpoint, '-l', location[0], '-l', location[1]])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_viewpoints, ['--export'])
        assert result.exit_code == 0

        viewpoint_serde = ViewpointSerde(None)
        assert result.output == viewpoint + '=' + viewpoint_serde.to_json(value) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_viewpoint, [viewpoint, '--unset'])
        assert result.exit_code == 0
