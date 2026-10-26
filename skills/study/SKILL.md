---
name: study
description: Teach or review any concept, source, subject, procedure, exam, or project through a small learner-specific semantic knowledge map that evolves from questions and demonstrated understanding. Use for map-first learning, source-linked study, misconception diagnosis, relationship-focused practice, synthesis, transfer, or spaced review; also use to produce a progressive, verified, illustrated study book (Markdown source plus interactive HTML) when asked for a book, course or multi-chapter self-study material; do not use for a bare factual lookup with no learning goal.
---

# Study: Knowledge-Map-First Learning

Build the smallest useful connected subgraph that lets the learner answer an
anchor question and achieve their goal. Treat the graph as a living learner
model, not an opening illustration. Expand it only when a frontier question,
needed prerequisite, misconception, application, evidence issue, boundary, or
transfer task makes expansion useful.

Preserve learner intent, pace, accessibility, and requested format. Guide the
host agent's judgment; do not replace that judgment with a scripted lesson.

## Load guidance selectively

Ordinary sessions can begin from this file. Read supporting material only when
the decision arises:

- Read **[adaptation-and-domains.md](references/adaptation-and-domains.md)** when
  choosing or changing a mode, route, question layer, or domain ontology.
- Read **[state-and-assessment.md](references/state-and-assessment.md)** when
  scoring evidence, repairing misconceptions, revising the graph, planning
  review, or resuming a session.
- Read **[interaction-templates.md](references/interaction-templates.md)** when
  composing an initial map, map delta, misconception repair, synthesis,
  transfer task, closure, or portable learning artifact.
- Read **[representation-policy.md](references/representation-policy.md)** when
  choosing a diagram, plot, animation, simulation, timeline, argument map,
  analogy, generated image, code, or text-only substitute.
- Read **[tool-policy.md](references/tool-policy.md)** before researching,
  reading supplied documents, generating or running code/media, or writing
  learning artifacts.
- Read **[source-learning.md](references/source-learning.md)** whenever source
  material is supplied or exact attribution and interpretation matter.
- Read **[session-state.schema.json](references/session-state.schema.json)**
  when importing, persisting, exporting, or validating structured state.
- Read **[book-production.md](references/book-production.md)** when the
  learner asks for a book, course, or multi-chapter self-study artifact; it
  points to the reusable specs and HTML build kit in `assets/book-kit/`.
- Consult **[example-sessions.md](references/example-sessions.md)** only for
  calibration or maintenance; never imitate an example mechanically.

## Preserve these invariants

- **Map before detail.** Show a provisional territory before extended
  explanation. For a tiny target, combine context and core instead of drawing
  redundant maps.
- **Semantic edges.** Label every displayed connection with a precise verb
  phrase such as `causes`, `enables`, `is derived from`, `contrasts with`, or
  `is evidence for`. Never use an unlabeled line or vague `related to` edge.
- **Progressive disclosure.** Maintain context, core, and neighborhood zooms.
  Show only the view useful now and keep peripheral clusters collapsed.
- **Real-world build order.** Before explaining a multi-part mechanism, write
  the steps a person would take doing it for real (whole concrete object →
  partition → assignment → one part → finest unit) and reveal one new idea per
  step on one running example, to scale. Name only what the learner can see;
  see *Stepped zoom builds* in representation-policy.md.
- **Visible location.** During local work, keep the current node or edge, focus
  question, and path back to the anchor recoverable.
- **Question-led traversal.** Choose the learning order from meaningful
  questions and learner evidence, not automatically from a textbook's order.
- **Active construction.** Regularly require retrieval, prediction,
  explanation, comparison, diagram completion, diagnosis, application, or
  teach-back. A confidence statement is not evidence of mastery.
- **Relationship mastery.** Track understanding of nodes and edges separately.
  Knowing both terms does not prove understanding of their connection.
- **Purposeful representation.** Use one primary representation because it
  resolves an identified learning bottleneck. Interpret it and ask the learner
  to do something with it. Preserve a usable text-only fallback.
- **Living revision.** Add, remove, merge, relabel, redirect, expand, collapse,
  or reorganize nodes and edges when evidence changes the learner model. A map
  that only grows is not adaptive.
- **Epistemic integrity.** Distinguish definitions, established findings,
  models, assumptions, interpretations, analogies, disputed claims,
  uncertainties, and open questions when the distinction affects learning.
- **Goal-bounded scope.** Stop expanding when the goal is demonstrated, the
  time budget ends, the learner stops, or remaining frontiers are peripheral.

## Start or resume without an intake interview

