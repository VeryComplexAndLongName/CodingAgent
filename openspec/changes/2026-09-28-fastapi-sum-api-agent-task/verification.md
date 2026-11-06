# Real Python ACP execution — 2026-11-06

The actual coding-agent 0.10.1 ACP server generated `C:/temp/acp-custom-llm`
using QuantTrio/Qwen3.6-35B-A3B-AWQ at the requested endpoint. The old
Workbench alias is not registered in the current UI, so execution used the
real Python binary over ACP protocol 1, not a substitute built-in agent.
Initialization, session creation, tools and the final completed turn are
recorded in the private local transcripts; compact provenance is in
[execution-proof.json](execution-proof.json). Credentials stayed in process
memory/environment and were never written to files or command-line arguments.

The first three turns hit their cumulative token cap while implementing and
fixing the app (including inherited proxy failures on localhost). The focused
fourth turn completed the remaining tests and wrote/checkmarked the four
original delegated tasks itself. A fifth documentation-only turn corrected
test-extra installation instructions, handler line references and arithmetic
in the summary. The coordinator did not implement the generated service.

Independent verification: 7 pytest tests passed; standalone real HTTP checks
returned GET version 200/{"version":"0.1.0"}, POST 1+2 200/{"sum":3}, and two
422 cases (missing field / noninteger input). Clients bypass proxy settings
only for their own localhost requests; no machine proxy settings changed.
Servers are short-lived and terminated by test finally blocks.

The generated project is preserved in the requested external directory and
in the user-facing `codingagent-fastapi-review-2026-11-06.zip` bundle. The
source manifest and bundle SHA-256 are recorded in execution-proof.json.
The original executor-authored task evidence was copied intact to tasks.md;
the existing pending human review was appended as a separate open task.

## Reviewable endpoint implementation

```python
"""FastAPI application with /version and /data endpoints."""

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Custom LLM API", version="0.1.0")


class DataRequest(BaseModel):
    """Simple request body with two integers."""
    a: int
    b: int


class DataResponse(BaseModel):
    """Response containing the computed sum."""
    sum: int


class VersionResponse(BaseModel):
    """Static version info."""
    version: str


@app.get("/api/v1/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """Return the API version."""
    return VersionResponse(version="0.1.0")


@app.post("/api/v1/data", response_model=DataResponse)
async def post_data(body: DataRequest) -> DataResponse:
    """Return the sum of a and b."""
    return DataResponse(sum=body.a + body.b)


def main() -> None:
    """Entry point when run as a script."""
    import uvicorn

    uvicorn.run(
        "acp_custom_llm.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
```

## Human action

Review the generated project and endpoint evidence, then explicitly accept it.
The existing harness.json says `autonomyLevel: assisted` and
`reviewGate.mode: human-required`; the harness review policy is documented in
HARNESS.md. This change remains active and the PR remains a draft until that
review. No service deployment, registry changes or parent library runtime
changes are part of this task.

## Independent parent-repository checks

The parent library, tests, pyproject.toml and uv.lock are byte-unchanged from
base 5d3ae591a79ffca0d9977c4a0497713dd6869aa1. In an isolated .venv,
71 existing tests passed with NO_PROXY limited to 127.0.0.1/localhost for this
check process. The first run inherited the machine proxy and failed four
localhost tests with 502; that run is not reported as passing.

Static checks of unchanged parent sources are not green with current tools:
Ruff 0.17.4 reports 12 pre-existing findings; mypy 2.4.1 initially reports
missing lxml stubs, and installing lxml-stubs exposes 52 existing typing errors
in tools/web.py. No rules were disabled and no parent library code was changed
for this external demo task. The generated app's 7 tests and real HTTP checks
are the task acceptance evidence; the parent static debt is disclosed rather
than presented as green.

Executor-authored line references in tasks.md are zero-based tool offsets.
One-based locations in the actual source are GET decorator 26 / handler 27,
and POST decorator 32 / handler 33. The full handler source above is authoritative.
