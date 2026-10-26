# Book Comparison Example: 10-Book Parallel Analysis

Complete walkthrough of comparing a research document against 10 source books using parallel worker orchestration.

## Scenario

**User Request**:

```
"Compare my research manuscript (Chapter 3: Methodology) against these 10 source books on research methods:

1. Creswell (2018) - Research Design: Qualitative, Quantitative, and Mixed Methods
2. Saldaña (2015) - The Coding Manual for Qualitative Researchers
3. Miles & Huberman (2014) - Qualitative Data Analysis
4. Yin (2017) - Case Study Research and Applications
5. Bryman (2016) - Social Research Methods
6. Patton (2015) - Qualitative Research & Evaluation Methods
7. Charmaz (2014) - Constructing Grounded Theory
8. Denzin & Lincoln (2017) - The SAGE Handbook of Qualitative Research
9. Maxwell (2012) - Qualitative Research Design
10. Merriam (2015) - Qualitative Research: A Guide to Design and Implementation

Identify alignment, contradictions, and novel contributions in my methodology chapter."
```

---

## Phase 0: Request Understanding

**Sequential-Thinking Analysis**:

```json
{
  "goal": "Compare manuscript Chapter 3 against 10 methodology books to identify alignment, contradictions, and novel contributions",
  "success_criteria": [
    "All 10 books compared against manuscript",
    "Alignment status determined for key methodological claims",
    "Contradictions explicitly identified",
    "Novel contributions highlighted"
  ],
  "requirements": [
    "Precise citations from books (page numbers)",
    "Exact quotes for evidence",
    "Systematic comparison framework",
    "Synthesis of findings across all books"
  ],
  "constraints": [
    "Must maintain attribution to specific books",
    "No hallucination of quotes or citations",
    "Complete coverage of all 10 books"
  ],
  "output_format": "Structured report with per-book findings and integrated synthesis",
  "task_type": "comparison",
  "complexity": "high",
  "reasoning": "This is a complex multi-source comparison requiring parallel processing of 10 independent book comparisons, followed by synthesis. High complexity due to citation requirements and need for accuracy."
}
```

**Output**: `request_analysis.json`

---

## Phase 1: Task Decomposition

**AI-Generated Task Plan**:

```json
{
  "subtasks": [
    {
      "id": "task_1",
      "description": "Compare manuscript Chapter 3 methodology against Creswell (2018) book",
      "complexity": "medium",
      "output_format": "Markdown comparison report with claims, alignment, evidence, citations",
      "worker_type": "comparison",
      "data_context": "Book: Creswell (2018) Research Design\nManuscript: Chapter 3 sections 3.1-3.5"
    },
    {
      "id": "task_2",
      "description": "Compare manuscript Chapter 3 methodology against Saldaña (2015) book",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Saldaña (2015) Coding Manual\nManuscript: Chapter 3 sections 3.1-3.5"
    },
    {
      "id": "task_3",
      "description": "Compare manuscript against Miles & Huberman (2014)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Miles & Huberman (2014) Qualitative Data Analysis"
    },
    {
      "id": "task_4",
      "description": "Compare manuscript against Yin (2017)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Yin (2017) Case Study Research"
    },
    {
      "id": "task_5",
      "description": "Compare manuscript against Bryman (2016)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Bryman (2016) Social Research Methods"
    },
    {
      "id": "task_6",
      "description": "Compare manuscript against Patton (2015)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Patton (2015) Qualitative Research"
    },
    {
      "id": "task_7",
      "description": "Compare manuscript against Charmaz (2014)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Charmaz (2014) Grounded Theory"
    },
    {
      "id": "task_8",
      "description": "Compare manuscript against Denzin & Lincoln (2017)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Denzin & Lincoln (2017) SAGE Handbook"
    },
    {
      "id": "task_9",
      "description": "Compare manuscript against Maxwell (2012)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Maxwell (2012) Qualitative Research Design"
    },
    {
      "id": "task_10",
      "description": "Compare manuscript against Merriam (2015)",
      "complexity": "medium",
      "output_format": "Markdown comparison report",
      "worker_type": "comparison",
      "data_context": "Book: Merriam (2015) Qualitative Research Guide"
    }
  ],
  "dependencies": {},
  "execution_order": [
    "task_1",
    "task_2",
    "task_3",
    "task_4",
    "task_5",
    "task_6",
    "task_7",
    "task_8",
    "task_9",
    "task_10"
  ],
  "reasoning": "Each book comparison is independent and can be parallelized. All 10 tasks have medium complexity (substantial but not highly complex). No dependencies between tasks. Results will be aggregated in synthesis phase."
}
```

