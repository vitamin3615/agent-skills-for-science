# Worker Output Evaluation Rubrics

Comprehensive quality assessment criteria for worker outputs using 4-layer evaluation system.

## Overview

Phase 5 (Response Evaluation) uses a multi-layer quality control system to assess worker outputs objectively. Each layer examines different quality dimensions with specific scoring criteria and quality gates.

---

## Evaluation Architecture

### Layer Weights

**Standard 3-Layer Evaluation** (default):
- Layer 1 (Structural): 25%
- Layer 2 (Completeness): 45%
- Layer 3 (Hallucination Detection): 30%
- **Total**: 100%

**4-Layer Evaluation** (high-stakes tasks):
- Layer 1 (Structural): 20%
- Layer 2 (Completeness): 30%
- Layer 3 (Hallucination Detection): 20%
- Layer 4 (AI Evaluation): 30%
- **Total**: 100%

### Quality Gates

| Score Range | Gate | Action |
|-------------|------|--------|
| **< 60** | REJECT | Re-execute required, output not usable |
| **60-80** | FLAG | Acceptable but review recommended |
| **> 80** | ACCEPT | High quality, ready to use |

---

## Layer 1: Structural Check (Weight: 25%)

### Purpose
Verify output meets basic format and structure requirements.

### Scoring Criteria

#### 1.1 Non-Empty Output (Critical)
- **Check**: Output exists and has content
- **Scoring**:
  - Empty or whitespace-only → **0 points** (automatic fail)
  - Has content → Continue to next checks

#### 1.2 Minimum Length
- **Check**: Output length ≥ 100 characters
- **Scoring**:
  - < 100 chars → **-40 points**
  - ≥ 100 chars → No penalty

**Rationale**: Substantive analysis requires minimum content depth

#### 1.3 Structural Elements
- **Check**: Output contains organizational structure
- **Indicators**:
  - Headers: `^#+\s+` (Markdown) or `===` (text)
  - Lists: `^\s*[-*]\s+` or numbered lists
  - Paragraphs: Multiple distinct paragraphs
- **Scoring**:
  - No headers AND no lists → **-30 points**
  - Has structure → No penalty

**Rationale**: Structured output indicates organized thinking

#### 1.4 Content Depth
- **Check**: Output has ≥ 5 lines of content
- **Scoring**:
  - < 5 lines → **-20 points**
  - ≥ 5 lines → No penalty

**Rationale**: Minimal depth indicates insufficient analysis

### Layer 1 Scoring Formula

```python
score = 100
if empty: return 0
if len(output) < 100: score -= 40
if not has_structure: score -= 30
if lines < 5: score -= 20
return max(0, score)
```

### Examples

**Score: 100/100** (Perfect)
```markdown
# Customer Feedback Analysis

## Executive Summary
Analysis of 487 mobile app reviews reveals...

## Top Themes
1. **Battery Drain** (87 instances, 11%)
   - "App drains battery in 2 hours" [Review #4821]

2. **Slow Performance** (64 instances, 8%)
   - "Takes forever to load" [Review #3204]

...
```
✓ Has content, >100 chars, clear structure, >5 lines

**Score: 60/100** (Minimal Pass)
```
Found 3 themes: battery, performance, UI.
Battery mentioned 87 times.
Performance mentioned 64 times.
UI mentioned 52 times.
Some users happy, some not.
```
✓ Has content, ≥100 chars, ≥5 lines
✗ No headers or lists (-30)

**Score: 0/100** (Fail)
```
Analysis complete.
```
✗ Empty/minimal output (automatic 0)

---

## Layer 2: Completeness Check (Weight: 45%)

### Purpose
Verify output addresses all task requirements and success criteria.

### Scoring Criteria

#### 2.1 Keyword Coverage
- **Check**: Required keywords from task description present in output
- **Extraction**:
  - Parse task description
  - Extract key nouns and action verbs
  - Check output for keyword presence (case-insensitive)
- **Scoring**:
  - Missing > 50% of keywords → **-40 points**
  - Missing 25-50% → **-20 points**
  - Missing < 25% → No penalty

