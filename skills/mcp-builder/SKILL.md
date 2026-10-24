---
name: mcp-builder
description: Design, implement, and verify Model Context Protocol servers in Python or TypeScript, including tool contracts, pagination, errors, and transport behavior. Use when exposing a local resource or authorized service to an MCP client.
license: Apache-2.0; see LICENSE.txt and SOURCES.md
---

# MCP builder

Build against the project's chosen SDK and the resource the user wants exposed. A local server and protocol client suffice for verification; no model-provider subscription or paid evaluation service is required.

## Define the contract

Inspect installed SDK types/examples and the matching specification before selecting APIs. When online access is available, use the official [specification](https://modelcontextprotocol.io/specification/), [Python SDK](https://github.com/modelcontextprotocol/python-sdk), or [TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk). If offline, use versioned local documentation and disclose unresolved compatibility questions.

Identify realistic tasks, required operations, inputs, outputs, and failures. Prefer stdio for a local subprocess; use a supported HTTP transport when remote access is required. Do not mirror an entire service API without a use case. Any external service needs its own credentials, network access, and authorization; choose local fixtures for tests.

## Choose the smallest sufficient implementation

Separate the required operations and preserved contracts from the proposed design. Apply YAGNI: implement tools for current tasks, not every endpoint or a speculative plugin system. Reuse existing project code, then standard-library facilities, native SDK/platform features, and installed dependencies before adding a new layer. Validate uncertain SDK behavior with the installed version or a focused local experiment. Add persistence, caching, retries, or orchestration only for a demonstrated need; preserve required authorization and consistency guarantees.

Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, evidence for its likelihood (or uncertainty), implementation and maintenance cost, and simpler alternative. Get user buy-in for that scope expansion unless existing approval already covers the trade-off. Do not silently add theoretical robustness, weaken required controls, or delay an already-authorized fix for a demonstrated defect.

## Implement

- Name tools by their action and explain when each applies. Validate bounds, enumerations, identifiers, and omitted/null semantics.
- Return useful structured results and a concise summary. Paginate/filter large outputs with explicit continuation state.
- Share authentication, timeouts, transport handling, and error translation. Distinguish invalid input, missing records, permission errors, rate limits, and service outages.
- Set behavior annotations accurately, including read-only, destructive, and idempotent properties. Annotations do not enforce access control.
- Keep stdio diagnostics on stderr and protocol traffic on stdout. Do not expose secrets in logs or errors.
- Pin dependencies and commit the applicable lockfile in the destination project. Preserve its existing stack.

## Verify and deliver

Type-check or compile where applicable. Use an SDK client or a locally installed, pinned MCP Inspector to test initialization, discovery, schemas, calls, and shutdown. Cover empty results, invalid inputs, pagination, and representative failures. Exercise writes only on authorized disposable fixtures.

Derive tests from the required operations and contracts, not the chosen implementation. Fix root causes and add regression coverage for reproduced failures. After tests pass, review the diff for duplicated validation, unnecessary adapters, and unused options; consolidate only genuinely shared behavior and preserve ordering, errors, and public interfaces.

Check that the tools can complete realistic tasks with known answers, not merely return success. Deliver source, run/configuration instructions, dependencies, and actual test outcomes. Separate protocol verification from model-based evaluation and name untested clients.

Example: “Expose a local reference directory with search and read tools.” Test allowed files, missing files, pagination, and attempts to escape the directory; return actionable errors without exposing arbitrary filesystem content.
