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
    OffDelayedAlarm, ShelvedAlarm, OverriddenAlarmValue
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
    def _to_dict(obj, ctx):
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
            "screenpath": obj.screen_path,
            "class": obj.alarm_class,
            "producer": obj.producer
        }

    @staticmethod
    def _from_dict(values, ctx):
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
            obj = EPICSAlarming(alarmingdict['sevr'], alarmingdict['stat'])
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


class OverriddenAlarmSerde:
    """
        Provides OverriddenAlarm serde utilities
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
                         "reason": obj.msg.reason, "oneshot": obj.msg.oneshot}
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
                               alarmingdict['reason'], alarmingdict['oneshot'])
        else:
            print("Unknown alarming type: {}".format(values['msg']))
            obj = LatchedAlarm()

        return OverriddenAlarmValue(obj)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an OverriddenAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                OverriddenAlarmSerde._from_dict, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an OverriddenAlarm serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/overridden-alarms-value.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, value_schema_str,
                              OverriddenAlarmSerde._to_dict, None)