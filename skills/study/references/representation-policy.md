# Representation-selection policy

Read this reference when prose alone may not expose the current learning
bottleneck. Choose a medium for explanatory leverage, not decoration or tool
availability.

## Selection gate

Before creating a representation, determine internally:

1. What exact question should it answer?
2. What structure is hard to perceive in the current form?
3. What is the simplest medium that exposes that structure?
4. What will the learner predict, identify, manipulate, translate, or diagnose?
5. What text-only form preserves the same learning function?

If the first two answers are vague, continue with concise text or a labeled
semantic map. Use one primary rich representation at a time unless two distinct
bottlenecks require different media.

## Bottleneck-to-medium map

| Learning bottleneck | Prefer | Text-only fallback | Required learner action |
|---|---|---|---|
| Parts, topology, or multiple dependency paths | Concept/relationship diagram | Labeled adjacency list or ASCII graph | Fill or explain an edge |
| Hidden spatial structure, anatomy, or geometry | Labeled spatial diagram or generated image | Coordinate/component-location description | Label, rotate mentally, or predict placement |
| Change, movement, accumulation, or transformation over time | Animation or step sequence | Key-frame storyboard | Predict next frame or explain transition |
| A whole split, assigned, and subdivided across scales | Stepped zoom build, to scale | Ordered list of levels with sizes and zoom factors | Predict what the next zoom will show |
| Causal feedback, equilibrium, or parameter sensitivity | Interactive simulation | Counterfactual scenario table | Change a parameter and explain result |
| Quantitative pattern, distribution, threshold, or tradeoff | Data visualization | Units-labeled numerical table | Predict trend, locate threshold, or interpret shape |
| Abstract notation or computation | Annotated equation, code, or notebook | Worked symbolic/numeric trace | Translate, complete, or change an input |
| Procedural sequence and branching | State diagram, flowchart, or decision tree | State-action-decision table | Choose next action and diagnose an error |
| Historical order, duration, and overlap | Timeline with causal annotations | Ordered dated sequence | Explain a turning point or causal link |
| Claims, evidence, assumptions, and objections | Argument map | Claim-evidence-objection tree | Find unsupported edge or weakest premise |
| Structurally similar abstraction | Explicit analogy/correspondence map | Two-column mapping | Identify preserved relation and breakdown |
| High-dimensional or competing explanations | Small multiples, projection, or comparison matrix | Structured contrast table | Choose model and justify discriminating feature |
| Uncertainty | Distribution, interval, ensemble, or confidence encoding | Scenario/range table | State what is and is not supported |

## Semantic concept and relationship diagrams

Use when global structure, dependencies, or alternative paths are the
bottleneck.

Require:

- five to twelve visible core nodes by default
- directional or explicitly symmetric edges
- semantic verb-phrase edge labels
- visual distinction for current location, prerequisites, and collapsed nodes
- a clear anchor path rather than an evenly emphasized web
- readable linear alternative for accessibility

Avoid decorative bubbles, crossed-edge clutter, or a diagram that merely
duplicates adjacent prose. Ask the learner to label a missing edge, trace a
path, compare two routes, or diagnose a flawed connection.

## Animation and storyboard

Use only when the key relation depends on change over time and a static
sequence would hide the mechanism.

Include:

- state before
- changing variable or active mechanism
- ordered transformations
- state after
- labels or narration
- prediction pause points
- pause, step, or frame descriptions when the medium permits

When animation tools are absent or motion adds little, use three to seven
numbered key frames, a sequence diagram, or executable animation code. Ask the
learner to predict a next frame or explain why one state follows another.

## Stepped zoom builds

Use when a whole is divided, assigned, and subdivided (a genome into datasets,
a dataset into batches, an organ into tissues), or when the learner must hold
several scales at once.

Plan before drawing: write the step list in the order the work happens in
reality, from the whole concrete object to its finest unit, one new idea per
step. Example: one chromosome → its labelled regions → labels become roles →
zoom into one region → the units tiling it → the same on every chromosome.
Keep one real, running example throughout.

Build:

- Reveal one step at a time (step-through slide, key frames, or numbered
  panels). Earlier levels stay visible as context, joined by zoom connectors.
- Draw every level to scale, with an axis and the zoom factor on each.
- Show each concept at the step that names it. Everything the text names must
  be findable in the picture: label narrow features with call-outs rather than
  dropping them. If the example lacks a category the text mentions, say so on
  the slide and show where it does occur.
- Keep local views and totals apart. A zoom shows one neighbourhood, not
  proportions, so give totals separately. Never draw totals as a bar aligned
  with a positional axis, because readers take it as positions; use a colour
  key or a separately titled chart.
- Separate colliding terms explicitly, such as a source's `fold0` labels versus
  a model's `FOLD_0`.

