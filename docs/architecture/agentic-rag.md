# Proposed agentic RAG architecture

**Status: proposal.** The source solver was removed. This document records the target flow for discussion and implementation planning; it does not claim that these components or interfaces exist yet. The team will confirm retrieval units, plan format, tools and model after validating the 30 training-business catalogs and tracing the 60 representative questions.

## System context

```mermaid
flowchart LR
    U["Question + business_id + as_of_date"] --> A["Offline answer agent"]
    A --> D["Business package<br/>CSV / Excel / SQLite"]
    A --> R["README + rulebook + calendar"]
    A --> S["Typed answer + diagnostics"]
    T["Train questions + labels"] -. "development evaluation only" .-> E["Local evaluator"]
    S --> E
    P["Public-test package"] -. "structure compatibility only" .-> A
    H["Holdout labels exposed in 12 sample rows"] -. "caveat: not independent" .-> E
```

## Component and evidence flow

```mermaid
flowchart TD
    Q["Request validator"] --> C["Business context loader"]
    C --> K["Verified schema catalog"]
    C --> D["README / rule / calendar retrieval"]
    C --> N["Entity and value lookup"]
    K --> X["Context pack with source references"]
    D --> X
    N --> X
    X --> M["Model planner"]
    M --> V["Plan validator"]
    V -->|"valid and grounded"| T["Read-only query/tool executor"]
    V -->|"invalid or ungrounded"| F["Structured failure / bounded retry"]
    T --> E["Evidence verifier"]
    E -->|"more evidence needed and budget remains"| X
    E -->|"sufficient evidence"| W["Typed answer writer"]
    E -->|"insufficient / failed / budget exhausted"| A["unanswerable or abstain"]
    W --> O["submission.jsonl"]
    F --> L["Per-question diagnostics"]
    A --> O
    E --> L
    T --> L
```

The executor handles one business context at a time. The validator restricts operations to the approved read-only interface and verifies referenced tables/columns against the retrieved catalog. The verifier checks evidence and result shape before answer serialization. Retrieval and tool retries are bounded; errors, empty results and valid zero values remain distinct.

## Per-question sequence

```mermaid
sequenceDiagram
    participant Runner
    participant Retriever
    participant Planner as Offline model
    participant Guard as Plan validator
    participant Tool as Read-only executor
    participant Verify as Evidence verifier
    participant Writer

    Runner->>Retriever: question, business_id, as_of_date
    Retriever-->>Runner: schema, rules, entities, source references
    Runner->>Planner: question + bounded grounded context
    Planner-->>Guard: structured plan with cited sources
    Guard->>Guard: validate fields, references and allowed operations
    Guard->>Tool: validated query/tool request
    Tool-->>Verify: typed rows, schema, status, provenance
    Verify->>Verify: check date, filters, units, grain and evidence
    alt More evidence required and budget remains
        Verify-->>Retriever: targeted evidence request
        Retriever-->>Planner: additional bounded context
    else Evidence sufficient
        Verify->>Writer: verified result + answer type
        Writer-->>Runner: typed answer + trace reference
    else Cannot conclude
        Verify-->>Runner: unanswerable or abstain + reason
    end
```

## Data preparation and evaluation boundary

```mermaid
flowchart LR
    RAW["Read-only train business packages"] --> CAT["Verified catalog:<br/>files, sheets, headers, grain, keys, quality"]
    RAW --> TRACE["60 question traces:<br/>source → rule → calculation → answer comparison"]
    CAT --> DESIGN["Inference contract and retrieval/tool design"]
    TRACE --> DESIGN
    DESIGN --> BASE["Baseline on traced examples"]
    DEV["24 development businesses"] --> TUNE["Development comparison and iteration"]
    BASE --> TUNE
    EXPOSED["6 holdout businesses;<br/>12 sample labels already exposed"] --> CAVEAT["Exploratory only;<br/>not an independent final evaluation"]
    PUBLIC["Public-test packages"] --> STRUCT["Schema compatibility inspection only"]
```

Development/holdout assignment follows `configs/splits/seed_2026.json`. The representative sample contains 48 development and 12 holdout questions. The team may trace all 60 as agreed, while reporting the holdout exposure caveat and avoiding claims of independent evaluation on those examples.

## Decisions deferred until data tracing

- Lexical, schema-aware or dense retrieval and whether an index is needed.
- Structured JSON plan versus constrained SQL, or a measured combination.
- Exact tool schemas, error statuses, retry/budget limits and evidence thresholds.
- Model and runtime selection under offline, parameter, latency and memory limits.
- Package boundaries and final code-level dependency graph.
