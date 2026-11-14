# DataMate source

`datamate.agent` implements inference-contract guardrails. `datamate.data.catalog_audit`
contains catalog scanning, review and validation. `datamate.evaluation.tracing`
contains development trace comparison and SQL audit helpers. Runtime loaders,
execution, model integration, ranking and the inference entrypoint remain future work.

See [the current package architecture](../docs/architecture/package-structure.md)
for dependency rules and the distinction between existing code and planned runtime.
