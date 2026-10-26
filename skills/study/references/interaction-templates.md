# Interaction and export templates

Use these as adaptable semantic slots, not mandatory headings. Omit any slot
that does not help the learner. Vary phrasing and density with the topic, goal,
time, and interaction style.

## Lightweight intake

Do not conduct a questionnaire. Extract supplied inputs, infer defaults, then
ask at most one material question.

```text
Target: {topic/source/procedure/project}
Goal: {stated or durable conceptual understanding}
Known background: {stated or unknown}
Time/depth: {stated or intermediate, open-ended}
Mode: {inferred or requested}

One clarification, only if route-changing:
{single question}

Useful start in the same response:
{provisional anchor or compact map}
```

High-value clarifications distinguish routes: “Is your goal to derive the
formula or use it correctly?” Low-value clarifications merely collect
preferences that can be inferred while teaching.

## Initial map

```text
Learning target: {target}
Anchor question: {question with explanatory or predictive force}
Why it matters: {one or two lines tied to learner goal}

Context map
{larger field} --contains/frames/enables--> {target cluster}
{neighbor} --contrasts with/connects to--> {target cluster}

Core map — provisional
{node A} --precise relationship--> {node B}
{node B} --precise relationship--> {node C}
{needed prerequisite} --enables--> {important edge or node}
[{collapsed cluster}: {reason it remains closed}]

Frontier
- {two to five unanswered questions}

Proposed route: {route} because {goal/evidence/time rationale}
Diagnostic: {one prediction, retrieval, comparison, or missing-edge prompt}
```

Keep five to twelve visible core nodes in total. A prose adjacency list, ASCII
map, Mermaid graph, or small diagram is acceptable. Never use unlabeled arrows.

## Location marker

Use the smallest marker that restores orientation:

```text
Here: {context} > {cluster} > {node A} --{edge under study}--> {node B}
Focus: {current question}
```

For screen-reader-first output, use one relationship per line and state the
current item before its neighbors.

## Diagnostic prompt patterns

Choose one to discriminate between plausible learner models.

```text
Cause: Explain what you currently think causes {outcome}.
Contrast: Which of {case A} and {case B} fits {model}, and why?
Missing edge: Complete {node A} --?--> {node B}.
Prediction: If {variable/assumption} changes, what should happen next?
Formal meaning: Translate {equation/code/claim} into words.
Boundary: Name a case where this explanation would stop working.
Source: Which passage or result supports {claim}, and what exactly does it support?
```

Do not ask several low-information prompts when one contrast reveals the gap.

## Learning micro-cycle

```text
{optional location marker}

Focus question
{one meaningful question}

Attempt before exposure
{retrieval/prediction/partial solution, unless immediate explanation is better}

Smallest sufficient explanation
{plain model -> formal term/notation only when useful}

Primary representation
Question it answers: {bottleneck-specific question}
{diagram/table/trace/timeline/etc.}
Notice: {important pattern, not decorative description}

Worked case
{one example showing the critical relationship}

Faded learner task
{nearby case with less support}

Feedback after response
Correct: {specific node/edge/step}
Missing or faulty: {specific relation and why}
Next evidence needed: {one task}

{optional compact map delta and frontier}
```

The attempt may appear at the end of one response and feedback at the start of
the next. Do not expose empty template slots or internal phase labels.

## Worked-example fading

```text
Example 1: complete solution with why each important step follows.
Example 2: preserve setup and one cue; learner supplies central step/edge.
Example 3: learner chooses the model and solves a new surface case.
```

Fade based on demonstrated evidence, not a fixed number of examples. If the
learner fails because a relation is missing, restore only the needed support.

## Map delta

```text
Map revision {old} -> {new}
- Added: {node/edge} because {frontier/evidence}
- Revised: {old relationship} -> {new relationship}
- Merged/removed/collapsed: {item} because {reason}
- Route: {old} -> {new} because {evidence}
- Anchor effect: We can now explain {portion}; {portion} remains open.
```

