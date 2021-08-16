"""
    Serialization and Deserialization utilities
"""

import pkgutil
from json import loads

from confluent_kafka.schema_registry import SchemaReference, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from fastavro import parse_schema

from jlab_jaws.avro.referenced_schemas.entities import AlarmLocation, AlarmCategory, AlarmPriority
from jlab_jaws.avro.subject_schemas.entities import SimpleProducer, RegisteredAlarm, ActiveAlarm, SimpleAlarming, \
    EPICSAlarming, NoteAlarming, DisabledAlarm, FilteredAlarm, LatchedAlarm, MaskedAlarm, OnDelayedAlarm, \
    OffDelayedAlarm, ShelvedAlarm, OverriddenAlarmValue, OverriddenAlarmType, OverriddenAlarmKey, ShelvedAlarmReason, \
    EPICSSEVR, EPICSSTAT, UnionEncoding, CALCProducer, EPICSProducer, RegisteredClass, \
    AlarmStateValue, AlarmStateEnum
from jlab_jaws.serde.avro import AvroDeserializerWithReferences, AvroSerializerWithReferences


def _unwrap_enum(value, enum_class):
    """
    When instantiating classes using _from_dict often a variable intended to be an enum is encountered that
    may actually be a String, a Tuple, or an Enum so this function attempts to convert to an Enum if needed.

    A tuple is allowed due to fastavro supporting tuples for complex types.

    :param value: The value to massage into the correct type
    :param enum_class: Enum class to instantiate
    :return: A value likely as an Enum or None
    """

    if value is None:
        result = None
    elif type(value) is tuple:
        result = enum_class[value[1]]
    elif type(value) is str:
        result = enum_class[value]
    else:  # return as is (hopefully already an Enum)
        result = value
    return result


