"""Internal data structures for type representation."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------
# Primitive Types & Formats
# ---------------------------

class PrimitiveType(str, Enum):
    """Primitive JSON types."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    NULL = "null"


class StringFormat(str, Enum):
    """String format hints."""
    EMAIL = "email"
    URI = "uri"
    DATE_TIME = "date-time"
    DATE = "date"
    TIME = "time"
    UUID = "uuid"


# ---------------------------
# Base Type
# ---------------------------

class InferredType(BaseModel):
    """Base class for inferred types."""
    nullable: bool = False


# ---------------------------
# Concrete Types
# ---------------------------

class PrimitiveInferredType(InferredType):
    """Primitive type representation."""
    kind: PrimitiveType
    format: Optional[StringFormat] = None


class ArrayInferredType(InferredType):
    """Array type representation."""
    items: "InferredType"


class ObjectInferredType(InferredType):
    """Object type representation."""
    properties: dict[str, "InferredType"] = Field(default_factory=dict)
    required: set[str] = Field(default_factory=set)


class UnionInferredType(InferredType):
    """Union (oneOf) type representation."""
    types: list["InferredType"]


# ---------------------------
# Forward Reference Fix
# ---------------------------

ArrayInferredType.model_rebuild()
ObjectInferredType.model_rebuild()
UnionInferredType.model_rebuild()
