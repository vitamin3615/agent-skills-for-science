# Task Decomposition Patterns

Common patterns for breaking down complex requests into subtasks for multi-agent orchestration.

## Overview

Task decomposition is the process of breaking a complex user request into discrete subtasks that can be executed by individual worker agents. Good decomposition maximizes parallelization while maintaining clear task boundaries and minimal dependencies.

---

## Pattern 0: Direct Parallel (Simple Bash Execution)

> [!WARNING]
> **Implementation Status**: The `simple_parallel.py` script referenced below is currently **in development**. Until implementation is complete, use the full orchestrator (`scripts/orchestrator.py`).

**When to Use**: Straightforward parallel tasks with explicit item list and no synthesis complexity

**Structure**:
```bash
python scripts/simple_parallel.py --tasks "task1, task2, task3, task4, task5"
```

**Characteristics**:
- **Explicit task list**: User provides 3-10 clearly defined tasks
- **Independent execution**: Zero dependencies between tasks
- **Simple aggregation**: Results combined via concatenation or basic structure
- **Minimal overhead**: ~5% overhead vs direct execution
- **No AI planning**: Tasks executed directly without decomposition analysis

**Example Use Cases**:
- "Analyze security vulnerabilities in auth.py, database.py, api.py, utils.py, models.py"
- "Summarize chapters 1-8 of this book"
- "Extract key insights from these 6 interview transcripts"
- "Review code quality in utils.py, models.py, views.py, controllers.py"

**When NOT to Use**:
- Unclear task boundaries (need AI decomposition → Pattern 1)
- Complex dependencies (need sequential planning → Pattern 2)
- Intelligent synthesis required (need consensus/evidence building → Patterns 3-4)
- High-stakes decisions (need meta-cognitive quality review → Full Orchestrator)

**Performance Comparison**:
```
Direct execution:    245s (1 task at a time, sequential)
Pattern 0 (Simple):  282s (5 parallel workers) ← 5% overhead, 100% success
Pattern 1 (Full):    FAILED or 600s+ (145% overhead, Phase 0 stuck)
```

**Optimal Worker Count**: min(task_count, 7)

**Migration Path**:
- If synthesis complexity increases → Upgrade to Pattern 1 (Full Orchestrator with Phases 3-6)
- If task boundaries unclear → Upgrade to Pattern 1 (Full Orchestrator with Phases 0-1)
- If quality issues arise → Upgrade to Full Orchestrator (Phases 0-8)

**Implementation**: See [references/simple-parallel-guide.md](../references/simple-parallel-guide.md) for complete guide

**Command Examples**:
```bash
# Security analysis across 5 files
python scripts/simple_parallel.py \
  --tasks "Analyze auth.py, Analyze database.py, Analyze api.py, Analyze utils.py, Analyze models.py" \
  --worker-type gemini \
  --complexity medium \
  --output security_report/

# Document summarization
python scripts/simple_parallel.py \
  --task-file chapters.txt \
  --worker-type gemini \
  --complexity low \
  --output summaries/
```

---

## Pattern 1: Parallel Independent Analysis

**When to Use**: Analyzing multiple independent sources or components

**Structure**:
```
Task: Analyze 5 research papers
Decomposition:
  - Subtask 1: Analyze paper 1
  - Subtask 2: Analyze paper 2
  - Subtask 3: Analyze paper 3
  - Subtask 4: Analyze paper 4
  - Subtask 5: Analyze paper 5
Dependencies: None (fully parallel)
```

**Characteristics**:
- No dependencies between subtasks
- Each subtask processes different data
- Results aggregated at synthesis stage
- High parallelization potential

**Example Use Cases**:
- Book comparison across multiple sources
- Code review across different modules
- Customer feedback analysis by channel
- Multi-document summarization

**Optimal Worker Count**: min(5, task_count)

---

## Pattern 2: Sequential Pipeline

