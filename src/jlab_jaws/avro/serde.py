"""
    Serialization and Deserialization utilities
"""

import pkgutil
from json import loads

from confluent_kafka.schema_registry import SchemaReference, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from fastavro import parse_schema

from jlab_jaws.avro.entities import AlarmLocation, AlarmCategory, AlarmPriority
from jlab_jaws.avro.entities import SimpleProducer, AlarmRegistration, AlarmActivationUnion, SimpleAlarming, \
    EPICSAlarming, NoteAlarming, DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, \
    OffDelayedOverride, ShelvedOverride, AlarmOverrideUnion, OverriddenAlarmType, AlarmOverrideKey, ShelvedReason, \
    EPICSSEVR, EPICSSTAT, UnionEncoding, CALCProducer, EPICSProducer, AlarmClass, \
    Alarm, AlarmStateEnum
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


class AlarmClassSerde:
    """
        Provides AlarmClass serde utilities
    """

    @staticmethod
    def setClassDefaults(registration: AlarmRegistration, alarm_class: AlarmClass):
        """
        Merge an AlarmClass into a AlarmRegistration (apply class default values).

        :param registration: The AlarmRegistration
        :param alarm_class: The AlarmClass
        """
        if registration.priority is None:
            registration.priority = alarm_class.priority

        if registration.category is None:
            registration.category = alarm_class.category

        if registration.location is None:
            registration.location = alarm_class.location

        if registration.corrective_action is None:
            registration.corrective_action = alarm_class.corrective_action

        if registration.filterable is None:
            registration.filterable = alarm_class.filterable

        if registration.latching is None:
            registration.latching = alarm_class.latching

        if registration.masked_by is None:
            registration.masked_by = alarm_class.masked_by

        if registration.off_delay_seconds is None:
            registration.off_delay_seconds = alarm_class.off_delay_seconds

        if registration.on_delay_seconds is None:
            registration.on_delay_seconds = alarm_class.on_delay_seconds

        if registration.point_of_contact_username is None:
            registration.point_of_contact_username = alarm_class.point_of_contact_username

        if registration.rationale is None:
            registration.rationale = alarm_class.rationale

        if registration.screen_path is None:
            registration.screen_path = alarm_class.screen_path

    @staticmethod
    def to_dict(obj):
        """
        Converts an AlarmClass to a dict.

        :param obj: The AlarmClass
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
        return AlarmClassSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmClass.

        :param the_dict: The dict
        :return: The AlarmClass
        """
        return AlarmClass(_unwrap_enum(the_dict.get('location'), AlarmLocation),
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
        return AlarmClassSerde.from_dict(the_dict)

    @staticmethod
    def _named_schemas():
        location_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmLocation.avsc")
        location_schema_str = location_bytes.decode('utf-8')

        category_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmCategory.avsc")
        category_schema_str = category_bytes.decode('utf-8')

        priority_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmPriority.avsc")
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
            Return an AlarmClass deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              AlarmClassSerde._from_dict_with_ctx, True,
                                              AlarmClassSerde._named_schemas())

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmClass serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        value_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmClass.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmClassSerde._to_dict_with_ctx, None,
                                            AlarmClassSerde._named_schemas())


class AlarmRegistrationSerde:
    """
        Provides AlarmRegistration serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an AlarmRegistration to a dict.

        :param obj: The AlarmRegistration
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
        return AlarmRegistrationSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmRegistration.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param the_dict: The dict
        :return: The AlarmRegistration
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

        return AlarmRegistration(_unwrap_enum(the_dict.get('location'), AlarmLocation),
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
        return AlarmRegistrationSerde.from_dict(the_dict)

    @staticmethod
    def _named_schemas():
        named_schemas = AlarmClassSerde._named_schemas()

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmRegistration deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        named_schemas = AlarmRegistrationSerde._named_schemas()

        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              AlarmRegistrationSerde._from_dict_with_ctx, True,
                                              named_schemas)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmRegistration serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        named_schemas = AlarmRegistrationSerde._named_schemas()

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmRegistration.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        schema = Schema(value_schema_str, "AVRO",
                        [location_schema_ref, category_schema_ref, priority_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmRegistrationSerde._to_dict_with_ctx, None,
                                            named_schemas)


class AlarmActivationUnionSerde:
    """
        Provides AlarmActivationUnion serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an AlarmActivationUnion to a dict.

        :param obj: The AlarmActivationUnion
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
        return AlarmActivationUnionSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmActivationUnion.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param the_dict: The dict
        :return: The AlarmActivationUnion
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

        return AlarmActivationUnion(obj)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return AlarmActivationUnionSerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmActivationUnion deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                AlarmActivationUnionSerde._from_dict_with_ctx, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmActivationUnion serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        value_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmActivationUnion.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, value_schema_str,
                              AlarmActivationUnionSerde._to_dict_with_ctx, None)


