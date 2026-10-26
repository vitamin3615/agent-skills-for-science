# File Locations

Treat the skill directory as read-only code and reference material. Resolve scripts from the directory containing this `SKILL.md`; do not assume the current project has a `.claude/skills/` tree or is named `DailyUse`.

Write the research question, cleaned corpus, chunks, state, extracted records, and synthesis to a user-approved project directory. A practical layout is:

```text
<project-output>/
├── research_question.yaml
├── corpus_cleaned.md
├── chunks/
├── extracted/
└── synthesis/
```

Pass explicit input and output paths to scripts. Inspect each script's `--help` because defaults and required flags differ. Do not place generated output, caches, or credentials inside the globally installed skill.

For resumable work, keep the state file beside the corresponding project output so runs from different projects cannot collide. Delete or reset state only when the user requests a restart and the exact state path has been confirmed.
