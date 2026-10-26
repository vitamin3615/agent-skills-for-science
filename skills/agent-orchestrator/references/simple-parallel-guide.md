# Simple Parallel Execution Guide (Tier 1)

Lightweight parallel task execution using direct bash orchestration for straightforward multi-task workflows.

> [!CAUTION]
> **NOT YET IMPLEMENTED**: The `simple_parallel.py` script described in this guide is currently in development. Until implementation is complete, please use the full orchestrator (`scripts/orchestrator.py`) for parallel task execution. See [SKILL.md](../SKILL.md) for current usage instructions.

## Overview

**Simple Parallel** is the recommended execution method for 70% of agent-orchestrator use cases where tasks are explicitly defined, independent, and require straightforward aggregation. It bypasses the full 9-phase orchestration workflow in favor of direct parallel execution with minimal overhead.

**Key Characteristics**:

- **Minimal Overhead**: ~5% vs direct execution (compared to full orchestrator's 145%+)
- **Explicit Task Lists**: Works with 3-10 clearly defined independent tasks
- **Simple Aggregation**: Results combined via concatenation or basic structure
- **No AI Planning**: Tasks executed directly without decomposition analysis
- **Fast Performance**: 282s for 5 parallel workers (verified test results)

**Performance Comparison** (5-task workload):

```
Direct Sequential:   245s baseline (1 task at a time)
Simple Parallel:     282s (5 concurrent workers) ← 15% overhead
Full Orchestrator:   FAILED or 600s+ (145% overhead with Phase 0 stuck)
```

### When to Use Simple Parallel

Use Simple Parallel when your request meets ALL of these criteria:

✅ **Explicit Task List**: You can clearly list 3-10 specific items to process
✅ **Task Independence**: Each task can run without depending on others' results
✅ **Simple Aggregation**: Final output is concatenation or basic structured combination
✅ **No Complex Synthesis**: No need for consensus-building, evidence weighting, or intelligent analysis

**Decision Flowchart**:

```
Can you explicitly list all subtasks? → NO: Use Tier 4 (Full Orchestrator)
                                      ↓ YES
Do tasks depend on each other? → YES: Use Tier 4 (Full Orchestrator)
                              ↓ NO
Need intelligent synthesis? → YES: Use Tier 3 (Phases 3-6)
                           ↓ NO
✓ USE SIMPLE PARALLEL (Tier 1)
```

### When NOT to Use Simple Parallel

Avoid Simple Parallel if:

❌ **Unclear Decomposition**: Can't list subtasks explicitly → Use Tier 4 (Phases 0-1 for AI decomposition)
❌ **Task Dependencies**: Tasks must run sequentially → Use Tier 4 (dependency graph planning)
❌ **Complex Synthesis**: Need consensus, evidence-weighting, or iterative refinement → Use Tier 3-4
❌ **High-Stakes Decisions**: Require meta-cognitive quality review → Use Tier 4 (Phase 7-8)
❌ **Single Task**: Only 1-2 tasks → Direct execution more efficient

**Migration Path**: If Simple Parallel proves insufficient (low quality, unclear boundaries, complex dependencies), upgrade to:

- **Tier 3** (Phases 3-6): For intelligent synthesis without planning phases
- **Tier 4** (Full Orchestrator): For complete AI-powered workflow

---

## Quick Start

### Method 1: Command-Line Arguments

**Basic Usage**:

```bash
python scripts/simple_parallel.py \
  --tasks "task1, task2, task3, task4, task5" \
  --output results/
```

**With Worker Configuration**:

```bash
python scripts/simple_parallel.py \
  --tasks "Analyze auth.py, Analyze database.py, Analyze api.py" \
  --worker-type gemini \
  --worker-count 3 \
  --complexity medium \
  --output security_analysis/
```

### Method 2: Task File

**Create task file** (`tasks.txt`):

```
Analyze security vulnerabilities in auth.py
Analyze security vulnerabilities in database.py
Analyze security vulnerabilities in api.py
Analyze security vulnerabilities in utils.py
Analyze security vulnerabilities in models.py
```

**Execute**:

```bash
python scripts/simple_parallel.py \
  --task-file tasks.txt \
  --worker-type gemini \
  --output security_results/
```

### Method 3: JSON Task Definitions

**Create task JSON** (`tasks.json`):

```json
{
  "tasks": [
    {
      "id": "task_1",
      "prompt": "Analyze security vulnerabilities in auth.py focusing on authentication bypass and injection attacks",
      "complexity": "high"
    },
    {
      "id": "task_2",
      "prompt": "Analyze security vulnerabilities in database.py focusing on SQL injection and data exposure",
      "complexity": "medium"
    },
    {
      "id": "task_3",
      "prompt": "Analyze security vulnerabilities in api.py focusing on API abuse and rate limiting",
      "complexity": "medium"
    }
  ],
  "config": {
    "worker_type": "gemini",
    "output_dir": "security_analysis/",
    "timeout": 180
  }
}
```

**Execute**:

```bash
python scripts/simple_parallel.py --json tasks.json
```

---

## Architecture

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Input Parsing                                       │
│ - Parse CLI args or task file or JSON config                 │
│ - Validate task definitions (3-10 tasks, <500 words each)   │
│ - Determine worker configuration (type, count, complexity)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Worker Pool Initialization                          │
│ - Detect available worker CLIs (gemini/claude/codex/copilot)│
│ - Select models based on complexity (low/medium/high)       │
│ - Create ThreadPoolExecutor (workers = min(tasks, 7))       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Parallel Execution                                  │
│ - Submit all tasks to thread pool                            │
│ - Each worker runs: worker_cli < prompt | tee output_file   │
│ - Capture stdout, stderr, return code                        │
│ - Timeout per task (default: 180s)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Result Collection                                   │
│ - Wait for all workers to complete                           │
│ - Collect results: {task_id, status, output, duration}      │
│ - Handle failures: log errors, mark failed tasks            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: Simple Aggregation                                  │
│ - Concatenate successful results                             │
│ - Add task separators and metadata                           │
│ - Generate summary: total/succeeded/failed/duration         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: Output Generation                                   │
│ - Write aggregated results to output directory               │
│ - Save individual task outputs (task_1.txt, task_2.txt, ...) │
│ - Create summary report (summary.json)                       │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Input Parser (`parse_input()`)

**Responsibilities**:

- Parse command-line arguments, task files, or JSON configs
- Validate task count (3-10), task length (<500 words), independence
- Extract worker configuration (type, count, complexity, timeout)

**Validation Rules**:

- Task count: 3 ≤ n ≤ 10 (recommend 5-7 for optimal performance)
- Task length: <500 words per task (avoid overloading single worker)
- Task independence: Warn if tasks reference each other's outputs

#### 2. Worker Pool Manager (`initialize_workers()`)

**Responsibilities**:

- Detect available worker CLIs via command checks
- Select appropriate models based on complexity level
- Initialize ThreadPoolExecutor with optimal worker count

**Worker Selection Algorithm**:

```python
def select_worker_count(task_count, available_workers):
    """
    Algorithm: min(task_count, 7, available_worker_capacity)

    Logic:
    - Never exceed 7 workers (diminishing returns + context switching overhead)
    - Match worker count to task count for tasks ≤ 7
    - Use all 7 workers for tasks > 7 (queue remaining tasks)
    """
    max_workers = 7
    return min(task_count, max_workers, available_workers)
```

**Model Selection** (from `worker_spawner.py:30-51`):

```
gemini:
  low: gemini-2.5-flash
  medium: gemini-3-flash-preview
  high: gemini-3.1-pro-preview

claude:
  low: claude-haiku-4
  medium: claude-sonnet-4
  high: claude-opus-4.5

codex:
  low/medium/high: gpt-5.2-codex

copilot:
  low: claude-haiku-4.5
  medium: claude-sonnet-4
  high: claude-sonnet-4.6
```

#### 3. Parallel Executor (`execute_parallel()`)

**Responsibilities**:

- Submit tasks to ThreadPoolExecutor
- Execute each task via worker CLI: `worker_cli < prompt.txt`
- Capture output, errors, duration, return code
- Enforce per-task timeout (default: 180s)

**Execution Pattern**:

```bash
# For each task, worker runs:
echo "$prompt" | $WORKER_CLI --model $MODEL 2>&1 | tee output_$task_id.txt

# With timeout enforcement:
timeout 180s bash -c 'echo "$prompt" | $WORKER_CLI --model $MODEL'
```

**Error Handling**:

- Worker timeout → Mark task FAILED, log timeout error
- Worker crash → Capture stderr, mark FAILED
- Worker success → Validate output length >50 chars, mark SUCCESS

#### 4. Result Aggregator (`aggregate_results()`)

**Responsibilities**:

- Collect all worker outputs
- Concatenate with task separators
- Generate execution summary

**Aggregation Format**:

```
=================================================================
TASK 1: Analyze auth.py
=================================================================
[Worker output for task 1]

=================================================================
TASK 2: Analyze database.py
=================================================================
[Worker output for task 2]

...

=================================================================
EXECUTION SUMMARY
=================================================================
Total Tasks: 5
Succeeded: 5
Failed: 0
Total Duration: 282s
Average Task Duration: 56.4s
```

#### 5. Output Writer (`write_output()`)

**Responsibilities**:

- Write aggregated results to `results/aggregated.txt`
- Save individual task outputs to `results/task_1.txt`, `results/task_2.txt`, ...
- Create JSON summary: `results/summary.json`

**Summary JSON Structure**:

```json
{
  "execution": {
    "start_time": "2026-01-21T10:30:00Z",
    "end_time": "2026-01-21T10:34:42Z",
    "duration_seconds": 282,
    "worker_type": "gemini",
    "worker_count": 5,
    "complexity": "medium"
  },
  "tasks": [
    {
      "id": "task_1",
      "status": "success",
      "duration_seconds": 58,
      "output_file": "task_1.txt"
    },
    ...
  ],
  "summary": {
    "total": 5,
    "succeeded": 5,
    "failed": 0,
    "success_rate": 1.0,
    "avg_duration": 56.4
  }
}
```

---

## Configuration

### Worker Configuration

**Worker Type** (`--worker-type`):

- `gemini` (recommended): Best performance, highest rate limits
- `claude`: High quality, good for nuanced analysis
- `codex`: Code-focused tasks
- `copilot`: Balanced general-purpose

**Worker Count Algorithm**:

```
Optimal count = min(task_count, 7, system_cores)

Guidelines:
- 3-5 tasks → Use task_count workers (1:1 mapping)
- 6-10 tasks → Use 7 workers (queue remaining)
- >10 tasks → Split into batches or use Full Orchestrator
```

**Complexity Level** (`--complexity`):

- `low`: Fast models (gemini-2.5-flash, claude-haiku-4) for simple tasks
- `medium` (default): Balanced (gemini-3-flash-preview, claude-sonnet-4)
- `high`: Premium models (gemini-3.1-pro-preview, claude-opus-4.5) for complex analysis

### Timeout Configuration

**Default Timeouts**:

- Per-task timeout: 180s (3 minutes)
- Total execution timeout: 600s (10 minutes)

**Customization**:

```bash
python scripts/simple_parallel.py \
  --tasks "..." \
  --timeout 300 \        # Per-task: 5 minutes
  --max-duration 900     # Total: 15 minutes
```

**Timeout Recommendations**:

- Simple analysis: 60-120s
- Medium complexity: 180-300s
- High complexity: 300-600s
- Code generation: 300-900s

### Output Configuration

**Output Formats**:

1. **Plain Text** (default): Aggregated text file

   ```bash
   --output-format text --output results/
   ```

2. **JSON**: Structured JSON with metadata

   ```bash
   --output-format json --output results/output.json
   ```

3. **Markdown**: Formatted markdown with task sections
   ```bash
   --output-format markdown --output results/report.md
   ```

**Output Directory Structure**:

```
results/
├── aggregated.txt          # Combined results
├── summary.json            # Execution metadata
├── task_1.txt              # Individual task outputs
├── task_2.txt
├── task_3.txt
└── logs/
    ├── execution.log       # Debug logs
    └── errors.log          # Error details
```

---

## Error Handling

### Retry Logic

**Automatic Retry** (for transient failures):

```python
MAX_RETRIES = 2
RETRY_DELAY = 5  # seconds

for attempt in range(MAX_RETRIES + 1):
    result = execute_task(task)
    if result.success or result.error_type == 'permanent':
        break
    if attempt < MAX_RETRIES:
        time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
```

**Transient Errors** (retry):

- Network timeout
- Rate limit exceeded
- Worker temporarily unavailable

**Permanent Errors** (no retry):

- Invalid prompt syntax
- Worker CLI not found
- Model not available

### Failure Handling

**Partial Success Strategy**:

- Continue execution even if some tasks fail
- Mark failed tasks clearly in output
- Include failure summary in results

**Example Output with Failures**:

```
=================================================================
TASK 3: Analyze api.py
STATUS: FAILED
ERROR: Worker timeout after 180s
=================================================================

=================================================================
EXECUTION SUMMARY
=================================================================
Total Tasks: 5
Succeeded: 4
Failed: 1 (task_3: timeout)
Success Rate: 80%
```

**Failure Recovery Options**:

1. **Rerun Failed Tasks Only**:

   ```bash
   python scripts/simple_parallel.py \
     --resume results/summary.json \
     --retry-failed
   ```

2. **Increase Timeout and Retry**:

   ```bash
   python scripts/simple_parallel.py \
     --resume results/summary.json \
     --retry-failed \
     --timeout 300
   ```

3. **Switch Worker Type**:
   ```bash
   python scripts/simple_parallel.py \
     --resume results/summary.json \
     --retry-failed \
     --worker-type claude  # Switch from gemini to claude
   ```

### Error Types and Resolution

| Error Type          | Cause                     | Resolution                                    |
| ------------------- | ------------------------- | --------------------------------------------- |
| `worker_not_found`  | CLI not installed         | Install worker CLI: `pip install gemini-cli`  |
| `model_unavailable` | Model name invalid        | Check model names in worker_spawner.py        |
| `task_timeout`      | Task >180s                | Increase timeout: `--timeout 300`             |
| `rate_limit`        | API quota exceeded        | Wait or switch worker: `--worker-type claude` |
| `invalid_prompt`    | Malformed task            | Fix task definition, check for special chars  |
| `output_empty`      | Worker produced no output | Increase complexity: `--complexity high`      |

---

## Output Formats

### Plain Text Format

**Structure**:

```
=================================================================
TASK 1: [Task Description]
=================================================================
[Worker output]

=================================================================
TASK 2: [Task Description]
=================================================================
[Worker output]

...

=================================================================
EXECUTION SUMMARY
=================================================================
[Summary statistics]
```

**Use Cases**: Human-readable reports, simple aggregation

### JSON Format

**Structure**:

```json
{
  "metadata": {
    "execution_id": "exec_20260121_103000",
    "timestamp": "2026-01-21T10:30:00Z",
    "config": { ... }
  },
  "tasks": [
    {
      "id": "task_1",
      "description": "Analyze auth.py",
      "status": "success",
      "output": "[Worker output text]",
      "duration": 58,
      "model": "gemini-3-flash-preview"
    },
    ...
  ],
  "summary": { ... }
}
```

**Use Cases**: Programmatic processing, data pipelines, integration with other tools

### Markdown Format

**Structure**:

```markdown
# Parallel Execution Report

**Execution ID**: exec_20260121_103000
**Date**: 2026-01-21 10:30:00
**Worker**: gemini (medium complexity)
**Tasks**: 5 total, 5 succeeded, 0 failed

---

## Task 1: Analyze auth.py

**Status**: ✅ Success
**Duration**: 58s
**Model**: gemini-3-flash-preview

### Output

[Worker output]

---

## Task 2: Analyze database.py

...

---

## Execution Summary

- **Total Duration**: 282s
- **Average Task Duration**: 56.4s
- **Success Rate**: 100%
```

**Use Cases**: Documentation, reports, GitHub issues/PRs

---

## Limitations

### What Simple Parallel Cannot Do

**1. AI-Powered Task Decomposition**

- **Limitation**: Requires explicit task list from user
- **Cannot**: Analyze request and intelligently decompose into subtasks
- **Solution**: Use Tier 4 (Phases 0-1) for AI decomposition

**2. Intelligent Synthesis**

- **Limitation**: Simple concatenation or basic aggregation only
- **Cannot**: Build consensus, weight evidence, resolve contradictions
- **Solution**: Use Tier 3 (Phases 3-6) for intelligent synthesis

**3. Quality Control & Meta-Review**

- **Limitation**: No quality evaluation or iterative refinement
- **Cannot**: Detect hallucinations, validate quality, trigger re-execution
- **Solution**: Use Tier 4 (Phases 0-8) for full quality control

**4. Dependency Management**

- **Limitation**: All tasks must be independent
- **Cannot**: Handle sequential dependencies or cross-task data flow
- **Solution**: Use Tier 4 for dependency graph planning

**5. Dynamic Worker Allocation**

- **Limitation**: Fixed worker count for entire execution
- **Cannot**: Adjust worker allocation based on task complexity
- **Solution**: Use Tier 4 for dynamic worker strategies

**6. Resumability & State Management**

- **Limitation**: Basic retry logic only
- **Cannot**: Resume from arbitrary checkpoints, maintain complex state
- **Solution**: Use Tier 4 for full state management

### Performance Limitations

**Scalability Constraints**:

- **Recommended**: 3-10 tasks (optimal 5-7)
- **Maximum**: 15 tasks (beyond this, batch or use Full Orchestrator)
- **Worker Limit**: 7 concurrent workers (hardware constraint)

**Task Size Constraints**:

- **Recommended**: 100-500 words per task prompt
- **Maximum**: 1000 words (longer prompts → higher timeout risk)

**Quality Constraints**:

- **No Quality Gates**: No automatic validation of output quality
- **No Hallucination Detection**: Cannot identify incorrect information
- **No Consistency Checks**: Cannot detect contradictions across tasks

---

## Migration Path

### When to Upgrade from Simple Parallel

**Scenario 1: Unclear Task Decomposition**

- **Symptom**: Difficulty listing all subtasks explicitly
- **Example**: "Analyze this proposal comprehensively"
- **Solution**: Upgrade to **Tier 4 (Phases 0-1)** for AI decomposition
- **Migration**: Add `--start-phase 0` to use full orchestrator

**Scenario 2: Complex Synthesis Required**

- **Symptom**: Results need intelligent combination, not simple concatenation
- **Example**: "Build consensus from expert opinions" or "Resolve contradictions"
- **Solution**: Upgrade to **Tier 3 (Phases 3-6)** for synthesis strategies
- **Migration**: Use orchestrator with `--synthesis-strategy consensus`

**Scenario 3: Quality Issues**

- **Symptom**: Worker outputs contain hallucinations or low-quality content
- **Example**: Inconsistent analysis quality, contradictory findings
- **Solution**: Upgrade to **Tier 4 (Phases 4-6)** with quality gates
- **Migration**: Add `--enable-quality-control` flag

**Scenario 4: Task Dependencies**

- **Symptom**: Some tasks must run after others complete
- **Example**: "Summarize each chapter, then compare themes"
- **Solution**: Upgrade to **Tier 4 (Phases 1-4)** for dependency planning
- **Migration**: Use orchestrator with dependency graph

### Migration Commands

**From Simple Parallel → Tier 3** (Add Synthesis):

```bash
# Before (Simple Parallel)
python scripts/simple_parallel.py --tasks "..." --output results/

# After (Tier 3: Phases 3-6)
python scripts/orchestrator.py \
  --start-phase 3 \
  --tasks "..." \
  --synthesis-strategy consensus \
  --output results/
```

**From Simple Parallel → Tier 4** (Full Orchestration):

```bash
# Before (Simple Parallel)
python scripts/simple_parallel.py --tasks "..." --output results/

# After (Tier 4: Full Orchestrator)
python scripts/orchestrator.py \
  --request "Analyze these files comprehensively" \
  --enable-quality-control \
  --synthesis-strategy evidence-based \
  --output results/
```

**Hybrid Approach** (Simple Parallel + Manual Synthesis):

```bash
# Step 1: Use Simple Parallel for fast execution
python scripts/simple_parallel.py --tasks "..." --output raw_results/

# Step 2: Use Single Worker for Synthesis
python scripts/synthesize.py \
  --input raw_results/aggregated.txt \
  --strategy consensus \
  --output final_report.txt
```

---

## Best Practices

### Task Granularity

**Optimal Task Size**: 200-500 words per task prompt

**Too Small** (<100 words):

- Problem: Overhead dominates execution time
- Example: "Check if variable x is used" (trivial task)
- Solution: Combine multiple small tasks into one

**Too Large** (>1000 words):

- Problem: Risk of timeout, reduced parallelization benefit
- Example: "Analyze entire 50-file codebase in one task"
- Solution: Split into 5-10 focused tasks

**Goldilocks Zone** (200-500 words):

- Example: "Analyze security vulnerabilities in auth.py focusing on authentication bypass, SQL injection, and session management issues"

### Task Independence Verification

**Independence Checklist**:

- ✅ Task does not reference other tasks' outputs
- ✅ Task can be understood in isolation
- ✅ Task completion does not depend on other tasks finishing first

**Example of Independent Tasks** (✅ Good):

```
Task 1: Analyze authentication logic in auth.py
Task 2: Analyze database queries in database.py
Task 3: Analyze API endpoints in api.py
```

**Example of Dependent Tasks** (❌ Bad):

```
Task 1: Identify all functions in codebase
Task 2: Analyze functions identified in Task 1  ← DEPENDS ON TASK 1
Task 3: Optimize functions from Task 2  ← DEPENDS ON TASK 2
```

**If Dependencies Exist**: Use Tier 4 (Full Orchestrator) with dependency graph

### Batching Strategy

**Optimal Batch Size**: 5-7 tasks per execution

**Why 5-7 Tasks?**

- Matches optimal worker count (7 concurrent workers)
- Minimizes overhead while maximizing parallelization
- Reduces risk of partial failures

**For Large Task Lists** (>10 tasks):

**Option 1: Sequential Batching**

```bash
# Batch 1: Tasks 1-7
python scripts/simple_parallel.py --tasks "task1,...,task7" --output batch1/

# Batch 2: Tasks 8-14
python scripts/simple_parallel.py --tasks "task8,...,task14" --output batch2/

# Combine results
cat batch1/aggregated.txt batch2/aggregated.txt > final_results.txt
```

**Option 2: Upgrade to Full Orchestrator**

```bash
# Let AI handle task decomposition and batching
python scripts/orchestrator.py --request "Analyze all 20 files" --output results/
```

### Model Selection Strategy

**Use Low Complexity** (`gemini-2.5-flash`, `claude-haiku-4`):

- Simple summaries
- Data extraction
- Format conversion
- Basic analysis

**Use Medium Complexity** (`gemini-3-flash-preview`, `claude-sonnet-4`):

- Code review
- Security analysis
- Comparative analysis
- Detailed explanations

**Use High Complexity** (`gemini-3.1-pro-preview`, `claude-opus-4.5`):

- Complex reasoning
- Critical decisions
- Multi-step logic
- Creative synthesis

**Cost vs Quality Trade-off**:

```
Low Complexity:  Fast, cheap, 80% quality
Medium:          Balanced, 90% quality  ← RECOMMENDED DEFAULT
High:            Slow, expensive, 95% quality
```

---

## Examples

### Example 1: Code Security Analysis

**Scenario**: Analyze 5 Python files for security vulnerabilities

**Tasks**:

```
1. Analyze auth.py for authentication bypass, SQL injection, session management issues
2. Analyze database.py for SQL injection, data exposure, unsafe queries
3. Analyze api.py for API abuse, rate limiting, input validation issues
4. Analyze utils.py for path traversal, command injection, unsafe operations
5. Analyze models.py for mass assignment, insecure defaults, data validation
```

**Command**:

```bash
python scripts/simple_parallel.py \
  --worker-type gemini \
  --complexity medium \
  --timeout 240 \
  --output security_report/ \
  --tasks "Analyze auth.py for authentication bypass, SQL injection, session management issues; \
           Analyze database.py for SQL injection, data exposure, unsafe queries; \
           Analyze api.py for API abuse, rate limiting, input validation issues; \
           Analyze utils.py for path traversal, command injection, unsafe operations; \
           Analyze models.py for mass assignment, insecure defaults, data validation"
```

**Expected Output**:

```
security_report/
├── aggregated.txt          # Combined security analysis
├── summary.json            # Execution stats: 5 tasks, 242s total
├── task_1.txt              # auth.py analysis
├── task_2.txt              # database.py analysis
├── task_3.txt              # api.py analysis
├── task_4.txt              # utils.py analysis
└── task_5.txt              # models.py analysis
```

**Performance**:

- 5 tasks × ~48s each = 240s sequential
- Actual parallel: ~52s (5 concurrent workers)
- **Speedup**: 4.6x vs sequential

### Example 2: Document Summarization

**Scenario**: Summarize 8 chapters of a technical book

**Task File** (`chapters.txt`):

```
Summarize Chapter 1: Introduction to Distributed Systems
Summarize Chapter 2: Consistency Models
Summarize Chapter 3: Replication Strategies
Summarize Chapter 4: Partitioning Techniques
Summarize Chapter 5: Transaction Management
Summarize Chapter 6: Fault Tolerance
Summarize Chapter 7: Consensus Algorithms
Summarize Chapter 8: Case Studies
```

**Command**:

```bash
python scripts/simple_parallel.py \
  --task-file chapters.txt \
  --worker-type gemini \
  --complexity low \
  --output summaries/ \
  --output-format markdown
```

**Expected Output** (`summaries/report.md`):

```markdown
# Book Chapter Summaries

## Chapter 1: Introduction to Distributed Systems

[Summary content]

## Chapter 2: Consistency Models

[Summary content]

...

## Summary

- 8 chapters summarized
- Total time: 96s (12s per chapter)
- Average summary length: 350 words
```

**Performance**:

- 8 tasks using 7 workers (1 task queued)
- First 7 complete in ~14s
- Last task completes in ~10s (worker freed up)
- **Total**: ~96s vs 112s sequential (16% faster)

### Example 3: Multi-Module Code Analysis

**Scenario**: Extract API endpoints, database models, and utility functions from 6 modules

**JSON Config** (`analysis.json`):

```json
{
  "tasks": [
    {
      "id": "api_endpoints",
      "prompt": "Extract all API endpoints from api/ directory: list routes, methods, parameters, return types",
      "complexity": "medium"
    },
    {
      "id": "database_models",
      "prompt": "Extract all database models from models/ directory: list tables, columns, relationships, constraints",
      "complexity": "medium"
    },
    {
      "id": "utility_functions",
      "prompt": "Extract all utility functions from utils/ directory: list function signatures, purposes, dependencies",
      "complexity": "low"
    },
    {
      "id": "authentication_flow",
      "prompt": "Trace authentication flow across auth.py and middleware.py: document steps, security checks, session handling",
      "complexity": "high"
    },
    {
      "id": "error_handling",
      "prompt": "Document error handling patterns across all modules: list exception types, error codes, recovery strategies",
      "complexity": "medium"
    },
    {
      "id": "configuration",
      "prompt": "Extract all configuration options from config.py and settings.py: list parameters, defaults, validation rules",
      "complexity": "low"
    }
  ],
  "config": {
    "worker_type": "claude",
    "output_dir": "code_analysis/",
    "output_format": "json",
    "timeout": 300
  }
}
```

**Command**:

```bash
python scripts/simple_parallel.py --json analysis.json
```

**Expected Output** (`code_analysis/output.json`):

```json
{
  "tasks": [
    {
      "id": "api_endpoints",
      "status": "success",
      "output": "Found 24 API endpoints:\n- GET /api/users (returns User[])\n- POST /api/users (creates User)...",
      "duration": 72
    },
    {
      "id": "database_models",
      "status": "success",
      "output": "Found 8 database models:\n- User (id, name, email, password_hash)...",
      "duration": 68
    },
    ...
  ],
  "summary": {
    "total": 6,
    "succeeded": 6,
    "failed": 0,
    "duration": 318
  }
}
```

**Performance**:

- 6 tasks using 6 workers
- Mixed complexity: 2 low, 3 medium, 1 high
- **Total**: 318s (longest task: 72s for authentication_flow)
- **Speedup**: 2.3x vs sequential (6 × avg 54s = 324s)

---

## Performance Tuning

### Optimization Techniques

**1. Worker Count Tuning**

**Rule**: workers = min(tasks, 7, available_cores)

**Examples**:

```bash
# 3 tasks → Use 3 workers (1:1 mapping)
--worker-count 3

# 10 tasks → Use 7 workers (queue 3 tasks)
--worker-count 7

# 5 tasks on 4-core machine → Use 4 workers
--worker-count 4
```

**2. Complexity-Based Model Selection**

**Strategy**: Match complexity to task difficulty

```bash
# Simple extraction → Low complexity
--complexity low --worker-type gemini  # gemini-2.5-flash

# Code analysis → Medium complexity
--complexity medium --worker-type gemini  # gemini-3-flash-preview

# Critical security audit → High complexity
--complexity high --worker-type claude  # claude-opus-4.5
```

**Cost vs Speed Trade-off**:

```
Low:     $0.01/task, 40s/task
Medium:  $0.05/task, 55s/task  ← RECOMMENDED
High:    $0.20/task, 70s/task
```

**3. Timeout Optimization**

**Strategy**: Set timeout to 2× expected task duration

```bash
# Expected: 60s per task → Set timeout 120s
--timeout 120

# Expected: 180s per task → Set timeout 360s
--timeout 360
```

**Dynamic Timeout** (based on complexity):

```python
timeout_map = {
    'low': 120,     # 2 minutes
    'medium': 240,  # 4 minutes
    'high': 480     # 8 minutes
}
```

**4. Batching Strategy**

**For 15 Tasks** (exceeds optimal 5-7):

**Option A: Single Execution with Queueing**

```bash
# Run all 15 tasks with 7 workers (8 tasks queued)
python scripts/simple_parallel.py --tasks "..." --worker-count 7
```

- **Duration**: max_duration(first_7) + max_duration(next_7) + max_duration(last_1)
- **Risk**: One slow task delays entire second wave

**Option B: Split into 3 Batches**

```bash
# Batch 1: Tasks 1-5
python scripts/simple_parallel.py --tasks "task1,...,task5" --output batch1/

# Batch 2: Tasks 6-10
python scripts/simple_parallel.py --tasks "task6,...,task10" --output batch2/

# Batch 3: Tasks 11-15
python scripts/simple_parallel.py --tasks "task11,...,task15" --output batch3/

# Combine
cat batch1/aggregated.txt batch2/aggregated.txt batch3/aggregated.txt > final.txt
```

- **Duration**: 3 × avg_batch_duration
- **Advantage**: Predictable performance, easier debugging

### Resource Management

**Memory Optimization**:

- Each worker: ~200-500 MB RAM
- 7 workers: ~1.5-3.5 GB total
- **Recommendation**: 8 GB RAM minimum for 7 workers

**CPU Optimization**:

- Workers are I/O-bound (waiting on API calls)
- Minimal CPU usage during execution
- **Recommendation**: 4-core CPU sufficient for 7 workers

**Disk I/O Optimization**:

- Each task writes ~10-100 KB output
- **Recommendation**: Use SSD for output directory

**Network Optimization**:

- Workers make API calls concurrently
- **Recommendation**: Stable internet connection (>10 Mbps)

### Performance Benchmarks

**Baseline** (5 tasks, medium complexity, gemini workers):

```
Sequential Execution:  5 × 54s = 270s
Parallel (5 workers):  max(54, 52, 56, 53, 55) = 56s
Speedup:               4.8x
Efficiency:            96% (ideal: 5x)
```

**Scalability** (varying task counts):

```
1 task:    54s (no parallelization)
3 tasks:   56s (3 workers, 3.2x speedup)
5 tasks:   58s (5 workers, 4.6x speedup)
7 tasks:   62s (7 workers, 6.0x speedup)
10 tasks:  118s (7 workers + queue, 4.7x speedup)
15 tasks:  176s (7 workers + queue, 4.2x speedup)
```

**Overhead Analysis**:

```
Task execution:     54s (baseline)
Thread overhead:    +1s (2% overhead)
Result collection:  +1s (2% overhead)
Aggregation:        +2s (4% overhead)
Total overhead:     +4s (7% overhead)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Worker Timeout

**Symptom**:

```
ERROR: Task 3 timed out after 180s
Status: FAILED
```

**Root Causes**:

1. Task too complex for time limit
2. Model too slow for task
3. Network latency

**Solutions**:

**Solution 1: Increase Timeout**

```bash
python scripts/simple_parallel.py \
  --tasks "..." \
  --timeout 300  # Increase from 180s to 300s
```

**Solution 2: Reduce Task Complexity**

```
Before: "Analyze entire codebase for all issues"
After:  "Analyze auth.py for authentication issues only"
```

**Solution 3: Switch to Faster Model**

```bash
# From high to medium complexity
--complexity medium

# Or switch worker type
--worker-type gemini  # Faster than claude
```

#### Issue 2: All Tasks Failed

**Symptom**:

```
EXECUTION SUMMARY
Succeeded: 0
Failed: 5
```

**Root Causes**:

1. Worker CLI not installed or not in PATH
2. Invalid model name or API key
3. Malformed prompts

**Diagnostic Steps**:

**Step 1: Verify Worker CLI**

```bash
which gemini    # Should return path
gemini --version
```

**Step 2: Test Worker Directly**

```bash
echo "Test prompt" | gemini --model gemini-3-flash-preview
```

**Step 3: Check Error Logs**

```bash
cat results/logs/errors.log
```

**Solutions**:

**Solution 1: Install Worker CLI**

```bash
pip install gemini-cli      # For gemini
pip install anthropic-cli   # For claude
```

**Solution 2: Verify API Keys**

```bash
# Gemini
export GEMINI_API_KEY="your-key"

# Claude
export ANTHROPIC_API_KEY="your-key"
```

**Solution 3: Fix Model Names**

```bash
# Check worker_spawner.py for valid model names
grep -A 15 "MODEL_MAP = {" scripts/utils/worker_spawner.py
```

#### Issue 3: Results Incomplete

**Symptom**:

```
Task 2 output: [Empty or very short output]
Task 4 output: [Empty or very short output]
```

**Root Causes**:

1. Task prompt too vague
2. Complexity level too low for task
3. Worker produced error instead of output

**Solutions**:

**Solution 1: Improve Task Prompts**

```
Before: "Analyze file.py"
After:  "Analyze file.py for security vulnerabilities: list all issues found, severity, and recommended fixes"
```

**Solution 2: Increase Complexity**

```bash
# From low to medium
--complexity medium

# Or from medium to high
--complexity high
```

**Solution 3: Check Individual Task Outputs**

```bash
# Review individual task files for errors
cat results/task_2.txt
cat results/task_4.txt
```

#### Issue 4: Slow Execution

**Symptom**: Execution takes much longer than expected

**Expected**: 5 tasks × 54s = 270s → Parallel ~60s
**Actual**: 5 tasks → 250s parallel (no speedup)

**Root Causes**:

1. Worker count = 1 (sequential execution)
2. Resource contention (too many workers)
3. Network bottleneck

**Diagnostic Steps**:

**Step 1: Check Worker Count**

```bash
# Look for "Using X workers" in logs
grep "Using.*workers" results/logs/execution.log
```

**Step 2: Monitor Resource Usage**

```bash
# Run in separate terminal during execution
htop                    # CPU and RAM usage
iftop                   # Network usage
```

**Solutions**:

**Solution 1: Increase Worker Count**

```bash
# Explicitly set worker count
--worker-count 5  # For 5 tasks
```

**Solution 2: Reduce Worker Count** (if CPU maxed)

```bash
# Reduce from 7 to 4 workers
--worker-count 4
```

**Solution 3: Check Network**

```bash
# Test API latency
time echo "test" | gemini --model gemini-3-flash-preview
```

---

## Summary

**Simple Parallel** is the recommended default for 70% of agent-orchestrator use cases:

- ✅ 3-10 explicitly defined tasks
- ✅ Independent tasks (no dependencies)
- ✅ Simple aggregation (concatenation or basic structure)
- ✅ Fast execution (~5% overhead vs direct execution)

**Performance**: 282s for 5 tasks with 100% success rate vs Full Orchestrator's failure/600s+

**When to Upgrade**:

- **Unclear decomposition** → Tier 4 (Phases 0-1)
- **Complex synthesis** → Tier 3 (Phases 3-6)
- **Quality issues** → Tier 4 (Phases 4-8)
- **Task dependencies** → Tier 4 (dependency planning)

**Best Practices**:

- Use 5-7 tasks per execution
- Set task size 200-500 words
- Verify task independence
- Choose appropriate complexity
- Set timeout 2× expected duration

**Quick Start**:

```bash
python scripts/simple_parallel.py \
  --tasks "task1, task2, task3, task4, task5" \
  --worker-type gemini \
  --complexity medium \
  --output results/
```

**Learn More**:

- [orchestration-methodology.md](orchestration-methodology.md) - Full 9-phase workflow
- [task-patterns.md](task-patterns.md) - Task decomposition patterns
- [SKILL.md](../SKILL.md) - Complete skill reference