Before delivery, run a misreading check on every step: what would a newcomer
infer from the picture alone about positions versus totals, missing categories,
relative sizes, or a local view standing for the whole? Fix wrong inferences in
the figure, not only in the caption.

## Data visualization

State the question before the chart. Make explicit:

- variables and units
- axes, encodings, and scale
- data source or whether values are simulated
- assumptions and held-constant conditions
- the pattern, threshold, distribution, sensitivity, or tradeoff to notice
- uncertainty or variability when relevant
- a prediction or interpretation task

Prefer a small, direct plot over a dashboard. Execute plotting code and inspect
the output when tools exist. Do not imply empirical data when values are
illustrative or simulated.

## Interactive simulation

Use when learning requires changing a cause and observing consequences,
especially for feedback, sensitivity, equilibrium, or counterfactuals.

Prefer a few meaningful controls:

- sliders with units and plausible ranges
- toggles for assumptions or mechanisms
- reset and step-through controls
- scenario selectors that isolate one contrast

Define the model and simplifying assumptions. Show initial state, manipulated
cause, measured outcome, and success criterion. Ask for a prediction before
revealing the result. If interaction is unavailable, provide a scenario table
or short executable model whose inputs can be edited.

## Timeline

Use when order, duration, overlap, or historical context carries explanatory
weight. Keep chronological edges distinct from causal or interpretive edges.
Mark uncertain dates and disputed causal readings. Ask why one event is a
turning point, which condition persisted across events, or whether chronology
alone establishes causation.

## Argument map

Use when the bottleneck is inferential support rather than chronology or topic
organization. Distinguish:

- main claim and subclaims
- evidence and source
- warrants or assumptions
- objections and counterexamples
- rebuttals or qualifications
- interpretation and uncertainty

Use `supports`, `undermines`, `assumes`, `qualifies`, and `responds to` rather
than generic arrows. Ask the learner to locate a missing warrant, judge which
evidence supports which claim, or reconstruct the strongest objection.

## Executable code and notebooks

Use when computation, state change, iteration, numerical verification, or model
manipulation is itself part of understanding.

- Keep code focused on the anchor question.
- Expose inputs the learner should change.
- Connect variables and operations back to map nodes and edges.
- Run the code, inspect outputs, and fix errors when execution exists.
- Explain what the computation demonstrates and what it does not prove.
- Fade from worked execution to learner modification or prediction.

When code cannot run, use pseudocode or a checked hand trace and state the
limitation.

## Analogy

Use when a known system preserves a difficult relation in the target system.
Always provide:

1. a correspondence table from source to target
2. the exact relationship preserved
3. the aspects not represented
4. at least one point where reasoning from the analogy would fail

Ask the learner to translate one relation back to the target and identify a
breakdown. Do not use an analogy as evidence for a factual claim.

## Generated images and spatial diagrams

Use image generation only when shape, configuration, anatomy, geometry,
physical arrangement, or a spatial comparison is central. Prefer deterministic
diagram code for exact labels, topology, equations, or quantitative scales.

Before generation, specify the conceptual content, viewpoint, required labels,
spatial relationships, irrelevant decoration to omit, accessibility needs, and
learner task. Inspect the result when image-viewing tools exist. Generated
images are representations, never evidence or sources.

## Equations and formal notation

Treat an equation as a relationship map:

- identify every term and unit
- state which quantities vary and which assumptions are fixed
- translate the relation into plain language
- show direction, proportionality, constraint, or conservation encoded
- connect algebraic transformations to their conceptual purpose
- use a numerical or geometric instance when it reveals structure

Ask the learner to predict a sign, limiting case, dimensional consequence, or
effect of changing a term before performing routine calculation.

## Accessibility

Honor the learner's stated accessibility needs over the default medium.

- Supply alt text that communicates relationships, not colors alone.
- Never encode meaning by color alone; add labels, shapes, or line styles.
- Use high contrast and readable type for generated visual artifacts.
- Provide linear edge lists and ordered descriptions for screen readers.
- Describe animation state transitions and expose pause points.
- Avoid interaction requiring precise pointing when a keyboard/text alternative
  can express the same reasoning.
- Let the learner choose lower sensory density without reducing conceptual
  rigor.

## Post-representation check

Do not ask only whether the representation helped. Ask for evidence:

- “Which edge does the steep section of this curve represent?”
- “Predict the next frame before revealing it.”
- “Change this parameter; what should remain invariant?”
- “Translate this diagram into one equation or mechanism chain.”
- “Find the edge this argument map does not justify.”
- “Where does this analogy stop preserving the target relation?”

Record the response against targeted nodes and edges. If the representation
does not resolve the bottleneck, revise the explanation or medium rather than
adding more media at once.
