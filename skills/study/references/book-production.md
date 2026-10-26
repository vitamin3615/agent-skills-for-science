# Book production

Read this when the learner asks for a book, course or multi-chapter self-study artifact rather than a live session. A book is the asynchronous form of a study session. The invariants of SKILL.md still hold; they become fixed devices on the page:

| Invariant | Book device |
|---|---|
| Map before detail, semantic edges | Whole-subject map in the front matter, redrawn at each chapter opener with the chapter's nodes highlighted and every edge labeled |
| Question-led traversal | One anchor question; each chapter answers one part of it; each section opens with the problem a naive approach fails on |
| Active construction | Predict pauses (answer, then reveal), mid-chapter exercises, graded end exercises with expected observables, and a transfer task |
| Relationship mastery | Each owned edge stated in words; review questions target edges and mechanisms |
| Purposeful representation | Visuals chosen per mechanism; ≥3 interactive widgets per chapter; text-only fallbacks |
| Epistemic integrity | "source states" / "code does" / "our reading" labels; a source↔code audit table |
| Goal-bounded scope | A chapter structure sized to the scope (from one chapter with sections to many chapters); foundations taught just in time, never as a preamble |

## 1. Frame (leader, before any writing)

1. Inspect the sources and any learner state (plan, progress, misconceptions). Set the reader profile from evidence: what they know, what they have never built, and the goals as observable capabilities ("can write the training loop from scratch").
2. Fix the arc: an anchor question and a chapter structure that the leader designs to fit the scope and goals. A narrow topic may need one chapter with several sections; a broad one may need many chapters. If the user gives a count, follow it. Order the chapters by dependency, each with a chapter question and the map nodes and edges it owns. Note which chapters can be read in either order.
3. Style: if the user names reference books, one worker samples each (TOC, one chapter opening, one math+code section, one chapter ending; ≤1,500 lines per book) and returns a ranked verdict, chapter template, rules and anti-patterns. Otherwise use `assets/book-kit/specs/style_guide.md`.
4. Write the front matter yourself (`README.md`): title, anchor, chapter table, the map with stable node IDs and labeled edges, a notation table fixed for the whole book, conventions (citation formats, epistemic labels, Predict pauses, listings, exercises and solutions), and how to run the code: the environment, the working directory (`code/`), the setup-listing convention, and, when the learner works in a notebook or on a remote runtime such as Colab, how to get the code there.
5. Pin the environment and data before parallel work: verify the runtime, install dependencies, pre-download shared real data so workers don't race, and git-ignore it.
6. Define the shared contract: the modules one chapter builds and later chapters import (names, signatures, keys, shapes). With it, independent chapters can be written in parallel. Copy `code/bookutil.py` from the kit into the book first: every chapter fetches its data through it (or through a subject helper built on it) and catches up on long prerequisites with it.
7. Fill the spec templates in `assets/book-kit/specs/` into the scratchpad, plus one short brief per chapter (sections, sources with pages/lines, required checks, known pitfalls, exercises).

## 2. Roles and pipeline

- **Leader**: framing, specs, adjudication, cross-chapter consistency, visual QA, small surgical fixes, bookkeeping. **Workhorses**: writing, verifying, illustrating.
  - Claude Code: Opus leads; workers are Agent calls with `model: sonnet`.
  - Codex: Astra leads; workers run on Sol through the host's subagent and model settings.
  - Without subagents: run the same phases yourself, in sequence, and make verification a fresh-context pass.
- **Per chapter**: write → independent verify → leader adjudicates each finding (accept, reject with evidence, or modify; verifiers are sometimes wrong) → the same writer fixes (resume it, so it keeps its context) → illustrate → leader QA → build.
- Run independent chapters in parallel. Start a dependent chapter once the modules it imports exist. Send scope changes to running workers as messages instead of restarting them.
- Parallel illustrators use per-chapter fragment prefixes. Only the leader edits the shared CSS, JS and build script.
- The leader reads reports and findings, spot-checks each chapter (headings, opening, one random section) and the screenshots. It does not reread whole chapters.
- When workers hit a usage limit, wait for the reset and resume each one with its context. Do not silently move work to the leader model: the user chose the split to control cost.
- When a parity check exposes a bug in a dependency (a port, a shared module), fix it narrowly, rerun its tests and every dependent chapter, and record it.

## 3. Chapter contract (details in the specs)

