from jaws_libp.avro.serde import AlarmSerde
from jaws_libp.entities import UnionEncoding


def test_alarm_serde():

    serde = AlarmSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)

    expected_json = '{"action": "base", "location": ["INJ"], "managedby": null, "maskedby": null, "screencommand": "/", "source": {' \
                    '"org.jlab.jaws.entity.EPICSSource": {"pv": "channel1"}}}'

    entity = serde.from_json(expected_json)

    actual_json = serde.to_json(entity)

    print(expected_json)
    print('vs')
    print(actual_json)

    assert actual_json == expected_json
