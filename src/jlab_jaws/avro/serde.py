"""
    Serialization and Deserialization utilities
"""

import pkgutil
from json import loads

from confluent_kafka.schema_registry import SchemaReference, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from fastavro import parse_schema

from jlab_jaws.avro.entities import AlarmLocation, AlarmCategory, AlarmPriority
from jlab_jaws.avro.entities import SimpleProducer, AlarmInstance, AlarmActivationUnion, SimpleAlarming, \
    EPICSAlarming, NoteAlarming, DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride, \
    OffDelayedOverride, ShelvedOverride, AlarmOverrideUnion, OverriddenAlarmType, AlarmOverrideKey, ShelvedReason, \
    EPICSSEVR, EPICSSTAT, UnionEncoding, CALCProducer, EPICSProducer, AlarmClass, EffectiveRegistration, \
    EffectiveActivation, EffectiveAlarm, IntermediateMonolog, AlarmState, AlarmOverrideSet, ProcessorTransitions
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
    def set_class_defaults(registration: AlarmInstance, alarm_class: AlarmClass):
        """
        Merge an AlarmClass into a AlarmInstance (apply class default values).

        :param registration: The AlarmInstance
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

        if obj is None:
            return None

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
        if the_dict is None:
            return None

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
    def references():
        location_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmLocation", "alarm-location", 1)
        category_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmCategory", "alarm-category", 1)
        priority_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmPriority", "alarm-priority", 1)

        return [location_schema_ref, category_schema_ref, priority_schema_ref]

    @staticmethod
    def named_schemas():
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
                                              AlarmClassSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmClass serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        value_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmClass.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        schema = Schema(value_schema_str, "AVRO",
                        AlarmClassSerde.references())

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmClassSerde._to_dict_with_ctx, None,
                                            AlarmClassSerde.named_schemas())


class AlarmInstanceSerde:
    """
        Provides AlarmInstance serde utilities
    """

    @staticmethod
    def to_dict(obj, union_encoding=UnionEncoding.TUPLE):
        """
        Converts an AlarmInstance to a dict.

        :param obj: The AlarmInstance
        :param union_encoding: How the union should be encoded
        :return: A dict
        """

        if obj is None:
            return None

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
        return AlarmInstanceSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to an AlarmInstance.

        Note: UnionEncoding.POSSIBLY_AMBIGUOUS_DICT is not supported.

        :param the_dict: The dict
        :return: The AlarmInstance
        """

        if the_dict is None:
            return None

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

        return AlarmInstance(_unwrap_enum(the_dict.get('location'), AlarmLocation),
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
        return AlarmInstanceSerde.from_dict(the_dict)

    @staticmethod
    def references():
        return AlarmClassSerde.references()

    @staticmethod
    def named_schemas():
        return AlarmClassSerde.named_schemas()

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an AlarmInstance deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """
        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              AlarmInstanceSerde._from_dict_with_ctx, True,
                                              AlarmInstanceSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmInstance serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """
        value_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmInstance.avsc")
        value_schema_str = value_bytes.decode('utf-8')

        schema = Schema(value_schema_str, "AVRO",
                        AlarmInstanceSerde.references())

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmInstanceSerde._to_dict_with_ctx, None,
                                            AlarmInstanceSerde.named_schemas())


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

        if obj is None:
            return None

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

        if the_dict is None:
            return None

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
            uniontype = None
            uniondict = None

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
            obj = None

        return AlarmOverrideUnion(obj)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return AlarmOverrideUnionSerde.from_dict(the_dict)

    @staticmethod
    def references():
        disabled_schema_ref = SchemaReference("org.jlab.jaws.entity.DisabledOverride", "disabled-override", 1)
        filtered_schema_ref = SchemaReference("org.jlab.jaws.entity.FilteredOverride", "filtered-override", 1)
        latched_schema_ref = SchemaReference("org.jlab.jaws.entity.LatchedOverride", "latched-override", 1)
        masked_schema_ref = SchemaReference("org.jlab.jaws.entity.MaskedOverride", "masked-override", 1)
        off_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OffDelayedOverride", "off-delayed-override", 1)
        on_delayed_schema_ref = SchemaReference("org.jlab.jaws.entity.OnDelayedOverride", "on-delayed-override", 1)
        shelved_schema_ref = SchemaReference("org.jlab.jaws.entity.ShelvedOverride", "shelved-override", 1)

        return [disabled_schema_ref,
                filtered_schema_ref,
                latched_schema_ref,
                masked_schema_ref,
                off_delayed_schema_ref,
                on_delayed_schema_ref,
                shelved_schema_ref]

    @staticmethod
    def named_schemas():
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

        return AvroDeserializerWithReferences(schema_registry_client, None,
                                              AlarmOverrideUnionSerde._from_dict_with_ctx, True,
                                              AlarmOverrideUnionSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client):
        """
            Return an AlarmOverrideUnion serializer.

            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideUnion.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        schema = Schema(subject_schema_str, "AVRO",
                        AlarmOverrideUnionSerde.references())

        return AvroSerializerWithReferences(schema_registry_client, schema,
                                            AlarmOverrideUnionSerde._to_dict_with_ctx, None,
                                            AlarmOverrideUnionSerde.named_schemas())


class AlarmOverrideSetSerde:
    """
        Provides AlarmOverrideSet serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts AlarmOverrideSet to a dict

        :param obj: The AlarmOverrideSet
        :return: A dict
        """
        return {
            "disabled": {"comments": obj.disabled.comments} if obj.disabled is not None else None,
            "filtered": {"filtername": obj.filtered.filtername} if obj.filtered is not None else None,
            "latched": {} if obj.latched is not None else None,
            "masked": {} if obj.masked is not None else None,
            "ondelayed": {"expiration": obj.ondelayed.expiration} if obj.ondelayed is not None else None,
            "offdelayed": {"expiration": obj.offdelayed.expiration} if obj.offdelayed is not None else None,
            "shelved": {"expiration": obj.shelved.expiration,
                        "comments": obj.shelved.comments,
                        "oneshot": obj.shelved.oneshot,
                        "reason": obj.shelved.reason.name} if obj.shelved is not None else None
        }

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to AlarmOverrideSet.

        :param the_dict: The dict
        :return: The AlarmOverrideSet
        """
        return AlarmOverrideSet(DisabledOverride(the_dict['disabled'][1]['comments'])
                                if the_dict.get('disabled') is not None else None,
                                FilteredOverride(the_dict['filtered'][1]['filtername'])
                                if the_dict.get('filtered') is not None else None,
                                LatchedOverride()
                                if the_dict.get('latched') is not None else None,
                                MaskedOverride()
                                if the_dict.get('masked') is not None else None,
                                OnDelayedOverride(the_dict['ondelayed'][1]['expiration'])
                                if the_dict.get('ondelayed') is not None else None,
                                OffDelayedOverride(the_dict['offdelayed'][1]['expiration'])
                                if the_dict.get('offdelayed') is not None else None,
                                ShelvedOverride(the_dict['shelved'][1]['expiration'],
                                                the_dict['shelved'][1]['comments'],
                                                ShelvedReason[the_dict['shelved'][1]['reason']],
                                                the_dict['shelved'][1]['oneshot'])
                                if the_dict.get('shelved') is not None else None)


