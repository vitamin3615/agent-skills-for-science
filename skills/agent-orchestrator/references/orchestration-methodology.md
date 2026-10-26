## Multi-Agent Orchestration Methodology

Comprehensive guide to the 9-phase workflow (Phases 0-8) for intelligent multi-agent task coordination.

## Overview

The Agent Orchestrator implements a systematic 9-phase workflow (Phases 0-8) that transforms user requests into high-quality synthesized results through intelligent task decomposition, parallel execution, quality control, and context-dependent synthesis.

**Design Principles**:

1. **Fully Automated**: No manual checkpoints (user reviews final results)
2. **Intelligence-Driven**: AI-powered task decomposition (not hardcoded workflows)
3. **Quality-Focused**: Multi-layer evaluation with automatic re-execution
4. **Resumable**: Full state management for fault tolerance
5. **General-Purpose**: Handles any task type through dynamic adaptation

---

## Quick Decision: Which Tier Should You Use?

Before diving into the full 9-phase workflow, determine if you need it:

### Tier Selection Flowchart

```
START: What is your request?
│
├─ "Analyze these 5 independent files" → CLEAR TASKS?
│   └─ YES → Need synthesis beyond aggregation?
│       ├─ NO → **TIER 1: Simple Parallel** ✓ (70% of tasks)
│       └─ YES → **TIER 3: Phases 3-6** (10% of tasks)
│
├─ "I have a task plan, just execute it" → TASK PLAN PROVIDED?
│   └─ YES → **TIER 2: Phase 4 Only** (15% of tasks)
│
└─ "Evaluate proposal from multiple perspectives" → COMPLEX DECOMPOSITION?
    └─ YES → **TIER 4: Full Orchestrator** ✓ (5% of tasks)
```

### When to Use Each Tier

**Tier 1: Simple Parallel** (See [simple-parallel-guide.md](simple-parallel-guide.md))

- Request contains explicit list of 3-10 independent items
- Output is straightforward aggregation (concatenation or basic structure)
- No need for intelligent synthesis (consensus, evidence-weighting, etc.)
- **Performance**: 282s for 5 workers (100% success rate), ~5% overhead
- **Example**: "Analyze security vulnerabilities in auth.py, database.py, api.py, utils.py, models.py"

**Tier 2: Phase 4 Only** (Manual decomposition)

- You provide explicit task plan with worker prompts
- Need execution infrastructure but not AI planning
- Skip Phases 0-3, execute your custom task definitions
- **Performance**: ~15% overhead vs Simple Parallel
- **Example**: "Execute these 6 analysis tasks I've defined in tasks.json"

**Tier 3: Phases 3-6** (Parallel + Synthesis)

- Clear task decomposition (you can list subtasks)
- Need intelligent synthesis beyond simple concatenation
- Skip planning phases (Phases 0-2), focus on execution + synthesis
- **Performance**: ~40% overhead
- **Example**: "Analyze 5 research papers and build consensus on key findings"

**Tier 4: Full Orchestrator** (This guide)

- Request requires intelligent decomposition (Phases 0-1)
- Complex synthesis with meta-cognitive quality review
- High-stakes decisions requiring iteration and validation
- Unclear task boundaries or dependencies
- **Performance**: Full 9-phase workflow
- **Example**: "Conduct comprehensive evaluation of research proposal from multiple expert perspectives"

### Performance Comparison (5-task workload)

```
Tier 1 (Simple Parallel):   282s (100% success) ← RECOMMENDED DEFAULT
Tier 2 (Phase 4 Only):       ~325s (~15% overhead)
Tier 3 (Phases 3-6):         ~395s (~40% overhead)
Tier 4 (Full Orchestrator):  600s+ or FAILED (Phase 0 can get stuck)
```

### Decision Rules

**Use Tier 1** if:

- ✅ You can explicitly list 3-10 independent tasks
- ✅ Tasks don't depend on each other's results
- ✅ Simple aggregation is sufficient (no complex synthesis)

**Use Tier 4** if:

- ❌ Cannot list subtasks explicitly (need AI decomposition)
- ❌ Tasks have complex dependencies
- ❌ Need intelligent synthesis (consensus, evidence-weighting)
- ❌ High-stakes decision requiring quality review

---