**Example**:
- Task: "Identify top 5 **themes** in customer **feedback** with **frequency** counts"
- Keywords: [themes, feedback, frequency]
- Output must contain these terms or close synonyms

#### 2.2 Success Criteria Addressed
- **Check**: Each success criterion from task config addressed
- **Extraction**:
  - Identify success criteria from request analysis
  - Check if output contains relevant content for each
- **Scoring**:
  - Each unaddressed criterion → **-15 points** (max 3 criteria checked)

**Example**:
- Criterion: "Identify sentiment for each theme"
- Check: Does output mention positive/negative/neutral for themes?

#### 2.3 Output Format Compliance
- **Check**: Output matches requested format
- **Format Types**:
  - **JSON**: Must contain valid JSON structure
  - **Markdown**: Must contain headers (`#` symbols)
  - **Table**: Must contain table structure
  - **List**: Must contain list items
- **Scoring**:
  - Wrong format → **-30 points**
  - Partially correct → **-15 points**
  - Correct format → No penalty

**Example**:
- Requested: JSON output
- Received: Plain text → **-30 points**

#### 2.4 Required Sections Present
- **Check**: All required sections specified in task
- **Extraction**: Parse section requirements from prompt
- **Scoring**:
  - Missing > 50% of sections → **-30 points**
  - Missing 1-2 sections → **-10 points** each
  - All sections present → No penalty

### Layer 2 Scoring Formula

```python
score = 100
if missing_keywords > 0.5: score -= 40
for criterion in unaddressed_criteria[:3]: score -= 15
if wrong_format: score -= 30
if missing_sections > 0: score -= (10 * min(3, missing_sections))
return max(0, score)
```

### Examples

**Score: 100/100** (Complete)
```markdown
Task: Analyze sentiment in reviews
Required: Top themes, frequency, sentiment, evidence

Output:
# Sentiment Analysis

## Top Themes
1. Battery Drain: 87 mentions (11%), Negative sentiment
   Evidence: "Drains battery fast" [#4821]
2. Performance: 64 mentions (8%), Negative sentiment
   Evidence: "App is slow" [#3204]
...
```
✓ Keywords present (themes, frequency, sentiment)
✓ Success criteria met (all themes have sentiment)
✓ Correct format (Markdown)
✓ Required sections present

**Score: 55/100** (Incomplete)
```markdown
# Themes
- Battery issues
- Performance problems
- UI concerns
```
✗ Missing frequency counts (-15)
✗ Missing sentiment analysis (-15)
✗ Missing evidence/citations (-15)

---

## Layer 3: Hallucination Detection (Weight: 30%)

### Purpose
Detect unsupported claims, vague generalizations, and potential fabrications.

### Scoring Criteria

#### 3.1 Vague Claim Patterns
- **Check**: Excessive use of vague qualifiers
- **Patterns**:
  - Unsupported quantity: "many studies", "numerous users", "several reports"
  - Weasel words: "it is well known", "obviously", "clearly", "certainly"
  - Absolutes: "always", "never", "all", "none", "everyone"
- **Scoring**:
  - > 5 vague patterns → **-25 points**
  - 3-5 patterns → **-15 points**
  - < 3 patterns → No penalty

**Rationale**: Vague language often masks lack of specific evidence

#### 3.2 Citation Density
- **Check**: Sufficient citations for claims made
- **Heuristic**: > 200 words without citations suggests unsupported claims
- **Exceptions**:
  - Introductory/summary sections (first 100 words)
  - Methodology explanations
- **Scoring**:
  - Long sections (>200 words) without citations → **-30 points**
  - Moderate sections (100-200 words) → **-15 points**

**Rationale**: Evidence-based output requires traceable sources

#### 3.3 Comparative Claims Without Baseline
- **Check**: Comparisons made without context
- **Patterns**:
  - "Increased by 40%" (compared to what?)
  - "Significantly better" (than what?)
  - "High performance" (relative to what?)
- **Scoring**:
  - Multiple comparative claims without baseline → **-15 points**

#### 3.4 Simple Contradictions
- **Check**: Internally inconsistent statements
- **Detection**:
  - Same entity with conflicting attributes
  - Contradictory numerical claims
- **Scoring**:
  - Each contradiction → **-20 points** (max 1 checked)

