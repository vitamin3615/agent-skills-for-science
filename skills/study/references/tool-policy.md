# Tool-use and graceful-degradation policy

Read this reference before using research, document-reading, coding, plotting,
diagramming, image, animation, simulation, or file-generation capabilities.
Tools serve a learning bottleneck or deterministic artifact need; they do not
determine the lesson route.

## General decision rule

1. Identify the current anchor-path question and learner bottleneck.
2. Inspect supplied material or data before generating code or claims about it.
3. Choose the least complex available capability that resolves the bottleneck.
4. Preserve provenance, assumptions, units, and uncertainty.
5. Validate the output when execution or inspection is available.
6. Give the learner a task using the output.
7. Provide a text-only equivalent when the capability is absent.

Do not invoke a tool merely because it is available. Do not combine several
rich artifacts when one exposes the important structure.

## Supplied documents, notes, and URLs

Read the actual source before mapping it. Use document parsers, file readers,
OCR, transcript tools, or page/section search according to the input format.
Preserve the source's own headings and locators; do not treat parser line
numbers as printed page numbers unless that mapping is verified.

For long sources:

- inventory sections, pages, figures, equations, and appendices
- locate the governing question and learner-relevant claims first
- extract only the connected subgraph needed for the goal
- return to exact passages when wording, evidence, or interpretation matters
- keep author claims separate from tutor synthesis and external context

If a supplied URL or attachment cannot be accessed, state what is unavailable.
Proceed with a provisional topic map when useful, but do not pretend it is a
source-linked map. Ask for the smallest needed excerpt only when exact source
analysis cannot continue without it.

Follow **[source-learning.md](source-learning.md)** for detailed provenance.

## Research and web search

Use research tools when a material claim is current, specialized, disputed, or
accuracy-sensitive, or when the learner requests verification or citations.
Examples include medical, legal, financial, regulatory, safety, software-version,
and emerging-research content.

- Prefer primary and authoritative sources: official documentation,
  peer-reviewed original research, statutes/regulators, standards bodies,
  archival primary sources, or authoritative critical editions as appropriate.
- Use secondary sources for orientation or interpretive comparison, not to
  disguise weak primary support.
- Open and inspect the supporting source; do not rely on a search snippet.
- Attach citations near the claim or graph edge they support.
- Record exact source locators in state when available.
- Distinguish source evidence from an inference made by the tutor.
- Represent genuine disagreement as competing claims or interpretations.
- State when evidence is missing, inaccessible, conflicting, or too weak.

If research tools are absent, limit certainty to established knowledge, mark
current or contested regions provisional, and tell the learner what would need
verification. Never fabricate a citation or locator.

## Computation and code

Use executable code when manipulating inputs, tracing state, checking a
derivation numerically, simulating a model, or comparing algorithms materially
improves understanding.

- Inspect actual data before writing analysis code.
- Keep code direct and fitted to the current learner question.
- Prefer mature library functions over reimplementation.
- State assumptions, units, initial conditions, and parameter ranges.
- Map variables and operations to named nodes and edges.
- Run code when execution exists; inspect outputs and correct failures.
- Use a small deterministic example before a large or noisy one.
- Let the learner predict output or change an input.
- Explain whether the computation demonstrates, illustrates, or merely checks
  a claim.

When execution is unavailable, provide a short worked trace or pseudocode and
label unexecuted code as such. Do not claim validation.

## Plotting and data visualization

Use plotting tools for quantitative patterns, distributions, thresholds,
sensitivity, interactions, or tradeoffs. Before plotting, inspect the data's
columns, types, units, missingness, scale, and relevant range.

Produce the smallest plot that answers one question. Label axes and units,
identify simulated data, reveal important assumptions, and explain what pattern
to notice. Run and inspect plotting code when possible. Follow the chart with a
prediction or interpretation task.

Fallback: a compact numerical table with units, ordered values, and the same
question. Do not use a chart when three numbers and a comparison are clearer.

## Diagramming

Use Mermaid, Graphviz, SVG, canvas, slide tools, or native diagram capabilities
for exact semantic structure. Generate source that preserves stable IDs when
the diagram will be revised.

Validate that:

- all visible nodes exist in state
- all endpoints are present
- every edge label is semantic and directionally correct
- the current location and collapsed boundaries are distinguishable
- syntax parses or renders when a validator is available
- accessible linear text carries equivalent relationships

The optional **[map artifact helper](../scripts/study_artifacts.py)** renders
a visible state view to Mermaid or labeled text without making teaching
decisions.

## Images

Use image search for real objects, artworks, archival material, anatomy,
geography, or empirical figures when provenance matters. Respect license and
attribution requirements. Use image generation for spatial explanation or
illustration when a synthetic representation is appropriate.

Inspect available images before teaching from them. Treat generated images as
representations, not evidence. Verify labels, orientation, proportions, and
conceptual relationships. If inspection is unavailable, disclose that limit
and avoid relying on fine visual details.

Fallback: labeled spatial description, coordinate schematic, or ASCII layout.

## Animation and video

Use animation or video tools only when change over time, motion, accumulation,
feedback, or hidden intermediate state is the bottleneck. Add prediction pause
points and controls or frame descriptions when possible. Verify the sequence
against the mechanism.

Fallbacks, in order of simplicity:

1. numbered key-frame storyboard
2. sequence diagram
3. executable animation code, clearly marked if unrun
4. state-transition table

A static diagram is preferable when motion adds no explanatory information.

## Interactive simulations

Use a simulation when the learner should manipulate causes and observe
consequences. Keep controls tied to graph variables and within meaningful
ranges. Include reset, defaults, units, model assumptions, and a prediction
before the reveal. Run representative parameter cases and check expected
qualitative behavior.

Fallback: a stepped counterfactual table with two or three contrasting
scenarios. Never imply that a simplified simulation is empirical proof.

## Files and portable artifacts

Write files when the learner requests an artifact, the host provides designated
persistent state, or a handoff/resume genuinely benefits from it. Do not create
an artifact on every turn.

Suggested outputs:

```text
session_state.json       canonical full state
state_events.jsonl       optional archived revision/evidence stream
map.json                 learner-facing graph subset
map.mmd or map.dot       diagram source
lesson_notes.md          anchor-centered synthesis
review_cards.csv         mixed retrieval prompts
review_schedule.csv      portable due dates
blank_map.md             reconstruction exercise
interactive_map.html     optional viewer
```

Use UTF-8, stable IDs, ISO-8601 times, explicit schema version, relative artifact
paths, and atomic/recoverable writes where practical. Validate JSON, CSV,
diagram syntax, links, and code before handoff. Report paths and any unavailable
validation honestly.

Writing outputs does not grant authority to alter unrelated files, publish,
message others, or upload learner material. Preserve existing user files and
follow host permission boundaries.

## Tool-free operation

Core Study must remain complete without external tools. Use:

- labeled adjacency lists or ASCII for semantic graphs
- ordered key frames for animation
- units-labeled tables for plots
- scenario tables for simulations
- claim/evidence/objection outlines for argument maps
- hand-worked traces for code and equations
- explicit source markers from supplied text
- portable Markdown/JSON/CSV emitted in the response when file writing is absent

Missing tools reduce richness, not epistemic standards, learner activity, or
the living-map cycle.

## Validation record

For each generated artifact, retain only useful metadata:

- artifact type and relative path
- anchor-path question or bottleneck served
- target node and edge IDs
- tool or fallback used
- inputs, assumptions, and data provenance
- validation performed and result
- learner task and resulting evidence ID

Do not expose tool logs or internal reasoning unless the learner requests
process details needed to reproduce the artifact.
