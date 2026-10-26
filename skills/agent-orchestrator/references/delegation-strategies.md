# Worker Delegation Strategies

Best practices for selecting worker types, allocating tasks, and generating effective worker prompts.

## Overview

Delegation is the process of assigning subtasks to worker AI agents with optimized prompts. Effective delegation ensures workers understand their role, context, and output requirements.

---

## Worker Type Selection

### Available Worker Types

| Worker Type    | Best For                            | Template File           |
| -------------- | ----------------------------------- | ----------------------- |
| **comparison** | Side-by-side analysis, benchmarking | `comparison_worker.txt` |
| **analysis**   | Deep investigation, evaluation      | `analysis_worker.txt`   |
| **synthesis**  | Integration, aggregation, consensus | `synthesis_worker.txt`  |
| **evaluation** | Scoring, assessment, validation     | `evaluation_worker.txt` |

### Selection Decision Tree

```
Is the task comparing multiple items?
  → YES: Use comparison_worker
  → NO: Continue

Is the task combining results from other workers?
  → YES: Use synthesis_worker
  → NO: Continue

Is the task scoring or assessing quality?
  → YES: Use evaluation_worker
  → NO: Use analysis_worker (default)
```

---

## Worker Complexity Mapping

### Complexity Levels

**Low Complexity**:

- Factual extraction
- Simple summarization
- Basic classification
- Template filling

**Medium Complexity**:

- Multi-criteria analysis
- Comparative evaluation
- Pattern identification
- Structured synthesis

**High Complexity**:

- Novel insight generation
- Complex reasoning chains
- Nuanced judgment
- Cross-domain synthesis

### Model Assignment Strategy

Current implementation (`worker_spawner.py`):

- **Low complexity**: `gemini-2.5-flash` (fast, cost-effective)
- **Medium complexity**: `gemini-3-flash-preview` (balanced performance)
- **High complexity**: `gemini-3.1-pro-preview` (maximum reasoning capability)

**Alternative Models**:

- **Claude**: `claude-sonnet-4.6` (strong for analysis, synthesis)
- **Codex**: Specialized for code-related tasks
- **Copilot**: Specialized for code assistance

---

## Prompt Engineering Principles

### Hierarchical Prompt Structure

All worker prompts follow this 7-layer structure:

```
1. SYSTEM CONTEXT
   - Worker role and identity
   - Coordination mode (parallel/sequential)
   - Total worker count
   - Cross-worker awareness

2. TASK DEFINITION
   - Task ID and clear description
   - Complexity level
   - Expected deliverables

3. METHODOLOGY
   - Step-by-step approach
   - Domain-specific framework
   - Best practices

4. DATA/CONTENT
   - Specific data to analyze
   - Context and background
   - Scope boundaries

5. OUTPUT FORMAT
   - Exact structure required
   - Examples if applicable
   - Format constraints (JSON, Markdown, etc.)

6. QUALITY CRITERIA
   - Completeness requirements
   - Evidence standards
   - Success criteria

7. CRITICAL CONSTRAINTS
   - No hallucination policy
   - Citation requirements
   - Task boundaries
   - User-specified constraints
```

### Layer 1: System Context

**Purpose**: Orient the worker to its role in the larger orchestration

**Example**:

```
You are Worker 3 of 5 in a parallel multi-agent orchestration.

Your role: Analyze customer feedback from the mobile app channel.

Coordination mode: PARALLEL
- Your results will be synthesized alongside 4 other workers
- Each worker analyzes a different channel independently
- Do not make assumptions about other workers' findings

Total orchestration goal: Identify common themes across all customer feedback channels
```

**Critical Elements**:

- Worker ID (for traceability)
- Total worker count (for context)
- Coordination awareness (parallel vs sequential)
- Role in larger task

---

### Layer 2: Task Definition

**Purpose**: Specify exactly what this worker must accomplish

**Example**:

```
TASK ID: feedback_analysis_mobile
DESCRIPTION: Analyze customer feedback from mobile app reviews (Jan-Mar 2024)

COMPLEXITY: Medium (requires pattern identification and thematic analysis)

EXPECTED OUTPUT:
- Top 5 themes identified with frequency counts
- Sentiment breakdown (positive/negative/neutral)
- Critical issues requiring immediate attention
- Supporting evidence with specific review citations
```

**Critical Elements**:

- Unique task ID
- Clear, specific description
- Complexity level (helps worker calibrate effort)
- Concrete output expectations

---

### Layer 3: Methodology

**Purpose**: Guide the worker's approach (not just what, but how)

**Example**:

