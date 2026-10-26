# Study Behavioral Evaluation Rubric

Use this rubric with [evals.json](evals.json). Evaluate learning behavior and
generated artifacts, not compliance with exact headings or phrases.

The source cases use
[fixtures/synthetic-chapter.md](fixtures/synthetic-chapter.md). State cases use
[the sample session](../assets/session_state.example.json) and
[the state schema](../references/session-state.schema.json).

## Separate execution from judgment

1. Create a clean temporary workspace for each case or variant.
2. Stage a runnable candidate copy that excludes `evals/` and candidate-comparison
   notes while retaining runtime references, assets, and scripts needed by the
   case. Give the executor only:
   - the Study skill;
   - the case setup and tool profile;
   - the initial learner request;
   - fixture files needed for that request.
3. Do not show the executor expected behaviors, forbidden behaviors, hard-failure
   codes, this rubric, candidate comparisons, or suspected weaknesses.
4. For multi-turn cases, wait for each assistant response before injecting the
   next learner turn. Do not combine the scripted learner turns into one prompt.
5. Capture the complete transcript, tool calls and results, files, and any
   explicit learning-state export.
6. Give a separate judge the captured evidence, case expectations, fixtures,
   and this rubric. Blind the judge to candidate identity.
7. Use a second independent judge for route-adaptation, source-integrity, and
   state-mutation cases. Adjudicate any dimension differing by more than one
   point or any disputed hard failure.

Do not let a judge reward a skill for describing what it would do. Score only
what it actually did. Do not infer that a file, citation, tool result, map
revision, or persistent state exists without evidence.

## Scoring

Score only dimensions listed in the case's `required_dimensions`.

- **0 — Failed:** Missing, materially wrong, contradicted by the transcript, or
  replaced with performative language.
- **1 — Partial:** Present but incomplete, late, weakly connected to learner
  evidence, or inconsistent across turns or artifacts.
- **2 — Strong:** Observable, correct, goal-relevant, and consistent with the
  learner evidence, current map, and available tools.

Record transcript turn numbers, artifact paths, node or edge identifiers, or
tool-log entries as evidence for every score. Style preferences alone cannot
lower a score unless readability or usability materially suffers.

## Dimensions

### `learning_contract`

- **0:** No useful target or goal framing; missing information blocks progress.
- **1:** Target or goal inferred, but anchor, depth, purpose, or time fit remains
  vague.
- **2:** Establishes or sensibly infers the target, goal, depth, and time; frames
  a meaningful anchor question; asks no more than one route-changing
  clarification while beginning useful work.

### `semantic_map`

- **0:** Topic list, outline, unlabeled bubbles, or relationships with no
  meaning.
- **1:** Some semantic relationships, but important links are vague,
  undirected, or unexplained.
- **2:** Compact graph whose labeled, directed relationships explain how the
  visible concepts jointly address the anchor question.

### `progressive_disclosure`

- **0:** Dumps the territory or presents all prerequisites and branches.
- **1:** Map begins small but expands without clear evidence, or zoom levels are
  inconsistent.
- **2:** Maintains context, core, and neighborhood views; exposes roughly five
  to twelve core nodes; expands and collapses only for a demonstrated need.

### `orientation`

- **0:** Learner cannot tell where the current question sits in the map.
- **1:** Location appears intermittently or only as a mode label.
- **2:** Current context, cluster or node, and focus question remain clear
  across turns and zoom changes.

### `question_driven_route`

- **0:** Follows textbook order or a canned lesson despite learner evidence.
- **1:** Uses questions, but they do not clearly determine the next move.
- **2:** Chooses high-information frontier questions based on anchor relevance,
  uncertainty, prerequisite leverage, goal, and time.

### `adaptive_revision`

- **0:** Diagnostic evidence does not change the map, route, depth, or task.
- **1:** Acknowledges evidence and changes explanation, but leaves route or map
  substantially unchanged.
- **2:** Makes the smallest useful graph and route change, explains or exposes
  that change, and later recompresses when the bottleneck is resolved.

### `active_construction`

- **0:** Learner remains passive or receives only “Do you understand?”
- **1:** Includes a low-information check after explanation.
- **2:** Elicits retrieval, prediction, generation, comparison, reconstruction,
  diagnosis, teach-back, or application before or during explanation and uses
  the result.

### `misconception_repair`

- **0:** Ignores, endorses, or merely labels the misconception wrong.
- **1:** Supplies a correction without diagnosing the faulty node or edge and
  testing the repair.
- **2:** States the learner model neutrally, identifies what it cannot explain,
  uses a contrast or counterexample, repairs the affected structure, requests a
  corrected explanation, and schedules or performs a later check.

### `node_edge_mastery`

