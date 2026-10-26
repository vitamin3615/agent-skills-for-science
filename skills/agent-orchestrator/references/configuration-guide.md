# Configuration Guide

Comprehensive configuration reference for the Agent Orchestrator.

## Output Configuration

### Default Output Location

All generated files are stored in `<project_root>/Temp/agent-orchestrator/`

The orchestrator automatically detects your project root and creates output directories there for cross-platform compatibility.

### Output Directory Structure

```
Temp/orchestrator_work/
├── .orchestrator_state.json          # State for resumability
├── request_analysis.json             # Phase 0 output
├── task_plan.json                    # Phase 1 output
├── worker_prompts.json               # Phase 3 output
├── worker_results/                   # Phase 4 outputs
│   ├── worker_1.txt
│   ├── worker_2.txt
│   └── ...
├── worker_results.json               # Aggregated results
├── evaluation_results.json           # Phase 5 output
├── synthesis_result.json             # Phase 6 output (JSON)
├── synthesis_result.md               # Phase 6 output (Markdown)
├── meta_review.json                  # Phase 7 output
└── final_report.md                   # Phase 8 output (FINAL)
```

### Custom Output Location

```bash
# Specify a custom output directory
python scripts/orchestrator.py --request "Your request" --output-dir /custom/path
```

---

## State Management

### State File Location

State is stored in `.orchestrator_state.json` within your output directory.

### State Management Commands

```bash
# Check current state
python scripts/state_manager.py --action status

# Clear state to start fresh
python scripts/state_manager.py --action clear

# Recover from backup
python scripts/state_manager.py --action recover

# With custom work directory
python scripts/state_manager.py --action status --work-dir Temp/orchestrator_work
```

### Programmatic State Access

```python
from state_manager import StateManager

# Manual state manipulation
manager = StateManager(work_dir="Temp/orchestrator_work")
manager.load_state()

# Check resumption info
info = manager.get_resumption_info()
print(f"Can resume: {info['can_resume']}")
print(f"Current phase: {info['current_phase']}")
print(f"Completed phases: {info['completed_phases']}")

# Clear state and start fresh
manager.clear_state()
```

### Resume from Interruption

```bash
# If interrupted during execution, resume from saved state
python orchestrator.py --resume ~/my_orchestration/.orchestrator_state.json
```

---

## Worker Models Configuration

### Default Model Assignment

Models are configured in `worker_spawner.py` based on task complexity:

| Complexity | Default Model          | Characteristics              |
| ---------- | ---------------------- | ---------------------------- |
| Low        | gemini-2.5-flash       | Fast, cost-effective         |
| Medium     | gemini-3-flash-preview | Balanced performance         |
| High       | gemini-3.1-pro-preview | Maximum reasoning capability |

### Supported Worker Models by Provider

| Provider             | Models                                                           |
| -------------------- | ---------------------------------------------------------------- |
| **Gemini** (primary) | gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-2.5-flash |
| **Claude**           | claude-sonnet-4.6, claude-haiku-4                                |
| **Codex**            | gpt-5.2-codex                                                    |
| **Copilot**          | claude-sonnet-4.6, claude-sonnet-4, claude-haiku-4.5             |

### Customizing Models

To customize model selection, edit the model selection logic in `worker_spawner.py`:

```python
# Example: Change high-complexity model
if complexity == "high":
    return "claude-sonnet-4.6"  # Instead of gemini-3.1-pro-preview
```

---

## Quality Gates Configuration

Quality gates are configured in `response_evaluator.py`:

| Gate       | Threshold | Action                          |
| ---------- | --------- | ------------------------------- |
| **Reject** | < 60      | Output rejected, triggers retry |
| **Flag**   | 60-80     | Output accepted with warnings   |
| **Accept** | > 80      | Output fully accepted           |

### Quality Control Layers

| Layer                            | Weight   | Purpose                                                         |
| -------------------------------- | -------- | --------------------------------------------------------------- |
| Layer 1: Structural              | 25%      | Format compliance (non-empty, reasonable length, has structure) |
| Layer 2: Completeness            | 45%      | Requirements addressed, expected format followed                |
| Layer 3: Hallucination Detection | 30%      | Vague claims, missing citations, contradictions                 |
| Layer 4: AI Evaluation           | Optional | Deep quality assessment for high-stakes tasks                   |

See [evaluation-rubrics.md](evaluation-rubrics.md) for complete scoring criteria.

---

## Parallelization Configuration

### Worker Count Limits

| Setting             | Value | Notes                        |
| ------------------- | ----- | ---------------------------- |
| Minimum workers     | 1     | Sequential execution         |
| Recommended maximum | 5     | Optimal for most tasks       |
| Absolute maximum    | 7     | To avoid resource contention |

### Dynamic Allocation Algorithm

Worker count is determined algorithmically based on task characteristics:

```python
def determine_worker_count(parallel_tasks, avg_complexity, has_dependencies):
    if has_dependencies:
        return 1  # Sequential execution

    if parallel_tasks <= 2:
        return min(2, parallel_tasks)
    elif parallel_tasks <= 5 and avg_complexity == "low":
        return min(5, parallel_tasks)
    elif avg_complexity == "high":
        return min(3, parallel_tasks)  # Heavy tasks need resources
    else:
        return min(5, parallel_tasks)
```

---

## Custom Worker Prompts

### Prompt Template Directory

Add custom templates to `worker_prompts/`:

```
worker_prompts/
├── comparison_worker.txt
├── analysis_worker.txt
├── synthesis_worker.txt
├── evaluation_worker.txt
└── meta_orchestrator.txt
```

### Hierarchical Prompt Structure

All worker prompts follow this structure for optimal quality:

```
1. SYSTEM CONTEXT (Role & Purpose)
2. TASK DEFINITION (Clear goal)
3. METHODOLOGY (How to approach)
4. DATA/CONTENT (What to analyze)
5. OUTPUT FORMAT (Exact structure)
6. QUALITY CRITERIA (Requirements)
7. CRITICAL CONSTRAINTS (Must-dos)
```

See [delegation-strategies.md](delegation-strategies.md) for prompt engineering best practices.

---

## Cost Considerations

### API Call Estimates

- Each worker makes 1-3 API calls (initial execution + potential retries)
- 5 workers × 3 calls = ~15 API calls per orchestration

### Cost per Provider

| Provider | Cost per Worker | Notes                  |
| -------- | --------------- | ---------------------- |
| Gemini   | ~$0.001-0.01    | Low/medium complexity  |
| Claude   | ~$0.01-0.10     | Medium/high complexity |

### Typical Orchestration Costs

- **5 workers @ $0.05 average**: ~$0.25 per orchestration
- **Large tasks (10+ workers)**: Can exceed $1.00

---

## Data Size Limits

| Limit                    | Value             |
| ------------------------ | ----------------- |
| Maximum worker output    | ~100KB per task   |
| Maximum input prompt     | ~50KB per task    |
| Total orchestration data | <10MB recommended |

---

## See Also

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [orchestration-methodology.md](orchestration-methodology.md) - Complete 9-phase workflow
- [delegation-strategies.md](delegation-strategies.md) - Worker selection and prompts
- [evaluation-rubrics.md](evaluation-rubrics.md) - Quality assessment criteria