## Full 9-Phase Workflow (Tier 4)

The following sections describe the complete orchestration workflow for Tier 4 execution.

---

## Phase 0: Request Understanding

**Objective**: Parse and deeply understand the user's request using Sequential-Thinking.

**Process**:

1. **Sequential-Thinking Analysis**
   - Call Sequential-Thinking MCP with structured prompt
   - Extract: goal, success criteria, requirements, constraints
   - Identify task type and complexity

2. **Request Parsing**

   ```
   Goal Identification: What is the user trying to achieve?
   Success Criteria: How will we know the task is complete?
   Requirements: What are explicit/implicit requirements?
   Constraints: Time, resource, or quality constraints?
   Output Format: What form should results take?
   Context Clues: Domain-specific context?
   ```

3. **Categorization**
   - **Task Type**: comparison | analysis | synthesis | evaluation | mixed
   - **Complexity**: low | medium | high

**Output**: `request_analysis.json`

```json
{
  "goal": "Clear statement of goal",
  "success_criteria": ["criterion 1", "criterion 2"],
  "requirements": ["req 1", "req 2"],
  "constraints": ["constraint 1"],
  "output_format": "Expected output description",
  "task_type": "comparison",
  "complexity": "high",
  "reasoning": "Step-by-step reasoning from Sequential-Thinking"
}
```

**Decision Points**:

- If Sequential-Thinking unavailable → FAIL with clear error
- If request too vague → Proceed with conservative assumptions

---

## Phase 1: Task Decomposition & Planning

**Objective**: Intelligently decompose request into subtasks using AI-powered reasoning.

**Process**:

1. **Load Meta-Orchestrator Template**
   - Template: `worker_prompts/meta_orchestrator.txt`
   - Inject request analysis context

2. **Delegate to High-Complexity Worker AI**
   - Model: gemini-3.1-pro-preview (high reasoning capability)
   - Prompt includes: request, goal, requirements, task type, complexity
   - Request JSON output with subtasks and dependencies

3. **Parse Task Plan**
   - Extract subtasks array
   - Build dependency graph
   - Determine execution order

4. **Fallback Handling**
   - If AI decomposition fails → Create single-task plan
   - If JSON parsing fails → Extract manual structure

**Output**: `task_plan.json`

```json
{
  "subtasks": [
    {
      "id": "task_1",
      "description": "Clear task description",
      "complexity": "medium",
      "output_format": "Expected output",
      "worker_type": "analysis",
      "data_context": "Specific data/content"
    }
  ],
  "dependencies": {
    "task_2": ["task_1"]
  },
  "execution_order": ["task_1", "task_2"],
  "reasoning": "AI reasoning for decomposition"
}
```

**Quality Criteria**:

- Subtasks should be substantial (not micro-tasks)
- Clear boundaries between subtasks
- Dependencies accurately captured
- Realistic complexity assessments

See **[task-patterns.md](task-patterns.md)** for decomposition best practices.

---

## Phase 2: Parallelization Strategy

**Objective**: Determine optimal worker allocation (1-7 workers) based on task characteristics.

**Algorithm**:

```python
def determine_worker_count(parallel_tasks, avg_complexity, has_dependencies):
    # Rule 1: Heavy dependencies → Sequential
    if has_dependencies:
        return 1

    # Rule 2: Few tasks → Match worker count
    if parallel_tasks <= 2:
        return min(2, parallel_tasks)

    # Rule 3: Many low-complexity tasks → More workers
    elif parallel_tasks <= 5 and avg_complexity == "low":
        return min(5, parallel_tasks)

    # Rule 4: High-complexity tasks → Fewer workers (resource needs)
    elif avg_complexity == "high":
        return min(3, parallel_tasks)

    # Rule 5: Default balanced allocation
    else:
        return min(5, parallel_tasks)
```

**Process**:

1. **Identify Parallel Tasks**
   - Tasks with no dependencies
   - Can execute concurrently

2. **Identify Sequential Tasks**
   - Tasks with dependencies
   - Must execute in order

3. **Calculate Average Complexity**
   - Count low/medium/high across subtasks
   - Determine dominant complexity level