```
METHODOLOGY:
Follow this systematic approach:

1. Initial Review
   - Read all feedback chronologically
   - Note recurring topics or keywords

2. Thematic Coding
   - Identify distinct themes (aim for 5-10)
   - Tag each piece of feedback with relevant themes
   - Count theme frequency

3. Sentiment Analysis
   - Assess overall sentiment per theme
   - Identify intensity (mild vs strong sentiment)

4. Critical Issue Detection
   - Flag feedback mentioning: bugs, crashes, data loss, security
   - Assess severity and frequency

5. Evidence Selection
   - Select 2-3 representative quotes per theme
   - Include review ID and date for traceability
```

**Critical Elements**:

- Step-by-step process
- Decision points clarified
- Domain-specific techniques
- Quality checkpoints

---

### Layer 4: Data/Content

**Purpose**: Provide the actual content to analyze

**Example**:

```
DATA SOURCE: mobile_app_reviews.json

CONTENT SUMMARY:
- 487 reviews from iOS App Store (Jan 1 - Mar 31, 2024)
- 312 reviews from Google Play Store (same period)
- Total: 799 reviews

SCOPE:
- Focus on substantive feedback (ignore "great app" without details)
- Include both positive and negative themes
- Pay special attention to reviews mentioning specific features

DATA ACCESS: [Path to file or inline data]
```

**Critical Elements**:

- Clear data source identification
- Data characteristics (volume, date range, format)
- Scope guidance (what to include/exclude)
- Access method

---

### Layer 5: Output Format

**Purpose**: Specify exact structure for results

**Example**:

```
OUTPUT FORMAT: Markdown report

Required sections:
1. Executive Summary (3-5 sentences)
2. Top Themes (table format)
   | Theme | Frequency | Sentiment | Key Evidence |
3. Critical Issues (bulleted list with severity)
4. Detailed Analysis (paragraph per theme)
5. Recommendations (3-5 actionable items)

Example theme entry:
| Battery Drain | 87 (11%) | Negative | "App drains battery in 2 hours" [Review #4821] |

AVOID:
- JSON format (use Markdown)
- Executive jargon
- Vague claims without evidence
```

**Critical Elements**:

- Format specification (Markdown, JSON, etc.)
- Required sections/fields
- Examples for clarity
- Anti-patterns to avoid

---

### Layer 6: Quality Criteria

**Purpose**: Define success conditions

**Example**:

```
QUALITY CRITERIA:
Your output will be evaluated on:

1. Completeness (45% weight)
   ✓ All 5 required sections present
   ✓ At least 5 themes identified
   ✓ Each theme has supporting evidence

2. Evidence Quality (30% weight)
   ✓ Every claim backed by specific citations
   ✓ Review IDs provided for traceability
   ✓ No vague generalizations

3. Structure (25% weight)
   ✓ Clear headers and formatting
   ✓ Consistent table structure
   ✓ Logical flow

SUCCESS CRITERIA:
- Identified themes account for >70% of substantive feedback
- No theme has <5 supporting examples
- Critical issues flagged if any exist
```

**Critical Elements**:

- Evaluation dimensions with weights
- Specific checkable criteria
- Success thresholds
- Quality standards

---

### Layer 7: Critical Constraints

**Purpose**: Enforce boundaries and prevent common failures

**Example**:

```
CRITICAL CONSTRAINTS:

1. NO HALLUCINATION
   ✗ Do not invent review content
   ✗ Do not cite non-existent review IDs
   ✗ Do not claim themes exist without evidence
   ✓ Only report what you actually find in the data

2. EXACT CITATIONS REQUIRED
   - Every theme must have ≥2 direct quotes
   - Every quote must include review ID
   - Format: "Quote text" [Review #ID, Date]

3. STAY ON TASK
   ✗ Do not analyze other channels (that's other workers' jobs)
   ✗ Do not make recommendations about channels you didn't analyze
   ✓ Focus exclusively on mobile app feedback

4. USER CONSTRAINTS
   - Analysis deadline: Complete within token budget
   - Language: English only (flag non-English reviews)
```

**Critical Elements**:

- Anti-hallucination warnings
- Citation requirements
- Task boundaries
- User-specified constraints

---

## Cross-Worker Awareness

### Parallel Coordination

When workers execute in parallel:

```
CROSS-WORKER CONTEXT:
You are one of 5 workers analyzing different aspects independently.

Worker 1: Technical performance issues
Worker 2: User interface feedback (THIS IS YOU)
Worker 3: Feature requests
Worker 4: Customer support quality
Worker 5: Pricing and value perception

IMPORTANT:
- Do not attempt to synthesize across all aspects (that happens later)
- Focus exclusively on your assigned aspect
- Your results will be combined with others in Phase 6
```

### Sequential Coordination

