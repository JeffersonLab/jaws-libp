from dataclasses import dataclass
from jlab_jaws.entities.referenced_schemas import AlarmClass, AlarmLocation, AlarmCategory, AlarmPriority

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