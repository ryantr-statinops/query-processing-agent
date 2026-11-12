# Inference harness responsibilities

This page describes the boundaries a new DataMate harness should provide. The implementation is being rebuilt; see the [architecture proposal](architecture/agentic-rag.md) for the system graph and sequence. These responsibilities are design targets until a baseline demonstrates them.

## Responsibilities

| Stage | Responsibility | Required record |
|---|---|---|
| Request | Validate question ID, business ID, question text and `as_of_date`. | Request identity and validation result. |
| Retrieval | Load the matching business README, verified schema, relevant rules/calendar entries and entity evidence. | Retrieved source references and retrieval reason. |
| Planning | Produce a bounded structured plan grounded in retrieved schema and rules. | Plan, assumptions, expected answer type and cited sources. |
| Tool execution | Validate the plan and run only allowed read-only operations against the current business. | Query/tool request, typed result, error and elapsed time. |
| Verification | Check row grain, date range, filters, units, evidence coverage and answer shape. | Verification checks and unresolved evidence. |
| Answer | Return a competition typed answer, `unanswerable` when evidence is insufficient, or `abstain` when the system cannot safely conclude. | Final answer keyed by question ID. |

## Evidence and failure states

An empty valid result, a numeric zero, missing source, invalid schema, unsupported rule, malformed date, execution error, timeout and weak evidence must remain distinguishable. A tool failure must never be interpreted as a valid empty answer. Preserve source provenance through planning, execution and final verification.

The model receives no reference answers. Gold labels are used by development evaluation after predictions are produced. The 60-question exploration set includes 12 holdout questions whose labels have already been exposed, so results on those rows cannot be presented as an independent holdout score.

## Runtime boundary

The eventual submission runner must operate offline, read `/data` without modifying it, write typed answers to `/result/submission.jsonl`, and keep diagnostics under `/result/logs/`. Tool calls, retries, output rows and model resources must have explicit bounds. Exact model, retrieval, tool and plan contracts will be recorded after data tracing.
