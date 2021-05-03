"""
    Serialization and Deserialization utilities
"""

import pkgutil
from json import loads

from confluent_kafka.schema_registry import SchemaReference, Schema
from fastavro import parse_schema

from jlab_jaws.avro.subject_schemas.entities import SimpleProducer, RegisteredAlarm
from jlab_jaws.serde.avro import AvroDeserializerWithReferences, AvroSerializerWithReferences


def _default_if_none(value, default):
    return default if value is None else value


def _unwrap_ref_tuple(ref):
    if ref is not None:
        result = ref[1]
    else:
        result = None
    return result


class RegisteredAlarmSerde:
    """
        Provides RegisteredAlarm serde utilities
    """
    # TODO: Defaults should come from registered-class
    defaults = {
        "location": "CEBAF",
        "category": "RF",
        "priority": "P1",
        "rationale": "Timely operator action is required",
        "correctiveaction": "Call Department Leadership",
        "pointofcontactusername": "erb",
        "latching": True,
        "filterable": True,
        "ondelayseconds": None,
        "offdelayseconds": None,
        "maskedby": None,
        "screenpath": None,
        "class": "Base_Class",
        "producer": SimpleProducer()
    }

    @staticmethod
    def _to_dict_registered_alarm(obj, ctx):
        return {
            "location": obj.location,
            "category": obj.category,
            "priority": obj.priority,
            "rationale": obj.rationale,
            "correctiveaction": obj.corrective_action,
            "pointofcontactusername": obj.point_of_contact_username,
            "latching": obj.latching,
            "filterable": obj.filterable,
            "ondelayseconds": obj.on_delay_seconds,
            "offdelayseconds": obj.off_delay_seconds,
            "maskedby": obj.masked_by,
            "screenpath": obj.screenpath,
            "class": obj.alarm_class,
            "producer": obj.producer
        }

    @staticmethod
    def _from_dict_registered_alarm(values, ctx):
        return RegisteredAlarm(_default_if_none(_unwrap_ref_tuple(values['location']),
                                                RegisteredAlarmSerde.defaults['location']),
                               _default_if_none(_unwrap_ref_tuple(values['category']),
                                                RegisteredAlarmSerde.defaults['category']),
                               _default_if_none(_unwrap_ref_tuple(values['priority']),
                                                RegisteredAlarmSerde.defaults['priority']),
                               _default_if_none(values['rationale'],
                                                RegisteredAlarmSerde.defaults['rationale']),
                               _default_if_none(values['correctiveaction'],
                                                RegisteredAlarmSerde.defaults['correctiveaction']),
                               _default_if_none(values['pointofcontactusername'],
                                                RegisteredAlarmSerde.defaults['pointofcontactusername']),
                               _default_if_none(values['latching'],
                                                RegisteredAlarmSerde.defaults['latching']),
                               _default_if_none(values['filterable'],
                                                RegisteredAlarmSerde.defaults['filterable']),
                               _default_if_none(values['ondelayseconds'],
                                                RegisteredAlarmSerde.defaults['ondelayseconds']),
                               _default_if_none(values['offdelayseconds'],
                                                RegisteredAlarmSerde.defaults['offdelayseconds']),
                               _default_if_none(values['maskedby'],
                                                RegisteredAlarmSerde.defaults['maskedby']),
                               _default_if_none(values['screenpath'],
                                                RegisteredAlarmSerde.defaults['screenpath']),
                               _default_if_none(values['class'],
                                                RegisteredAlarmSerde.defaults['class']),
                               _default_if_none(values['producer'],
                                                RegisteredAlarmSerde.defaults['producer']))

    @staticmethod
    def _get_registered_alarm_named_schemas():
        class_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmClass.avsc")
        class_schema_str = class_bytes.decode('utf-8')

        location_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmLocation.avsc")
        location_schema_str = location_bytes.decode('utf-8')

        category_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmCategory.avsc")
        category_schema_str = category_bytes.decode('utf-8')

        priority_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmPriority.avsc")
        priority_schema_str = priority_bytes.decode('utf-8')

        named_schemas = {}
        ref_dict = loads(class_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(location_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(category_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(priority_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def get_registered_alarm_deserializer(schema_registry_client):
        """
            Return a RegisteredAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        named_schemas = RegisteredAlarmSerde._get_registered_alarm_named_schemas()

        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              RegisteredAlarmSerde._from_dict_registered_alarm, True,
                                              named_schemas)

    @staticmethod
    def get_registered_alarm_serializer(schema_registry_client):
        """
            Return a RegisteredAlarm serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        named_schemas = RegisteredAlarmSerde._get_registered_alarm_named_schemas()

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/registered-alarms-value.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        class_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmClass", "alarm-class", 1)
        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [class_schema_ref, location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            RegisteredAlarmSerde._to_dict_registered_alarm, None,
                                            named_schemas)
