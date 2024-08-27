from click.testing import CliRunner
from jaws_libp.avro.serde import SystemSerde
from jaws_libp.entities import AlarmSystem
from jaws_libp.scripts.client.list_systems import list_systems
from jaws_libp.scripts.client.set_system import set_system


def test_system():
    system = 'EXAMPLE_SYSTEM'
    team = "Testers"
    value = AlarmSystem(team)
    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_system, [system, '--team', team])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_systems, ['--export'])
        assert result.exit_code == 0

        system_serde = SystemSerde(None)
        assert result.output == system + '=' + system_serde.to_json(value) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_system, [system, '--unset'])
        assert result.exit_code == 0
