"""TypeScript type generation from inferred types."""

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


# -------------------------------------------------------
# Helper: Sanitize names
# -------------------------------------------------------

def sanitize_name(name: str) -> str:
    """Convert raw keys into valid PascalCase TS identifiers."""
    sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)

    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized

    if not sanitized:
        return "Type"

    return sanitized[0].upper() + sanitized[1:]


# -------------------------------------------------------
# Primitive → TS type
# -------------------------------------------------------

def primitive_to_ts_type(primitive: PrimitiveInferredType) -> str:
    """Convert primitive type to TypeScript type."""
    type_map = {
        PrimitiveType.STRING: "string",
        PrimitiveType.NUMBER: "number",
        PrimitiveType.INTEGER: "number",
        PrimitiveType.BOOLEAN: "boolean",
        PrimitiveType.NULL: "null",
    }
    return type_map.get(primitive.kind, "any")


# -------------------------------------------------------
# Recursive conversion
# -------------------------------------------------------

def type_to_ts(
    inferred_type: InferredType,
    type_name: str,
    interfaces: dict[str, str],
) -> str:
    """
    Convert internal inferred types into TS representation.

    - Objects → interfaces
    - Primitives, arrays, unions → type aliases or inline types
    """

    # -------------------------
    # Primitive
    # -------------------------
    if isinstance(inferred_type, PrimitiveInferredType):
        ts = primitive_to_ts_type(inferred_type)
        return f"{ts} | null" if inferred_type.nullable else ts

    # -------------------------
    # Array
    # -------------------------
    if isinstance(inferred_type, ArrayInferredType):
        item_name = f"{type_name}Item"
        item_ts = type_to_ts(inferred_type.items, item_name, interfaces)
        result = f"{item_ts}[]"
        return f"{result} | null" if inferred_type.nullable else result

    # -------------------------
    # Object → interface
    # -------------------------
    if isinstance(inferred_type, ObjectInferredType):
        if type_name not in interfaces:
            lines = [f"export interface {type_name} {{"]
            for key, value in sorted(inferred_type.properties.items()):
                optional = "" if key in inferred_type.required else "?"
                nested_name = sanitize_name(f"{type_name}_{key}")
                ts_value = type_to_ts(value, nested_name, interfaces)
                lines.append(f"  {key}{optional}: {ts_value};")
            lines.append("}")

            interfaces[type_name] = "\n".join(lines)

        return f"{type_name} | null" if inferred_type.nullable else type_name

    # -------------------------
    # Union
    # -------------------------
    if isinstance(inferred_type, UnionInferredType):
        parts = []
        for i, t in enumerate(inferred_type.types):
            nested_name = f"{type_name}Option{i+1}"
            parts.append(type_to_ts(t, nested_name, interfaces))

        union_ts = " | ".join(parts)
        return f"{union_ts} | null" if inferred_type.nullable else union_ts

    return "any"


# -------------------------------------------------------
# High-level generator
# -------------------------------------------------------

def generate_typescript(
    samples: list[Any],
    root_name: str = "Root"
) -> str:
    """Generate TypeScript interfaces + types from JSON samples."""

    inferred = infer_from_samples(samples)
    interfaces: dict[str, str] = {}

    # Convert
    root_ts = type_to_ts(inferred, sanitize_name(root_name), interfaces)

    # Build final TS result
    lines = []

    # Add all nested interfaces (except root), reversed for dependency order
    names = sorted(interfaces.keys())
    for n in names:
        if n != root_name:
            lines.append(interfaces[n])
            lines.append("")

    # Root interface or type
    if root_name in interfaces:
        lines.append(interfaces[root_name])
    else:
        # Root is primitive/union → type alias
        lines.append(f"export type {root_name} = {root_ts};")

    return "\n".join(lines)
