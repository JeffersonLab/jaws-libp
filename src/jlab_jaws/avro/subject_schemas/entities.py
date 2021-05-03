"""
    Python entities corresponding to AVRO schemas.
"""

from dataclasses import dataclass, asdict
from dacite import from_dict
from jlab_jaws.avro.referenced_schemas.entities import AlarmClass, AlarmLocation, AlarmCategory, AlarmPriority


@dataclass
class RegisteredAlarm:
    alarmClass: AlarmClass
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

    def as_dict(self):
        return asdict(self)

    def from_dict(self, d: dict):
        return from_dict(data_class=self.__class__, data=d)
