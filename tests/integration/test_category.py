from click.testing import CliRunner
from jaws_libp.avro.serde import CategorySerde
from jaws_libp.entities import AlarmCategory
from jaws_libp.scripts.client.list_systems import list_categories
from jaws_libp.scripts.client.set_system import set_category


def test_category():
    category = 'EXAMPLE_CATEGORY'
    team = "Testers"
    value = AlarmCategory(team)
    runner = CliRunner()

    try:
        # Set
        result = runner.invoke(set_category, [category, '--team', team])
        assert result.exit_code == 0

        # Get
        result = runner.invoke(list_categories, ['--export'])
        assert result.exit_code == 0

        category_serde = CategorySerde(None)
        assert result.output == category + '=' + category_serde.to_json(value) + '\n'

    finally:
        # Clear
        result = runner.invoke(set_category, [category, '--unset'])
        assert result.exit_code == 0