When workers execute sequentially:

```
CROSS-WORKER CONTEXT:
You are Worker 2 in a sequential pipeline.

Previous Worker (Worker 1): Identified candidate themes in raw data
Your Task: Validate and refine those candidate themes
Next Worker (Worker 3): Will use your validated themes for quantitative analysis

INPUT FROM PREVIOUS WORKER:
[Output from Worker 1]

YOUR OUTPUT WILL BE USED BY:
Worker 3 expects a validated list of themes with clear definitions
```

---

## Load Balancing

### Even Distribution

**Bad** (Unbalanced):

```
Worker 1: Analyze 100 reviews
Worker 2: Analyze 50 reviews
Worker 3: Analyze 10 reviews
```

**Good** (Balanced):

```
Worker 1: Analyze reviews 1-54
Worker 2: Analyze reviews 55-107
Worker 3: Analyze reviews 108-160
```

### Complexity Balancing

**Bad** (Unbalanced complexity):

```
Worker 1: Simple keyword extraction (low complexity)
Worker 2: Deep thematic analysis + sentiment + recommendations (high complexity)
```

**Good** (Balanced complexity):

```
Worker 1: Thematic analysis + sentiment
Worker 2: Critical issue detection + severity assessment
```

---

## Model Selection Best Practices

### When to Use Fast Models (gemini-2.0-flash)

- Simple data extraction
- Template-based analysis
- High-volume, low-complexity tasks
- Cost-sensitive applications

### When to Use Advanced Models (gemini-3-pro, claude-sonnet-4.6)

- Novel insight generation
- Complex reasoning required
- High-stakes decisions
- Synthesis tasks

### When to Use Specialized Models

- **Code analysis**: Codex, Copilot
- **Long documents**: Models with large context windows
- **Multilingual**: Models with strong language support

---

## Retry Strategy

### When to Retry

- Network failures
- Timeout errors
- Rate limiting
- Transient API errors

### When NOT to Retry

- Invalid prompts (syntax errors)
- Model capability limitations
- Content policy violations
- Quota exhaustion

### Retry Configuration

Current implementation:

- **Max retries**: 2 (total 3 attempts: initial + 2 retries)
- **Backoff**: Exponential (1s, 2s, 4s)
- **Fallback model**: Switch to alternative if primary fails

---

## Common Delegation Anti-Patterns

### Anti-Pattern 1: Vague Task Definition

**Bad**:

```
TASK: Look at the data and find interesting stuff
```

**Good**:

```
TASK: Identify top 5 recurring themes in customer feedback with frequency counts and sentiment analysis
```

### Anti-Pattern 2: Missing Context

**Bad**:

```
Analyze these reviews: [data dump]
```

**Good**:

```
CONTEXT: You are analyzing mobile app reviews from Q1 2024 as part of a larger study across all channels.
YOUR ROLE: Focus exclusively on mobile app feedback.
DATA: [data]
```

### Anti-Pattern 3: No Output Specification

**Bad**:

```
Analyze the data and report findings
```

**Good**:

```
OUTPUT FORMAT: Markdown table with columns: Theme | Frequency | Sentiment | Evidence
Required: Minimum 5 themes, each with 2+ citations
```

### Anti-Pattern 4: Unclear Quality Standards

**Bad**:

```
Do a good job analyzing this
```

**Good**:

```
QUALITY CRITERIA:
- Every claim must have specific evidence citations
- Themes must account for >70% of feedback
- No vague generalizations allowed
```

---

## Testing Worker Prompts

### Pre-Flight Checklist

Before deploying worker prompts:

- [ ] All 7 layers present and complete?
- [ ] Task boundaries clearly defined?
- [ ] Output format specified with examples?
- [ ] Quality criteria measurable?
- [ ] Anti-hallucination constraints included?
- [ ] Cross-worker coordination clarified?
- [ ] Data access method verified?

### Validation Questions

1. Could two workers executing this prompt produce wildly different outputs?
   - If YES: Prompt needs more specificity

2. Does the prompt tell the worker WHAT to produce and HOW to produce it?
   - If NO: Add methodology layer

3. Can output quality be objectively measured?
   - If NO: Add specific quality criteria

4. Are success conditions clear?
   - If NO: Add concrete success thresholds

---

## Summary

Effective delegation requires:

1. **Right worker type** for task characteristics
2. **Appropriate model** for complexity level
3. **Comprehensive prompts** using 7-layer structure
4. **Clear boundaries** to prevent scope creep
5. **Quality criteria** for objective evaluation
6. **Load balancing** across workers
7. **Retry strategies** for robustness

Following these strategies ensures workers produce consistent, high-quality outputs that can be effectively synthesized.
