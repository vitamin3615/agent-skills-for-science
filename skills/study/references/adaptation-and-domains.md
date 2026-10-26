# Adaptation, routes, modes, and domain lenses

Read this reference when selecting a learning route, changing mode, building the
question frontier, or adapting the graph ontology. Treat every list as a menu,
not a required sequence.

## Choose the next question

Select the question that most reduces uncertainty on the learner's critical
path to the anchor answer. Prefer questions that expose a high-leverage missing
edge over questions that merely add another node.

Use these signals qualitatively:

- **Anchor leverage:** answering it materially advances the central question.
- **Dependency leverage:** several useful ideas depend on it.
- **Diagnostic value:** different answers distinguish plausible learner models.
- **Misconception value:** it tests a suspected faulty connection.
- **Goal fit:** it supports the requested exam, project, explanation, or task.
- **Transfer value:** it enables prediction or use outside the worked example.
- **Time cost:** it can be resolved within the useful remaining scope.

Do not assign a numeric priority unless the learner or host workflow needs one.
Store a short reason in state.

## Question graph layers

Draw selectively from these layers. Do not ask every question or assume the
layers must be traversed in order.

1. **Orientation:** What is the phenomenon, problem, argument, or system? Why
   does it matter? Where does it fit?
2. **Structure:** What are its important parts, roles, or variables? How are
   they related?
3. **Mechanism:** What changes what? Through which intermediate steps? What
   produces the observed behavior?
4. **Formalization:** Can the relation be expressed mathematically, logically,
   algorithmically, or procedurally? What assumptions make that form valid?
5. **Evidence:** How do we know? What observation, source, derivation, or
   argument supports the edge?
6. **Contrast and boundary:** What looks similar but differs structurally? When
   does the model fail? Which counterexample matters?
7. **Consequence and application:** What follows? Where is the structure useful?
8. **Transfer:** What does the map predict in a changed case? Which model should
   the learner choose there?
9. **Synthesis:** Can the learner reconstruct the critical subgraph and explain
   why each important edge holds?

## Route selection

Routes bias attention; they do not create separate graphs.

| Route | Prefer when | First useful move | Evidence that changes route |
|---|---|---|---|
| Top-down overview | Learner lacks orientation or requests a field map | Context-to-core map | A specific bottleneck emerges |
| Bottom-up foundations | Several critical edges depend on one weak foundation | Test the nearest prerequisite | Foundation is sufficient or was not the real gap |
| Problem-first | Goal is practical or motivation is weak | Present a meaningful case/puzzle | Learner cannot parse the problem state |
| Mechanism-first | Learner knows vocabulary but not causation | Predict an intermediate change | Missing entity/property becomes blocking |
| Example-first | Abstraction or notation is the bottleneck | Compare one worked and one near case | Learner can generalize the structure |
| Proof-first | Goal is mathematical justification and definitions are ready | Identify assumptions and desired implication | A missing lemma or representation appears |
| Application-first | Goal is immediate use or project delivery | Attempt a realistic task | Error reveals a just-in-time concept |
| Exam-focused | Objectives and assessment forms are known | Map objectives to concept/edge/task | Diagnostic shows a foundational misconception |
| Misconception-repair | Evidence supports a faulty node or edge | Contrast case that current model cannot explain | Corrected relation is independently demonstrated |
| Project-driven | Artifact or investigation is the learning vehicle | Map decisions to concepts and success criteria | Project failure exposes another dependency |

Default route:

`short top-down orientation -> meaningful problem -> just-in-time prerequisite
-> mechanism -> formalization when useful -> transfer`

## Modes over one shared state

Switch modes without resetting identifiers, evidence, mastery, misconceptions,
or source references.

| Mode | Attention bias | Typical learner action |
|---|---|---|
| Explore | Widen context while keeping branches collapsed | Choose a promising frontier and explain why |
| Learn | Follow the smallest critical path | Predict, explain, and apply each key relation |
| Deep-Dive | Expand one node, mechanism, derivation, source, or controversy | Reconstruct internal steps or inspect limits |
| Review | Hide/reduce the map and retrieve | Rebuild nodes and labeled edges from memory |
| Challenge | Increase transfer distance, ambiguity, and counterexamples | Diagnose a flawed map or solve a novel case |
| Source | Prioritize provenance, section roles, claims, evidence, and dependency | Link a claim to its locator and support |
| Exam | Align the map with objectives and assessment forms | Choose and justify a method under exam conditions |
| Project | Connect concepts to artifact decisions, feedback, and criteria | Build, analyze, write, design, or investigate |
| Teach-Back | Treat learner explanation as diagnostic evidence | Teach the path while the agent probes gaps |

