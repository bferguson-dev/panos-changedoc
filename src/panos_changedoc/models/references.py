from dataclasses import dataclass


@dataclass(frozen=True)
class Reference:
    source_type: str
    source_name: str
    field: str