**Output**: `task_plan.json`

**Key Decisions**:

- 10 independent parallel tasks (one per book)
- Medium complexity (each comparison is substantial)
- Comparison worker type for all tasks
- No dependencies (fully parallelizable)

---

## Phase 2: Parallelization Strategy

**Worker Allocation Algorithm**:

```python
parallel_tasks = 10
avg_complexity = "medium"
has_dependencies = False

# Algorithm determines: min(5, 10) = 5 workers
# (Medium complexity allows up to 5 workers)
```

**Parallelization Configuration**:

```json
{
  "worker_count": 5,
  "parallel_groups": [
    [{"id": "task_1", ...}, {"id": "task_6", ...}],
    [{"id": "task_2", ...}, {"id": "task_7", ...}],
    [{"id": "task_3", ...}, {"id": "task_8", ...}],
    [{"id": "task_4", ...}, {"id": "task_9", ...}],
    [{"id": "task_5", ...}, {"id": "task_10", ...}]
  ],
  "sequential_tasks": [],
  "avg_complexity": "medium",
  "total_tasks": 10,
  "parallel_tasks_count": 10,
  "sequential_tasks_count": 0
}
```

**Execution Plan**:

- **Round 1**: Workers 1-5 process tasks 1-5 in parallel
- **Round 2**: Workers 1-5 process tasks 6-10 in parallel
- Total execution time ≈ 2 × (single task time)

---

## Phase 3: Worker Prompt Generation

**Sample Prompt for Worker 1 (Creswell comparison)**:

````markdown
# 1. SYSTEM CONTEXT

You are Worker AI #1 in a multi-agent orchestration system.

**Coordination Mode**: Parallel execution
**Your Role**: Worker 1 of 5
**Group**: Parallel Group 1
**Independence**: Your task is independent of other workers. Results will be synthesized separately.
**Focus**: Concentrate solely on comparing manuscript against Creswell (2018).

# 2. TASK DEFINITION

**Task ID**: task_1
**Description**: Compare manuscript Chapter 3 methodology against Creswell (2018) book
**Complexity**: medium

# 3. METHODOLOGY

**FRAMEWORK**:

1. Identify claims/elements in manuscript Chapter 3
2. Find corresponding content in Creswell (2018)
3. Assess alignment: ALIGNED | PARTIAL | MISSING | CONTRADICTORY
4. Extract verbatim evidence with citations
5. Note novel additions in manuscript

# 4. DATA/CONTENT

**Manuscript**: Chapter 3 Methodology (sections 3.1-3.5)
**Book**: Creswell (2018) - Research Design: Qualitative, Quantitative, and Mixed Methods Approaches

# 5. OUTPUT FORMAT

Generate structured markdown report:

```markdown
# Comparison: Manuscript vs Creswell (2018)

## Summary

[Brief overview]

## Alignment Analysis

### Claim 1: [Manuscript claim]

- **Source Quote**: "[Exact quote from manuscript]" (p. X)
- **Creswell Quote**: "[Exact quote from book]" (p. Y)
- **Alignment**: ALIGNED | PARTIAL | MISSING | CONTRADICTORY
- **Evidence**: [Supporting evidence]

[Continue for all claims...]

## Novel Elements in Manuscript

[Elements not in Creswell]

## Overall Assessment

[Synthesis]
```
````

# 6. QUALITY CRITERIA

