from enum import StrEnum


class PersonKind(StrEnum):
    PATIENT = "patient"
    THERAPIST = "therapist"


class ResourceKind(StrEnum):
    THERAPIST = "therapist"
    ROOM = "room"