**When to Use**: Tasks where each step depends on previous output

**Structure**:
```
Task: Research → Analyze → Synthesize findings
Decomposition:
  - Subtask 1: Gather relevant data
  - Subtask 2: Analyze gathered data (depends on Subtask 1)
  - Subtask 3: Synthesize analysis (depends on Subtask 2)
Dependencies: Linear chain
```

**Characteristics**:
- Strong dependencies (each task needs previous output)
- Must execute sequentially
- No parallelization opportunity
- Worker count: 1 (sequential execution)

**Example Use Cases**:
- Multi-stage research workflows
- Data transformation pipelines
- Progressive refinement tasks
- Iterative improvement processes

**Optimal Worker Count**: 1 worker executing tasks sequentially (no parallelization)

---

## Pattern 3: Map-Reduce

**When to Use**: Process multiple items independently, then aggregate

**Structure**:
```
Task: Analyze 10 customer reviews and identify themes
Decomposition:
  Map Phase (Parallel):
    - Subtask 1-10: Analyze each review independently
  Reduce Phase (Sequential):
    - Subtask 11: Aggregate findings and identify common themes
Dependencies: Subtask 11 depends on all map tasks
```

**Characteristics**:
- Initial parallel phase (map)
- Final aggregation phase (reduce)
- Partial dependencies
- High parallelization in map phase

**Example Use Cases**:
- Sentiment analysis across multiple reviews
- Pattern detection in distributed data
- Multi-source data aggregation
- Consensus building from multiple analyses

**Optimal Worker Count**: min(5, map_task_count)

---

## Pattern 4: Dimensional Analysis

**When to Use**: Analyze same content from multiple perspectives

**Structure**:
```
Task: Evaluate research proposal
Decomposition:
  - Subtask 1: Evaluate methodology quality
  - Subtask 2: Evaluate novelty and impact
  - Subtask 3: Evaluate feasibility and resources
  - Subtask 4: Evaluate alignment with goals
Dependencies: None (parallel, same input)
```

**Characteristics**:
- Multiple workers on same content
- Different evaluation criteria per worker
- Synthesis requires consensus building
- Results may conflict (need resolution)

**Example Use Cases**:
- Multi-criteria evaluation
- Peer review simulation
- Risk assessment from multiple angles
- Quality assurance with different standards

**Optimal Worker Count**: Number of dimensions (typically 3-5)

---

## Pattern 5: Hybrid (Parallel + Sequential)

**When to Use**: Mixed dependencies with some parallel opportunity

**Structure**:
```
Task: Literature review with meta-analysis
Decomposition:
  Parallel Group 1:
    - Subtask 1: Review papers in domain A
    - Subtask 2: Review papers in domain B
    - Subtask 3: Review papers in domain C
  Sequential:
    - Subtask 4: Cross-domain synthesis (depends on 1-3)
    - Subtask 5: Meta-analysis (depends on 4)
Dependencies: Subtask 4 → [1,2,3], Subtask 5 → [4]
```

**Characteristics**:
- Mix of parallel and sequential tasks
- Partial dependencies
- Moderate parallelization
- Requires careful scheduling

**Example Use Cases**:
- Research synthesis with cross-cutting analysis
- Multi-stage processing with parallel components
- Hierarchical analysis (bottom-up aggregation)

**Optimal Worker Count**: min(5, parallel_task_count)

---

## Pattern 6: Comparison Matrix

**When to Use**: Pairwise comparisons or cross-product analysis

**Structure**:
```
Task: Compare 3 approaches across 4 criteria
Decomposition:
  - Subtask 1: Compare Approach A vs criteria 1-4
  - Subtask 2: Compare Approach B vs criteria 1-4
  - Subtask 3: Compare Approach C vs criteria 1-4
  - Subtask 4: Cross-comparison synthesis
Dependencies: Subtask 4 depends on 1-3
```

