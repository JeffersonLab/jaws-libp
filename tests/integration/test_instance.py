from click import Choice
from click.testing import CliRunner
from jaws_libp.avro.serde import InstanceSerde
from jaws_libp.entities import AlarmInstance, Source, UnionEncoding, EPICSSource
from jaws_libp.scripts.client.list_instances import list_instances
from jaws_libp.scripts.client.set_instance import set_instance


def test_simple_instance():
    alarm_name = "alarm1"
    action_name = "TESTING_ACTION"
    location = ["LOCATION1"]
    source = Source()
    managed_by = None
    masked_by = None
    screen_command = None
    instance = AlarmInstance(action_name, source, location, managed_by, masked_by, screen_command)

    runner = CliRunner()

    set_instance.params[5].type = Choice(location)

    try:
        # Set
        result = runner.invoke(set_instance, [alarm_name,
                                              '--action', action_name,
                                              '--location', location[0]])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_instances, ['--export'])
        assert result.exit_code == 0

        instance_serde = InstanceSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)
        assert result.output == alarm_name + '=' + instance_serde.to_json(instance) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_instance, [alarm_name, '--unset'])
        assert result.exit_code == 0


def test_epics_instance():
    alarm_name = "alarm1"
    action_name = "TESTING_ACTION"
    location = ["LOCATION1"]
    source = EPICSSource("channel1")
    managed_by = None
    masked_by = None
    screen_command = None
    instance = AlarmInstance(action_name, source, location, managed_by, masked_by, screen_command)

    runner = CliRunner()

    set_instance.params[5].type = Choice(location)

    try:
        # Set
        result = runner.invoke(set_instance, [alarm_name,
                                              '--pv', source.pv,
                                              '--action', action_name,
                                              '--location', location[0]])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_instances, ['--export'])
        assert result.exit_code == 0

        instance_serde = InstanceSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)
        assert result.output == alarm_name + '=' + instance_serde.to_json(instance) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_instance, [alarm_name, '--unset'])
        assert result.exit_code == 0