class RegisteredClassSerde:
    """
        Provides RegisteredClass serde utilities
    """

    @staticmethod
    def setClassDefaults(alarm: RegisteredAlarm, alarm_class: RegisteredClass):
        """
        Merge a RegisteredClass into a RegisteredAlarm (apply class default values).

        :param alarm: The RegisteredAlarm
        :param alarm_class: The RegisteredClass
        """
        if alarm.priority is None:
            alarm.priority = alarm_class.priority

        if alarm.category is None:
            alarm.category = alarm_class.category

        if alarm.location is None:
            alarm.location = alarm_class.location

        if alarm.corrective_action is None:
            alarm.corrective_action = alarm_class.corrective_action

        if alarm.filterable is None:
            alarm.filterable = alarm_class.filterable

        if alarm.latching is None:
            alarm.latching = alarm_class.latching

        if alarm.masked_by is None:
            alarm.masked_by = alarm_class.masked_by

        if alarm.off_delay_seconds is None:
            alarm.off_delay_seconds = alarm_class.off_delay_seconds

        if alarm.on_delay_seconds is None:
            alarm.on_delay_seconds = alarm_class.on_delay_seconds

        if alarm.point_of_contact_username is None:
            alarm.point_of_contact_username = alarm_class.point_of_contact_username

        if alarm.rationale is None:
            alarm.rationale = alarm_class.rationale

        if alarm.screen_path is None:
            alarm.screen_path = alarm_class.screen_path

    @staticmethod
    def to_dict(obj):
        """
        Converts a RegisteredClass to a dict.

        :param obj: The RegisteredClass
        :return: A dict
        """

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
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return RegisteredClassSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to a RegisteredClass.

        :param the_dict: The dict
        :return: The RegisteredClass
        """
        return RegisteredClass(_unwrap_enum(the_dict.get('location'), AlarmLocation),
                               _unwrap_enum(the_dict.get('category'), AlarmCategory),
                               _unwrap_enum(the_dict.get('priority'), AlarmPriority),
                               the_dict.get('rationale'),
                               the_dict.get('correctiveaction'),
                               the_dict.get('pointofcontactusername'),
                               the_dict.get('latching'),
                               the_dict.get('filterable'),
                               the_dict.get('ondelayseconds'),
                               the_dict.get('offdelayseconds'),
                               the_dict.get('maskedby'),
                               the_dict.get('screenpath'))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return RegisteredClassSerde.from_dict(the_dict)

    @staticmethod
    def _named_schemas():
        location_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmLocation.avsc")
        location_schema_str = location_bytes.decode('utf-8')

        category_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmCategory.avsc")
        category_schema_str = category_bytes.decode('utf-8')

        priority_bytes = pkgutil.get_data("jlab_jaws", "avro/referenced_schemas/AlarmPriority.avsc")
        priority_schema_str = priority_bytes.decode('utf-8')

        named_schemas = {}
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
            Return a RegisteredClass deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              RegisteredClassSerde._from_dict_with_ctx, True,
                                              RegisteredClassSerde._named_schemas())

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return a RegisteredClass serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        value_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/registered-classes-value.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            RegisteredClassSerde._to_dict_with_ctx, None,
                                            RegisteredClassSerde._named_schemas())


class RegisteredAlarmSerde:
    """
        Provides RegisteredAlarm serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts a RegisteredAlarm to a dict.

        :param obj: The RegisteredAlarm
        :param union_encoding: How the union should be encoded
        :return: A dict
        """

        if isinstance(obj.producer, SimpleProducer):
            uniontype = "org.jlab.jaws.entity.SimpleProducer"
            uniondict = {}
        elif isinstance(obj.producer, EPICSProducer):
            uniontype = "org.jlab.jaws.entity.EPICSProducer"
            uniondict = {"pv": obj.producer.pv}
        elif isinstance(obj.producer, CALCProducer):
            uniontype = "org.jlab.jaws.entity.CALCProducer"
            uniondict = {"expression": obj.producer.expression}
        else:
            raise Exception("Unknown alarming union type: {}".format(obj.producer))

        if union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "location": obj.location.name if obj.location is not None else None,
            "category": obj.category.name if obj.category is not None else None,
            "priority": obj.priority.name if obj.priority is not None else None,
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
            "producer": union
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return RegisteredAlarmSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to a RegisteredAlarm.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param the_dict: The dict
        :return: The RegisteredAlarm
        """

        unionobj = the_dict['producer']

        if type(unionobj) is tuple:
            uniontype = unionobj[0]
            uniondict = unionobj[1]
        elif type(unionobj is dict):
            value = next(iter(unionobj.items()))
            uniontype = value[0]
            uniondict = value[1]
        else:
            raise Exception("Unsupported union encoding")

        if uniontype == "org.jlab.jaws.entity.CalcProducer":
            producer = CALCProducer(uniondict['expression'])
        elif uniontype == "org.jlab.jaws.entity.EPICSProducer":
            producer = EPICSProducer(uniondict['pv'])
        else:
            producer = SimpleProducer()

        return RegisteredAlarm(_unwrap_enum(the_dict.get('location'), AlarmLocation),
                               _unwrap_enum(the_dict.get('category'), AlarmCategory),
                               _unwrap_enum(the_dict.get('priority'), AlarmPriority),
                               the_dict.get('rationale'),
                               the_dict.get('correctiveaction'),
                               the_dict.get('pointofcontactusername'),
                               the_dict.get('latching'),
                               the_dict.get('filterable'),
                               the_dict.get('ondelayseconds'),
                               the_dict.get('offdelayseconds'),
                               the_dict.get('maskedby'),
                               the_dict.get('screenpath'),
                               the_dict.get('class'),
                               producer)  # Also not optional

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return RegisteredAlarmSerde.from_dict(the_dict)

    @staticmethod
    def _named_schemas():
        named_schemas = RegisteredClassSerde._named_schemas()

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
                                              RegisteredAlarmSerde._from_dict_with_ctx, True,
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

        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            RegisteredAlarmSerde._to_dict_with_ctx, None,
                                            named_schemas)