**Characteristics**:
- Grid-based analysis
- Partial parallelization (rows or columns)
- Final synthesis combines perspectives
- Clear comparison structure

**Example Use Cases**:
- Technology stack comparison
- Vendor evaluation
- Algorithm benchmarking
- Feature comparison matrices

**Optimal Worker Count**: min(5, row_or_column_count)

---

## Anti-Patterns (Avoid These)

### Anti-Pattern 1: Over-Decomposition
**Problem**: Breaking tasks too granularly
```
BAD:
  - Subtask 1: Read introduction of paper 1
  - Subtask 2: Read methods of paper 1
  - Subtask 3: Read results of paper 1
  ...
```
**Why Bad**: Overhead exceeds benefit, context fragmentation
**Solution**: Keep subtasks substantial (each should produce meaningful output)

### Anti-Pattern 2: Hidden Dependencies
**Problem**: Tasks appear parallel but have implicit dependencies
```
BAD:
  - Subtask 1: Analyze code quality
  - Subtask 2: Suggest refactoring (needs quality analysis)
  Dependencies: None (WRONG!)
```
**Why Bad**: Execution order failures, missing context
**Solution**: Explicitly declare all dependencies

### Anti-Pattern 3: Redundant Overlap
**Problem**: Multiple subtasks doing the same work
```
BAD:
  - Subtask 1: Analyze sentiment in reviews 1-10
  - Subtask 2: Identify themes in reviews 1-10
  - Subtask 3: Extract keywords in reviews 1-10
```
**Why Bad**: Same input processed multiple times wastefully
**Solution**: Combine related analysis into single subtask or use dimensional pattern

### Anti-Pattern 4: Vague Task Boundaries
**Problem**: Unclear what each subtask should produce
```
BAD:
  - Subtask 1: Look at the data
  - Subtask 2: Find interesting stuff
  - Subtask 3: Write something useful
```
**Why Bad**: Ambiguity leads to inconsistent outputs
**Solution**: Specify clear output format and success criteria for each subtask

---

## Selection Guide

| User Request Characteristics | Recommended Pattern |
|------------------------------|---------------------|
| Multiple independent sources | Parallel Independent |
| Sequential processing needed | Sequential Pipeline |
| Same analysis on many items | Map-Reduce |
| Multi-criteria evaluation | Dimensional Analysis |
| Mixed dependencies | Hybrid |
| Cross-product comparisons | Comparison Matrix |

---

## Best Practices

1. **Aim for 3-10 Subtasks**: Fewer than 3 = minimal orchestration benefit; more than 10 = complexity overhead

2. **Balance Granularity**: Each subtask should be substantial enough to justify worker overhead (typically 200+ words output)

3. **Minimize Dependencies**: Prefer parallel execution when possible (better resource utilization)

4. **Clear Boundaries**: Each subtask should have clear input, output, and success criteria

5. **Consistent Output Format**: All subtasks in a group should produce compatible output structures

6. **Name Tasks Descriptively**: Use action verbs and specific objects (e.g., "Analyze security vulnerabilities in auth.py" not "Check code")

7. **Avoid Circular Dependencies**: Dependency graph must be acyclic (DAG)

8. **Consider Worker Load**: Distribute work evenly across workers (avoid 1 task = 80% of work)

---

## Complexity Assessment

**Low Complexity Tasks**:
- Simple data extraction
- Straightforward summarization
- Basic classification
- Template-based analysis

**Medium Complexity Tasks**:
- Multi-criteria evaluation
- Comparative analysis
- Synthesis requiring judgment
- Pattern identification

**High Complexity Tasks**:
- Novel insight generation
- Complex reasoning chains
- Cross-domain synthesis
- Nuanced judgment calls

**Rule of Thumb**: High complexity tasks → fewer workers (3 max), Low complexity → more workers (5-7)

---

This guide helps ensure effective task decomposition that maximizes parallel execution while maintaining clear task boundaries and manageable dependencies.
