- [x] **Delegated to python-coding-agent-acp** In `C:/temp/acp-custom-llm`, create a Python FastAPI project that exposes `GET /api/v1/version` and `POST /api/v1/data` with Pydantic request model `{a: int, b: int}` and JSON response containing the sum. Evidence required: list of created files and endpoint handler code locations.
- [x] **Delegated to python-coding-agent-acp** Add runnable startup command and dependency definition for FastAPI + Pydantic (+ ASGI server). Evidence required: exact run command and dependency file content.
- [x] **Delegated to python-coding-agent-acp** Verify endpoint behavior with concrete requests: `GET /api/v1/version` and `POST /api/v1/data` body `{"a":1,"b":2}`. Evidence required: command(s) executed and captured responses showing expected output.
- [x] **Delegated to python-coding-agent-acp** Mark all tasks complete only after evidence is written into this file.

---

## Evidence

### Created file list

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, build system, pytest config |
| `src/acp_custom_llm/__init__.py` | Package init (entry-point stub) |
| `src/acp_custom_llm/main.py` | FastAPI app, models, route handlers |
| `tests/test_main.py` | Unit tests (ASGI transport) + integration tests (real HTTP subprocess) |
| `tests/test_integration.py` | Standalone integration test script with server lifecycle management |
| `README.md` | Documentation, quick start, API reference |

### Endpoint handler line locations (`src/acp_custom_llm/main.py`)

- `GET /api/v1/version` — line 25 (`@app.get("/api/v1/version", response_model=VersionResponse)`), handler body at lines 26–28
- `POST /api/v1/data` — line 31 (`@app.post("/api/v1/data", response_model=DataResponse)`), handler body at lines 32–34

### Dependency content (`pyproject.toml`)

```toml
dependencies = [
    "fastapi>=0.162.0",
    "pydantic>=2.14.3",
    "uvicorn[standard]>=0.54.0",
]

[project.optional-dependencies]
test = [
    "pytest",
    "pytest-asyncio",
    "httpx",
]
```

### README startup command

```bash
uv run uvicorn acp_custom_llm.main:app --host 127.0.0.1 --port 8000 --reload
```

### Actual executed checks

```
uv run pytest -q
uv run python tests/test_integration.py
```

### Captured responses

**GET /api/v1/version** (status 200):
```json
{"version": "0.1.0"}
```

**POST /api/v1/data  {"a":1,"b":2}** (status 200):
```json
{"sum": 3}
```

**POST /api/v1/data  missing "a" (expect 422)** (status 422):
```json
{"detail": [{"type": "missing", "loc": ["body", "a"], "msg": "Field required", "input": {"b": 2}}]}
```

**POST /api/v1/data  non-int "a" (expect 422)** (status 422):
```json
{"detail": [{"type": "int_parsing", "loc": ["body", "a"], "msg": "Input should be a valid integer, unable to parse string as an integer", "input": "x"}]}
```

### Test results summary

- `uv run pytest -q`: **7 passed** in 5.26s (4 ASGI unit tests + 3 real HTTP integration tests)
- `uv run python tests/test_integration.py`: **All tests passed: True** (4 standalone checks — 1 GET 200, 1 POST 200, 2 POST 422)


## Existing external review gate

- [ ] **Human-only** Accept the generated FastAPI project and verification evidence under the existing `harness.json` `reviewGate.mode: human-required`; then permit archive/merge. The four delegated checkboxes above and their evidence were copied byte-for-byte from the actual executor; this pending gate was appended by the coordinator.