## Domain ontology lenses

Seed a graph from the relevant lens, then keep only nodes and edges that serve
the anchor question. Add domain-specific node and relationship types when more
precise. Lenses are not checklists or learning order.

### Science and scientific mechanisms

Seed structure:

`entities -> properties -> mechanisms -> evidence -> predictions -> limits`

Useful relations include `interacts with`, `transforms into`, `increases`,
`inhibits`, `is measured by`, `supports`, `predicts`, and `is limited by`.
Separate observation from model and mechanism from correlation. When scale or
time changes matter, make those conditions explicit on edges.

### Mathematics and theorems

Seed structure:

`definitions -> assumptions -> representations -> lemmas -> derivation/proof
-> theorem -> examples/counterexamples -> applications`

Useful relations include `satisfies`, `is equivalent to`, `implies`, `is used
by`, `is necessary for`, `is sufficient for`, `generalizes`, and `refutes`.
Track conceptual meaning separately from symbolic manipulation. A learner may
master a definition node while not mastering the implication used in a proof.

### History

Seed structure:

`context -> actors/institutions -> constraints -> events -> causes ->
consequences -> evidence -> interpretations`

Keep chronological edges (`precedes`, `overlaps`, `lasts through`) distinct from
causal edges (`contributes to`, `enables`, `constrains`). Mark causal weight and
interpretive disagreement without presenting one contested account as fact.

### Humanities, philosophy, and arguments

Seed structure:

`claims/concepts/themes -> evidence -> assumptions -> counterarguments ->
responses -> interpretations -> implications`

For literary works, add speaker, scene, motif, form, textual evidence, and
interpretation nodes as needed. Distinguish what the text says, what a critic
argues, and what the tutor infers. Ask where evidence underdetermines a reading.

### Procedures and practical skills

Seed structure:

`goal -> state -> action -> decision -> feedback -> error mode -> correction
-> success criterion`

Useful relations include `requires`, `changes state to`, `triggers`, `is
detected by`, `corrects`, and `satisfies`. Assess decision edges and error
recovery, not only ordered step recall. Use realistic state changes and stop
conditions.

### Technical systems and programming

Seed structure:

`requirements -> components -> interfaces -> data flow/control flow -> failure
modes -> tradeoffs -> observability`

Useful relations include `calls`, `reads from`, `writes to`, `owns`, `depends
on`, `validates`, `retries`, `fails when`, and `is observed by`. For programming
concepts, use execution traces when state and control flow are the bottleneck;
connect syntax nodes only when they serve semantic understanding.

### Papers, chapters, syllabi, and whole subjects

Use a content map for what is present and a dependency or argument map for why
parts support one another. For a whole subject or syllabus, show a small context
map, choose an anchor tied to the learner goal, and represent major clusters as
collapsed nodes. Do not expand the field merely because its scope is large.

### Project-based learning

Map the project goal to deliverables, decisions, required concepts, evidence,
feedback loops, risks, and success criteria. Let project evidence reveal what to
learn next. Keep task completion and conceptual mastery distinct: a working
artifact can conceal a weak explanation, and a strong explanation can precede
implementation skill.

## Pace and scope adaptation

- **Under 10 minutes:** one anchor path, one diagnostic, one mechanism or
  contrast, one transfer prediction, compact review.
- **10-45 minutes:** initial map, two or three micro-cycles, zoom-out,
  synthesis, transfer, review queue.
- **Longer study:** partition by connected clusters, close each session with
  portable state, and begin later sessions with retrieval rather than recap.
- **Large target:** keep clusters collapsed and negotiate the anchor through one
  high-value question rather than displaying the whole ontology.
- **Advanced learner:** shorten explanations, test boundaries and evidence, and
  move sooner to comparison, derivation, or transfer.
- **Novice learner:** reduce visible nodes, use concrete contrasts, and add one
  prerequisite only when the target relation needs it.