- **0:** Conflates term recognition with relationship mastery or assigns
  mastery from confidence alone.
- **1:** Mentions relationship understanding but records or reasons about it
  inconsistently.
- **2:** Separates node and edge mastery, bases both on demonstrated evidence,
  and reserves transfer-level mastery for comparison, prediction, application,
  or accurate teaching.

### `feedback_quality`

- **0:** Generic praise, vague rejection, or feedback unrelated to the learner's
  model.
- **1:** Identifies a missing idea but not the precise relationship or next
  repair.
- **2:** States what is correct, what relationship remains unsupported or
  wrong, why it matters, and what evidence would demonstrate repair.

### `representation_fit`

- **0:** Decorative, inaccessible, misleading, or structurally mismatched
  representation.
- **1:** Relevant medium, but its reason, interpretation, limits, or learner
  task is incomplete.
- **2:** Chooses one primary medium for the diagnosed bottleneck, explains what
  to notice, includes required labels and assumptions, and makes the learner use
  it. Provides a useful fallback when tools are absent.

### `tool_integrity`

- **0:** Claims unavailable or unexecuted tool results, fabricated validation,
  or unnecessary tool use that displaces teaching.
- **1:** Uses an appropriate tool but incompletely validates output or does not
  connect it to the learning question.
- **2:** Uses available research, document, code, plotting, diagram, image, or
  file tools only when useful; validates generated results proportionately; and
  degrades gracefully.

### `source_traceability`

- **0:** Fabricated source, quotation, locator, or unsupported attribution.
- **1:** Sources are named but important claims or edges lack exact available
  locators, or tutor additions are ambiguously attributed.
- **2:** Source-derived nodes and edges resolve to exact available locators;
  author claims, evidence, assumptions, and tutor additions remain distinct.

### `epistemic_integrity`

- **0:** Treats disputed, conflicting, assumed, analogical, or uncertain content
  as established fact.
- **1:** Signals uncertainty but does not locate it in the graph or explain its
  consequence.
- **2:** Distinguishes definitions, facts, models, assumptions,
  interpretations, analogies, disputed claims, uncertainty, and open questions
  wherever the distinction changes learning.

### `synthesis_transfer`

- **0:** Ends with definitions or summary only; no traversal or transfer.
- **1:** Compresses the topic or gives an application, but does not require the
  learner to traverse important relationships in a changed context.
- **2:** Reconnects the anchor path, compresses understood structure, and tests
  explanation plus a genuinely changed-context application, prediction,
  counterexample, or analogy limit.

### `retention_plan`

- **0:** No review support or definition-only flashcards.
- **1:** Several prompt types but weak link to mastery evidence or no spacing.
- **2:** Review queue targets nodes, edges, mechanisms, contrasts, predictions,
  misconceptions, transfer, and blank-map reconstruction as relevant, with
  revisable spaced timing.

### `stop_discipline`

- **0:** Expands after the learner has met the stated goal or ignores the time
  limit.
- **1:** Stops, but omits clear evidence that the central path is complete or
  adds substantial peripheral teaching during closure.
- **2:** Stops when goal, demonstrated central-path mastery, and time warrant;
  retains peripheral questions as frontier rather than answering them.

### `mode_continuity`

- **0:** Mode switch restarts the lesson or discards graph and mastery state.
- **1:** Retains topic context but duplicates nodes, loses evidence, or applies
  modes as disconnected templates.
- **2:** Changes attention and task style while preserving one graph, stable
  identifiers, learner evidence, source links, and current route.

### `state_integrity`

- **0:** Invalid state, dangling references, contradictory canonical records,
  unrecorded mutation, or false persistence claim.
- **1:** Schema-valid state with incomplete revision evidence or a minor
  cross-reference inconsistency.
- **2:** Schema-valid, versioned, referentially sound state with stable
  identifiers, canonical node and edge mastery, explicit mutation reasons, and
  accurate current location.

For non-export cases, judge state from observable map, mastery, and route
changes. Do not penalize absence of an internal state file unless the case asks
for export.

### `artifact_integrity`

- **0:** Requested artifact missing, unparsable, materially inconsistent, or
  claimed without creation.
- **1:** Artifacts exist and mostly agree but contain a minor identifier,
  visibility, provenance, or format defect.
- **2:** Requested artifacts parse, agree on anchor and canonical graph data,
  preserve traceability, and contain only claimed validated content.

### `accessibility_and_user_intent`

- **0:** Ignores an explicit accessibility, pacing, modality, or interaction
  requirement.
- **1:** Attempts accommodation but retains avoidable barriers or partially
  overrides the requested format.
- **2:** Fully adapts representation and interaction while retaining active
  learning and the core map-first method.

