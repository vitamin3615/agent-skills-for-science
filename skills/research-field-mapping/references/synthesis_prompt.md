# Literature Synthesis Prompt

Organize extracted records into a field map that answers the research question and preserves source traceability.

## Inputs

Use the research question, corpus scope, structured records, and their PMIDs or other stable identifiers. Respect source_level and confidence fields.

## Build the taxonomy from the corpus

Choose an organizational axis that best represents the observed literature, such as mechanism, population, method, disease stage, intervention, or competing explanations. The corpus may support one axis, a hybrid, or only a flat map.

Do not force:

- a fixed number of scopes, sections, or papers per section;
- question-form headings;
- a phenomenon-to-mechanism-to-therapy narrative;
- exclusive assignment when a paper legitimately informs multiple themes.

Explain the organizing logic briefly and identify material records that do not fit it.

## Consolidate evidence

Within each theme:

- group genuinely equivalent findings and retain every supporting identifier;
- keep different populations, models, methods, or outcomes separate when they affect interpretation;
- surface contradictory and null findings;
- distinguish abstract-level reports from full-text-verified evidence;
- separate source statements from cross-paper inference;
- note whether apparent disagreement could arise from design or context.

Do not merge findings solely because they mention the same entity and direction.

## Validate coverage

Report identifier coverage, duplicates, excluded records and reasons, unmapped records, schema failures, and claims requiring full-text verification. Coverage is a data-processing measure, not proof that the taxonomy or synthesis is correct.

Inspect representative records from each major theme and a sample of excluded/unmapped records before finalizing.

## Output

Return the requested JSON, table, outline, or narrative. Every substantive theme and claim must remain traceable to source identifiers. Include a short methods and limitations note describing corpus source, dates, source level, and validation performed.
