# ⚡ JSON Schema Forge — FastAPI Backend  
Powerful API for generating **JSON Schema**, **TypeScript interfaces**, and **Python Pydantic models** directly from JSON samples.

This backend powers the **JSON Schema Forge Web UI** and can also be used independently in any automation pipeline.

---

## ✨ Features

- 🔍 **Smart type inference** from raw JSON samples  
- 📝 Generate:
  - JSON Schema (Draft 2020-12)
  - TypeScript interfaces
  - Python Pydantic v2 models  
- 🎯 Detects common string formats:
  - Email  
  - URI  
  - ISO datetime  
  - UUID  
- 🧠 Handles:
  - Unions
  - Nullables
  - Nested objects
  - Arrays of mixed types  
- ⚡ Fast, production-ready API built with **FastAPI**
- 🌐 Fully CORS-enabled for frontend integration

---

## 🏗 Tech Stack

- **Python 3.11+**
- FastAPI
- Pydantic (v2)
- Uvicorn
- Typer (CLI support)
- pytest (optional dev)

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/json-schema-forge-api.git
cd json-schema-forge-api
```
Create a virtual environment:
```bash
python -m venv venv
```
Activate it:
Windows (PowerShell)
```bash
.\venv\Scripts\Activate
```
Linux / macOS
```bash
source venv/bin/activate
```
Install dependencies:
```bash
pip install -e .
```
🚀 Running the API
Start the FastAPI server:
```bash
uvicorn json_schema_forge.api:app --reload --port 8000
```
API will be available at:
```bash
http://localhost:8000
```
Interactive docs (Swagger):
```bash
http://localhost:8000/docs
```

⚙ pyproject.toml
Configured with:
- Build metadata
- Dependencies
- Optional dev tools (ruff, pytest, mypy)
- CLI entry point: json-schema-forge
  
🤝 Contributing
- Fork the repository
- Create a feature branch
- Commit your changes
- Submit a pull request

⭐ Support the Project
If you find JSON Schema Forge useful:
- Star the repo ⭐
- Share it with other developers
- Open issues for ideas & improvements