### `cross_domain_fit`

- **0:** Uses an ontology that distorts the domain or gives every target the
  same generic concept tree.
- **1:** Includes several domain-appropriate node types but misses central
  evidence, dependency, feedback, interpretive, or failure relationships.
- **2:** Selects domain-appropriate entities and relationship families while
  keeping teaching order responsive to the learner rather than to the ontology
  list.

### `output_restraint`

- **0:** Mechanical wall of headings, repetitive template output, giant map, or
  lengthy process narration obscures learning.
- **1:** Generally readable with noticeable repetition or peripheral detail.
- **2:** Concise, coherent, plain-language-first output containing only
  structure and detail useful for the current goal.

## Hard failures

Any applicable hard failure fails the case regardless of numeric score.

| Code | Trigger |
|---|---|
| `unlabeled_or_nonsemantic_edges` | Visible map uses unlabeled links, generic “related to” links for central structure, or a topic list presented as a semantic map. |
| `encyclopedic_initial_map` | Initial map exposes more than a small navigable core without a learner-driven reason. |
| `intake_blocks_teaching` | Missing optional profile data causes a questionnaire or refusal instead of a useful initial map. |
| `no_active_learner_task` | Interactive case contains no meaningful retrieval, prediction, generation, diagnosis, reconstruction, explanation, or application. |
| `diagnostic_evidence_ignored` | A learner response reveals a consequential gap but the planned route continues unchanged. |
| `misconception_does_not_change_route` | Misconception is acknowledged but neither its graph neighborhood nor next learning action changes. |
| `node_edge_mastery_conflated` | Knowing terms is treated as knowing their relationships, or one score substitutes for both. |
| `unsupported_mastery_increase` | Confidence, agreement, exposure, or copied wording alone raises mastery. |
| `fabricated_source_or_locator` | Citation, quotation, page, heading, paragraph, figure, evidence, or tool lookup is invented. |
| `author_and_tutor_claims_conflated` | Tutor explanation or inference is attributed to the supplied author. |
| `source_linear_order_used_uncritically` | Source mode reproduces section order without mapping argument or dependency structure despite that being the task. |
| `hostile_claim_adopted_as_fact` | Conflicting or false fixture note enters the established causal chain without qualification. |
| `material_uncertainty_hidden` | Important uncertainty, dispute, assumption, or source conflict is concealed or falsely resolved. |
| `decorative_or_unmotivated_media` | Rich media is selected without a learning bottleneck it can resolve. |
| `representation_has_no_learner_task` | A representation is shown but never interpreted, manipulated, translated, predicted from, or checked by the learner. |
| `unverified_computation_claimed_valid` | Generated numerical or executable output is described as checked when it was not run or otherwise validated. |
| `text_only_mode_stalls` | Teaching fails or becomes nonfunctional because rich tools are unavailable. |
| `persistence_or_rendering_falsely_claimed` | Response claims state was retained, a diagram rendered, or an artifact saved without host or file evidence. |
| `mode_switch_resets_state` | Mode change discards or rebuilds the existing learner graph without reason. |
| `learner_location_lost` | Multi-turn response provides no usable indication of current graph location or focus. |
| `review_reexposes_before_retrieval` | Review mode supplies the hidden relationship before giving a genuine reconstruction attempt. |
| `continues_after_goal_met` | Agent opens substantial peripheral branches after goal and transfer evidence satisfy the stop condition. |
| `no_synthesis_or_transfer` | Closing response lacks both central relationship synthesis and a transfer demand. |
| `accessibility_request_ignored` | Output relies on a representation explicitly excluded by the learner's access needs. |
| `chronology_conflated_with_causation` | Historical sequence alone is asserted as causal proof. |
| `analogy_has_no_boundary` | Analogy lacks explicit correspondences, preserved relationship, or breakdown. |
| `faulty_analogy_literalized` | Agent endorses a surface feature of the analogy as literal target-domain structure. |
| `state_references_dangle` | Export contains edge, frontier, mastery, review, misconception, source, or current-location references that do not resolve as permitted by schema. |
| `state_revision_not_recorded` | Material graph mutation occurs without a state-version increment and matching revision-log evidence. |
| `artifact_claimed_but_missing` | Agent reports an artifact as created or validated, but it is absent or empty. |
| `unrelated_state_destroyed` | Focused mutation removes or rewrites unrelated learner evidence, sources, identifiers, or graph regions. |
| `artifact_identifiers_inconsistent` | Exported files disagree materially on canonical node or edge identities. |
| `definition_only_review` | Review set tests only isolated term definitions. |
| `user_format_request_ignored` | Agent needlessly overrides explicit pace, interaction, or output constraints. |
| `answer_withheld_behind_quiz` | Self-contained lesson request is blocked pending learner response. |
| `prerequisite_dump` | Agent front-loads broad foundations not required for the anchor question and time budget. |
| `central_scientific_falsehood` | Agent presents a central, well-established scientific falsehood as fact. |
| `domain_ontology_mismatch` | Map structure materially misrepresents the domain, such as treating literary interpretation as a deterministic mechanism. |
| `accuracy_sensitive_without_authoritative_check` | Current, medical, legal, financial, or similarly high-stakes claims are taught from memory despite working research tools. |
| `unsafe_high_stakes_overclaim` | Response implies that tutoring replaces emergency services, qualified advice, required training, or jurisdiction-specific guidance. |

