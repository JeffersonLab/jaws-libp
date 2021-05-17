"""
    Serialization and Deserialization utilities
"""

import pkgutil
from json import loads

from confluent_kafka.schema_registry import SchemaReference, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from fastavro import parse_schema

from jlab_jaws.avro.subject_schemas.entities import SimpleProducer, RegisteredAlarm, ActiveAlarm, SimpleAlarming, \
    EPICSAlarming, NoteAlarming, DisabledAlarm, FilteredAlarm, LatchedAlarm, MaskedAlarm, OnDelayedAlarm, \
    OffDelayedAlarm, ShelvedAlarm, OverriddenAlarmValue, OverriddenAlarmType, OverriddenAlarmKey, ShelvedAlarmReason
from jlab_jaws.serde.avro import AvroDeserializerWithReferences, AvroSerializerWithReferences


def _default_if_none(value, default):
    return default if value is None else value


def _unwrap_ref_tuple(ref):
    if ref is None:
        result = None
    elif type(ref) is tuple:
        result = ref[1]
    else:  # not None and not a tuple, so return as is
        result = ref
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
    def _to_dict(obj, ctx):
        return {
            "location": obj.location.name,
            "category": obj.category.name,
            "priority": obj.priority.name,
            "rationale": obj.rationale,
            "correctiveaction": obj.corrective_action,
            "pointofcontactusername": obj.point_of_contact_username,
            "latching": obj.latching,
            "filterable": obj.filterable,
            "ondelayseconds": obj.on_delay_seconds,
            "offdelayseconds": obj.off_delay_seconds,
            "maskedby": obj.masked_by,
            "screenpath": obj.screen_path,
            "class": obj.alarm_class.name,
            "producer": obj.producer
        }

    @staticmethod
    def _from_dict(values, ctx):
        return RegisteredAlarm(_unwrap_ref_tuple(values.get('location')),
                               _unwrap_ref_tuple(values.get('category')),
                               _unwrap_ref_tuple(values.get('priority')),
                               values.get('rationale'),
                               values.get('correctiveaction'),
                               values.get('pointofcontactusername'),
                               values.get('latching'),
                               values.get('filterable'),
                               values.get('ondelayseconds'),
                               values.get('offdelayseconds'),
                               values.get('maskedby'),
                               values.get('screenpath'),
                               values['class'],  # Not optional - we want key error if this is missing
                               values['producer'])  # Also not optional

    @staticmethod
    def _named_schemas():
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
    def deserializer(schema_registry_client):
        """
            Return a RegisteredAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        named_schemas = RegisteredAlarmSerde._named_schemas()

        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              RegisteredAlarmSerde._from_dict, True,
                                              named_schemas)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return a RegisteredAlarm serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        named_schemas = RegisteredAlarmSerde._named_schemas()

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/registered-alarms-value.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        class_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmClass", "alarm-class", 1)
        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [class_schema_ref, location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            RegisteredAlarmSerde._to_dict, None,
                                            named_schemas)


class ActiveAlarmSerde:
    """
        Provides ActiveAlarm serde utilities
    """

    @staticmethod
    def _to_dict(obj, ctx):
        if isinstance(obj.msg, SimpleAlarming):
            uniondict = {}
        elif isinstance(obj.msg, EPICSAlarming):
            uniondict = {"sevr": obj.msg.sevr, "stat": obj.msg.stat}
        elif isinstance(obj.msg, NoteAlarming):
            uniondict = {"note": obj.msg.note}
        else:
            print("Unknown alarming union type: {}".format(obj.msg))
            uniondict = {}

        return {
            "msg": uniondict
        }

    @staticmethod
    def _from_dict(values, ctx):
        alarmingtuple = values['msg']
        alarmingtype = alarmingtuple[0]
        alarmingdict = alarmingtuple[1]

        if alarmingtype == "org.jlab.jaws.entity.NoteAlarming":
            obj = NoteAlarming(alarmingdict['note'])
        elif alarmingtype == "org.jlab.jaws.entity.EPICSAlarming":
            obj = EPICSAlarming(alarmingdict['sevr'].name, alarmingdict['stat'].name)
        else:
            obj = SimpleAlarming()

        return ActiveAlarm(obj)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an ActiveAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                ActiveAlarmSerde._from_dict, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an ActiveAlarm serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/active-alarms-value.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, value_schema_str,
                              ActiveAlarmSerde._to_dict, None)


class OverriddenAlarmKeySerde:
    """
        Provides OverriddenAlarmKey serde utilities
    """

    @staticmethod
    def _to_dict(obj, ctx):
        return {
            "name": obj.name,
            "type": obj.type.name
        }

    @staticmethod
    def _from_dict(values, ctx):
        return OverriddenAlarmKey(values['name'], OverriddenAlarmType[values['type']])

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an OverriddenAlarmKey deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                OverriddenAlarmKeySerde._from_dict, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an OverriddenAlarmKey serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/overridden-alarms-key.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, subject_schema_str,
                              OverriddenAlarmKeySerde._to_dict, None)


class OverriddenAlarmValueSerde:
    """
        Provides OverriddenAlarmValue serde utilities
    """

    @staticmethod
    def _to_dict(obj, ctx):
        if isinstance(obj.msg, DisabledAlarm):
            uniontype = "org.jlab.jaws.entity.DisabledAlarm"
            uniondict = {"comments": obj.msg.comments}
        elif isinstance(obj.msg, FilteredAlarm):
            uniontype = "org.jlab.jaws.entity.FilteredAlarm"
            uniondict = {"filtername": obj.msg.filtername}
        elif isinstance(obj.msg, LatchedAlarm):
            uniontype = "org.jlab.jaws.entity.LatchedAlarm"
            uniondict = {}
        elif isinstance(obj.msg, MaskedAlarm):
            uniontype = "org.jlab.jaws.entity.MaskedAlarm"
            uniondict = {}
        elif isinstance(obj.msg, OnDelayedAlarm):
            uniontype = "org.jlab.jaws.entity.OnDelayedAlarm"
            uniondict = {"expiration": obj.msg.expiration}
        elif isinstance(obj.msg, OffDelayedAlarm):
            uniontype = "org.jlab.jaws.entity.OffDelayedAlarm"
            uniondict = {"expiration": obj.msg.expiration}
        elif isinstance(obj.msg, ShelvedAlarm):
            uniontype = "org.jlab.jaws.entity.ShelvedAlarm"
            uniondict = {"expiration": obj.msg.expiration, "comments": obj.msg.comments,
                         "reason": obj.msg.reason.name, "oneshot": obj.msg.oneshot}
        else:
            print("Unknown alarming union type: {}".format(obj.msg))
            uniontype = "org.jlab.jaws.entity.LatchedAlarm"
            uniondict = {}

        return {
            "msg": (uniontype, uniondict)
        }

    @staticmethod
    def _from_dict(values, ctx):
        alarmingtuple = values['msg']
        alarmingtype = alarmingtuple[0]
        alarmingdict = alarmingtuple[1]

        if alarmingtype == "org.jlab.jaws.entity.DisabledAlarm":
            obj = DisabledAlarm(alarmingdict['comments'])
        elif alarmingtype == "org.jlab.jaws.entity.FilteredAlarm":
            obj = FilteredAlarm(alarmingdict['filtername'])
        elif alarmingtype == "org.jlab.jaws.entity.LatchedAlarm":
            obj = LatchedAlarm()
        elif alarmingtype == "org.jlab.jaws.entity.MaskedAlarm":
            obj = MaskedAlarm()
        elif alarmingtype == "org.jlab.jaws.entity.OnDelayedAlarm":
            obj = OnDelayedAlarm(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.OffDelayedAlarm":
            obj = OffDelayedAlarm(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.ShelvedAlarm":
            obj = ShelvedAlarm(alarmingdict['expiration'], alarmingdict['comments'],
                               ShelvedAlarmReason[alarmingdict['reason']], alarmingdict['oneshot'])
        else:
            print("Unknown alarming type: {}".format(values['msg']))
            obj = LatchedAlarm()

        return OverriddenAlarmValue(obj)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an OverriddenAlarmValue deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                OverriddenAlarmValueSerde._from_dict, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an OverriddenAlarmValue serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/overridden-alarms-value.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, subject_schema_str,
                              OverriddenAlarmValueSerde._to_dict, None)