class ProcessorTransitionsSerde:
    """
        Provides ProcessorTransitions serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts ProcessorTransitions to a dict

        :param obj: The ProcessorTransitions
        :return: A dict
        """
        return {
            "transitionToActive": obj.transitionToActive,
            "transitionToNormal": obj.transitionToNormal,
            "latching": obj.latching,
            "unshelving": obj.unshelving,
            "masking": obj.masking,
            "unmasking": obj.unmasking,
            "ondelaying": obj.ondelaying,
            "offdelaying": obj.offdelaying
        }

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to ProcessorTransitions.

        :param the_dict: The dict
        :return: The ProcessorTransitions
        """
        return ProcessorTransitions(the_dict['transitionToActive'],
                                    the_dict['transitionToNormal'],
                                    the_dict['latching'],
                                    the_dict['unshelving'],
                                    the_dict['masking'],
                                    the_dict['unmasking'],
                                    the_dict['ondelaying'],
                                    the_dict['offdelaying'])


class EffectiveRegistrationSerde:
    """
        Provides EffectiveRegistration serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts EffectiveRegistration to a dict.

        :param obj: The EffectiveRegistration
        :return: A dict
        """
        return {
            "class": AlarmClassSerde.to_dict(obj.alarm_class),
            "actual": AlarmInstanceSerde.to_dict(obj.actual),
            "calculated": AlarmInstanceSerde.to_dict(obj.calculated)
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return EffectiveRegistrationSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to EffectiveRegistration.

        :param the_dict: The dict
        :return: The EffectiveRegistration
        """
        return EffectiveRegistration(AlarmClassSerde.from_dict(the_dict['class'][1]) if the_dict.get('class') is not None else None,
                              AlarmInstanceSerde.from_dict(the_dict['actual'][1])
                              if the_dict.get('actual') is not None else None,
                              AlarmInstanceSerde.from_dict(the_dict['calculated'][1])
                              if the_dict.get('calculated') is not None else None)

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return EffectiveRegistrationSerde.from_dict(the_dict)

    @staticmethod
    def references():
        references = []

        classes_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmClass", "alarm-classes-value", 1)
        registration_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmInstance",
                                                  "alarm-instances-value", 1)

        references.append(classes_schema_ref)
        references.append(registration_schema_ref)

        return references

    @staticmethod
    def named_schemas():
        classes_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmClass.avsc")
        classes_schema_str = classes_bytes.decode('utf-8')

        registrations_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmInstance.avsc")
        registrations_schema_str = registrations_bytes.decode('utf-8')

        named_schemas = AlarmClassSerde.named_schemas()

        named_schemas.update(AlarmOverrideUnionSerde.named_schemas())

        ref_dict = loads(classes_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(registrations_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an EffectiveRegistration deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializerWithReferences(schema_registry_client,
                                              None,
                                              EffectiveRegistrationSerde._from_dict_with_ctx,
                                              True,
                                              EffectiveRegistrationSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client, conf=None):
        """
            Return an EffectiveRegistration serializer.

            :param conf: Configuration
            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveRegistration.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        schema = Schema(subject_schema_str, "AVRO",
                        EffectiveRegistrationSerde.references())

        return AvroSerializerWithReferences(schema_registry_client,
                                            schema,
                                            EffectiveRegistrationSerde._to_dict_with_ctx,
                                            conf,
                                            EffectiveRegistrationSerde.named_schemas())


class EffectiveActivationSerde:
    """
        Provides EffectiveActivation serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts EffectiveActivation to a dict.

        :param obj: The EffectiveActivation
        :return: A dict
        """
        return {
            "actual": AlarmActivationUnionSerde.to_dict(obj.actual),
            "overrides": AlarmOverrideSetSerde.to_dict(obj.overrides),
            "state": obj.state.name
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return EffectiveActivationSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to EffectiveActivation.

        :param the_dict: The dict
        :return: The EffectiveActivation
        """
        return EffectiveActivation(
                     AlarmActivationUnionSerde.from_dict(the_dict['actual'][1])
                     if the_dict.get('actual') is not None else None,
                     AlarmOverrideSetSerde.from_dict(the_dict['overrides']),
                     _unwrap_enum(the_dict['state'], AlarmState))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return EffectiveActivationSerde.from_dict(the_dict)

    @staticmethod
    def references():
        references = []

        activation_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmActivationUnion",
                                                "alarm-activations-value", 1)
        overrides_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmOverrideSet",
                                               "alarm-override-set", 1)
        state_schema_ref = SchemaReference("org.jlab.jaws.entity.AlarmState", "alarm-state", 1)

        references.append(activation_schema_ref)
        references.append(overrides_schema_ref)
        references.append(state_schema_ref)

        return references

    @staticmethod
    def named_schemas():
        activation_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmActivationUnion.avsc")
        activation_schema_str = activation_bytes.decode('utf-8')

        overrides_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmOverrideSet.avsc")
        overrides_schema_str = overrides_bytes.decode('utf-8')

        state_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/AlarmState.avsc")
        state_schema_str = state_bytes.decode('utf-8')

        named_schemas = AlarmClassSerde.named_schemas()

        named_schemas.update(AlarmOverrideUnionSerde.named_schemas())

        ref_dict = loads(activation_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(overrides_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(state_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an EffectiveActivation deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializerWithReferences(schema_registry_client,
                                              None,
                                              EffectiveActivationSerde._from_dict_with_ctx,
                                              True,
                                              EffectiveActivationSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client, conf=None):
        """
            Return an EffectiveActivation serializer.

            :param conf: Configuration
            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveActivation.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        schema = Schema(subject_schema_str, "AVRO",
                        EffectiveActivationSerde.references())

        return AvroSerializerWithReferences(schema_registry_client,
                                            schema,
                                            EffectiveActivationSerde._to_dict_with_ctx,
                                            conf,
                                            EffectiveActivationSerde.named_schemas())


class EffectiveAlarmSerde:
    """
        Provides EffectiveAlarm serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts EffectiveAlarm to a dict.

        :param obj: The EffectiveAlarm
        :return: A dict
        """
        return {
            "registration": EffectiveRegistrationSerde.to_dict(obj.registration),
            "activation": EffectiveActivationSerde.to_dict(obj.activation),
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return EffectiveAlarmSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to EffectiveAlarm.

        :param the_dict: The dict
        :return: The EffectiveAlarm
        """
        return EffectiveAlarm(EffectiveRegistrationSerde.from_dict(the_dict['registration']),
                              EffectiveActivationSerde.from_dict(the_dict['activation']))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return EffectiveAlarmSerde.from_dict(the_dict)

    @staticmethod
    def references():
        references = []

        registration_schema_ref = SchemaReference("org.jlab.jaws.entity.EffectiveRegistration",
                                                  "effective-registrations-value", 1)
        activation_schema_ref = SchemaReference("org.jlab.jaws.entity.EffectiveActivation",
                                                "effective-activations-value", 1)

        references.append(registration_schema_ref)
        references.append(activation_schema_ref)

        return references

    @staticmethod
    def named_schemas():
        registrations_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveRegistration.avsc")
        registrations_schema_str = registrations_bytes.decode('utf-8')

        activation_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveActivation.avsc")
        activation_schema_str = activation_bytes.decode('utf-8')

        named_schemas = EffectiveRegistrationSerde.named_schemas()
        named_schemas.update(EffectiveActivationSerde.named_schemas())

        ref_dict = loads(registrations_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)
        ref_dict = loads(activation_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an EffectiveAlarm deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializerWithReferences(schema_registry_client,
                                              None,
                                              EffectiveAlarmSerde._from_dict_with_ctx,
                                              True,
                                              EffectiveAlarmSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client, conf=None):
        """
            Return an EffectiveAlarm serializer.

            :param conf: Configuration
            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveAlarm.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        schema = Schema(subject_schema_str, "AVRO",
                        EffectiveAlarmSerde.references())

        return AvroSerializerWithReferences(schema_registry_client,
                                            schema,
                                            EffectiveAlarmSerde._to_dict_with_ctx,
                                            conf,
                                            EffectiveAlarmSerde.named_schemas())


class IntermediateMonologSerde:
    """
        Provides IntermediateMonolog serde utilities
    """

    @staticmethod
    def to_dict(obj):
        """
        Converts IntermediateMonolog to a dict.

        :param obj: The IntermediateMonolog
        :return: A dict
        """
        return {
            "registration": EffectiveRegistrationSerde.to_dict(obj.registration),
            "activation": EffectiveActivationSerde.to_dict(obj.activation),
            "transitions": ProcessorTransitionsSerde.to_dict(obj.transitions)
        }

    @staticmethod
    def _to_dict_with_ctx(obj, ctx):
        return EffectiveAlarmSerde.to_dict(obj)

    @staticmethod
    def from_dict(the_dict):
        """
        Converts a dict to IntermediateMonolog.

        :param the_dict: The dict
        :return: The IntermediateMonolog
        """
        return IntermediateMonolog(EffectiveRegistrationSerde.from_dict(the_dict['registration']),
                                   EffectiveActivationSerde.from_dict(the_dict['activation']),
                                   ProcessorTransitionsSerde.from_dict(the_dict['transitions']))

    @staticmethod
    def _from_dict_with_ctx(the_dict, ctx):
        return IntermediateMonologSerde.from_dict(the_dict)

    @staticmethod
    def references():
        references = []

        registration_schema_ref = SchemaReference("org.jlab.jaws.entity.EffectiveRegistration",
                                                  "effective-registrations-value", 1)

        activation_schema_ref = SchemaReference("org.jlab.jaws.entity.EffectiveActivation",
                                                "effective-activations-value", 1)

        transitions_schema_ref = SchemaReference("org.jlab.jaws.entity.ProcessorTransitions",
                                                 "processor-transitions", 1)

        references.append(registration_schema_ref)
        references.append(activation_schema_ref)
        references.append(transitions_schema_ref)

        return references

    @staticmethod
    def named_schemas():
        registrations_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveRegistration.avsc")
        registrations_schema_str = registrations_bytes.decode('utf-8')

        activation_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/EffectiveActivation.avsc")
        activation_schema_str = activation_bytes.decode('utf-8')

        transitions_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/ProcessorTransitions.avsc")
        transitions_schema_str = transitions_bytes.decode('utf-8')

        named_schemas = EffectiveRegistrationSerde.named_schemas()
        named_schemas.update(EffectiveActivationSerde.named_schemas())

        ref_dict = loads(registrations_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        ref_dict = loads(activation_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        ref_dict = loads(transitions_schema_str)
        parse_schema(ref_dict, named_schemas=named_schemas)

        return named_schemas

    @staticmethod
    def deserializer(schema_registry_client):
        """
            Return an IntermediateMonolog deserializer.

            :param schema_registry_client: The Confluent Schema Registry Client
            :return: Deserializer
        """

        return AvroDeserializerWithReferences(schema_registry_client,
                                              None,
                                              IntermediateMonologSerde._from_dict_with_ctx,
                                              True,
                                              IntermediateMonologSerde.named_schemas())

    @staticmethod
    def serializer(schema_registry_client, conf=None):
        """
            Return an IntermediateMonolog serializer.

            :param conf: Configuration
            :param schema_registry_client: The Confluent Schema Registry client
            :return: Serializer
        """

        subject_bytes = pkgutil.get_data("jlab_jaws", "avro/schemas/IntermediateMonolog.avsc")
        subject_schema_str = subject_bytes.decode('utf-8')

        schema = Schema(subject_schema_str, "AVRO",
                        IntermediateMonologSerde.references())

        return AvroSerializerWithReferences(schema_registry_client,
                                            schema,
                                            IntermediateMonologSerde._to_dict_with_ctx,
                                            conf,
                                            IntermediateMonologSerde.named_schemas())