**Completeness**: Cover all methodology claims in Chapter 3
**Evidence**: Support all assessments with exact quotes
**Accuracy**: Ensure citations are precise (page numbers)
**Clarity**: Use clear alignment categories

# 7. CRITICAL CONSTRAINTS

**NO HALLUCINATION**: Only quote text actually present in sources
**EXACT CITATIONS**: Always include page numbers for quotes
**STAY ON TASK**: Only compare against Creswell (2018), not other books

```

**Total Prompts Generated**: 10 (one per worker/book)

**Output**: `worker_prompts.json` with all 10 prompts

---

## Phase 4: Parallel Worker Execution

**Execution Timeline**:

```

Time 0:00 - Workers 1-5 start (tasks 1-5)
Time 0:00 - Worker 1: Creswell comparison begins
Time 0:00 - Worker 2: Saldaña comparison begins
Time 0:00 - Worker 3: Miles & Huberman comparison begins
Time 0:00 - Worker 4: Yin comparison begins
Time 0:00 - Worker 5: Bryman comparison begins

Time 8:45 - Worker 3 completes (Miles & Huberman)
Time 9:12 - Worker 1 completes (Creswell)
Time 9:30 - Worker 5 completes (Bryman)
Time 9:45 - Worker 2 completes (Saldaña)
Time 10:03 - Worker 4 completes (Yin)

Time 10:03 - Workers 1-5 start second round (tasks 6-10)
Time 10:03 - Worker 1: Patton comparison begins
Time 10:03 - Worker 2: Charmaz comparison begins
...

Time 19:30 - All workers complete

````

**Worker Results Summary**:
- Total workers: 5
- Total tasks: 10
- Execution time: ~20 minutes (vs ~100 minutes sequential)
- Success rate: 10/10 (100%)

**Sample Worker Output** (Worker 1 - Creswell):

**Sample Worker Output (Worker 7 - Charmaz, 2014)**

```markdown
# Comparison: Manuscript vs Charmaz (2014)

## Summary
The manuscript partially aligns with Charmaz's constructivist grounded theory, aligning on memoing and iterative coding but diverging on sampling rationale. Evidence below cites verbatim passages from Charmaz and the manuscript with page references.

## Alignment Analysis

### Claim 1: Researcher as co-constructor (Ontology)
- **Manuscript Quote**: "The researcher acknowledges their positionality and co-constructs meaning with participants" (Manuscript p. 49)
- **Charmaz Quote**: "Constructivist grounded theory assumes that data and analyses are created from shared experiences and relationships between participants and researchers" (Charmaz, 2014, p. 16)
- **Alignment**: ALIGNED
- **Evidence**: Both texts explicitly state a constructivist epistemology and the role of the researcher in co-construction; Charmaz's p.16 explains the stance that the manuscript adopts (direct quote).

### Claim 2: Coding strategy — initial vs focused coding
- **Manuscript Quote**: "Coding proceeded with an initial open pass followed by focused thematic coding to develop categories" (Manuscript p. 52)
- **Charmaz Quote**: "Initial coding fractures data into actions; focused coding sorts those codes into conceptual categories that drive theoretical direction" (Charmaz, 2014, p. 46)
- **Alignment**: ALIGNED
- **Evidence**: Manuscript and Charmaz describe the same two-stage coding progression; Charmaz's p.46 provides the methodological rationale that supports the manuscript's approach.

### Claim 3: Theoretical sampling and sampling rationale
- **Manuscript Quote**: "Participants were selected primarily for diversity of experience using purposive sampling" (Manuscript p. 50)
- **Charmaz Quote**: "Theoretical sampling involves selecting participants to develop and refine emerging categories rather than to ensure representativeness" (Charmaz, 2014, p. 120)
- **Alignment**: PARTIAL
- **Evidence**: Manuscript uses purposive sampling with an emphasis on diversity; Charmaz recommends theoretical sampling tied to analytic needs. Recommend clarifying whether purposive sampling was guided by emergent categories (to fully align with Charmaz).

## Contradictions and Resolution
- **Apparent Tension**: Manuscript emphasizes purposive diversity sampling while Charmaz foregrounds theoretical sampling (p.120). This is a contextual difference rather than a direct contradiction: if the manuscript reports that participant selection later targeted emergent categories, the approaches are compatible. If not, recommend updating methods to describe how sampling responded to analytic needs.

## Novel Elements
- Manuscript documents use of mixed deductive-inductive coding linking grounded theory steps to pre-existing frameworks (Manuscript p. 54). Charmaz discusses abductive moves but does not prescribe combining deductive frameworks; thus the manuscript's explicit hybridization is a novel operationalization with partial precedent (see Charmaz discussion of abductive analytic moves, p. 88).

## Overall Assessment
- Charmaz (2014) largely supports the manuscript's grounded-theory-informed practices (alignment on researcher reflexivity, coding stages, memoing). The primary gap is explicit linkage between sampling decisions and emerging theory; recommend revising the Methods to state how sampling decisions were driven by analytic progress (or provide examples from memos showing such linkage).
````

-- Output: worker_7_result.md (sample)

```markdown
# Comparison: Manuscript vs Creswell (2018)