Opener ("This chapter covers", highlighted map, chapter question) → concept sections (naive failure → one analogy → picture → minimal math with a plain reading and a numeric example → code → result on the running example) → assemble → check against the reference → pitfalls → exercises → summary → recompressed map → bridge. Listings are ≤25 lines, numbered, with `#1` footnotes and shape comments, and appear verbatim in the companion script. They run as printed: each chapter opens with a setup listing, and after it every listing not captioned excerpt or abridged runs in book order in a fresh notebook (style guide, *Code listings*). Every number comes from a cited source or a real run. Use at most 3 callouts. Solutions live in `solutions/`. Writers leave `<!-- VISUAL: … -->` ideas for the illustrator.

## 4. Verification

Verifiers follow `specs/verifier_spec.md`: correctness → code (run it, diff the outputs, run `build/check_listings.py`) → pedagogy → consistency, and report severity-tagged findings with evidence. Before release, the leader runs `build/check_listings.py` on the whole book once from a copy of the code without `data/`, so first-use downloads are tested too. The failure modes it lists all occurred on a real book:
- design reasons and source silences presented as source statements;
- overclaimed matches, and circular or tautological checks;
- measurements in an unrepresentative mode, and seed-specific numbers;
- stale numbers and wrong line citations;
- unlabeled toys;
- repair history in reader-facing text.

Expect 5–15 findings per chapter, even from careful writers.

## 5. HTML book

- **Markdown is canonical; HTML is generated.** `build/build_html.py` turns md + `build/visuals/*.html` fragments + the template into pages. Never hand-edit the generated HTML. Start from `assets/book-kit/`. It contains:
  - `specs/`: the fill-in templates;
  - `build/build_html.py`: needs pandoc 3+ on PATH and beautifulsoup4;
  - `build/check_listings.py`: runs each chapter's listings from the Markdown, in book order, in a fresh interpreter, and checks them against the companion code;
  - `code/bookutil.py`: shared plumbing (`fetch`, `run_cells`);
  - `build/FRAGMENTS.md`: the fragment contract;
  - `build/shot.py`: Playwright screenshot QA;
  - `build/test_components.md`: a page that exercises every component;
  - `assets/book.css` and `assets/book.js`.
  Copy the kit into the new book and replace every `SUBJECT-SPECIFIC` spot: the title, the signature device, the map detection, the map layout, and the shared modules and extra code sources of the listing check.
- **Identity**: derive tokens per subject (light and dark palettes, display/body/mono faces, one signature device from the subject's own world). Load the host's design and diagramming guidance if it has any.
- **Components**: the chapter map rendered from data (highlighted nodes, labeled edges, text fallback); the Predict box (a per-viewer textarea plus a native reveal); callouts; listings with numbered badges and copy; MathJax SVG; highlight.js; mermaid; figures; exercises; an embedded companion-code appendix; prev/next and a theme toggle; reading progress (resume pill, "Continue reading" line and per-chapter percent on the index) and reader notes (select text, Add note, highlight via the CSS Custom Highlight API, a Notes panel with Markdown Export/Import). Progress and notes live in book.js only, stored per viewer in localStorage under one key per book folder; keep them when restyling.
- **Visuals**: the illustrator follows `specs/illustrator_spec.md`. It picks 6–10 mechanism visuals per chapter (≥3 interactive) and swaps `VISUAL` for `VISUAL-ID` markers. Data visuals embed real numbers extracted from the chapter's runs or artifacts; toys are labelled.
- **QA**: run `build/shot.py` (light/dark × 1280/400 px) and check horizontal overflow (wide display math needs its own scroll wrapper), console errors, MathJax errors, and clipped or overlapping labels. Exercise the per-viewer features once in a persistent browser profile: scroll a chapter and reload (resume pill), select text, add a note and reload (highlight returns), and open the Notes panel at 400 px (no overflow). Do one fix pass per round.

## 6. Close

- Log the artifact in the learner state without claiming mastery. Add the source↔code discrepancies found to the audit table, and record how to edit and rebuild the book in project memory.
- Report: where to open the book, a chapter table, what was verified (parity numbers, the `check_listings.py` result), dependency fixes, plain limitations, environment changes and git state. Tell the reader that progress and notes stay in the browser they use, and that Export/Import moves notes to another browser or machine.
- Exported notes (`*-notes.md`) saved in the study folder are learner evidence: read them at the next session for questions and confusions, and never rewrite them. Offer to publish where the host can.
