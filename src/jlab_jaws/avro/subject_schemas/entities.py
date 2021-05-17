"""
    Python entities corresponding to AVRO schemas.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Union

from jlab_jaws.avro.referenced_schemas.entities import AlarmClass, AlarmLocation, AlarmCategory, AlarmPriority


class UnionEncoding(Enum):
    """
        Enum of possible ways to encode an AVRO union in Python.
    """
    TUPLE = 1
    DICT_WITH_TYPE = 2
    POSSIBLY_AMBIGUOUS_DICT = 3


class AlarmState(Enum):
    NormalDisabled = 1
    Disabled = 2
    NormalFiltered = 3
    Filtered = 4
    Masked = 5
    OnDelayed = 6
    OneShotShelved = 7
    NormalContinuousShelved = 8
    ContinuousShelved = 9
    OffDelayed = 10
    NormalLatched = 11
    Latched = 12
    Active = 13
    Normal = 14


class OverriddenAlarmType(Enum):
    Disabled = 1
    Filtered = 2
    Masked = 3
    OnDelayed = 4
    OffDelayed = 5
    Shelved = 6
    Latched = 7


class ShelvedAlarmReason(Enum):
    Stale_Alarm = 1
    Chattering_Fleeting_Alarm = 2
    Other = 3


class EPICSSEVR(Enum):
    NO_ALARM = 1
    MINOR = 2
    MAJOR = 3
    INVALID = 4


class EPICSSTAT(Enum):
    NO_ALARM = 1
    READ = 2
    WRITE = 3
    HIHI = 4
    HIGH = 5
    LOLO = 6
    LOW = 7
    STATE = 8
    COS = 9
    COMM = 10
    TIMEOUT = 11
    HW_LIMIT = 12
    CALC = 13
    SCAN = 14
    LINK = 15
    SOFT = 16
    BAD_SUB = 17
    UDF = 18
    DISABLE = 19
    SIMM = 20
    READ_ACCESS = 21
    WRITE_ACCESS = 22


@dataclass
class SimpleAlarming:
    """
        Simple alarming record (no fields)
    """


@dataclass
class NoteAlarming:
    """
        An alarming record with a note
    """
    note: str


@dataclass
class EPICSAlarming:
    """
        An EPICS alarming record
    """
    sevr: EPICSSEVR
    stat: EPICSSTAT


@dataclass
class SimpleProducer:
    """
        Simple alarm producer (no fields)
    """


@dataclass
class EPICSProducer:
    """
        EPICS alarm producer
    """
    pv: str


@dataclass
class CALCProducer:
    """
        CALC expression alarm producer
    """
    expression: str


@dataclass
class DisabledAlarm:
    """
        Disabled override
    """
    comments: str


@dataclass
class FilteredAlarm:
    """
        Filtered override
    """
    filtername: str


@dataclass
class LatchedAlarm:
    """
        Latched override
    """


@dataclass
class MaskedAlarm:
    """
        Masked override
    """


@dataclass
class OnDelayedAlarm:
    """
        On-Delay override
    """
    expiration: int


@dataclass
class OffDelayedAlarm:
    """
        Off-Delay override
    """
    expiration: int


@dataclass
class ShelvedAlarm:
    """
        Shelved override
    """
    expiration: int
    comments: str
    reason: ShelvedAlarmReason
    oneshot: bool


@dataclass
class ClassAlarmKey:
    """
        registered-class-key subject
    """
    alarmClass: AlarmClass


@dataclass
class ClassAlarm:
    """
        registered-class-value subject
    """
    location: AlarmLocation
    category: AlarmCategory
    priority: AlarmPriority
    rationale: str
    corrective_action: str
    point_of_contact_username: str
    latching: bool
    filterable: bool
    on_delay_seconds: int
    off_delay_seconds: int
    masked_by: str
    screen_path: str


@dataclass
class RegisteredAlarm(ClassAlarm):
    """
        registered-alarm-value subject
    """
    alarm_class: AlarmClass
    producer:  Union[SimpleProducer, EPICSProducer, CALCProducer]


@dataclass
class ActiveAlarm:
    """
        active-alarm-value subject
    """
    msg: Union[SimpleAlarming, NoteAlarming, EPICSAlarming]


@dataclass(frozen=True)
class OverriddenAlarmKey:
    """
        overridden-alarms-key subject
    """
    name: str
    type: OverriddenAlarmType


@dataclass
class OverriddenAlarmValue:
    """
        overridden-alarms-value subject
    """
    msg: Union[DisabledAlarm, FilteredAlarm, LatchedAlarm, MaskedAlarm, OnDelayedAlarm, OffDelayedAlarm, ShelvedAlarm]


@dataclass
class AlarmStateValue:
    """
        alarm-state-value subject
    """
    type: AlarmState
