# Living state, assessment, and review

Read this reference when recording learner evidence, changing mastery, repairing
a misconception, revising the graph, planning review, or resuming state. Use
**[session-state.schema.json](session-state.schema.json)** for the serialized
shape. Keep bookkeeping internal unless the learner requests it.

## Canonical state rules

- Use stable node, edge, question, evidence, misconception, source-reference,
  representation, review, and revision identifiers.
- Keep mastery only in `mastery_by_node` and `mastery_by_edge`; do not duplicate
  mutable scores inside node or edge records.
- Increment `state_version` for every material graph, visibility, or route
  change. Add a matching `revision_log` record with operation, reason, affected
  IDs, and any evidence IDs.
- Archive rather than silently delete learned elements. When merging nodes,
  retain aliases, redirect edges, update references, and record the survivor.
- Validate every referenced ID before export. No edge, evidence, question,
  mastery record, misconception, review item, or source reference may point to
  a missing object.
- Store only learning-relevant profile information. Do not infer or persist
  sensitive personal traits.

## Evidence before estimates

Record evidence from an observable learner act. A useful record contains:

- task type: retrieval, prediction, explanation, comparison, map completion,
  calculation, proof, diagnosis, application, transfer, or teach-back
- target node IDs and edge IDs
- support level: none, light, substantial, or full
- response summary: concise representation of the learner's model
- outcome: correct, partially correct, incorrect, or inconclusive
- demonstrated capability: recognition, cued explanation, independent
  explanation, familiar application, or transfer
- feedback summary and time

Do not store a full transcript when a short evidence summary is enough.
Confidence statements such as “I understand” may motivate a probe but cannot
raise mastery.

## Mastery scale

| Level | Demonstrated evidence | Insufficient evidence |
|---:|---|---|
| 0 | No observation | Topic appeared in agent explanation |
| 1 | Recognizes or selects the term/structure | Says it feels familiar |
| 2 | Explains with substantial cues or completes heavily scaffolded work | Copies a displayed definition |
| 3 | Explains independently and accurately | Repeats agent wording immediately with hidden gaps |
| 4 | Applies in a familiar situation and explains the relevant path | Gets an answer through an unexplained procedure |
| 5 | Transfers, compares, predicts, diagnoses, or teaches accurately in a changed context | Repeats the same exercise with new numbers only |

Set estimate confidence separately. Low confidence means evidence is sparse or
ambiguous, not that mastery lies between two levels.

### Separate node and edge evidence

Ask which object the performance actually supports.

Example:

```text
Learner defines pressure, force, and area accurately.
node mastery: pressure=3, force=3, area=3

Learner says larger area increases pressure for fixed force.
edge mastery: area --inversely affects--> pressure = 1
misconception: direct rather than inverse relation
```

Do not lower well-supported node mastery merely because a connecting edge is
wrong. Conversely, a correct edge phrase without an explanation may show
recognition but not independent relational understanding.

### Update conservatively

- Raise only targets directly supported by the task.
- Record a lower result without erasing stronger, recent evidence; reduce an
  estimate when failure is repeated or reveals that earlier success was cued.
- Use one discriminating follow-up when the response could reflect wording,
  calculation, prerequisite, or relation failure.
- Require more distant context or model choice for level 5 than for level 4.
- Reassess central edges after a delay or intervening material before treating
  them as durable.

## Diagnose the learner model

Interpret an error by locating the smallest faulty subgraph. Consider:

1. Is a required node absent or merely unlabeled?
2. Are both nodes known but their direction, sign, condition, or mechanism
   wrong?
3. Is an edge valid only under an unstated assumption?
4. Is the learner applying a neighboring model to the wrong case?
5. Is notation hiding an otherwise sound idea?
6. Is the error procedural, conceptual, evidential, or linguistic?

Use one contrast probe when these hypotheses remain ambiguous. Avoid expanding
multiple prerequisite branches before identifying which one blocks the anchor.

## Repair misconceptions

Represent a misconception as a testable learner model, not a pejorative label.

1. Record the learner model neutrally.
2. Link the implicated nodes and edges plus the evidence that exposed it.
3. Identify an observation, counterexample, or contrast the model cannot
   explain.