4. **Create Parallel Groups** (Round-Robin Allocation)
   - Distribute parallel tasks across workers using round-robin strategy
   - **Round-Robin**: If you have N workers and M tasks (where M > N):
     - Worker 1 gets tasks: 1, N+1, 2N+1, ...
     - Worker 2 gets tasks: 2, N+2, 2N+2, ...
     - Worker i gets tasks: i, N+i, 2N+i, ...
   - Example: 5 workers, 10 tasks → Each worker handles 2 tasks in sequence
   - Balance load evenly across all workers

**Output**: Parallelization configuration

```json
{
  "worker_count": 5,
  "parallel_groups": [
    [{"id": "task_1", ...}],
    [{"id": "task_2", ...}]
  ],
  "sequential_tasks": [],
  "avg_complexity": "medium",
  "total_tasks": 10,
  "parallel_tasks_count": 10,
  "sequential_tasks_count": 0
}
```

---

## Phase 3: Worker Prompt Generation

**Objective**: Generate optimized prompts using hierarchical structure.

**Hierarchical Prompt Structure**:

```
1. SYSTEM CONTEXT
   - Worker role and ID
   - Coordination mode (parallel/sequential)
   - Total worker count
   - Cross-worker awareness

2. TASK DEFINITION
   - Task ID and description
   - Complexity level
   - Expected outputs

3. METHODOLOGY
   - Task-specific framework
   - Step-by-step approach
   - Best practices

4. DATA/CONTENT
   - Specific data to analyze
   - Context and background
   - Scope boundaries

5. OUTPUT FORMAT
   - Exact structure required
   - Examples if needed
   - Format constraints

6. QUALITY CRITERIA
   - Completeness requirements
   - Evidence standards
   - Success criteria

7. CRITICAL CONSTRAINTS
   - No hallucination
   - Exact citations
   - Stay on task
   - User constraints
```

**Process**:

1. **Select Worker Type Template**
   - comparison_worker.txt
   - analysis_worker.txt
   - synthesis_worker.txt
   - evaluation_worker.txt

2. **Inject Context**
   - Worker ID and coordination context
   - Task definition from plan
   - Success criteria from request analysis

3. **Generate Cross-Worker Awareness**
   - If parallel: "You are worker X of Y, results synthesized separately"
   - If sequential: "Your output used by downstream workers"

**Output**: `worker_prompts.json`

```json
[
  {
    "worker_id": "worker_1",
    "task_id": "task_1",
    "prompt": "Hierarchical prompt text...",
    "complexity": "medium",
    "worker_type": "analysis",
    "group": 0
  }
]
```

See **[delegation-strategies.md](delegation-strategies.md)** for prompt templates and strategies.

---

## Phase 4: Parallel Worker Execution

**Objective**: Execute workers concurrently with fault tolerance.

**Process**:

1. **Separate Parallel and Sequential**
   - Group ≥ 0: Parallel execution
   - Group = -1: Sequential execution

2. **Parallel Execution (ThreadPoolExecutor)**

   ```python
   with ThreadPoolExecutor(max_workers=5) as executor:
       futures = {
           executor.submit(execute_worker, prompt): prompt
           for prompt in parallel_prompts
       }

       for future in as_completed(futures):
           result = future.result(timeout=600)
           save_result(result)
   ```

3. **Sequential Execution**
   - Execute one worker at a time
   - Wait for completion before next
   - Pass outputs to dependent tasks if needed

4. **Retry Logic**
   - Automatic retry on failure (max 2 retries)
   - Exponential backoff
   - Fallback model if primary fails

5. **State Management**
   - Save worker result immediately upon completion
   - Update state file
   - Enable mid-execution resume

**Output**: `worker_results/` directory + `worker_results.json`

```json
[
  {
    "worker_id": "worker_1",
    "task_id": "task_1",
    "output": "Worker output text...",
    "status": "success",
    "execution_time": 45.2,
    "complexity": "medium"
  }
]
```

**Error Handling**:

- Worker failure → Record error, continue with other workers
- Timeout → Retry with longer timeout
- All workers fail → Report partial results

---

## Phase 5: Response Evaluation

**Objective**: Multi-layer quality control with automatic hallucination detection.

**4-Layer Evaluation**:

### Layer 1: Structural Check (Weight: 25%)

**Checks**:

- Non-empty output
- Minimum length (100 chars)
- Has structure (headers, lists)
- Reasonable line count (≥ 5 lines)

