"""Python Pydantic model generation from inferred types."""

from typing import Any

from json_schema_forge.core.models import (
    InferredType,
    PrimitiveInferredType,
    ArrayInferredType,
    ObjectInferredType,
    UnionInferredType,
    PrimitiveType,
    StringFormat,
)
from json_schema_forge.core.type_inference import infer_from_samples


# -------------------------------------------------------
# Name Sanitizer
# -------------------------------------------------------

def sanitize_class_name(name: str) -> str:
    """Convert raw names to valid PascalCase Python class names."""
    cleaned = "".join(c if c.isalnum() or c == "_" else "_" for c in name)

    if not cleaned:
        return "Model"

    if cleaned[0].isdigit():
        cleaned = "_" + cleaned

    return cleaned[0].upper() + cleaned[1:]


# -------------------------------------------------------
# Primitive Mapping
# -------------------------------------------------------

def primitive_to_py_type(primitive: PrimitiveInferredType) -> str:
    """Convert primitive JSON type → Python type."""
    if primitive.kind == PrimitiveType.STRING:
        if primitive.format == StringFormat.EMAIL:
            return "EmailStr"
        return "str"

    if primitive.kind == PrimitiveType.NUMBER:
        return "float"

    if primitive.kind == PrimitiveType.INTEGER:
        return "int"

    if primitive.kind == PrimitiveType.BOOLEAN:
        return "bool"

    if primitive.kind == PrimitiveType.NULL:
        return "None"

    return "Any"


# -------------------------------------------------------
# Recursive Type Conversion
# -------------------------------------------------------

def type_to_py(
    inferred_type: InferredType,
    type_name: str,
    models: dict[str, str],
    imports: set[str],
) -> str:
    """
    Convert inferred type → Python type hint.
    Generates Pydantic models for objects.
    """

    # -------------------------
    # Primitive
    # -------------------------
    if isinstance(inferred_type, PrimitiveInferredType):
        py = primitive_to_py_type(inferred_type)

        if py == "EmailStr":
            imports.add("EmailStr")

        if inferred_type.nullable and py != "None":
            imports.add("Optional")
            return f"Optional[{py}]"

        return py

    # -------------------------
    # Array
    # -------------------------
    if isinstance(inferred_type, ArrayInferredType):
        imports.add("List")

        nested_name = f"{type_name}Item"
        item_ts = type_to_py(inferred_type.items, nested_name, models, imports)

        list_type = f"List[{item_ts}]"

        if inferred_type.nullable:
            imports.add("Optional")
            return f"Optional[{list_type}]"

        return list_type

    # -------------------------
    # Object → BaseModel
    # -------------------------
    if isinstance(inferred_type, ObjectInferredType):
        if type_name not in models:
            lines = [f"class {type_name}(BaseModel):"]

            if not inferred_type.properties:
                lines.append("    pass")
            else:
                for key, value in sorted(inferred_type.properties.items()):
                    nested_name = sanitize_class_name(f"{type_name}_{key}")
                    value_type = type_to_py(value, nested_name, models, imports)

                    if key not in inferred_type.required:
                        imports.add("Optional")
                        lines.append(f"    {key}: Optional[{value_type}] = None")
                    else:
                        lines.append(f"    {key}: {value_type}")

            models[type_name] = "\n".join(lines)

        if inferred_type.nullable:
            imports.add("Optional")
            return f"Optional[{type_name}]"

        return type_name

    # -------------------------
    # Union
    # -------------------------
    if isinstance(inferred_type, UnionInferredType):
        imports.add("Union")

        parts = []
        for i, t in enumerate(inferred_type.types):
            nested_name = f"{type_name}Option{i+1}"
            parts.append(type_to_py(t, nested_name, models, imports))

        union_expr = f"Union[{', '.join(parts)}]"

        if inferred_type.nullable:
            imports.add("Optional")
            return f"Optional[{union_expr}]"

        return union_expr

    return "Any"


# -------------------------------------------------------
# High-Level Generator
# -------------------------------------------------------

def generate_pydantic(
    samples: list[Any],
    root_name: str = "Root"
) -> str:
    """Generate Python Pydantic models from JSON samples."""

    inferred = infer_from_samples(samples)

    models: dict[str, str] = {}
    imports: set[str] = set()

    root_type = type_to_py(inferred, sanitize_class_name(root_name), models, imports)

    # --------------------------
    # Build final output
    # --------------------------

    lines = []

    # Base import
    lines.append("from pydantic import BaseModel")

    # typing imports
    typing_imports = sorted({i for i in imports if i != "EmailStr"})
    if typing_imports:
        lines.append(f"from typing import {', '.join(typing_imports)}")

    # Special import
    if "EmailStr" in imports:
        lines.append("from pydantic import EmailStr")

    lines.append("")
    lines.append("")

    # Nested models first (reverse order)
    for name in sorted(models.keys()):
        if name != root_name:
            lines.append(models[name])
            lines.append("")
            lines.append("")

    # Root model
    if root_name in models:
        lines.append(models[root_name])
    else:
        # Root is primitive/union
        lines.append(f"class {root_name}(BaseModel):")
        lines.append(f"    value: {root_type}")

    return "\n".join(lines)