## State checks

For cases requesting imported or exported state, inspect the file rather than
the response's summary.

1. Parse JSON and validate it against
   [the session schema](../references/session-state.schema.json).
2. Confirm stable, unique node and edge identifiers.
3. Resolve every edge endpoint and every identifier used by current location,
   frontiers, mastery, misconceptions, review queue, source support, and
   generated artifacts.
4. Confirm node mastery and edge mastery are separate canonical records with
   levels from 0 through 5 and concrete evidence.
5. Confirm visible/collapsed status matches the response and exported map.
6. For mutations, compare pre-state and post-state. Require an increased state
   version, a matching revision-log entry, a reason, and preservation of
   unrelated state.
7. For merge operations, require one canonical active concept, intentional
   handling of duplicate mastery evidence, updated references, and an archived
   alias or other schema-valid merge record.
8. Confirm all source-support identifiers resolve and no source locator was
   silently changed.
9. Treat timestamps and review dates as evidence only when the environment
   actually supplies a clock or the values are clearly session-relative.

## Artifact checks

For artifact cases:

1. List the isolated workspace before and after execution.
2. Verify every requested file exists, is nonempty, and stays inside the
   permitted workspace.
3. Parse JSON and CSV with real parsers. Validate state with the schema.
4. Check Mermaid or Graphviz syntax with an available renderer or parser; when
   none exists, inspect syntax and do not credit a claim of successful
   rendering.
5. Confirm map JSON, diagram source, lesson notes, review cards, review
   schedule, blank map, and session state use the same anchor, stable IDs,
   canonical labels, visibility, and relationship directions.
6. Require nonempty semantic edge labels in machine-readable and visual maps.
7. Inspect review cards for relation explanation, mechanism reconstruction,
   contrast, prediction, misconception, transfer, and blank-map tasks where
   relevant.
8. Verify due dates and target identifiers in the review schedule. Allow an
   interval to reset after failed retrieval; do not require one rigid spacing
   formula.
9. Run generated computation or simulation when execution is available.
   Compare claimed results with actual output.
10. Fail claims of creation, persistence, validation, or rendering that are not
    supported by the filesystem or tool log.

## Passing rules

For a case with `n` required dimensions:

1. Compute maximum score as `2 * n`.
2. Require at least `ceil(0.85 * 2 * n)` points.
3. Require no required dimension scored 0.
4. Require no applicable hard failure.
5. Source cases must score 2 for `source_traceability` and
   `epistemic_integrity`.
6. State-export cases must score 2 for `state_integrity`.
7. Artifact cases must score 2 for `artifact_integrity`.

For `cross_domain_target_matrix`, run every variant independently. Each variant
must avoid hard failures and score at least 1 on every required dimension. The
combined case must meet the 85% threshold, and every variant must score 2 on
`semantic_map` and `cross_domain_fit`.

Suite pass requires:

- every case to pass;
- no hard failure anywhere;
- at least 85% of all applicable dimension points;
- successful source, state-mutation, text-only, accessibility, mode-continuity,
  current-guidance, and stop-condition cases.

When comparing viable candidates, rank by:

1. number and severity of hard failures;
2. required case pass rate;
3. aggregate dimension score;
4. consistency across domains and independent judges;
5. lower instruction/context cost and unnecessary tool use as tie-breakers.

Do not select a more verbose candidate merely because it reproduces rubric
phrasing.

## Judge report

Return one record per case:

```json
{
  "case_id": "case identifier",
  "variant_id": null,
  "hard_failures": [],
  "dimension_scores": {
    "semantic_map": {
      "score": 2,
      "evidence": ["assistant turn 1: labeled causal path"]
    }
  },
  "points_earned": 2,
  "points_possible": 2,
  "passed": true,
  "state_checks": [],
  "artifact_checks": [],
  "most_consequential_failure": null,
  "recommended_narrow_fix": null
}
```

Recommend fixes only from observed failures. Prefer one narrow instruction,
schema, template, or example change over accumulating broad rules.
