# Agent skills for science

Four agent skills I built and use in my research as a neuroscientist, selected from a personal library of 70+. Each skill is a folder with a `SKILL.md` (the instructions an agent loads), plus references and scripts. They follow the Agent Skills format used by Claude Code, Codex and Gemini CLI. The private version of `manuscript-editing` also draws on compiled sections of published papers, left out here for copyright.

Each skill builds a check into its workflow so an agent's output can be traced or tested, not just accepted.

| Skill | What it does | Built-in check |
|---|---|---|
| [`manuscript-editing`](skills/manuscript-editing) | Edits or drafts manuscript sections and cover letters at the requested scope: copy, scientific or structural edit, evaluation, or construction from supplied findings | An integrity protocol: never invents numbers, methods, citations or mechanisms; preserves claim strength and uncertainty; missing facts become editorial queries |
| [`study`](skills/study) | Teaches any subject from a small learner-specific knowledge map, using retrieval, prediction, worked examples, spaced review and transfer; in book mode, writer, verifier and illustrator agents produce a multi-chapter book (Markdown source plus interactive HTML) | Mastery is updated only from demonstrated understanding; book code listings are executed and checked; behavioral evaluation suite with a scoring rubric (`evals/`) |
| [`research-field-mapping`](skills/research-field-mapping) | Maps a PubMed corpus into themes, questions, methods and findings for a review structure or dataset | Every extracted item keeps its PMID; abstract-level signals are kept apart from claims that need full-text verification |
| [`raster-to-vector`](skills/raster-to-vector) | Redraws a raster scientific figure as a layered, editable vector illustration in [VectorCraft](https://github.com/storytold/vectorcraft), built from named parts rather than auto-traced | Pixel error and edge F1 against the source (`scripts/evaluate.py`), plus zoomed side-by-side reviews |

## Install

Copy or symlink a skill folder into your agent's skills directory, for example:

```bash
ln -s "$PWD/skills/study" ~/.claude/skills/study
```

Requirements by skill:

- `manuscript-editing`: none.
- `research-field-mapping`: Python 3 and `pysbd`.
- `raster-to-vector`: Python 3, the packages in `scripts/requirements.txt` and VectorCraft with its MCP server.
- `study`: none for tutoring; Python 3 and pandoc for book builds.

## Author

Zonghua Li, Ph.D. [Google Scholar](https://scholar.google.com/citations?user=novNNzUAAAAJ) · [LinkedIn](https://www.linkedin.com/in/zonghua-li-67b394146)

## License

[MIT](LICENSE)
