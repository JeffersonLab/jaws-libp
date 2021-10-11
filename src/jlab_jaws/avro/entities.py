"""
    Python entities corresponding to AVRO schemas.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

class AlarmLocation(Enum):
    S1D = 1
    S2D = 2
    S3D = 3
    S4D = 4
    S5D = 5
    L1 = 6
    L2 = 7
    L3 = 8
    L4 = 9
    L5 = 10
    L6 = 11
    L7 = 12
    L8 = 13
    L9 = 14
    LA = 15
    LB = 16
    A1 = 17
    A2 = 18
    A3 = 19
    A4 = 20
    A5 = 21
    A6 = 22
    A7 = 23
    A8 = 24
    A9 = 25
    AA = 26
    BSY2 = 27
    BSY4 = 28
    BSY6 = 29
    BSY8 = 30
    BSYA = 31
    BSYD = 32
    INJ = 33
    NL = 34
    SL = 35
    EA = 36
    WA = 37
    BSY = 38
    HA = 39
    HB = 40
    HC = 41
    HD = 42
    ACC = 43
    CHL = 44
    MCC = 45
    LERF = 46
    UITF = 47


class AlarmCategory(Enum):
    Aperture = 1
    BCM = 2
    Box = 3
    BPM = 4
    CAMAC = 5
    Crate = 6
    Dump = 7
    Gun = 8
    Harp = 9
    Helicity = 10
    IC = 11
    IOC = 12
    Laser = 13
    LCW = 14
    Misc = 15
    ODH = 16
    RADCON = 17
    RF = 18
    Vacuum = 19


class AlarmPriority(Enum):
    P1_CRITICAL = 1
    P2_MAJOR = 2
    P3_MINOR = 3
    P4_INCIDENTAL = 4

class UnionEncoding(Enum):
    """
        Enum of possible ways to encode an AVRO union instance in Python.
    """
    TUPLE = 1
    """Instance is a two-tuple of (str - type name, dict); this is how fastavro works 
    (https://fastavro.readthedocs.io/en/latest/writer.html#using-the-tuple-notation-to-specify-which-branch-of-a-union-to-take)"""
    DICT_WITH_TYPE = 2
    """Instance is a dict with one entry of key type name str and value dict; this serializes to JSON as AVRO expects 
    (except for logical types and bytes) - See:  http://avro.apache.org/docs/current/spec.html#json_encoding"""
    POSSIBLY_AMBIGUOUS_DICT = 3
    """Instance dict provided without type name - which in the case of records with identical fields there is no way
    to determine which is which (example: union of classes A and B where each has identical fields)"""


class AlarmState(Enum):
    NormalDisabled = 1
    """Effectively Normal, out-of-service"""
    NormalFiltered = 2
    """Effectively Normal, suppressed by design"""
    NormalMasked = 3
    """Effectively Normal, hidden by parent alarm"""
    NormalOnDelayed = 4
    """Effectively Normal, temporarily suppressed upon activation"""
    NormalOneShotShelved = 5
    """Effectively Normal, temporarily suppressed until next deactivation or expiration"""
    NormalContinuousShelved = 6
    """Effectively Normal, temporarily suppressed until expiration"""
    ActiveOffDelayed = 7
    """Effectively Active, temporarily incited upon deactivation"""
    ActiveLatched = 8
    """Effectively Active, temporarily incited upon activation"""
    Active = 9
    """Effectively Active, Actually Active, timely operator action required"""
    Normal = 10
    """Effectively Normal, Actually Normal, no action required"""


class OverriddenAlarmType(Enum):
    Disabled = 1
    """A broken alarm can be flagged as out-of-service"""
    Filtered = 2
    """An alarm can be "suppressed by design" - generally a group of alarms are filtered out when not needed for the
    current machine program. The Filter Processor helps operators filter multiple alarms with simple grouping
    commands (like by area)."""
    Masked = 3
    """An alarm can be suppressed by a parent alarm to minimize confusion during an alarm flood and build an 
    alarm hierarchy"""
    OnDelayed = 4
    """An alarm with an on-delay is temporarily suppressed upon activation to minimize fleeting/chattering"""
    OffDelayed = 5
    """An alarm with an off-delay is temporarily incited upon de-activation to minimize fleeting/chattering"""
    Shelved = 6
    """An alarm can be temporarily suppressed via manual operator command"""
    Latched = 7
    """A fleeting alarm (one that toggles between active and not active too quickly) can be configured to require 
    acknowledgement by operators - the alarm is latched once active and won't clear to Normal (or Active) until 
    acknowledged"""


class ShelvedReason(Enum):
    Stale_Alarm = 1
    """Nuisance alarm which remains active for an extended period of time"""
    Chattering_Fleeting_Alarm = 2
    """Nuisance alarm which toggles between active and normal states quickly (fleeting) and may do this often
    (chattering)"""
    Other = 3
    """Some other reason"""


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
class DisabledOverride:
    """
        Disabled override - Suppresses an alarm that is out-of-service (usually for maintenance)
    """
    comments: Optional[str]
    """Explanation of why the alarm is out-of-service"""


@dataclass
class FilteredOverride:
    """
        Filtered override - Suppresses an alarm via filter rule
    """
    filtername: str
    """Filter rule causing the alarm to be filtered"""


@dataclass
class LatchedOverride:
    """
        Latched override - Incites an alarm until an operator acknowledgement
    """


@dataclass
class MaskedOverride:
    """
        Masked override - Suppresses an alarm when a parent alarm is active
        (establishes a hierarchy and minimizes alarm flooding)
    """


@dataclass
class OnDelayedOverride:
    """
        On-Delay override - Suppresses an alarm for a short duration upon activation
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""


@dataclass
class OffDelayedOverride:
    """
        Off-Delay override - Incites an alarm for a short duration upon deactivation
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""


@dataclass
class ShelvedOverride:
    """
        Shelved override - a temporary override (expires)
    """
    expiration: int
    """Expiration timestamp (Unix timestamp of milliseconds since Epoch of Jan 1. 1970 UTC)"""
    comments: Optional[str]
    """Additional operator comments explaining why the alarm was shelved"""
    reason: ShelvedReason
    """The general motivation for shelving the alarm"""
    oneshot: bool
    """Indicates whether the override expires immediately upon next alarm deactivation (unless timestamp expiration occurs first)"""


@dataclass
class AlarmClass:
    """
        alarm-classes-value subject
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
class AlarmRegistration(AlarmClass):
    """
        alarm-registrations-value subject

        Note: Any attributes inherited from AlarmClass can be set to None which indicate the class value
        should be used.
    """
    alarm_class: str
    """The Alarm Class"""
    producer:  Union[SimpleProducer, EPICSProducer, CALCProducer]
    """The Alarm Producer"""


@dataclass
class AlarmActivationUnion:
    """
        alarm-activations-value subject
    """
    msg: Union[SimpleAlarming, NoteAlarming, EPICSAlarming]
    """The message payload is a union of possible alarming types"""


@dataclass(frozen=True)
class AlarmOverrideKey:
    """
        alarm-overrides-key subject
    """
    name: str
    """The alarm name"""
    type: OverriddenAlarmType
    """The override type"""


@dataclass
class AlarmOverrideUnion:
    """
        alarm-overrides-value subject
    """
    msg: Union[DisabledOverride, FilteredOverride, LatchedOverride, MaskedOverride, OnDelayedOverride,
               OffDelayedOverride, ShelvedOverride]
    """The message payload is a union of possible override types"""


@dataclass
class AlarmOverrideSet:
    """
        Set of all overrides for an alarm
    """
    disabled: DisabledOverride
    """Disabled Override"""
    filtered: FilteredOverride
    """Filtered Override"""
    latched: LatchedOverride
    """Latched Override"""
    masked: MaskedOverride
    """Masked Override"""
    ondelayed: OnDelayedOverride
    """On Delayed Override"""
    offdelayed: OffDelayedOverride
    """Off Delayed Override"""
    shelved: ShelvedOverride
    """Shelved Override"""


@dataclass
class ProcessorTransitions:
    """
        Set of transition states as alarm data is joined and processed
    """
    transitionToActive: bool
    """true when record is first one to indicate Active after being Normal"""
    transitionToNormal: bool
    """true when record is first one to indicate Normal after being Active"""
    latching: bool
    """true when record is in-process of latching, LatchOverride forthcoming"""
    unshelving: bool
    """true when record is in-process of being unshelved after one-shot, ShelvedOverride clearing"""
    masking: bool
    """true when record is in-process of being masked, MaskedOverride forthcoming"""
    unmasking: bool
    """true when record is in-process of being unmasked, MaskedOverride clearing"""
    ondelaying: bool
    """true when record is in-process of being on-delayed, OnDelayedOverride forthcoming"""
    offdelaying: bool
    """true when record is in-process of being off-delayed, OffDelayedOverride forthcoming"""


@dataclass
class Alarm:
    """
        alarm-value subject
    """
    alarm_class: AlarmClass
    """The Alarm Class"""

    registration: AlarmRegistration
    """The Alarm Registration"""

    effective_registration: AlarmRegistration
    """The Effective Alarm Registration consider class defaults"""

    activation: AlarmActivationUnion
    """The Alarm Activation"""

    overrides: AlarmOverrideSet
    """The Alarm Overrides"""

    transitions: ProcessorTransitions
    """The Processor Transitions"""

    state: AlarmState
    """The Alarm State"""
