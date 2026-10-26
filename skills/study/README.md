# Study: Knowledge-Map-First Learning

Study teaches through a small semantic knowledge map that changes with the
learner's demonstrated understanding. Questions select the route; labeled
relationships, misconception repair, synthesis, transfer, and review provide
the evidence for revision.

The runtime skill remains instruction-led. Optional scripts validate and export
state; they do not choose teaching content or replace the host agent's judgment.

## Installation and discovery

This repository keeps the package at:

```text
.claude/skills/study/
```

For current Codex repository discovery, expose the same folder at:

```text
.agents/skills/study/
```

The checked-in compatibility symlink prevents two copies from drifting. Codex
supports repository skills, optional `agents/openai.yaml`, and symlinked skill
folders; see the [official skill documentation](https://developers.openai.com/codex/skills/).

If copying elsewhere, copy the complete `study` directory into a supported
skill location. If an updated skill does not appear, restart the host.

## Invocation

Invoke explicitly in Codex with `$study`, or ask naturally for adaptive,
map-first learning. Example:

```text
Use $study to teach me gradient descent. My goal is to explain how learning
rate affects convergence, I know basic calculus, and I have 30 minutes. Begin
with the larger map and an anchor question.
```

Only a topic is required:

```text
Use $study to teach me why ice floats.
```

Study infers missing purpose, depth, route, modality, assessment, graph size,
and pacing. It asks at most one route-changing clarification before beginning
useful teaching.

## Modes

All modes share one living graph and learner state.

| Mode | Use |
|---|---|
| Explore | Build context and choose a promising frontier |
| Learn | Follow the smallest critical path to the anchor answer |
| Deep-Dive | Expand one mechanism, derivation, source, or controversy |
| Review | Hide and reconstruct nodes, edges, mechanisms, and maps |
| Challenge | Use transfer, counterexamples, and error diagnosis |
| Source | Preserve source structure, locators, claims, and evidence |
| Exam | Connect syllabus objectives to conceptual and assessment paths |
| Project | Learn through an artifact, investigation, or implementation |
| Teach-Back | Let the learner teach while Study diagnoses connections |

Mode switches preserve stable IDs, mastery evidence, misconceptions, source
links, and current route.

## State persistence

Study uses **[session-state.schema.json](references/session-state.schema.json)**
for portable state. The learner-facing map is one view of that state; canonical
node and edge mastery remain separate.

- When the host provides persistent state, store only learning-relevant data.
- When persistence is unavailable, request or produce `session_state.json` for
  a handoff or later session.
- Never assume that dialogue state survives a new session.
- Resume with retrieval and the current frontier rather than repeating the
  prior lesson.

The **[sample state](assets/session_state.example.json)** shows a
gradient-descent misconception, route revision, evidence records, separate
mastery, source-ready fields, and a mixed review queue.

## Artifact outputs

Core teaching works in plain text. When files help, Study can produce:

| File | Purpose |
|---|---|
| `session_state.json` | Canonical resumable learner state |
| `state_events.jsonl` | Optional archived evidence/revision stream |
| `map.json` | Learner-facing graph subset |
| `map.mmd` or `map.dot` | Mermaid or Graphviz diagram source |
| `lesson_notes.md` | Anchor-centered synthesis |
| `review_cards.csv` | Node, edge, mechanism, contrast, prediction, and transfer prompts |
| `review_schedule.csv` | Portable review dates and intervals |
| `blank_map.md` | Printable reconstruction exercise |
| `interactive_map.html` | Local state viewer with zoom and linear edge view |

Reusable output assets:

- **[blank-map-template.md](assets/blank-map-template.md)**
- **[review-cards.template.csv](assets/review_cards.template.csv)**
- **[review-schedule.template.csv](assets/review_schedule.template.csv)**
- **[interactive-map.html](assets/interactive-map.html)**

## Optional deterministic utilities

Both Python modules use the standard library and expose importable functions;
they intentionally provide no command-line interface.

```python
## Load and inspect state
## Validate references, then render the current core map.
import json
import sys
from pathlib import Path

skill_root = Path(".claude/skills/study").resolve()
sys.path.insert(0, str(skill_root))

from scripts.study_artifacts import render_mermaid, validate_state

state_path = skill_root / "assets/session_state.example.json"
state = json.loads(state_path.read_text(encoding="utf-8"))
errors = validate_state(state)
mermaid_source = render_mermaid(state, zoom="core")
```

```python
## Build portable review dates
## Schedule an agent-selected mixed queue without choosing its content.
from datetime import date

from scripts.review_scheduler import build_review_schedule

schedule = build_review_schedule(state, start_date=date.today())
```

`study_artifacts.export_artifacts` writes the portable map, notes, state, and
review CSVs into a caller-selected directory after validation.

## Example requests

```text
Use $study to teach me why ice floats. I know basic chemistry.

Use $study in Source mode. Map this chapter before we study it; I want the
argument, not paragraph memorization.

Use $study to teach Bayes' theorem through a knowledge map, interactive
examples, and progressive questions.

Use $study in Learn mode. I have 30 minutes to understand gradient descent
well enough to explain how learning rate affects convergence.

Use $study to build separate causal and chronological maps of the French
Revolution, then test connections rather than isolated dates.

Use $study in Source mode on these cellular-respiration notes. Identify
missing relationships and turn them into a guided path.

Use $study in Review mode. Hide parts of the map and make me reconstruct
them.

Use $study to teach recursion with visual execution traces, then connect it
to stacks, trees, induction, and dynamic programming.
```

## Package structure

```text
study/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── references/        conditional operational guidance and JSON Schema
├── assets/            portable templates, sample state, interactive viewer
├── scripts/           deterministic validation, rendering, export, scheduling
├── tests/             utility and package tests
└── evals/             behavioral cases, rubric, and synthetic source fixture
```

## Validation

Run package and utility checks from the repository root:

```bash
python .claude/skills/skill-audit/scripts/check_skill.py \
  .claude/skills/study

python -m unittest discover \
  -s .claude/skills/study/tests \
  -p 'test_*.py'
```

Parse the machine-readable resources directly:

```bash
python -m json.tool \
  .claude/skills/study/references/session-state.schema.json >/dev/null

python -m json.tool \
  .claude/skills/study/evals/evals.json >/dev/null
```

Behavioral evaluation uses **[evals.json](evals/evals.json)** and
**[rubric.md](evals/rubric.md)**. Run executors in isolated temporary
workspaces, hide expected behavior from them, and have independent judges score
actual transcripts and artifacts. The suite tests living multi-turn adaptation,
not exact wording or headings.

The **[design selection record](evals/design-selection.md)** summarizes the
three candidate versions, blinded shootout, finished-package forward tests, and
final adversarial audit.

## Example sessions

See **[example-sessions.md](references/example-sessions.md)** for four abridged
calibration sessions:

- why ice floats
- a source-linked synthetic textbook chapter
- gradient descent and learning rate
- a causal and chronological French Revolution map

These examples demonstrate decisions and state changes. They are not response
templates.
