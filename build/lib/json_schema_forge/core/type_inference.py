"""Type inference from JSON samples."""

import re
from typing import Any, Optional
from collections import defaultdict

from json_schema_forge.core.models import (
    InferredType,
    PrimitiveType,
    PrimitiveInferredType,
    ArrayInferredType,
    ObjectInferredType,
    UnionInferredType,
    StringFormat,
)

# Regex patterns for string format detection
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URI_PATTERN = re.compile(r"^https?://[^\s]+$")
ISO_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)


def detect_string_format(value: str) -> Optional[StringFormat]:
    """Detect string format for known patterns."""
    if EMAIL_PATTERN.match(value):
        return StringFormat.EMAIL
    if URI_PATTERN.match(value):
        return StringFormat.URI
    if ISO_DATETIME_PATTERN.match(value):
        return StringFormat.DATE_TIME
    if UUID_PATTERN.match(value):
        return StringFormat.UUID
    return None


def infer_type_from_value(value: Any) -> InferredType:
    """Infer type from a single JSON value."""
    if value is None:
        return PrimitiveInferredType(kind=PrimitiveType.NULL, nullable=True)

    if isinstance(value, bool):
        return PrimitiveInferredType(kind=PrimitiveType.BOOLEAN)

    if isinstance(value, int):
        return PrimitiveInferredType(kind=PrimitiveType.INTEGER)

    if isinstance(value, float):
        return PrimitiveInferredType(kind=PrimitiveType.NUMBER)

    if isinstance(value, str):
        format_hint = detect_string_format(value)
        return PrimitiveInferredType(kind=PrimitiveType.STRING, format=format_hint)

    if isinstance(value, list):
        if not value:
            return ArrayInferredType(items=UnionInferredType(types=[]))

        item_types = [infer_type_from_value(item) for item in value]
        merged_item_type = merge_types(item_types)
        return ArrayInferredType(items=merged_item_type)

    if isinstance(value, dict):
        properties = {k: infer_type_from_value(v) for k, v in value.items()}
        return ObjectInferredType(
            properties=properties,
            required=set(properties.keys())
        )

    # Fallback to string
    return PrimitiveInferredType(kind=PrimitiveType.STRING)


def merge_types(types: list[InferredType]) -> InferredType:
    """Merge multiple inferred types into one unified type."""
    if not types:
        return PrimitiveInferredType(kind=PrimitiveType.STRING)

    if len(types) == 1:
        return types[0]

    # ---- merge primitives ----
    if all(isinstance(t, PrimitiveInferredType) for t in types):
        primitives = types  # type: ignore
        kinds = {p.kind for p in primitives}

        # All same primitive
        if len(kinds) == 1:
            kind = next(iter(kinds))
            nullable = any(p.nullable for p in primitives)

            if kind == PrimitiveType.STRING:
                # Merge formats
                formats = {p.format for p in primitives if p.format}
                fmt = formats.pop() if len(formats) == 1 else None
                return PrimitiveInferredType(kind=kind, format=fmt, nullable=nullable)

            return PrimitiveInferredType(kind=kind, nullable=nullable)

        # Mixed primitives → union
        nullable = any(p.nullable or p.kind == PrimitiveType.NULL for p in primitives)
        non_null = [p for p in primitives if p.kind != PrimitiveType.NULL]

        if not non_null:
            return PrimitiveInferredType(kind=PrimitiveType.NULL, nullable=True)

        return UnionInferredType(types=non_null, nullable=nullable)

    # ---- merge arrays ----
    if all(isinstance(t, ArrayInferredType) for t in types):
        arrays = types  # type: ignore
        merged_items = merge_types([a.items for a in arrays])
        nullable = any(a.nullable for a in arrays)
        return ArrayInferredType(items=merged_items, nullable=nullable)

    # ---- merge objects ----
    if all(isinstance(t, ObjectInferredType) for t in types):
        objects = types  # type: ignore
        all_keys = set().union(*[obj.properties.keys() for obj in objects])

        merged_properties = {}
        required_keys = set(all_keys)

        for key in all_keys:
            key_types = []
            appears_in_all = True

            for obj in objects:
                if key in obj.properties:
                    key_types.append(obj.properties[key])
                else:
                    appears_in_all = False

            if not appears_in_all:
                required_keys.discard(key)

            merged_properties[key] = merge_types(key_types)

        nullable = any(o.nullable for o in objects)
        return ObjectInferredType(
            properties=merged_properties,
            required=required_keys,
            nullable=nullable,
        )

    # ---- mixed types → union ----
    nullable = any(getattr(t, "nullable", False) for t in types)
    return UnionInferredType(types=types, nullable=nullable)


def infer_from_samples(samples: list[Any]) -> InferredType:
    """Infer unified type from a list of samples."""
    if not samples:
        return PrimitiveInferredType(kind=PrimitiveType.STRING)

    return merge_types([infer_type_from_value(s) for s in samples])
