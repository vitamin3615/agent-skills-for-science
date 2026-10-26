# Field-Mapping Workflow Guide

Use only the stages needed for the corpus and requested deliverable.

## Configure

Record the review question, scope, corpus source, search or collection date, inclusion logic, source level, and output schema. A YAML file is convenient but optional. Do not encode a decimal relevance threshold as though it were a calibrated probability.

## Prepare the corpus

Preserve stable identifiers while cleaning and deduplicating. Create reproducible chunks for a large corpus and retain a manifest from each chunk to its input records.

## Extract

Apply one schema to every chunk. Require the worker to distinguish explicit source content from inference and to mark abstract-only records. Use native subagents when available. If the user deliberately selects an external provider, inspect the orchestrator's current `--help` and provide the required `--worker`; use an explicit `--model` only when the user wants to pin one.

## Validate and resume

Check schema conformance, identifier coverage, duplicates, exclusions, and a sample of source-to-extraction accuracy. A successful parse is not evidence of semantic accuracy. Preserve state for incomplete chunks; use reset only after confirming the exact project-local state file.

## Synthesize

Derive themes from the observed records rather than a fixed section count. Keep disagreement, uncertainty, and source-level limits visible. Findings extracted from an abstract are leads for synthesis, not automatically cite-ready support for details that require full text.

## Report

Return the map or dataset plus a concise methods note covering corpus provenance, inclusion logic, extraction method, validation, source level, and limitations.
