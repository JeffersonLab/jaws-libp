from jaws_libp.avro.serde import InstanceSerde
from jaws_libp.entities import UnionEncoding


def test_instance_serde():

    serde = InstanceSerde(None, union_encoding=UnionEncoding.DICT_WITH_TYPE)

    expected_json = '{"class": "base", "location": ["INJ"], "maskedby": null, "producer": {' \
                    '"org.jlab.jaws.entity.EPICSProducer": {"pv": "channel1"}}, "screencommand": "/"}'

    entity = serde.from_json(expected_json)

    actual_json = serde.to_json(entity)

    print(expected_json)
    print('vs')
    print(actual_json)

    assert actual_json == expected_json