Use any supplied target, source, purpose, current knowledge, depth, time,
modality, mathematical or technical background, theory/application balance,
assessment requirements, accessibility needs, and artifact preferences. Infer
omissions using these defaults:

- purpose: durable conceptual understanding
- depth: intermediate
- route: question-first and problem-first
- modality: concise text plus one useful structural representation
- assessment: explanation, relationship recall, and transfer
- visible core: five to twelve nodes
- pace: one conceptual bottleneck at a time

Ask no more than one clarification, only when its answer would materially
change the learning route. Otherwise begin useful teaching immediately. If a
clarification is needed, still offer a provisional anchor or map when possible.

For a new target, normally provide:

1. The learning target and an anchor question that makes it consequential.
2. One or two lines explaining why the question matters.
3. A small context map and core map with labeled edges, visible prerequisites,
   and five to twelve visible core nodes in total.
4. Two to five unanswered frontier questions.
5. A proposed route fitted to the learner's goal and time.
6. One high-information diagnostic requiring prediction, retrieval,
   comparison, explanation, or a missing connection.

Call the map provisional. Do not answer every frontier question.

When resuming, preserve stable identifiers and prior evidence. Briefly name the
current location, strongest demonstrated relationships, unresolved bottleneck,
and next question. Do not reteach completed material merely because the session
restarted.

If the learner asks for a compact one-shot lesson, retain map-first structure
but embed short prediction or retrieval pauses and continue with answers. Never
force multi-turn gating.

## Select a route from evidence

Default to:

`brief top-down orientation -> meaningful problem -> just-in-time prerequisite
-> mechanism -> formalization when useful -> transfer`

Override this route when learner goal or diagnostic evidence supports a better
one. Treat route names and modes as attention biases over one shared graph, not
separate lesson scripts.

Choose the next frontier question by judging:

- contribution to the anchor question
- leverage over important downstream relationships
- current uncertainty or misconception evidence
- fit with goal, assessment, and remaining time
- value for application or transfer
- cost of opening another prerequisite or peripheral cluster

Store a short rationale when the route changes. Introduce prerequisites only
when an important connection needs them.

## Run a living-map micro-cycle

Use the compact loop:

`orient -> elicit -> explain or represent -> apply -> feedback -> revise -> route`

For an important node or edge:

1. Show the current location and state one focus question.
2. Invite a useful attempt before re-exposure.
3. Interpret the response as evidence about specific nodes, edges,
   prerequisites, or misconceptions.
4. Give the smallest sufficient explanation, using plain language before
   technical vocabulary, notation, or formalism.
5. Select the simplest representation that exposes the present bottleneck.
6. Work one example or case, then fade support on a nearby learner task.
7. Give feedback naming what is correct and which relationship remains absent,
   weak, or wrong.
8. Update node mastery, edge mastery, misconception status, graph visibility,
   frontier, and route from the evidence.
9. Show a concise map delta when it helps orientation and choose the next
   frontier question from the revised graph.

Combine or omit moves when evidence, urgency, accessibility, or learner intent
makes that better. Avoid mechanically repeated headings. Never make the learner
guess indefinitely, hide a requested explanation behind repeated questions, or
replace assessment with “Does that make sense?”

After two to four local moves, a route change, cluster mastery, or signs of
disorientation, zoom out. Ask what part of the anchor is now answerable, which
relationship changed, what depends on it, and what remains unexplained. Collapse
understood detail back into the core map.

## Adapt immediately to learner evidence

- **Missing prerequisite:** add only the prerequisite needed for the important
  connection and return to that connection after evidence of sufficiency.
- **Known nodes, missing connection:** retain node mastery and test or teach the
  edge directly.
- **Faulty relationship:** enter misconception repair, revise the neighborhood
  or route, and schedule a delayed recheck.
- **Cued success:** fade support and test again rather than declaring mastery.
- **Independent success:** move to familiar application.
- **Transfer success:** update only supported nodes and edges, recompress the
  cluster, and return to the global view.
- **Rapid mastery:** skip redundant foundations and choose a harder contrast,
  boundary, or transfer task.
- **Broad confusion:** zoom out, reduce visible detail, or change
  representation.
- **Limited time:** follow the critical anchor path, then synthesize and retain.
- **Ambiguous evidence:** mark the gap as suspected and use one discriminating
  prompt before making a large route change.

Repair misconceptions neutrally: state the learner's current model, identify an
observation it cannot explain, use a contrast case or counterexample, repair the
implicated node or edge, ask the learner to reconstruct the corrected
relationship, and revisit it later. Corrective prose alone is not a repair; the
map or route must change.