Show only changes the learner benefits from seeing. Record fuller machine state
internally or in an export.

## Misconception repair

```text
Current model, stated neutrally
Your explanation currently connects {A} to {B} by {relationship}.

Case it cannot explain
{observation, contrast, or counterexample}

Prediction
What would your current model expect here?

Repair
{smallest explanation or representation replacing/qualifying the faulty edge}

Reconstruction
Explain {corrected relationship} and use it to account for {contrast case}.

State consequence
{edge/node/route revision and delayed recheck}
```

Avoid adversarial language. Separate a wrong connection from learner ability or
identity.

## Zoom-out checkpoint

Choose one or two, not all:

```text
What part of the anchor question can you now answer?
Which relationship did we add or repair?
What depends on the idea just learned?
Which frontier is still blocking the anchor path?
Reconstruct the path from {A} to {D} without looking.
Has the map's organization changed? Why?
```

Then show the recompressed core only if it adds orientation.

## Cluster compression

Match compression to structure:

```text
Mechanism: A --causes--> B --enables--> C --predicts--> D
Comparison: rows are structural questions; columns are competing concepts
Causal loop: signed/directional edges plus reinforcing or balancing effect
Equation: expression + term meanings + assumptions + verbal interpretation
Timeline: chronological edges distinct from causal annotations
Decision tree: state/condition --selects--> action --changes--> next state
Argument: claim <-supports-- evidence; objection --challenges--> assumption
Learner paragraph: concise answer preserving the critical relationships
```

Compression follows understanding; it does not substitute for mechanism or
evidence.

## Synthesis task

```text
Hide the map.

Rebuild the smallest path that answers {anchor question}. Include {N} central
nodes and label every edge. Then explain the path once in plain language and,
if relevant, once using {formal vocabulary/notation}. Mark one assumption or
limit.

Reveal and compare only after the learner attempts it.
```

Alternative synthesis forms: diagnose a flawed map, compare two paths, teach
the idea to a named audience, or connect evidence to each major claim.

## Transfer task

```text
Novel case: {changed surface context, initial state, parameter, source, or goal}
Prediction before solution: {what happens/which model applies?}
Required traversal: use {at least two important relationships}
Boundary check: {condition, counterexample, or analogy limit}
Success criterion: {observable explanation or result}
```

Changing only numbers may be familiar application rather than transfer. Change
the context, representation, assumption, or model choice enough to require
structural selection.

## Source-linked map

```text
Governing question: {question inferred from source and learner goal}

Content map
[{source node}] {author's definition/claim} ({source ref ID}: {locator})
  --{semantic relation}-->
[{source node}] ({source ref ID}: {locator})

Argument/dependency map
{evidence} --supports/qualifies--> {claim}
{assumption} --enables--> {inference}
{objection} --challenges--> {claim}

Tutor addition: {context or analogy, explicitly marked}
Tension/omission: {what the source leaves unresolved}
```

Use only locators actually available in the source.

## Session closure

Scale closure to the session. A short interaction does not need every heading.

```text
Current anchor answer
{concise synthesis proportional to evidence}

Recompressed map
{small connected graph with semantic edges}

Critical relationships (3-7)
- {A --relation--> B}: {why it holds/condition}

Demonstrated / not yet demonstrated
{node and edge evidence stated separately}

Remaining frontier
- {only relevant unresolved questions}

Synthesis task
{reconstruction or explanation}

Transfer task
{novel case and success criterion}

Review queue
- {due/interval}: {edge, mechanism, contrast, prediction, misconception,
  transfer, or blank-map prompt}

Recommended next route
{route and reason}

Artifacts, when requested
{relative paths and formats}
```

## Portable review-card rows

Use these columns when exporting CSV:

```text
review_id,kind,prompt,node_ids,edge_ids,misconception_id,success_criteria,source_reference_ids
```

Use these columns for the schedule:

```text
review_id,due_date,interval_days,kind,prompt,status
```

Quote CSV fields containing commas, lists, or line breaks.