## Summary

The manuscript's methodology shows strong alignment with Creswell's mixed methods framework. Of 12 key methodological claims examined, 8 are ALIGNED, 3 are PARTIAL, and 1 is MISSING. No contradictions identified.

## Alignment Analysis

### Claim 1: Sequential explanatory design

- **Manuscript Quote**: "This study employs a sequential explanatory design, beginning with quantitative data collection followed by qualitative interviews" (p. 42)
- **Creswell Quote**: "The sequential explanatory design consists of first collecting quantitative data and then collecting qualitative data to help explain the quantitative results" (p. 211)
- **Alignment**: ALIGNED
- **Evidence**: Both sources describe identical two-phase sequential approach with quantitative first, qualitative second.

### Claim 2: Purposive sampling strategy

- **Manuscript Quote**: "Participants were selected using purposive sampling to ensure diversity in experience levels" (p. 44)
- **Creswell Quote**: "Purposive sampling involves selecting individuals who can purposefully inform an understanding of the research problem" (p. 156)
- **Alignment**: ALIGNED
- **Evidence**: Manuscript application matches Creswell's definition of purposive sampling.

...

## Novel Elements in Manuscript

- **Integration of mobile data collection**: Manuscript describes use of mobile apps for real-time data capture (p. 45), not discussed in Creswell (2018)
- **Hybrid analysis approach**: Combines deductive and inductive coding in novel way (p. 47)

## Overall Assessment

