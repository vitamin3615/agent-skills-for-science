# Agent skills for science

Four agent skills I built and use in my research as a neuroscientist, selected from a personal library of 70+. Each skill is a folder with a `SKILL.md` (the instructions an agent loads), plus references and scripts. They follow the open Agent Skills format, so the same folders work in Claude Code, Codex, Gemini CLI and Antigravity. The private version of `manuscript-editing` also draws on compiled sections of published papers, left out here for copyright.

Each skill builds a check into its workflow so an agent's output can be traced or tested, not just accepted.

| Skill | What it does | Built-in check |
|---|---|---|
| [`manuscript-editing`](skills/manuscript-editing) | Edits or drafts manuscript sections and cover letters at the requested scope: copy, scientific or structural edit, evaluation, or construction from supplied findings | An integrity protocol: never invents numbers, methods, citations or mechanisms; preserves claim strength and uncertainty; missing facts become editorial queries |
| [`study`](skills/study) | Teaches any subject from a small learner-specific knowledge map, using retrieval, prediction, worked examples, spaced review and transfer; in book mode, writer, verifier and illustrator agents produce a multi-chapter book (Markdown source plus interactive HTML) | Mastery is updated only from demonstrated understanding; book code listings are executed and checked; behavioral evaluation suite with a scoring rubric (`evals/`) |
| [`research-field-mapping`](skills/research-field-mapping) | Maps a PubMed corpus into themes, questions, methods and findings for a review structure or dataset | Every extracted item keeps its PMID; abstract-level signals are kept apart from claims that need full-text verification |
| [`raster-to-vector`](skills/raster-to-vector) | Redraws a raster scientific figure as a layered, editable vector illustration in [VectorCraft](https://github.com/storytold/vectorcraft), built from named parts rather than auto-traced | Pixel error and edge F1 against the source (`scripts/evaluate.py`), plus zoomed side-by-side reviews |

## Install

Keep one clone of this repo and symlink each skill into every agent's skills folder. All agents then share the same files, and `git pull` updates them all at once.

```bash
git clone https://github.com/vitamin3615/agent-skills-for-science.git
cd agent-skills-for-science
```

Where each agent looks for skills:

| Agent | User folder (all projects) | Project folder |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex (CLI, IDE extension, app) | `~/.agents/skills/` | `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Antigravity app and IDE | `~/.gemini/config/skills/` | `.agents/skills/` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` |

### macOS, Linux and WSL

Link every skill into the user folders of all the agents above (`~/.agents/skills` serves both Codex and Gemini CLI). Drop any folder for an agent you don't use.

```bash
for dir in ~/.claude/skills ~/.agents/skills ~/.gemini/config/skills ~/.gemini/antigravity-cli/skills; do
  mkdir -p "$dir"
  for skill in "$PWD"/skills/*; do
    ln -sfn "$skill" "$dir/$(basename "$skill")"
  done
done
```

To install a single skill for a single agent, link just that folder, for example `ln -s "$PWD/skills/study" ~/.claude/skills/study`. Gemini CLI can also install straight from GitHub: `gemini skills install https://github.com/vitamin3615/agent-skills-for-science.git --path skills/study`.

### Windows (without WSL)

Symbolic links need Developer Mode or an administrator PowerShell. In PowerShell, from the repo folder:

```powershell
foreach ($dir in "$HOME\.claude\skills", "$HOME\.agents\skills", "$HOME\.gemini\config\skills") {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  Get-ChildItem .\skills -Directory | ForEach-Object {
    New-Item -ItemType SymbolicLink -Force -Path (Join-Path $dir $_.Name) -Target $_.FullName | Out-Null
  }
}
```

Without links, copy the folders instead (`Copy-Item -Recurse .\skills\study "$HOME\.claude\skills\"`) and copy again after each `git pull`.

### Check that a skill loaded

- **Claude Code:** run `/skills`, or call one directly with `/study`. New skills appear without a restart; run `/reload-skills` if the skills folder did not exist when the session started.
- **Codex:** new skills are detected automatically; call one with `$study`. Restart Codex if a skill does not appear.
- **Gemini CLI:** run `/skills list`; after changes, `/skills reload`.
- **Antigravity:** start a new conversation and ask the agent to use the skill by name.

Agents also pick a skill on their own when a request matches its description, for example "teach me how AlphaFold works" for `study`.

### Requirements by skill

- `manuscript-editing`: none.
- `research-field-mapping`: Python 3 and `pysbd`.
- `raster-to-vector`: Python 3, the packages in `scripts/requirements.txt` and VectorCraft with its MCP server.
- `study`: none for tutoring; Python 3 and pandoc for book builds.

## Author

Zonghua Li, Ph.D. [Google Scholar](https://scholar.google.com/citations?user=novNNzUAAAAJ) · [LinkedIn](https://www.linkedin.com/in/zonghua-li-67b394146)

## License

[MIT](LICENSE)