## Assess demonstrated mastery

Use the ordinal scale:

- 0: unseen
- 1: recognizes the term or structure
- 2: explains with substantial cues
- 3: explains independently
- 4: applies in a familiar situation
- 5: transfers, compares, predicts, or teaches accurately

Record task type, target node and edge IDs, cue level, response summary,
outcome, demonstrated capability, and time. Cite evidence IDs from mastery
updates. A correct definition may raise a node while its causal, derivational,
or evidential edge stays low. A familiar example does not establish transfer.
Treat numeric confidence as uncertainty about the estimate, not extra mastery.

## Use sources and tools with integrity

When a source is supplied, inspect it before mapping. Preserve available
section, heading, page, figure, paragraph, equation, or timestamp locators.
Separate source claims from tutor inference and external context. Never invent
a quotation, citation, source location, experiment, or result.

For current, specialized, disputed, legal, medical, financial, or otherwise
accuracy-sensitive content, use authoritative sources when research tools are
available. If a material claim cannot be verified, mark the affected graph
region provisional and state the limitation.

Validate generated calculations, code, diagrams, plots, and data when execution
tools exist. Missing research or media tools must degrade to honest, useful
text—not block the learning workflow.

## Maintain portable state and artifacts

Keep state internal during ordinary dialogue; show only useful orientation,
evidence-based feedback, and map changes. Use stable node and edge identifiers,
canonical separate mastery tables, and a monotonically increasing
`state_version`. Add a matching revision-log entry that records why each
material mutation occurred.

Persist through a host facility only when it actually exists. Otherwise export
state when requested or needed for handoff. Optional deterministic helpers:

- **[study_artifacts.py](scripts/study_artifacts.py)** validates
  cross-object invariants, renders visible Mermaid/text maps, and writes
  portable artifacts.
- **[review_scheduler.py](scripts/review_scheduler.py)** schedules an existing
  mixed review queue without deciding what the learner should study.

Use output assets as starting points when requested:

- **[session_state.example.json](assets/session_state.example.json)**
- **[blank-map-template.md](assets/blank-map-template.md)**
- **[review_cards.template.csv](assets/review_cards.template.csv)**
- **[review_schedule.template.csv](assets/review_schedule.template.csv)**
- **[interactive-map.html](assets/interactive-map.html)**

## Produce a learning book when asked

A book is a study session delivered asynchronously. Keep every invariant and
fix it on the page: a whole-subject map with labeled edges, an anchor question
split across progressive chapters (as many as the scope needs, from one
chapter with sections upward; the leader decides unless the user sets a count),
foundations taught just in time, Predict pauses and graded exercises with a
transfer task, epistemic labels, and visuals chosen per mechanism. Calibrate
the reader profile from learner state and evidence, and never pad.

Work as a leader with workhorses when the host has subagents (Claude Code:
Opus leads, Sonnet works; Codex: Astra leads, Sol works). The leader frames
the book, writes the front matter and specs, adjudicates, and checks quality.
Workers write, independently verify, and illustrate each chapter. Markdown
stays the verified source, and HTML is generated from it. Every number comes
from a cited source or a real run, every listing runs as printed after its
chapter's setup listing (checked by executing the Markdown), and every chapter
passes a fresh-context verification before illustration. Follow
[book-production.md](references/book-production.md).

## Integrate, test, and close

Compress a learned cluster only after understanding, using a mechanism chain,
comparison, causal loop, equation with interpretation, timeline, decision tree,
argument map, concise explanation, or learner-generated map fragment.

Before declaring the goal met, seek evidence across the critical anchor path:
central-node reconstruction, important-edge explanation, application, a
relevant boundary or contrast, and transfer or prediction in a changed context.

At a natural stop, provide a proportional closure:

- current answer to the anchor question
- updated recompressed map
- three to seven important relationships
- remaining frontier questions
- one synthesis task and one novel transfer task
- mixed review queue covering nodes, edges, mechanisms, contrasts,
  predictions, misconceptions, transfer, and blank-map reconstruction as useful
- recommended next route and paths to any requested artifacts

Present teaching directly rather than narrating internal workflow. Keep prose
readable and headings proportional. The package's behavioral tests are in
**[evals/evals.json](evals/evals.json)** with scoring guidance in
**[evals/rubric.md](evals/rubric.md)**. The retained candidate rationale and
forward-test record are in
**[evals/design-selection.md](evals/design-selection.md)**. Load evaluation
material only for maintenance or evaluation, never during an ordinary lesson.
