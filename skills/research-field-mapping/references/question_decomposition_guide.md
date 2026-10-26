# Question Decomposition Guide

Decompose a broad literature question only enough to make inclusion and extraction decisions reproducible.

## Identify the dimensions

Depending on the question, record:

- population, organism, tissue, or setting;
- focal entity, exposure, intervention, comparison, or mechanism;
- outcomes or phenomena of interest;
- eligible study designs, data modalities, and source types;
- date, language, publication-status, and other scope boundaries;
- distinctions the final map must preserve.

Generate synonyms and identifiers from relevant records and controlled vocabularies, not from a fixed template alone.

## Define inclusion logic

Write conditions that another analyst could apply. Distinguish hard exclusions from signals used only for prioritization. Direct mention of the focal term is not a universal gate: an indirect mechanistic, methodological, or contextual paper may belong if it materially answers the question.

Check for contradictions between comparison groups and inclusion criteria. Test the logic on a small sample of clearly eligible, clearly ineligible, and borderline records before scaling.

## Calibrate scope empirically

Estimate scope from a pilot search or the supplied corpus. There is no universal correct paper count or relevance cutoff. Narrow or broaden according to the intended review, available evidence, and feasible validation effort.

## Minimal configuration

A configuration may contain:

```yaml
question: "<precise review question>"
include:
  - "<source-verifiable condition>"
exclude:
  - "<non-overlapping exclusion>"
focus_terms:
  - "<term or synonym>"
context: "<purpose and distinctions to preserve>"
```

The extraction schema and written logic are authoritative. Any legacy numeric relevance field should be treated as an ordinal routing label unless the user supplies a validated scoring model.