class AlarmOverrideKeySerde:
    """
        Provides AlarmOverrideKey serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts an AlarmOverrideKey to a dict.

        :param obj: The AlarmOverrideKey
        :return: A dict
        """
        return {
            "name": obj.name,
            "type": obj.type.name
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return AlarmOverrideKeySerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmOverrideKey.

        :param the_dict: The dict
        :return: The AlarmOverrideKey
        """
        return AlarmOverrideKey(the_dict['name'], _unwrap_enum(the_dict['type'], OverriddenAlarmType))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return AlarmOverrideKeySerde.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmOverrideKey deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                AlarmOverrideKeySerde._from_dict_with_ctx, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmOverrideKey serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideKey.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, subject_schema_str,
                              AlarmOverrideKeySerde._to_dict_with_ctx, None)


class AlarmOverrideUnionSerde:
    """
        Provides AlarmOverrideUnion serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an AlarmOverrideUnion to a dict.

        :param obj: The AlarmOverrideUnion
        :param union_encoding: How the union should be encoded
        :return: A dict
        """
        if isinstance(obj.msg, DisabledOverride):
            uniontype = "org.jlab.jaws.entity.DisabledOverride"
            uniondict = {"comments": obj.msg.comments}
        elif isinstance(obj.msg, FilteredOverride):
            uniontype = "org.jlab.jaws.entity.FilteredOverride"
            uniondict = {"filtername": obj.msg.filtername}
        elif isinstance(obj.msg, LatchedOverride):
            uniontype = "org.jlab.jaws.entity.LatchedOverride"
            uniondict = {}
        elif isinstance(obj.msg, MaskedOverride):
            uniontype = "org.jlab.jaws.entity.MaskedOverride"
            uniondict = {}
        elif isinstance(obj.msg, OnDelayedOverride):
            uniontype = "org.jlab.jaws.entity.OnDelayedOverride"
            uniondict = {"expiration": obj.msg.expiration}
        elif isinstance(obj.msg, OffDelayedOverride):
            uniontype = "org.jlab.jaws.entity.OffDelayedOverride"
            uniondict = {"expiration": obj.msg.expiration}
        elif isinstance(obj.msg, ShelvedOverride):
            uniontype = "org.jlab.jaws.entity.ShelvedOverride"
            uniondict = {"expiration": obj.msg.expiration, "comments": obj.msg.comments,
                         "reason": obj.msg.reason.name, "oneshot": obj.msg.oneshot}
        else:
            print("Unknown alarming union type: {}".format(obj.msg))
            uniontype = "org.jlab.jaws.entity.LatchedOverride"
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
        return AlarmOverrideUnionSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmOverrideUnion.

        Note: Both UnionEncoding.TUPLE and UnionEncoding.DICT_WITH_TYPE are supported,
        but UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported at this time
        because I'm lazy and not going to try to guess what type is in your union.

        :param the_dict: The dict (or maybe it's a duck)
        :return: The AlarmOverrideUnion
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

        if alarmingtype == "org.jlab.jaws.entity.DisabledOverride":
            obj = DisabledOverride(alarmingdict['comments'])
        elif alarmingtype == "org.jlab.jaws.entity.FilteredOverride":
            obj = FilteredOverride(alarmingdict['filtername'])
        elif alarmingtype == "org.jlab.jaws.entity.LatchedOverride":
            obj = LatchedOverride()
        elif alarmingtype == "org.jlab.jaws.entity.MaskedOverride":
            obj = MaskedOverride()
        elif alarmingtype == "org.jlab.jaws.entity.OnDelayedOverride":
            obj = OnDelayedOverride(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.OffDelayedOverride":
            obj = OffDelayedOverride(alarmingdict['expiration'])
        elif alarmingtype == "org.jlab.jaws.entity.ShelvedOverride":
            obj = ShelvedOverride(alarmingdict['expiration'], alarmingdict['comments'],
                               _unwrap_enum(alarmingdict['reason'], ShelvedReason), alarmingdict['oneshot'])
        else:
            print("Unknown alarming type: {}".format(the_dict['msg']))
            obj = LatchedOverride()

        return AlarmOverrideUnion(obj)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return AlarmOverrideUnionSerde.from_dict(the_dict)

    @staticmethod
    def _named_schemas():
        disabled_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/DisabledOverride.avsc")
        disabled_schema_str = disabled_bytes.decode('utf-8')

        filtered_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/FilteredOverride.avsc")
        filtered_schema_str = filtered_bytes.decode('utf-8')

        latched_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/LatchedOverride.avsc")
        latched_schema_str = latched_bytes.decode('utf-8')

        masked_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/MaskedOverride.avsc")
        masked_schema_str = masked_bytes.decode('utf-8')

        off_delayed_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/OffDelayedOverride.avsc")
        off_delayed_schema_str = off_delayed_bytes.decode('utf-8')

        on_delayed_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/OnDelayedOverride.avsc")
        on_delayed_schema_str = on_delayed_bytes.decode('utf-8')

        shelved_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/ShelvedOverride.avsc")
        shelved_schema_str = shelved_bytes.decode('utf-8')

        named_schemas = {}
        ref_dict = loads(disabled_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(filtered_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(latched_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(masked_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(off_delayed_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(on_delayed_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(shelved_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmOverrideUnion deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        named_schemas = AlarmOverrideUnionSerde._named_schemas()

        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              AlarmOverrideUnionSerde._from_dict_with_ctx, True,
                                              named_schemas)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmOverrideUnion serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideUnion.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        named_schemas = AlarmOverrideUnionSerde._named_schemas()

        disabled_schema_ref = SchemaReference("org.jlab.jaws.entity.DisabledOverride", "disabled-override", 1)
        filtered_schema_ref = SchemaReference("org.jlab.jaws.entity.FilteredOverride", "filtered-override", 1)
        latched_schema_ref = SchemaReference("org.jlab.jaws.entity.LatchedOverride", "latched-override", 1)
        masked_schema_ref = SchemaReference("org.jlab.jaws.entity.MaskedOverride", "masked-override", 1)
        off_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OffDelayedOverride", "off-delayed-override", 1)
        on_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OnDelayedOverride", "on-delayed-override", 1)
        shelved_schema_ref = SchemaReference("org.jlab.jaws.entity.ShelvedOverride", "shelved-override", 1)

        schema = Schema(subject_schema_str, "AVRO",
                        [disabled_schema_ref,
                         filtered_schema_ref,
                         latched_schema_ref,
                         masked_schema_ref,
                         off_delayed_schema_ref,
                         on_delayed_schema_ref,
                         shelved_schema_ref])

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmOverrideUnionSerde._to_dict_with_ctx, None,
                                            named_schemas)


class AlarmSerde:
    """
        Provides Alarm serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts Alarm to a dict.

        :param obj: The Alarm
        :return: A dict
        """
        return {
            "type": obj.type.name
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return Alarm.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to Alarm.

        :param the_dict: The dict
        :return: The Alarm
        """
        return Alarm(_unwrap_enum(the_dict['type'], AlarmStateEnum))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return Alarm.from_dict(the_dict)

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an Alarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializer(schema_registry_client, None,
                                Alarm._from_dict_with_ctx, True)

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an Alarm serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/Alarm.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        return AvroSerializer(schema_registry_client, subject_schema_str,
                              Alarm._to_dict_with_ctx, None)