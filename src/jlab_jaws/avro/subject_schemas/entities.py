"""
    Python entities corresponding to AVRO schemas.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

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
    """A note containing extra information generated at the time of activation"""


@dataclass
class EPICSAlarming:
    """
        An EPICS alarming record
    """
    sevr: EPICSSEVR
    """The severity"""
    stat: EPICSSTAT
    """The status"""


@dataclass
class SimpleProducer:
    """
        Simple alarm producer (no fields)
    """


@dataclass
class EPICSProducer:
    """
        EPICS alarm producer - An alarm producer that produces alarms from EPICS
    """
    pv: str
    """The EPICS Process Variable name"""


@dataclass
class CALCProducer:
    """
        CALC expression alarm producer - An alarm producer that evaluates a CALC expression to produce alarms
    """
    expression: str
    """The CALC (calculate) expression"""


@dataclass
class DisabledAlarm:
    """
        Disabled override - Suppresses an alarm that is out-of-service (usually for maintenance)
    """
    comments: Optional[str]
    """Explanation of why the alarm is out-of-service"""


@dataclass
class FilteredAlarm:
    """
        Filtered override - Suppresses an alarm via filter rule
    """
    filtername: str
    """Filter rule causing the alarm to be filtered"""


@dataclass
class LatchedAlarm:
    """
        Latched override - Incites an alarm until an operator acknowledgement
    """


@dataclass
class MaskedAlarm:
    """
        Masked override - Suppresses an alarm when a parent alarm is active
        (establishes a hierarchy and minimizes alarm flooding)
    """


@dataclass
class OnDelayedAlarm:
    """
        On-Delay override - Suppresses an alarm for a short duration upon activation
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""


@dataclass
class OffDelayedAlarm:
    """
        Off-Delay override - Incites an alarm for a short duration upon deactivation
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""


@dataclass
class ShelvedAlarm:
    """
        Shelved override - a temporary override (expires)
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""
    comments: Optional[str]
    """Additional operator comments explaining why the alarm was shelved"""
    reason: ShelvedAlarmReason
    """The general motivation for shelving the alarm"""
    oneshot: bool
    """Indicates whether the override expires immediately upon next alarm deactivation (unless timestamp expiration occurs first)"""


@dataclass(frozen=True)
class RegisteredClassKey:
    """
        registered-class-key subject
    """
    alarm_class: AlarmClass
    """The Alarm Class"""


@dataclass
class RegisteredClass:
    """
        registered-class-value subject
    """
    location: AlarmLocation
    """The Alarm Location"""
    category: AlarmCategory
    """The Alarm Category"""
    priority: AlarmPriority
    """The Alarm Priority"""
    rationale: str
    """The Rationale"""
    corrective_action: str
    """The Corrective Action"""
    point_of_contact_username: str
    """The Point of Contact Username"""
    latching: bool
    """Indicates whether the alarm latches"""
    filterable: bool
    """Indicates whether the alarm can be filtered"""
    on_delay_seconds: Optional[int]
    """(optional) The on-delay in seconds - non-positive is treated as None"""
    off_delay_seconds: Optional[int]
    """(optional) The off-delay in seconds - non-positive is treated as None"""
    masked_by: Optional[str]
    """(optional) The parent alarm which masks this one"""
    screen_path: str
    """The control screen path which provides additional alarm information"""


@dataclass
class RegisteredAlarm(RegisteredClass):
    """
        registered-alarm-value subject

        Note: Any attributes inherited from RegisteredClass can be set to None which indicate the class value
        should be used.
    """
    alarm_class: AlarmClass
    """The Alarm Class"""
    producer:  Union[SimpleProducer, EPICSProducer, CALCProducer]
    """The Alarm Producer"""


@dataclass
class ActiveAlarm:
    """
        active-alarm-value subject
    """
    msg: Union[SimpleAlarming, NoteAlarming, EPICSAlarming]
    """The message payload is a union of possible alarming types"""


@dataclass(frozen=True)
class OverriddenAlarmKey:
    """
        overridden-alarms-key subject
    """
    name: str
    """The alarm name"""
    type: OverriddenAlarmType
    """The override type"""


@dataclass
class OverriddenAlarmValue:
    """
        overridden-alarms-value subject
    """
    msg: Union[DisabledAlarm, FilteredAlarm, LatchedAlarm, MaskedAlarm, OnDelayedAlarm, OffDelayedAlarm, ShelvedAlarm]
    """The message payload is a union of possible override types"""


@dataclass
class AlarmStateValue:
    """
        alarm-state-value subject
    """
    type: AlarmState
    """The Alarm State"""
