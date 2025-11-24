"""FastAPI backend for JSON Schema Forge."""

from typing import Any, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from json_schema_forge.core.schema_generator import generate_schema
from json_schema_forge.core.ts_generator import generate_typescript
from json_schema_forge.core.pydantic_generator import generate_pydantic
from json_schema_forge.config import __version__


app = FastAPI(
    title="JSON Schema Forge API",
    description="Generate JSON Schema, TypeScript types, and Pydantic models from JSON samples",
    version=__version__,
)

# CORS configuration (Next.js compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to exact domain before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------
# Request & Response Models
# -----------------------

class GenerateRequest(BaseModel):
    """Payload for /generate."""
    samples: list[Any] = Field(..., description="List of JSON objects or arrays of objects")
    outputs: list[Literal["schema", "ts", "py"]] = Field(
        default=["schema", "ts", "py"],
        description="Which outputs to generate",
    )
    rootName: str = Field(default="Root", description="Root type or class name")


class GenerateResponse(BaseModel):
    """API response."""
    schema: dict[str, Any] | None = None
    typescript: str | None = None
    python: str | None = None


# -----------------------
# Health Check
# -----------------------

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": __version__,
    }


# -----------------------
# Main Generator Endpoint
# -----------------------

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """Generate schema, TypeScript, or Python models."""

    if not request.samples:
        raise HTTPException(status_code=400, detail="No samples provided")

    response = GenerateResponse()

    try:
        # Generate JSON Schema
        if "schema" in request.outputs:
            response.schema = generate_schema(
                request.samples,
                root_name=request.rootName,
            )

        # Generate TypeScript Definitions
        if "ts" in request.outputs:
            response.typescript = generate_typescript(
                request.samples,
                root_name=request.rootName,
            )

        # Generate Python Pydantic Model
        if "py" in request.outputs:
            response.python = generate_pydantic(
                request.samples,
                root_name=request.rootName,
            )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


# -----------------------
# Root Endpoint
# -----------------------

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "JSON Schema Forge API",
        "version": __version__,
        "docs": "/docs",
    }