Strong methodological alignment with Creswell's framework. The manuscript demonstrates appropriate application of mixed methods principles. Novel contributions include mobile data collection and hybrid analysis approach.
```

**Output**: 10 worker result files + `worker_results.json`

---

## Phase 5: Response Evaluation

**Quality Evaluation** (Sample - Worker 1):

**Layer 1: Structural Check**

- Non-empty: ✓
- Length: 2,450 characters ✓
- Has headers: ✓
- Has lists: ✓
- **Score**: 100/100

**Layer 2: Completeness**

- Keywords present: "methodology", "sequential", "qualitative", "quantitative" ✓
- Success criteria addressed: Alignment status ✓, Citations ✓, Novel elements ✓
- Format: Markdown with headers ✓
- **Score**: 95/100 (missing one minor detail)

**Layer 3: Hallucination Detection**

- Vague claims: 1 instance (acceptable)
- Citations present: 15 citations ✓
- No comparatives without baseline: ✓
- No contradictions: ✓
- **Score**: 95/100

**Overall Score**: (100 × 0.25) + (95 × 0.45) + (95 × 0.3) = **96.25/100**

**Quality Gate**: ACCEPT

**Evaluation Summary Across All Workers**:

```json
{
  "individual_evaluations": {
    "worker_1": { "score": 96.25, "quality_gate": "accept" },
    "worker_2": { "score": 92.5, "quality_gate": "accept" },
    "worker_3": { "score": 88.0, "quality_gate": "accept" },
    "worker_4": { "score": 94.5, "quality_gate": "accept" },
    "worker_5": { "score": 91.0, "quality_gate": "accept" },
    "worker_6": { "score": 85.5, "quality_gate": "accept" },
    "worker_7": { "score": 92.0, "quality_gate": "accept" },
    "worker_8": { "score": 93.0, "quality_gate": "accept" },
    "worker_9": { "score": 89.5, "quality_gate": "accept" },
    "worker_10": { "score": 87.0, "quality_gate": "accept" }
  },
  "overall_quality": {
    "average_score": 90.9,
    "quality": "very_good",
    "min_score": 85.5,
    "max_score": 96.25
  },
  "passed_workers": 10,
  "flagged_workers": 0,
  "failed_workers": 0
}
```

**Output**: `evaluation_results.json`

---

## Phase 6: Result Synthesis

**Strategy Selection**:

- Task type: comparison
- Citation density: 150 citations / 10 workers = 15 citations/worker
- Decision: **Evidence Database** strategy (high citation density)

Alternative: **Aggregation** strategy would also work (independent tasks)

**Synthesis Process** (Evidence Database):

1. **Extract Evidence Database**:

   ```json
   [
     {
       "claim": "Sequential explanatory design",
       "citation": "Creswell p. 211",
       "worker_id": "worker_1"
     },
     {
       "claim": "Sequential explanatory design",
       "citation": "Maxwell p. 45",
       "worker_id": "worker_9"
     },
     ...
   ]
   ```

   Total evidence entries: 150

2. **Delegate to Synthesis Worker**:
   - Model: gemini-3.1-pro-preview (high complexity)
   - Prompt: Organize evidence by themes, build synthesis

3. **Generate Integrated Synthesis**

**Synthesized Output** (excerpt):

```markdown
# Synthesis: Manuscript Methodology vs 10 Source Books

## Executive Summary

The manuscript's methodology demonstrates strong alignment with established research methods literature. Across 10 authoritative sources, 78% of methodological claims are fully aligned, 18% partially aligned, 3% missing, and 1% contradictory. The manuscript makes several novel contributions including mobile data collection integration and hybrid analysis frameworks.

## Theme-Based Evidence Analysis

### Theme 1: Research Design Framework

**Finding**: Manuscript uses sequential explanatory mixed methods design
**Evidence**:

- Creswell (2018, p. 211): "Sequential explanatory design consists of first collecting quantitative data..." [ALIGNED]
- Maxwell (2012, p. 45): "Sequential designs allow quantitative results to inform qualitative inquiry" [ALIGNED]
- Bryman (2016, p. 639): Describes same two-phase approach [ALIGNED]
- **Consensus**: Strong (3/10 books explicitly support, 0 contradict)

### Theme 2: Sampling Strategy

**Finding**: Purposive sampling for participant selection
**Evidence**:

- Creswell (2018, p. 156): "Purposive sampling involves selecting individuals..." [ALIGNED]
- Patton (2015, p. 264): "Purposive sampling focuses on information-rich cases" [ALIGNED]
- Merriam (2015, p. 96): Similar definition [ALIGNED]
- **Consensus**: Strong (3/10 books support)

...

## Novel Contributions

### Mobile Data Collection (Not in sources)

- Manuscript describes real-time mobile app data capture
- Not mentioned in: Creswell, Saldaña, Miles & Huberman, Yin, Bryman, Patton, Charmaz, Denzin & Lincoln, Maxwell, Merriam
- **Assessment**: Novel methodological innovation

### Hybrid Coding Approach

- Combines deductive and inductive coding uniquely
- Partial mention in: Saldaña (2015, p. 142) - but different implementation
- **Assessment**: Novel synthesis of existing approaches

## Contradictions

### Data Analysis Sequencing

- **Manuscript**: Recommends simultaneous qualitative and quantitative analysis (p. 47)
- **Yin (2017, p. 178)**: "Analysis should follow data collection sequentially"
- **Resolution**: Manuscript approach may be appropriate for specific context (real-time data)
- **Status**: MINOR CONTRADICTION - Context-dependent validity

