from click import Choice
from click.testing import CliRunner
from jaws_libp.avro.serde import ActionSerde
from jaws_libp.entities import AlarmAction, AlarmPriority
from jaws_libp.scripts.client.list_actions import list_actions
from jaws_libp.scripts.client.set_action import set_action


def test_action():
    category = 'EXAMPLE_CATEGORY'
    action_name = "TESTING_ACTION"
    action = AlarmAction(category, AlarmPriority.P3_MINOR, 'TESTING_RATIONALE',
                             'TESTING_CORRECTIVE_ACTION', True, True, None, None)

    runner = CliRunner()

    set_action.params[2].type = Choice([category])

    try:
        # Set
        result = runner.invoke(set_action, [action_name,
                                           '--category', action.category,
                                           '--priority', action.priority.name,
                                           '--rationale', action.rationale,
                                           '--correctiveaction', action.corrective_action])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_actions, ['--export'])
        assert result.exit_code == 0

        action_serde = ActionSerde(None)
        assert result.output == action_name + '=' + action_serde.to_json(action) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_action, [action_name, '--unset'])
        assert result.exit_code == 0
