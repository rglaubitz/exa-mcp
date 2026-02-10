# Session: Fix 2 — Flatten Tool Signatures (Slices 1-3)

Parent: ~/.claude/plans/breezy-singing-ladybug.md
Estimated TDD cycles: 3

## Problem

All exa tools use `async def tool(params: PydanticModel, ctx: Context)`. FastMCP exposes
this as `{"params": {"query": "..."}}` but models send flat `{"query": "..."}`, causing
validation failures. Fix: change tool functions to accept individual keyword arguments.

## Slices

### Slice 1: exa_answer

- Test: tests/tools/test_answer.py
- Source: src/exa_mcp/tools/answer.py, src/exa_mcp/models/answer.py

RED: Add test that calls `exa_answer` with flat `{"query": "..."}` (no `params` wrapper).
GREEN: Refactor `exa_answer` to accept individual kwargs. Keep AnswerInput model for internal validation.
REFACTOR: Update existing tests from `{"params": {...}}` to flat format.

### Slice 2: exa_search

- Test: tests/tools/test_search.py
- Source: src/exa_mcp/tools/search.py, src/exa_mcp/models/search.py

RED: Add test that calls `exa_search` with flat `{"query": "..."}` (no `params` wrapper).
GREEN: Refactor `exa_search` to accept individual kwargs. Keep SearchInput model for internal validation.
REFACTOR: Update existing tests from `{"params": {...}}` to flat format.

### Slice 3: exa_get_contents

- Test: tests/tools/test_contents.py
- Source: src/exa_mcp/tools/contents.py, src/exa_mcp/models/contents.py

RED: Add test that calls `exa_get_contents` with flat `{"urls": [...]}` (no `params` wrapper).
GREEN: Refactor `exa_get_contents` to accept individual kwargs. Keep GetContentsInput model for internal validation.
REFACTOR: Update existing tests from `{"params": {...}}` to flat format.

## Approach

For each tool, the transformation is:

```python
# BEFORE (nested params)
@mcp.tool()
async def exa_answer(params: AnswerInput, ctx: Context) -> str:
    query = params.query
    ...

# AFTER (flat kwargs)
@mcp.tool()
async def exa_answer(
    query: str,
    num_results: int = 5,
    ...,
    ctx: Context,
) -> str:
    ...
```

FastMCP injects `ctx: Context` automatically when it sees the type annotation — it won't
appear in the tool schema. Individual kwargs become flat top-level properties in the schema.

## Done When

- [ ] All slices committed
- [ ] Full suite passes
- [ ] `client.call_tool("exa_answer", {"query": "..."})` works (no params wrapper)