**Example Contradiction**:
```
"Battery theme appears in 87 reviews"
...later...
"Only 42 users mentioned battery issues"
```

### Layer 3 Scoring Formula

```python
score = 100
if vague_patterns > 5: score -= 25
if long_text_without_citations: score -= 30
if comparative_claims_without_baseline > 2: score -= 15
if contradictions_found: score -= 20
return max(0, score)
```

### Examples

**Score: 100/100** (Evidence-Based)
```markdown
Theme: Battery Drain (87 instances, 11% of reviews)

Representative evidence:
- "App drains battery in 2 hours" [Review #4821, Jan 15]
- "Battery life terrible since update" [Review #5103, Feb 3]
- "Have to charge phone twice daily" [Review #5892, Mar 12]

Frequency breakdown:
- iOS: 52 instances (60% of 87)
- Android: 35 instances (40% of 87)
```
✓ Specific numbers with context
✓ Citations provided for claims
✓ No vague generalizations

**Score: 45/100** (High Hallucination Risk)
```markdown
Many users complained about battery issues. Several reviews
mentioned performance problems. It is well known that mobile
apps often have these issues. Obviously, this is a significant
concern. Everyone agrees that battery optimization is critical.

The app performs significantly better than competitors, though
some users disagree. Battery life has increased dramatically
since the previous version.
```
✗ Excessive vague patterns (many, several, well known, obviously, everyone) → -25
✗ No citations for 100+ word section → -30
✗ Comparative claims without baseline → -15

---

## Layer 4: AI Evaluation (Weight: 30%, Optional)

### Purpose
Deep quality assessment using AI reasoning (for high-stakes tasks).

### Scoring Criteria

#### 4.1 Reasoning Quality (25 points)
- **Check**: Logical flow and argumentation
- **Assessment**:
  - Conclusions follow from evidence
  - No logical fallacies
  - Appropriate inferences
- **Scoring Scale**:
  - 0-8: Poor reasoning (logical gaps)
  - 9-16: Adequate reasoning (mostly sound)
  - 17-25: Excellent reasoning (rigorous)

#### 4.2 Evidence Strength (25 points)
- **Check**: Quality and relevance of supporting evidence
- **Assessment**:
  - Evidence directly supports claims
  - Sufficient evidence quantity
  - Evidence is specific (not generic)
- **Scoring Scale**:
  - 0-8: Weak evidence (vague, insufficient)
  - 9-16: Moderate evidence (adequate support)
  - 17-25: Strong evidence (comprehensive, specific)

#### 4.3 Logical Consistency (25 points)
- **Check**: Internal coherence and absence of contradictions
- **Assessment**:
  - No contradictory statements
  - Definitions used consistently
  - Numerical claims add up correctly
- **Scoring Scale**:
  - 0-8: Inconsistent (contradictions found)
  - 9-16: Mostly consistent (minor issues)
  - 17-25: Fully consistent (no issues)

#### 4.4 Task Fulfillment (25 points)
- **Check**: Degree to which output accomplishes task goal
- **Assessment**:
  - All requirements addressed
  - Appropriate depth and breadth
  - Actionable insights provided
- **Scoring Scale**:
  - 0-8: Poor fulfillment (misses key requirements)
  - 9-16: Partial fulfillment (meets basic requirements)
  - 17-25: Complete fulfillment (exceeds expectations)

### Layer 4 Implementation

**Delegation**:
- Use high-complexity worker AI for evaluation
- Provide evaluation rubric and output to assess
- Request structured JSON response with scores

**Output Format**:
```json
{
  "reasoning_quality": 22,
  "evidence_strength": 19,
  "logical_consistency": 24,
  "task_fulfillment": 20,
  "total_score": 85,
  "justification": "Detailed reasoning for scores..."
}
```

---

## Composite Scoring Examples

### Example 1: High-Quality Output

