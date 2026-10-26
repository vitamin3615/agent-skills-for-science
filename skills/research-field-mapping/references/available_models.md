# External Worker Configuration

Model catalogs change frequently. Do not select a model from a static list in this skill.

## Preferred execution

Use native Codex subagents when available. They share the current environment and do not require a separate model catalog.

Use the legacy external worker adapter only when the user has selected an external provider or the workflow already depends on that provider's CLI.

## Model selection

By default, the worker adapter lets the installed provider CLI use its configured default. To pin a model deliberately, pass --model in the calling script or set the corresponding environment variable:

| Provider | Environment variable |
|---|---|
| Gemini | FIELD_MAPPING_GEMINI_MODEL |
| Claude | FIELD_MAPPING_CLAUDE_MODEL |
| Codex | FIELD_MAPPING_CODEX_MODEL |
| Copilot | FIELD_MAPPING_COPILOT_MODEL |
| GPT through Copilot | FIELD_MAPPING_GPT_MODEL |

Before a large run:

1. inspect the installed CLI's current help and authentication state;
2. test one small chunk with the selected/default model;
3. verify output schema and source fidelity;
4. estimate cost and concurrency limits when the provider charges externally.

Do not infer current availability, quality, context length, or price from a model name recorded in an old run.

## Availability checker

scripts/check_model_availability.py checks each installed CLI with its configured override or provider default. It makes real model calls; run it only when those calls are authorized and their cost is acceptable.

A successful “OK” response establishes connectivity, not suitability for literature extraction. Validate extraction quality on representative records before scaling.
