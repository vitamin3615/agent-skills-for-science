---
name: agent-orchestrator
description: "Intelligent multi-agent orchestrator that analyzes requests, decomposes tasks, delegates to 1-5 parallel worker AI agents (up to 7 maximum), and synthesizes results. Use when you need to coordinate multiple AI agents for complex analysis, comparison, or synthesis tasks."
---

# Multi-Agent Orchestrator

Expert orchestrator for complex tasks requiring parallel AI worker coordination.

> **🚀 New to Agent-Orchestrator?** See [references/QUICKSTART.md](references/QUICKSTART.md) for a 5-minute getting started guide.

## Overview

The Agent Orchestrator intelligently decomposes complex user requests, delegates work to 1-5 parallel worker AI agents (up to 7 maximum), evaluates quality, and synthesizes results.

**Key Features**:

- Automated 9-phase workflow (Phases 0-8)
- Dynamic worker allocation (1-5 workers recommended, 7 maximum)
- 3-layer quality control with automatic hallucination detection
- Context-dependent synthesis strategies
- Full resumability with state management
- Support for Gemini, Claude, Codex, and Copilot workers

## When to Use

| Use Case                       | Example                                                 |
| ------------------------------ | ------------------------------------------------------- |
| **Multi-Source Analysis**      | Compare document against 10 source books                |
| **Complex Task Decomposition** | Comprehensive market analysis across 4 sectors          |
| **Parallel Independent Tasks** | Review code quality in 6 modules                        |
| **Quality-Critical Synthesis** | Synthesize findings from multiple papers with citations |

### When NOT to Use

- **Simple 1-3 task workflows**: Use direct execution
- **Real-time interactive tasks**: Multi-agent adds latency
- **Single-source analysis**: No parallelization benefit

## Execution Tier Selection

Choose the right tier based on your task complexity:

| Tier             | When to Use                                       | Overhead |
| ---------------- | ------------------------------------------------- | -------- |
| **Tier 1** (70%) | Independent tasks, clear list, simple aggregation | ~5%      |
| **Tier 2** (15%) | You provide the task plan                         | ~15%     |
| **Tier 3** (10%) | Need intelligent synthesis                        | ~40%     |
| **Tier 4** (5%)  | Complex/unclear tasks, high-stakes                | Full     |

**Quick Decision**:

```
Can you list all subtasks? → YES: Tier 1-2 | NO: Tier 4
Need synthesis?           → YES: Tier 3-4 | NO: Tier 1-2
High-stakes decision?     → YES: Tier 4   | NO: Tier 1-3
```

> [!WARNING]
> **Tier 1 Status**: `simple_parallel.py` is in development. Use `orchestrator.py` for now.

See **[references/tier-selection-guide.md](references/tier-selection-guide.md)** for complete tier details and performance data.

## Prerequisites

**Required**: At least one AI CLI tool installed:

- **Gemini** (recommended): `gemini` CLI + Docker
- **Claude**: `claude` CLI
- **Codex**: `codex` CLI
- **Copilot**: `copilot` CLI

```bash
# Verify installation
gemini --version && docker --version
```

First Gemini execution may take 5-10 minutes for Docker image pull.

## Quick Start

```bash
cd <project_root>/.claude/skills/agent-orchestrator/scripts

# Simple analysis
python orchestrator.py --request "Analyze sentiment in 3 customer reviews"

# Book comparison (10 parallel workers)
python orchestrator.py --request "Compare my research document against these 10 source books"

# Resume from interruption
python orchestrator.py --resume ~/my_orchestration/.orchestrator_state.json
```

### Example Request Patterns

**Multi-Source Comparison**:

```
"Compare section 3 of my manuscript against the following 5 papers:
1. Smith et al. (2023) - paper1.pdf
2. Jones (2022) - paper2.pdf ..."
```

**Parallel Analysis**:

```
"Analyze these 6 code modules for security vulnerabilities:
- auth.py, database.py, api.py ..."
```

**Synthesis Task**:

```
"Review these 8 research proposals and identify common themes,
unique approaches, and provide consensus recommendations"
```

## 9-Phase Workflow

| Phase | Name                     | Purpose                                | Output                    |
| ----- | ------------------------ | -------------------------------------- | ------------------------- |
| 0     | Request Understanding    | Parse goals, requirements, constraints | `request_analysis.json`   |
| 1     | Task Decomposition       | AI-powered task breakdown              | `task_plan.json`          |
| 2     | Parallelization Strategy | Determine optimal worker count         | Config                    |
| 3     | Prompt Generation        | Build hierarchical worker prompts      | `worker_prompts.json`     |
| 4     | Parallel Execution       | Concurrent worker execution            | `worker_results/`         |
| 5     | Response Evaluation      | 3-layer quality control                | `evaluation_results.json` |
| 6     | Result Synthesis         | Context-dependent aggregation          | `synthesis_result.md`     |
| 7     | Meta-Cognitive Review    | Iterative quality improvement          | `meta_review.json`        |
| 8     | Final Report             | Professional documentation             | `final_report.md`         |

