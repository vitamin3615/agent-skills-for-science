---
name: research-field-mapping
description: Map a biomedical literature corpus into source-traceable themes, questions, methods, and findings at scale. Use for organizing many PubMed records or abstracts into a review structure, coverage table, or structured dataset; distinguish abstract-level signals from full-text evidence.
---

# Research Field Mapping

Turn a literature corpus into a reproducible map without mistaking identifier coverage for analytical completeness.

## Define the map

Establish the review question, scope, intended audience, corpus source, date range, and inclusion logic. Decompose the question only as far as needed to distinguish meaningful themes. Do not force a fixed number of sections or a process-to-therapy narrative.

## Preserve source fidelity

For every extracted item retain its PMID or other stable identifier and the source location. Separate:

- what the abstract or full text explicitly reports;
- a synthesis inferred across sources;
- uncertainty or missing information.

Abstracts support abstract-level statements only. Mark claims requiring full-text verification before they are used as cite-ready evidence.

Use qualitative confidence (high, medium, low) with a reason instead of pseudo-precise relevance decimals unless a validated scoring model is part of the user's protocol.

## Scalable workflow

Adapt the mechanics to corpus size:

- clean and deduplicate records without changing identifiers;
- split large corpora into reproducible chunks;
- extract structured records under one schema;
- validate schema conformance and identifier coverage;
- inspect a sample for omission and misclassification;
- synthesize themes from the observed corpus;
- preserve checkpoints so failed chunks can resume.

A useful record normally contains the identifier, inclusion decision and reason, topic, focus, key findings, study context or methods, source level (abstract/full text), and confidence.

Direct mention of the focal entity is not universally required. Include indirect mechanistic, methodological, or contextual evidence when it materially answers the review question, and label the relationship.

## Workers and scripts

Use native Codex subagents when available for independent chunks, with one shared schema and a final reconciliation pass. External worker CLIs are optional, not prerequisites.

The deterministic scripts in scripts/ can clean, chunk, combine, validate, and format records. Resolve their paths relative to this skill. Inspect --help before use and write outputs only to the user-approved workspace.

scripts/utils/worker_spawner.py is a legacy external-CLI adapter. Use it only when the user selected that provider and supplied or accepted a current model configuration. Prefer the provider's configured default over hard-coded model names. Never remove Docker containers or unrelated temporary resources as part of retry handling.

Read these only when needed:

- [question decomposition](references/question_decomposition_guide.md)
- [survey extraction prompt](references/survey_prompt.md)
- [synthesis prompt](references/synthesis_prompt.md)
- [workflow details](references/workflow_guide.md)
- [external worker configuration](references/available_models.md)
- [file locations](references/file_locations.md)

Treat prompt templates as adaptable examples. Corpus-derived structure takes precedence over their suggested section counts or narrative order.

## Quality checks

Report separately:

- identifier coverage and duplicate handling;
- extraction/schema success;
- sampled extraction accuracy;
- excluded records and reasons;
- claims awaiting full-text verification;
- search and corpus limitations.

Do not call a map complete merely because every PMID appears in an output file.

## Output

Provide the requested structured file or narrative map plus a concise methods note. Themes should be traceable to records, disagreements should remain visible, and synthesis should not overstate what the source level supports.
