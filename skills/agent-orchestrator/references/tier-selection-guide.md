# Execution Tier Selection Guide

This guide provides detailed information on selecting the appropriate execution tier for your orchestration tasks.

## Overview

The Agent Orchestrator supports 4 execution tiers optimized for different complexity levels. Selecting the right tier is crucial for balancing performance overhead against orchestration capabilities.

> [!WARNING]
> **Tier 1 Implementation Status**: The `simple_parallel.py` script is currently **in development**. Until implementation is complete, please use Tier 4 (Full Orchestrator) via `scripts/orchestrator.py` for all parallel task execution.

## Tier Descriptions

### Tier 1: Simple Parallel (Recommended for 70% of tasks)

**Status**: *IN DEVELOPMENT*

| Aspect | Details |
|--------|---------|
| **When** | Independent tasks, clear decomposition, simple aggregation |
| **Method** | Direct bash parallel execution |
| **Performance** | ~5% overhead vs direct execution |
| **Benchmark** | 282s for 5 tasks, 100% success rate |

**Example Usage**:
```bash
python scripts/simple_parallel.py --tasks "task1, task2, task3" --output results/
```

**Best Use Cases**:
- Code security analysis across multiple files
- Document summarization (multiple docs)
- Multi-module analysis with independent outputs
- Batch processing with no inter-task dependencies

---

### Tier 2: Phase 4 Only (Manual decomposition)

| Aspect | Details |
|--------|---------|
| **When** | You provide task plan, need execution infrastructure |
| **Method** | Skip Phases 0-3, execute your prompts |
| **Performance** | ~15% overhead |

**Example Usage**:
```bash
python scripts/orchestrator.py --start-phase 4 --task-plan tasks.json
```

**Best Use Cases**:
- Pre-planned task execution
- When you've already decomposed tasks manually
- Integration with external planning systems

---

### Tier 3: Phases 3-6 (Parallel + Synthesis)

| Aspect | Details |
|--------|---------|
| **When** | Clear decomposition, need intelligent synthesis |
| **Method** | Skip planning phases, focus on execution + synthesis |
| **Performance** | ~40% overhead |

**Example Usage**:
```bash
python scripts/orchestrator.py --start-phase 3 --synthesis-strategy consensus
```

**Best Use Cases**:
- Multi-source comparison with synthesis
- Expert opinion aggregation
- Research paper synthesis

---

### Tier 4: Full Orchestrator (Complete workflow)

| Aspect | Details |
|--------|---------|
| **When** | Complex analysis, unclear decomposition, high-stakes decisions |
| **Method** | Complete Phases 0-8 with meta-cognitive iteration |
| **Performance** | Full orchestration overhead (Phases 0-8) |

**Example Usage**:
```bash
python scripts/orchestrator.py --request "Comprehensive analysis" --enable-quality-control
```

**Best Use Cases**:
- Complex analysis requiring intelligent decomposition
- High-stakes decisions needing quality control
- Tasks where the full scope isn't initially clear
- Situations requiring meta-cognitive review

---

## Quick Decision Guide

```
Can you list all subtasks clearly? → YES: Tier 1-2 | NO: Tier 4
Need intelligent synthesis?        → YES: Tier 3-4 | NO: Tier 1-2
High-stakes critical decision?     → YES: Tier 4   | NO: Tier 1-3
```

## Performance Comparison

| Tier | Example Performance | Success Rate | Recommended Use |
|------|---------------------|--------------|-----------------|
| Tier 1 (Simple Parallel) | 282s for 5 tasks | 100% | **DEFAULT** |
| Tier 4 (Full Orchestrator) | 600s+ | Variable | Complex/unclear tasks |

> [!IMPORTANT]
> Tier 1 is recommended as the default for 70% of use cases. Only escalate to higher tiers when you need the additional capabilities.

## Tier-to-Phase Mapping

| Tier | Phases Executed |
|------|-----------------|
| Tier 1 | Bypasses all phases (direct bash parallel execution) |
| Tier 2 | Phase 4 only (parallel worker execution) |
| Tier 3 | Phases 3-6 (prompt generation → execution → evaluation → synthesis) |
| Tier 4 | Phases 0-8 (full workflow: understanding → planning → execution → synthesis → meta-review → report) |

## Rule of Thumb Distribution

- **Simple parallel tasks** (explicit list) → **Tier 1** (70% of use cases)
- **Manual decomposition provided** → **Tier 2** (15% of use cases)
- **Need synthesis without planning** → **Tier 3** (10% of use cases)
- **Complex/unclear tasks** → **Tier 4** (5% of use cases)

## Decision Flowchart

```
                    ┌─────────────────────┐
                    │   Start: New Task   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Can you list all    │
                    │ subtasks clearly?   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │ YES            │                │ NO
              ▼                │                ▼
    ┌─────────────────┐        │      ┌─────────────────┐
    │ Need synthesis? │        │      │    Tier 4       │
    └────────┬────────┘        │      │ Full Orchestrator│
             │                 │      └─────────────────┘
    ┌────────┼────────┐        │
    │ NO     │        │ YES    │
    ▼        │        ▼        │
┌────────┐   │   ┌────────┐    │
│ Tier 1 │   │   │ Tier 3 │    │
│ Simple │   │   │ Parallel│   │
│ Parallel│  │   │+Synthesis│  │
└────────┘   │   └────────┘    │
             │                 │
             │ Have pre-made   │
             │ task plan?      │
             │        │        │
             │   YES  ▼        │
             │   ┌────────┐    │
             │   │ Tier 2 │    │
             │   │Phase 4 │    │
             │   │ Only   │    │
             │   └────────┘    │
             └─────────────────┘
```

## See Also

- [simple-parallel-guide.md](simple-parallel-guide.md) - Complete Tier 1 specification
- [orchestration-methodology.md](orchestration-methodology.md) - Full 9-phase workflow details