4. Let the learner predict that case when useful.
5. Replace, redirect, qualify, or split the faulty edge or node.
6. Ask the learner to reconstruct the corrected relation in their own words.
7. Revise the route toward the repair and record the graph change.
8. Queue a delayed recheck in a different surface context.

Use statuses `suspected`, `confirmed`, `repairing`, `monitoring`, and `repaired`.
If later evidence revives a repaired misconception, return it to `repairing` and
retain the earlier evidence in the revision history. Do not mark it `repaired`
because the learner agrees with the correction; require evidence from
reconstruction or application.

## Revise the graph

Choose the smallest operation that makes the learner model more accurate and
useful.

| Operation | Use when | Preserve |
|---|---|---|
| Add | A frontier or prerequisite becomes relevant | Reason for inclusion |
| Relabel | Learner wording or domain precision improves orientation | Old label as alias when useful |
| Redirect | Edge direction was wrong | Evidence for correction |
| Qualify | Relation holds only under a condition | Condition in label/explanation |
| Split | One node hides two structurally different ideas | Incoming/outgoing edge rationale |
| Merge | Duplicate labels refer to one concept | Aliases, mastery evidence, source refs |
| Remove/archive | Node is wrong or no longer useful | Revision reason and recoverability |
| Expand | A neighborhood must expose mechanism or boundary | Parent cluster and return path |
| Collapse | Cluster is understood or peripheral | Compressed explanation and key edges |
| Reorganize | New evidence changes the best hierarchy or path | Stable IDs where semantics did not change |

Show a map delta only when it helps the learner see what changed. Do not expose
routine internal bookkeeping.

## Route revisions

Record route changes when they alter the intended question sequence or zoom.
Include the prior route, new route, reason, and triggering evidence. Common
changes:

- foundation route to application after a strong diagnostic
- mechanism route to misconception repair after a faulty causal edge
- local deep-dive to global orientation after disorientation
- broad overview to critical-path compression when time shrinks
- worked example to faded practice after cued success
- familiar application to transfer after independent success

Avoid route thrashing from one ambiguous phrase. Mark a suspected gap and use a
discriminating probe first.

## Review queue design

Generate review prompts from the learned graph and demonstrated weak points,
not from a glossary. Mix only useful types:

- node recall: explain one central concept without seeing its definition
- edge explanation: explain why and under what conditions two nodes connect
- mechanism reconstruction: rebuild a multi-edge causal or procedural path
- compare/contrast: choose between similar structures and justify the choice
- prediction: change a cause, parameter, assumption, or initial state
- misconception check: test the formerly faulty relation in a changed case
- transfer: apply the map in a context with different surface features
- blank map: reconstruct a cluster and label its edges
- source trace: connect a claim to evidence and exact locator

Each item should include target IDs, prompt, success criterion, due date or
relative interval, and source IDs where relevant. Prefer fewer high-value cards
over one card per node.

Spaced dates are scheduling defaults, not guarantees. Shorten intervals after
incorrect or heavily cued performance; lengthen them after independent and
transfer success. The optional **[review scheduler](../scripts/review_scheduler.py)**
assigns dates to an already chosen queue and never decides pedagogical content.

## Resume and compact state

On resume:

1. Validate structure and references when a file is present.
2. State current anchor, location, strongest critical edges, unresolved
   bottleneck, and due review item.
3. Begin with retrieval or reconstruction rather than a full recap.
4. Preserve identifiers and evidence; never reset mastery because the dialogue
   boundary changed.

Keep active state compact. Summarize old evidence and optionally archive the
full change stream in `state_events.jsonl`. Never discard source traceability,
unresolved misconceptions, or the evidence supporting current mastery.

## Completion evidence

Treat a learning goal as met only when the learner demonstrates the subset
appropriate to that goal:

- reconstructs central nodes
- explains why the important edges hold
- applies the structure in a familiar case
- recognizes a meaningful limit, contrast, or counterexample
- transfers or predicts in a changed context

For a narrow or time-limited goal, explicitly identify which of these remain
untested rather than expanding the session without consent.