**Scoring**:

- Empty → 0
- Too short (< 100 chars) → -40
- No structure → -30
- Minimal content (< 5 lines) → -20

### Layer 2: Completeness (Weight: 45%)

**Checks**:

- Required keywords present
- Success criteria addressed
- Expected format followed
- Required sections present

**Scoring**:

- Missing > 50% keywords → -40
- Success criterion not addressed → -15 each
- Wrong format (JSON vs Markdown) → -30

### Layer 3: Hallucination Detection (Weight: 30%)

**Heuristics**:

- Vague patterns: "many studies", "it is well known", "obviously"
- Absolutes without evidence: "always", "never", "all"
- Missing citations (> 200 words without citations) → -30
- Comparative claims without baseline → -15
- Simple contradictions → -20

**Scoring**:

- Excessive vague claims (> 5) → -25
- Long text without citations → -30
- Multiple comparative claims → -15
- Contradictions detected → -20

### Layer 4: AI Evaluation (Optional, Weight: 30% if used)

**Criteria**:

- Reasoning quality (0-25)
- Evidence strength (0-25)
- Logical consistency (0-25)
- Task fulfillment (0-25)

Delegates to worker AI for meta-evaluation.

**Quality Gates**:

```
Score < 60:  REJECT  - Re-execute required
Score 60-80: FLAG    - Acceptable but review recommended
Score > 80:  ACCEPT  - High quality, ready to use
```

**Output**: `evaluation_results.json`

```json
{
  "individual_evaluations": {
    "worker_1": {
      "score": 85,
      "layer_scores": {...},
      "quality_gate": "accept",
      "issues": [],
      "recommendation": "Accept output. High quality."
    }
  },
  "overall_quality": {
    "average_score": 82.5,
    "quality": "good",
    "min_score": 75,
    "max_score": 90
  },
  "passed_workers": 8,
  "flagged_workers": 2,
  "failed_workers": 0
}
```

---

## Phase 6: Result Synthesis

**Objective**: Combine worker outputs using context-dependent strategy.

**Strategy Selection**:

```python
def select_strategy(worker_results, task_plan, request_analysis):
    """Automatically select optimal synthesis strategy.

    This logic is the canonical reference - matches synthesis-methods.md
    """
    task_type = request_analysis["task_type"]
    has_heavy_deps = analyze_dependencies(task_plan)
    citation_density = count_citations(worker_results)
    worker_count = len(worker_results)

    # Rule 1: Heavy dependencies → Iterative Integration
    if has_heavy_deps:
        return "iterative_integration"

    # Rule 2: Comparison with high citations → Evidence Database
    if task_type == "comparison" and citation_density > 5:
        return "evidence_database"

    # Rule 3: Multiple workers on same content → Consensus
    if worker_count > 3 and task_type in ["analysis", "evaluation"]:
        return "consensus"

    # Rule 4: Default → Aggregation
    return "aggregation"
```

### Strategy 1: Aggregation (Independent Tasks)

**When**: Book comparison, parallel independent analyses

**Approach**:

- Organize findings by worker/task
- Create clear sections for each contribution
- Identify cross-worker patterns
- Maintain traceability

**Example**: 10-book comparison

- Section per book
- Cross-reference common themes
- Executive summary of all findings

### Strategy 2: Consensus (Overlapping Analysis)

**When**: Multiple workers analyzing same content

**Approach**:

- Identify strong consensus (multiple workers)
- Identify weak consensus (single worker)
- Resolve contradictions (weight by quality scores)
- Flag unresolved disagreements

### Strategy 3: Iterative Integration (Sequential Dependencies)

**When**: Tasks with dependency chains

**Approach**:

- Process results in dependency order
- Each iteration builds on previous
- Maintain coherent flow
- Final integrated output

### Strategy 4: Evidence Database (Citation-Heavy)

**When**: Literature reviews, fact-checking, novelty analysis

**Approach**:

- Extract all evidence with citations
- Build structured evidence database
- Generate synthesis from evidence
- Maintain precise citations

**Output**: `synthesis_result.md` + `synthesis_result.json`

See **[synthesis-methods.md](synthesis-methods.md)** for detailed strategies.

---

## Phase 7: Meta-Review & Replanning