See **[references/orchestration-methodology.md](references/orchestration-methodology.md)** for detailed phase descriptions.

## Output Structure

```
Temp/orchestrator_work/
├── .orchestrator_state.json    # State for resumability
├── request_analysis.json       # Phase 0
├── task_plan.json              # Phase 1
├── worker_prompts.json         # Phase 3
├── worker_results/             # Phase 4
├── evaluation_results.json     # Phase 5
├── synthesis_result.md         # Phase 6
├── meta_review.json            # Phase 7
└── final_report.md             # Phase 8 (FINAL)
```

## Configuration

| Setting              | Default                | Notes          |
| -------------------- | ---------------------- | -------------- |
| Worker count         | 1-5 dynamic            | 7 maximum      |
| Quality threshold    | 60/80 (flag/accept)    | <60 rejected   |
| Default model (low)  | gemini-2.5-flash       | Fast           |
| Default model (high) | gemini-3.1-pro-preview | Best reasoning |

See **[references/configuration-guide.md](references/configuration-guide.md)** for all configuration options, state management, and cost estimates.

## Quality Control

**3-Layer Default** (4-layer for high-stakes):

| Layer         | Weight   | Checks                          |
| ------------- | -------- | ------------------------------- |
| Structural    | 25%      | Format, length, structure       |
| Completeness  | 45%      | Requirements addressed          |
| Hallucination | 30%      | Vague claims, missing citations |
| AI Evaluation | Optional | Deep reasoning validation       |

See **[references/evaluation-rubrics.md](references/evaluation-rubrics.md)** for complete scoring criteria.

## Synthesis Strategies

| Strategy                  | When to Use                      |
| ------------------------- | -------------------------------- |
| **Aggregation**           | Independent parallel tasks       |
| **Consensus**             | Multiple workers on same content |
| **Iterative Integration** | Sequential dependencies          |
| **Evidence Database**     | Citation-heavy tasks             |

See **[references/synthesis-methods.md](references/synthesis-methods.md)** for strategy details.

## Meta-Cognitive Iteration

Phase 7 automatically improves synthesis quality through up to 3 iterations:

- Detects information loss, quality degradation, synthesis coherence issues
- Applies one of 5 refinement strategies when needed
- Average +10-20 point quality improvement
- ~30% of tasks trigger iteration; 70% accept on first attempt

See **[references/meta-cognitive-iteration.md](references/meta-cognitive-iteration.md)** for architecture details.

## Limitations

- **AI Worker Dependency**: Requires at least one AI CLI installed
- **First Run Latency**: 5-10 minutes for Docker sandbox setup
- **Worker Count**: 5 recommended, 7 maximum
- **Cost**: ~$0.25 per orchestration (5 workers), can exceed $1.00 for 10+ workers
- **Data Limits**: ~100KB per worker output, <10MB total

## Best Practices

1. **Clear Requests**: Provide specific, detailed requests with success criteria
2. **Structured Data**: Provide clear file paths when comparing documents
3. **Realistic Scope**: Don't over-decompose; each subtask should be substantial
4. **Monitor State**: Check state file for long-running tasks
5. **Review Synthesis**: Always review before using as authoritative

## Troubleshooting

**Model Availability Checker**:

```bash
python scripts/check_model_availability.py        # Check all models
python scripts/check_model_availability.py --json # JSON output
```

See **[references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)** for common issues and solutions.

## Examples

- **[references/examples/book-comparison-example.md](references/examples/book-comparison-example.md)**: 10-book comparison walkthrough
- **[references/examples/parallel-analysis-example.md](references/examples/parallel-analysis-example.md)**: Code analysis across modules
- **[references/examples/sequential-synthesis-example.md](references/examples/sequential-synthesis-example.md)**: Sequential dependency handling

## References

| Reference                                                               | Content                          |
| ----------------------------------------------------------------------- | -------------------------------- |
| [tier-selection-guide.md](references/tier-selection-guide.md)           | Execution tier selection         |
| [simple-parallel-guide.md](references/simple-parallel-guide.md)         | Tier 1 (Simple Parallel) details |
| [configuration-guide.md](references/configuration-guide.md)             | All configuration options        |
| [orchestration-methodology.md](references/orchestration-methodology.md) | 9-phase workflow details         |
| [meta-cognitive-iteration.md](references/meta-cognitive-iteration.md)   | Iteration framework              |
| [task-patterns.md](references/task-patterns.md)                         | Task decomposition patterns      |
| [delegation-strategies.md](references/delegation-strategies.md)         | Worker selection & prompts       |
| [evaluation-rubrics.md](references/evaluation-rubrics.md)               | Quality assessment               |
| [synthesis-methods.md](references/synthesis-methods.md)                 | Synthesis strategies             |
| [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)                     | Issues & solutions               |

## Support

1. Check state file for execution details
2. Review worker outputs in `worker_results/`
3. Examine evaluation scores in `evaluation_results.json`
4. Consult reference documentation
