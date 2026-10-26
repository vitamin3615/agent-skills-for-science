# Survey Extraction Prompt

Extract source-traceable information from PubMed abstracts for a research-field map.

## Research context

{{research_question}}

## Source constraints

- Use only information stated in the supplied abstract.
- Do not infer sample sizes, methods, directions, mechanisms, or statistical results that are absent.
- Set source_level to “abstract”.
- Findings extracted from an abstract are mapping signals, not full-text-verified claims.
- Preserve the PMID exactly.

## Relevance

Include both direct and materially useful indirect evidence:

- 1.0: directly answers a central part of the research question;
- 0.5: indirect mechanistic, methodological, comparative, or contextual evidence that helps answer it;
- 0.0: does not materially contribute.

These values are ordinal triage labels for the legacy pipeline, not probabilities. Explain the inclusion or exclusion briefly. Do not require the focal entity's exact name when an accepted alias or clearly relevant indirect relationship is present.

## Extraction

For each abstract provide:

- pmid;
- relevance;
- inclusion_reason;
- topic: concise, groupable research area;
- focus: the paper's specific question;
- findings: only explicit abstract findings relevant to the map;
- details: sample, method, population/model, and entities only when stated;
- source_level;
- confidence: high, medium, or low, with a short reason.

Keep disagreements and null findings. Distinguish an author's causal claim from an association actually supported by the described design.

## Output

Return raw JSONL only, one object per abstract. Do not wrap it in a Markdown fence or add conversational text.

Example schema:

{"pmid":"12345678","relevance":1.0,"inclusion_reason":"Directly evaluates the focal exposure and outcome","topic":"Brief topic","focus":"Specific focus","findings":["Finding stated in the abstract"],"details":{"sample":"As reported or unknown","method":"As reported or unknown","entities":[]},"source_level":"abstract","confidence":{"level":"medium","reason":"Abstract lacks analysis details"}}

For an excluded record, retain the identifier:

{"pmid":"87654321","relevance":0.0,"inclusion_reason":"Does not address the mapped question","findings":[],"source_level":"abstract","confidence":{"level":"high","reason":"The abstract concerns a different topic"}}

## Final check

Before output, confirm that every finding is explicit in the abstract, every identifier is preserved, and no missing detail was filled from general knowledge.

{{chunk_content}}