**Objective**: Review orchestration quality and identify improvements.

**Assessment Dimensions**:

1. **Task Plan Quality**
   - Were subtasks well-defined?
   - Were dependencies accurate?
   - Was granularity appropriate?

2. **Worker Performance**
   - Success rate
   - Failure patterns
   - Quality distribution

3. **Quality Assessment**
   - Overall quality scores
   - Common issues across workers
   - Evaluation effectiveness

4. **Synthesis Quality**
   - Strategy appropriateness
   - Information preservation
   - Coherence

**Decision Logic**:

```python
def meta_review_decision(evaluation_results, worker_results):
    failure_rate = failed_workers / total_workers
    avg_quality = evaluation_results["overall_quality"]["average_score"]

    issues = []
    recommendations = []

    # Check 1: High failure rate
    if failure_rate > 0.3:
        issues.append("High worker failure rate")
        recommendations.append("Simplify task decomposition")
        decision = "replan"  # Consider re-execution

    # Check 2: Low quality
    elif avg_quality < 70:
        issues.append("Low overall quality")
        recommendations.append("Review worker prompts")
        decision = "continue"  # Acceptable but flag

    # Check 3: Success
    else:
        decision = "continue"

    return decision, issues, recommendations
```

**Output**: `meta_review.json`

---

## Phase 8: Final Report Generation

**Objective**: Generate professional report with full traceability.

**Report Structure**:

```markdown
# Multi-Agent Orchestration Report

**Generated**: [Timestamp]
**Session ID**: [Session ID]

## Executive Summary

- Goal
- Task Type
- Workers Used
- Quality Score
- Synthesis Strategy

## Methodology

### Task Decomposition

- Subtasks count
- Parallelization approach
- Worker allocation

## Synthesis Results

[Full synthesis output from Phase 6]

## Quality Assessment

- Average Score
- Accepted/Flagged/Rejected workers
- Key issues identified

## Worker Contributions

### Worker 1

- Task: [Task ID]
- Status: [Success/Failed]
- Quality Score: [Score/100]

[Repeat for all workers]

## Appendices

### A. Task Plan

[Full task plan JSON]

### B. State File

[Path to state file for resumability]
```

**Output**: `final_report.md`

---

## Resumability

**State File Structure**:

```json
{
  "session_id": "20260117_143022",
  "current_phase": "phase_4",
  "phase_complete": {
    "phase_0": true,
    "phase_1": true,
    "phase_2": true,
    "phase_3": true,
    "phase_4": false,
    ...
  },
  "files": {
    "request_analysis": "path/to/file",
    "task_plan": "path/to/file",
    ...
  },
  "worker_results": {...},
  "errors": [...]
}
```

**Resume Logic**:

1. Load state file
2. Find first incomplete phase
3. Load intermediate outputs from files
4. Continue execution from incomplete phase
5. Update state as phases complete

---

## Error Recovery

**Strategies**:

1. **Corrupted State** → Attempt recovery from backup → Reconstruct from output files
2. **Worker Failure** → Retry with exponential backoff → Use fallback model
3. **Partial Results** → Continue with successful workers → Report partial completion
4. **Quality Gate Failures** → Re-execute low-quality workers → Adjust synthesis strategy

---

## Performance Optimization

**Parallelization**:

- Use ThreadPoolExecutor for true parallelism
- Recommended: 5 workers maximum (optimal for most tasks)
- Absolute limit: 7 workers maximum (resource constraints)
- Balance CPU-bound vs I/O-bound tasks

**Caching**:

- State file enables resume without recomputation
- Worker outputs cached on disk
- Intermediate results preserved

**Cost Optimization**:

- Use appropriate model complexity
- Avoid over-decomposition (fewer workers)
- Skip optional Layer 4 evaluation for low-stakes tasks

---

## Best Practices

1. **Task Decomposition**: Aim for 3-10 subtasks; avoid micro-tasks
2. **Prompt Engineering**: Use hierarchical structure consistently
3. **Quality Control**: Always use Layers 1-3; reserve Layer 4 for critical tasks
4. **Synthesis**: Trust strategy selection logic; manual override rarely needed
5. **State Management**: Regularly backup state files for long-running tasks

This methodology ensures robust, high-quality multi-agent orchestration for complex tasks.
