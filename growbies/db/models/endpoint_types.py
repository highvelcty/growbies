from sqlmodel import SQLModel, Field
from typing import Optional

class EndpointTypes(SQLModel, table=True):
    """This is a lookup table, as opposed to an enumeration.

    Lookup tables are more flexible/future-proof than enumerations.Units are
    digital-analog-converted value (DAC)."""
    class Key:
        NAME = 'name'
        DESCRIPTION = 'description'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column_kwargs={"unique": True},
                      description="Sensor type name, e.g., 'mass', 'temperature'")
    description: Optional[str] = Field(default=None, description="Human-readable description")


