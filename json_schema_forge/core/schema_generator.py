"""JSON Schema generation from inferred types."""

from typing import Any

from json_schema_forge.core.models import (
    InferredType,
    PrimitiveInferredType,
    ArrayInferredType,
    ObjectInferredType,
    UnionInferredType,
    PrimitiveType,
)
from json_schema_forge.core.type_inference import infer_from_samples


def type_to_schema(inferred_type: InferredType) -> dict[str, Any]:
    """Convert internal inferred type representation into a JSON Schema node."""
    
    # -------------------------
    # Primitive Type
    # -------------------------
    if isinstance(inferred_type, PrimitiveInferredType):
        schema: dict[str, Any] = {"type": inferred_type.kind.value}

        if inferred_type.format:
            schema["format"] = inferred_type.format.value

        return schema

    # -------------------------
    # Array Type
    # -------------------------
    if isinstance(inferred_type, ArrayInferredType):
        return {
            "type": "array",
            "items": type_to_schema(inferred_type.items)
        }

    # -------------------------
    # Object Type
    # -------------------------
    if isinstance(inferred_type, ObjectInferredType):
        schema = {
            "type": "object",
            "properties": {
                key: type_to_schema(value)
                for key, value in inferred_type.properties.items()
            }
        }

        if inferred_type.required:
            schema["required"] = sorted(list(inferred_type.required))

        return schema

    # -------------------------
    # Union Type
    # -------------------------
    if isinstance(inferred_type, UnionInferredType):
        schemas = [type_to_schema(t) for t in inferred_type.types]

        # If union collapses to single element
        if len(schemas) == 1:
            return schemas[0]

        return {"anyOf": schemas}

    # -------------------------
    # Fallback → string
    # -------------------------
    return {"type": "string"}


def apply_nullable(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Wrap schema with {"anyOf": [..., {"type": "null"}]} for nullable types.
    """

    # For union schemas, add null inside the same anyOf
    if "anyOf" in schema:
        schema["anyOf"].append({"type": "null"})
        return schema

    # For normal schemas, wrap it
    return {
        "anyOf": [
            schema,
            {"type": "null"}
        ]
    }


def generate_schema(
    samples: list[Any],
    root_name: str = "Root",
    pretty: bool = False
) -> dict[str, Any]:
    """
    Generate JSON Schema (Draft 2020-12) from JSON samples.

    Args:
        samples: JSON object(s) for inference
        root_name: Title name for the root schema
        pretty: Pretty-print flag (unused here)

    Returns:
        JSON Schema dictionary
    """

    inferred = infer_from_samples(samples)
    schema = type_to_schema(inferred)

    # Add schema metadata
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"

    # Title for object root
    if isinstance(inferred, ObjectInferredType):
        schema["title"] = root_name

    # Handle nullable
    if inferred.nullable:
        schema = apply_nullable(schema)

    return schema