class ActiveAlarmSerde:
    """
        Provides ActiveAlarm serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an ActiveAlarmValue to a dict.

        :param obj: The ActiveAlarmValue
        :param union_encoding: How the union should be encoded
        :return: A dict
        """
        if isinstance(obj.msg, SimpleAlarming):
            uniontype = "org.jlab.jaws.entity.SimpleAlarming"
            uniondict = {}
        elif isinstance(obj.msg, EPICSAlarming):
            uniontype = "org.jlab.jaws.entity.EPICSAlarming"
            uniondict = {"sevr": obj.msg.sevr.name, "stat": obj.msg.stat.name}
        elif isinstance(obj.msg, NoteAlarming):
            uniontype = "org.jlab.jaws.entity.NoteAlarming"
            uniondict = {"note": obj.msg.note}
        else:
            raise Exception("Unknown alarming union type: {}".format(obj.msg))

        if union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "msg": union
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return ActiveAlarmSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an ActiveAlarm.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param the_dict: The dict
        :return: The ActiveAlarm
        """
        unionobj = the_dict['msg']

        if type(unionobj) is tuple:
            uniontype = unionobj[0]
            uniondict = unionobj[1]
        elif type(unionobj is dict):
            value = next(iter(unionobj.items()))
            uniontype = value[0]
            uniondict = value[1]
        else:
            raise Exception("Unsupported union encoding")

        if uniontype == "org.jlab.jaws.entity.NoteAlarming":
            obj = NoteAlarming(uniondict['note'])
        elif uniontype == "org.jlab.jaws.entity.EPICSAlarming":
            obj = EPICSAlarming(_unwrap_enum(uniondict['sevr'], EPICSSEVR), _unwrap_enum(uniondict['stat'],
                                                                                         EPICSSTAT))
        else:
            obj = SimpleAlarming()

        return ActiveAlarm(obj)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return ActiveAlarmSerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an ActiveAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                ActiveAlarmSerde._from_dict_with_ctx, True)

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
                              ActiveAlarmSerde._to_dict_with_ctx, None)


class OverriddenAlarmKeySerde:
    """
        Provides OverriddenAlarmKey serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts an OverriddenAlarmKey to a dict.

        :param obj: The OverriddenAlarmKey
        :return: A dict
        """
        return {
            "name": obj.name,
            "type": obj.type.name
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return OverriddenAlarmKeySerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an OverriddenAlarmKey.

        :param the_dict: The dict
        :return: The OverriddenAlarmKey
        """
        return OverriddenAlarmKey(the_dict['name'], _unwrap_enum(the_dict['type'], OverriddenAlarmType))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return OverriddenAlarmKeySerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an OverriddenAlarmKey deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                OverriddenAlarmKeySerde._from_dict_with_ctx, True)

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
                              OverriddenAlarmKeySerde._to_dict_with_ctx, None)


class OverriddenAlarmValueSerde:
    """
        Provides OverriddenAlarmValue serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an OverriddenAlarmValue to a dict.

        :param obj: The OverriddenAlarmValue
        :param union_encoding: How the union should be encoded
        :return: A dict
        """
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

        if union_encoding is UnionEncoding.TUPLE:
            union = (uniontype, uniondict)
        elif union_encoding is UnionEncoding.DICT_WITH_TYPE:
            union = {uniontype: uniondict}
        else:
            union = uniondict

        return {
            "msg": union
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return OverriddenAlarmValueSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an OverriddenAlarmValue.

        Note: Both UnionEncoding.TUPLE and UnionEncoding.DICT_WITH_TYPE are supported,
        but UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported at this time
        because I'm lazy and not going to try to guess what type is in your union.

        :param the_dict: The dict (or maybe it's a duck)
        :return: The OverriddenAlarmValue
        """
        alarmingobj = the_dict['msg']

        if type(alarmingobj) is tuple:
            alarmingtype = alarmingobj[0]
            alarmingdict = alarmingobj[1]
        elif type(alarmingobj is dict):
            value = next(iter(alarmingobj.items()))
            alarmingtype = value[0]
            alarmingdict = value[1]
        else:
            raise Exception("Unsupported union encoding")

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
                               _unwrap_enum(alarmingdict['reason'], ShelvedAlarmReason), alarmingdict['oneshot'])
        else:
            print("Unknown alarming type: {}".format(the_dict['msg']))
            obj = LatchedAlarm()

        return OverriddenAlarmValue(obj)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return OverriddenAlarmValueSerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an OverriddenAlarmValue deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                OverriddenAlarmValueSerde._from_dict_with_ctx, True)

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
                              OverriddenAlarmValueSerde._to_dict_with_ctx, None)


class AlarmStateSerde:
    """
        Provides AlarmState serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts AlarmState to a dict.

        :param obj: The AlarmStateValue
        :return: A dict
        """
        return {
            "type": obj.type.name
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return AlarmStateSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to AlarmState.

        :param the_dict: The dict
        :return: The AlarmStateValue
        """
        return AlarmStateValue(_unwrap_enum(the_dict['type'], AlarmStateEnum))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return AlarmStateSerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmStateValue deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                AlarmStateSerde._from_dict_with_ctx, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmStateValue serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/subject_schemas/alarm-state-value.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, subject_schema_str,
                              AlarmStateSerde._to_dict_with_ctx, None)