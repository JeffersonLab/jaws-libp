from click import Choice
from click.testing import CliRunner
from jaws_libp.avro.serde import AlarmSerde
from jaws_libp.entities import Alarm, Source, UnionEncoding, EPICSSource
from jaws_libp.scripts.client.list_alarms import list_alarms
from jaws_libp.scripts.client.set_alarm import set_alarm


def test_simple_alarm():
    alarm_name = "alarm1"
    action_name = "TESTING_ACTION"
    location = ["LOCATION1"]
    source = Source()
    managed_by = None
    masked_by = None
    screen_command = None
    alarm = Alarm(action_name, source, location, managed_by, masked_by, screen_command)

    runner = CliRunner()

    set_alarm.params[5].type = Choice(location)

    try:
        # Set
        result = runner.invoke(set_alarm, [alarm_name,
                                              '--action', action_name,
                                              '--location', location[0]])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_alarms, ['--export'])
        assert result.exit_code == 0

        alarm_serde = AlarmSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)
        assert result.output == alarm_name + '=' + alarm_serde.to_json(alarm) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_alarm, [alarm_name, '--unset'])
        assert result.exit_code == 0


def test_epics_alarm():
    alarm_name = "alarm1"
    action_name = "TESTING_ACTION"
    location = ["LOCATION1"]
    source = EPICSSource("channel1")
    managed_by = None
    masked_by = None
    screen_command = None
    alarm = Alarm(action_name, source, location, managed_by, masked_by, screen_command)

    runner = CliRunner()

    set_alarm.params[5].type = Choice(location)

    try:
        # Set
        result = runner.invoke(set_alarm, [alarm_name,
                                              '--pv', source.pv,
                                              '--action', action_name,
                                              '--location', location[0]])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_alarms, ['--export'])
        assert result.exit_code == 0

        instance_serde = AlarmSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)
        assert result.output == alarm_name + '=' + instance_serde.to_json(alarm) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_alarm, [alarm_name, '--unset'])
        assert result.exit_code == 0
