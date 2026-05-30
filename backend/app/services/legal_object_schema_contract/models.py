from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SchemaFieldType(str, Enum):
    """Proposed SQL column type labels for schema contract documentation."""

    UUID = "uuid"
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"
    ENUM = "enum"


class SchemaFieldDefinition(BaseModel):
    """A single proposed column in a schema contract table."""

    model_config = ConfigDict(extra="forbid")

    name: str
    field_type: SchemaFieldType
    required: bool = True
    nullable: bool = False
    description: str = ""


class SchemaTableDefinition(BaseModel):
    """Proposed table definition for schema contract documentation."""

    model_config = ConfigDict(extra="forbid")

    name: str
    purpose: str
    fields: list[SchemaFieldDefinition] = Field(min_length=1)

    def field_names(self) -> set[str]:
        return {field.name for field in self.fields}

    def has_required_field(self, name: str) -> bool:
        return name in self.field_names()
