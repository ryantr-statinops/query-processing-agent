# DataMate source

`datamate.agent` implements the inference-contract guardrails. Catalog audit and
trace audit helpers are being moved into their package boundaries as part of the
structure refactor. Runtime loaders, execution, model integration and the inference
entrypoint remain future work.

See [the current package architecture](../docs/architecture/package-structure.md)
for dependency rules and the distinction between existing code and planned runtime.