**Output** (excerpt):
```markdown
# Mobile App Feedback Analysis (Jan-Mar 2024)

## Executive Summary
Analysis of 799 reviews (487 iOS, 312 Android) identified 5 primary
themes accounting for 73% of substantive feedback. Critical issues
require immediate attention: battery drain affects 11% of users.

## Top 5 Themes

| Theme | Count | % | Sentiment | Key Evidence |
|-------|-------|---|-----------|--------------|
| Battery Drain | 87 | 11% | Negative | "Battery dies in 2 hours" [#4821] |
| Slow Load Times | 64 | 8% | Negative | "Takes 30+ seconds" [#3204] |
| UI Confusion | 52 | 7% | Negative | "Can't find settings" [#5103] |
| Helpful Support | 48 | 6% | Positive | "Support replied in 1 hour" [#2847] |
| Feature Request | 41 | 5% | Neutral | "Need dark mode" [#6291] |

## Critical Issues (Immediate Action Required)
...
```

**Layer 1: Structural** → 100/100
- ✓ Non-empty, >100 chars, clear structure, >5 lines

**Layer 2: Completeness** → 100/100
- ✓ All keywords present (themes, frequency, sentiment)
- ✓ Success criteria met (top 5, percentages, evidence)
- ✓ Correct format (Markdown table)
- ✓ Required sections present

**Layer 3: Hallucination Detection** → 100/100
- ✓ No vague patterns
- ✓ Citations throughout
- ✓ Specific numbers with context
- ✓ No contradictions

**Final Score** (3-layer):
```
(100 × 0.25) + (100 × 0.45) + (100 × 0.30) = 100/100
Quality Gate: ACCEPT
```

---

### Example 2: Flagged Output

**Output**:
```
Analysis shows several important themes. Many users mentioned
battery issues, which is concerning. Performance problems were
also noted by numerous reviewers. The UI seems confusing based
on feedback. Overall sentiment is mixed.

Some positive feedback about customer support. Feature requests
include dark mode and better navigation.
```

**Layer 1: Structural** → 70/100
- ✓ Non-empty, >100 chars, ≥5 lines
- ✗ No headers or lists → -30

**Layer 2: Completeness** → 55/100
- ✗ Missing specific frequency counts → -15
- ✗ Missing quantified sentiment → -15
- ✗ Missing evidence citations → -15

**Layer 3: Hallucination Detection** → 60/100
- ✗ Vague patterns (several, many, numerous) → -25
- ✗ 100+ words without citations → -15

**Final Score** (3-layer):
```
(70 × 0.25) + (55 × 0.45) + (60 × 0.30) = 60.25/100
Quality Gate: FLAG (acceptable but needs review)
```

---

### Example 3: Rejected Output

**Output**:
```
Reviewed the data. Found some themes.
```

**Layer 1: Structural** → 0/100
- ✗ < 100 chars, minimal content → automatic fail

**Final Score**: 0/100
**Quality Gate**: REJECT (unusable)

---

## Quality Gate Decision Logic

```python
def apply_quality_gate(score: float) -> str:
    if score < 60:
        return "reject"  # Re-execute required
    elif score >= 60 and score <= 80:
        return "flag"    # Review recommended
    else:  # score > 80
        return "accept"  # Ready to use
```

### Gate Actions

**REJECT (< 60)**:
- Do not use output in synthesis
- Attempt re-execution with refined prompt
- If retry fails, report partial results

**FLAG (60-80)**:
- Include in synthesis but mark with warnings
- Manual review recommended for critical tasks
- Note quality concerns in final report

**ACCEPT (> 80)**:
- Use output in synthesis without reservation
- High confidence in accuracy and completeness

---

## Evaluation Best Practices

1. **Use 3-Layer by Default**: Reserve Layer 4 (AI evaluation) for critical tasks

2. **Consistent Criteria**: Apply same rubric to all workers in a group

3. **Document Deductions**: Track which checks failed for debugging

4. **Adjust Thresholds**: Consider raising gates for high-stakes applications

5. **Review Borderline Cases**: Manually inspect outputs scoring 58-62 (near reject/flag boundary)

6. **Learn from Failures**: Analyze rejected outputs to improve prompt engineering

7. **Calibrate Expectations**: Lower complexity tasks may naturally score lower on depth

8. **Context Matters**: Quick summaries vs deep analysis have different quality standards

---

This rubric ensures objective, reproducible quality assessment across all worker outputs.