## Overall Assessment

**Alignment Score**: 87% (weighted by source authority)
**Novelty**: High (2 significant novel contributions)
**Methodological Rigor**: Strong (aligns with majority of authoritative sources)
**Recommendation**: Manuscript methodology is well-grounded in literature with meaningful innovations
```

**Output**: `synthesis_result.md`

---

## Phase 7: Meta-Review

**Meta-Review Assessment**:

```json
{
  "timestamp": "2026-01-17T14:35:22",
  "task_plan_quality": "excellent",
  "worker_performance": {
    "total": 10,
    "successful": 10,
    "failed": 0
  },
  "quality_assessment": {
    "average_score": 90.9,
    "quality": "very_good"
  },
  "synthesis_quality": "excellent",
  "issues_identified": [],
  "recommendations": [],
  "decision": "continue"
}
```

**Decision**: Continue to final report (quality acceptable)

---

## Phase 8: Final Report

**Final Report** (excerpt):

```markdown
# Multi-Agent Orchestration Report: Book Comparison Analysis

**Generated**: 2026-01-17 14:36:15
**Session ID**: 20260117_143022

## Executive Summary

**Goal**: Compare manuscript methodology chapter against 10 authoritative research methods books
**Task Type**: comparison
**Workers**: 10 (5 parallel workers, 2 rounds)
**Quality Score**: 89.6/100
**Synthesis Strategy**: evidence_database

## Methodology

### Task Decomposition

- Subtasks: 10 (one per book)
- Parallelization: 5 workers in 2 rounds
- Strategy: Evidence database synthesis
- Execution time: 19.5 minutes

## Synthesis Results

[Full synthesis from Phase 6...]

## Quality Assessment

- Average Score: 90.9/100
- Accepted Workers: 10
- Flagged Workers: 0
- Rejected Workers: 0

## Worker Contributions

### worker_1: Creswell (2018)

- **Task**: task_1
- **Status**: success
- **Quality Score**: 96.25/100
- **Key Findings**: Strong alignment on sequential design, purposive sampling

### worker_2: Saldaña (2015)

- **Task**: task_2
- **Status**: success
- **Quality Score**: 92.5/100
- **Key Findings**: Coding strategies aligned, novel hybrid approach identified

...

[Continues for all 10 workers]

## Appendices

### A. Task Plan

[Full task plan JSON]

### B. State File

State file: `Temp/orchestrator_work/.orchestrator_state.json`
```

**Output**: `final_report.md` - **COMPLETE**

---

## Performance Metrics

**Execution Stats**:

- **Total time**: 19.5 minutes
- **Sequential time (estimated)**: 100 minutes
- **Speedup**: 5.1× faster
- **Worker efficiency**: 100% success rate
- **Quality**: 89.6/100 average

**Resource Usage**:

- **API calls**: 11 (1 task decomposition + 10 comparisons)
- **Tokens used**: ~150,000 tokens
- **State file size**: 45 KB
- **Total output**: 10 worker files + 1 synthesis + 1 report = 12 files

**Cost-Benefit**:

- Parallelization reduces time by 80%
- High quality maintained (89.6/100)
- Full traceability preserved
- Resumable execution

---

## Lessons Learned

**What Worked Well**:

1. Parallel execution dramatically reduced time
2. Quality evaluation caught Worker 7 issues
3. Evidence database synthesis handled 150+ citations cleanly
4. Per-book structure maintained clear attribution

**Potential Improvements**:

1. Could increase to 7 workers for even faster execution
2. Layer 4 AI evaluation could catch subtle issues in edge cases

**Recommendations for Similar Tasks**:

1. Use evidence database strategy for citation-heavy comparisons
2. Allocate 5-7 workers for 10+ independent tasks
3. Medium complexity is appropriate for book comparisons
4. Always include precise citation requirements in prompts

This example demonstrates the full power of multi-agent orchestration for complex comparison tasks.
