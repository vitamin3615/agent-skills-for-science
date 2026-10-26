# Multi-Source Synthesis Methods

Context-dependent strategies for combining worker outputs into coherent final results.

## Overview

Phase 6 (Result Synthesis) combines outputs from multiple workers using different strategies based on task characteristics. The orchestrator automatically selects the optimal synthesis method based on task type, dependencies, and content characteristics.

---

## Strategy Selection Logic

```python
def select_synthesis_strategy(worker_results, task_plan, request_analysis):
    """Automatically select optimal synthesis strategy."""

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

---

## Strategy 1: Aggregation (Independent Tasks)

### When to Use
- Multiple independent parallel tasks
- Each worker analyzes different data
- No overlapping content
- Results need compilation, not integration

### Best For
- Book comparison across 10 sources
- Code analysis across different modules
- Multi-channel customer feedback
- Distributed data analysis

### Approach

**Phase 1: Organize by Worker**
```markdown
# Synthesis Results

## Worker 1: Analysis of Book 1 "Deep Work"
[Worker 1 output in full]

## Worker 2: Analysis of Book 2 "Atomic Habits"
[Worker 2 output in full]

...
```

**Phase 2: Identify Cross-Worker Patterns**
- Extract themes mentioned by multiple workers
- Note unique insights from individual workers
- Identify contradictions or disagreements

**Phase 3: Executive Summary**
- Synthesize high-level findings across all workers
- Highlight common themes
- Note unique contributions

### Implementation

```python
def aggregation_strategy(worker_results, evaluation_results):
    """Compile independent worker results with pattern identification."""

    # Filter to accepted workers
    accepted = [r for r in worker_results
                if evaluation_results[r["worker_id"]]["quality_gate"] in ["accept", "flag"]]

    # Build synthesis
    synthesis = "# Aggregated Results\n\n"

    # Executive summary
    synthesis += "## Executive Summary\n"
    synthesis += generate_cross_worker_summary(accepted)

    # Individual worker sections
    for result in accepted:
        synthesis += f"\n## {result['worker_id']}: {result['task_id']}\n"
        synthesis += result["output"]

    # Cross-cutting themes
    synthesis += "\n## Cross-Worker Patterns\n"
    synthesis += identify_common_themes(accepted)

    return synthesis
```

### Example Output

```markdown
# Multi-Book Comparison Results

## Executive Summary

Analyzed 10 productivity books (Jan-Mar 2024). Common themes emerged:
- **Focus**: 8/10 books emphasize deep work and distraction elimination
- **Habits**: 7/10 discuss habit formation and systems
- **Energy Management**: 6/10 address peak performance timing

Unique contributions:
- Worker 3: "Deep Work" introduces concept of attention residue
- Worker 7: "When" provides chronotype-specific strategies

## Worker 1: "Atomic Habits" by James Clear

**Core Thesis**: Small habit changes compound over time...

**Key Concepts**:
1. The aggregation of marginal gains...
2. Identity-based habits...

...

## Cross-Worker Pattern Analysis

### Theme 1: Deep Work & Focus (8 books)
- "Deep Work" (Newport): 4-hour blocks of undistracted work
- "Atomic Habits" (Clear): Environment design for focus
- "Hyperfocus" (Bailey): Managing attention deliberately
...
```

---

## Strategy 2: Consensus (Overlapping Analysis)

### When to Use
- Multiple workers analyzing same content
- Need to identify agreement vs disagreement
- Varying perspectives on shared data
- Require confidence assessment

### Best For
- Multi-reviewer evaluation
- Quality assessment from different angles
- Risk analysis with multiple perspectives
- Peer review simulation

### Approach

**Phase 1: Extract Claims**
- Parse each worker output into discrete claims
- Tag claims with worker ID and confidence

**Phase 2: Identify Consensus Strength**
- **Strong consensus**: Mentioned by ≥70% of workers
- **Moderate consensus**: Mentioned by 40-69% of workers
- **Weak consensus**: Mentioned by <40% of workers
- **Unique insights**: Mentioned by only 1 worker

**Phase 3: Resolve Contradictions**
- Weight by quality scores
- Flag unresolved disagreements
- Provide balanced view with attribution

### Implementation

```python
def consensus_strategy(worker_results, evaluation_results):
    """Build consensus from overlapping worker analyses."""

    # Extract claims from all workers
    all_claims = []
    for result in worker_results:
        claims = extract_claims(result["output"])
        quality = evaluation_results[result["worker_id"]]["score"]
        all_claims.extend([(claim, result["worker_id"], quality) for claim in claims])

    # Group similar claims
    claim_groups = cluster_similar_claims(all_claims)

    # Calculate consensus strength
    consensus_items = []
    for group in claim_groups:
        support_count = len(set([claim[1] for claim in group]))  # Unique workers
        avg_quality = mean([claim[2] for claim in group])
        consensus_strength = support_count / len(worker_results)

        consensus_items.append({
            "claim": group[0][0],
            "supporters": support_count,
            "strength": consensus_strength,
            "quality": avg_quality
        })

    # Generate synthesis
    return format_consensus_report(consensus_items)
```

### Example Output

```markdown
# Consensus Analysis: Research Proposal Evaluation

## Strong Consensus (≥70% agreement)

### Finding 1: Methodology is Sound
- **Support**: 4/5 workers
- **Confidence**: High (avg quality: 87/100)
- **Evidence**:
  - Worker 1: "Experimental design follows best practices"
  - Worker 2: "Statistical approach is rigorous"
  - Worker 3: "Controls are well-defined"
  - Worker 4: "Sample size calculation is appropriate"

### Finding 2: Budget is Underestimated
- **Support**: 5/5 workers (unanimous)
- **Confidence**: Very High (avg quality: 91/100)
- **Evidence**:
  - Worker 1: "Personnel costs seem low for 3-year project"
  - Worker 2: "Equipment budget doesn't account for maintenance"
  ...

## Moderate Consensus (40-69% agreement)

### Finding 3: Novelty Assessment
- **Support**: 3/5 workers
- **Confidence**: Medium (avg quality: 74/100)
- **Perspective A** (3 workers): "Incremental contribution to field"
- **Perspective B** (2 workers): "Novel methodology justifies funding"
- **Resolution**: Novelty depends on evaluation criteria; methodology is novel but domain application is incremental

## Unique Insights (single worker)

### Worker 5: Ethical Considerations
"Proposal lacks discussion of data privacy implications given GDPR requirements"
- **Note**: Not mentioned by other workers but valid concern
- **Recommendation**: Request clarification from PI

## Unresolved Disagreements

### Timeline Feasibility
- **Worker 1**: "3 years is adequate" (Quality: 82)
- **Worker 4**: "Needs 4 years minimum" (Quality: 89)
- **Analysis**: Disagreement stems from different assumptions about recruitment time
- **Recommendation**: Seek external expert opinion
```

---

## Strategy 3: Iterative Integration (Sequential Dependencies)

### When to Use
- Tasks with dependency chains
- Each step builds on previous
- Sequential pipeline execution
- Coherent narrative flow required

### Best For
- Multi-stage research workflows
- Progressive refinement tasks
- Data transformation pipelines
- Hierarchical analysis

### Approach

**Phase 1: Respect Dependency Order**
- Process results in dependency order
- Each integration step incorporates previous results

**Phase 2: Build Cumulative Output**
- Start with first worker output as base
- Integrate subsequent workers incrementally
- Maintain coherent narrative thread

**Phase 3: Ensure Continuity**
- Check for logical flow between stages
- Resolve inconsistencies introduced at each stage
- Final pass for coherence

### Implementation

```python
def iterative_integration_strategy(worker_results, task_plan):
    """Integrate sequential worker results maintaining flow."""

    # Sort by dependency order
    execution_order = task_plan["execution_order"]
    ordered_results = sorted(worker_results,
                            key=lambda r: execution_order.index(r["task_id"]))

    # Start with first result as base
    integrated = ordered_results[0]["output"]

    # Iteratively integrate subsequent results
    for i, result in enumerate(ordered_results[1:], start=1):
        integrated = merge_sequential_output(
            previous=integrated,
            current=result["output"],
            stage=i,
            context=f"Integrating {result['task_id']}"
        )

    return {
        "synthesis_output": integrated,
        "method": "iterative_integration",
        "stages": len(ordered_results)
    }
```

### Example Output

```markdown
# Sequential Analysis: Market Research → Strategy → Recommendations

## Stage 1: Market Analysis (Worker 1)

The SaaS market for project management tools is valued at $6.8B (2024),
growing at 13% CAGR. Three dominant players control 68% market share:
- Asana: 28%
- Monday.com: 22%
- Trello: 18%

Key market gaps identified:
1. No solution optimized for remote-first teams <50 employees
2. Integration complexity remains top complaint (42% of users)
3. Pricing models don't align with usage patterns for small teams

---

## Stage 2: Competitive Strategy (Worker 2)

*Building on Market Analysis findings:*

Given the identified market gap for small remote-first teams, a differentiated
strategy emerges:

**Target Segment**: Remote-first companies with 10-50 employees
- Market size: $850M (12.5% of total market)
- Current solutions overserve this segment (too complex)
- Willingness to pay: $8-12 per user/month

**Competitive Positioning**:
- **vs Asana**: Simpler onboarding, half the features → 60% of price
- **vs Monday.com**: Native async collaboration vs real-time focus
- **vs Trello**: More structure for distributed teams

**Differentiation Drivers**:
1. **Async-first design** (addresses remote team pain)
   - Leverages Market Analysis finding #1
2. **Pre-built integrations** (addresses Market Analysis finding #2)
   - Focus on top 10 tools only (vs 100+ for incumbents)
3. **Usage-based pricing** (addresses Market Analysis finding #3)
   - Pay per active project, not per seat

---

## Stage 3: Go-to-Market Recommendations (Worker 3)

*Synthesizing Market Analysis + Competitive Strategy:*

### Recommended Launch Strategy

**Phase 1: Beta (Months 1-3)**
- Target: 50 remote-first companies (10-30 employees)
- Focus: Validate async-first workflows resonate
- Success metric: 70% of beta users active after month 2

**Phase 2: Paid Launch (Months 4-6)**
- Positioning: "The project management tool built for async teams"
- Pricing: $10/user/month (middle of $8-12 range from competitive analysis)
- Channel: Product Hunt + remote work communities

**Phase 3: Scale (Months 7-12)**
- Expand integrations based on beta feedback
- Introduce usage-based pricing tier
- Target 1,000 paying users by month 12

### Budget Allocation (informed by market size)

$850M addressable market suggests:
- Marketing: $200k (customer acquisition focus)
- Product: $150k (integration development - addresses key complaint)
- Sales: $100k (outbound to 10-50 employee segment)

### Risk Mitigation

Risks identified in earlier stages:
1. **Market saturation concern** (from Market Analysis)
   - Mitigation: Async-first positioning creates new category
2. **Integration complexity** (from Competitive Strategy)
   - Mitigation: Launch with 10 integrations only, add based on data

---

**Synthesis Note**: This integrated analysis flows from market insights →
strategic positioning → tactical recommendations, with each stage building
on and referencing prior findings.
```

---

## Strategy 4: Evidence Database (Citation-Heavy)

### When to Use
- Literature reviews or fact-checking
- High citation density (>5 citations per worker)
- Need precise evidence tracking
- Comparison tasks requiring source attribution

### Best For
- Academic literature synthesis
- Novelty analysis with prior art
- Regulatory compliance checks
- Source comparison with citations

### Approach

**Phase 1: Extract Evidence Database**
- Parse all citations from worker outputs
- Build structured evidence DB with sources

**Phase 2: Generate Evidence-Based Synthesis**
- Group evidence by theme
- Maintain precise citation tracking
- Avoid claim repetition across sources

**Phase 3: Ensure Citation Integrity**
- Every claim links to specific evidence
- No evidence-free assertions
- Source attribution clear

### Implementation

```python
def evidence_database_strategy(worker_results, evaluation_results):
    """Build evidence-based synthesis with precise citations."""

    # Extract all evidence with citations
    evidence_db = []
    for result in worker_results:
        citations = extract_citations(result["output"])
        for citation in citations:
            evidence_db.append({
                "claim": citation["claim"],
                "source": citation["source"],
                "worker_id": result["worker_id"],
                "context": citation["context"]
            })

    # Group evidence by theme
    themes = cluster_evidence_by_theme(evidence_db)

    # Generate synthesis with citations
    synthesis = "# Evidence-Based Synthesis\n\n"

    for theme, evidence_items in themes.items():
        synthesis += f"## {theme}\n\n"
        synthesis += synthesize_evidence_for_theme(evidence_items)
        synthesis += "\n\n"

    # Add evidence database appendix
    synthesis += "\n## Evidence Database\n\n"
    synthesis += format_evidence_table(evidence_db)

    return synthesis
```

### Example Output

```markdown
# Literature Synthesis: Deep Learning for Medical Imaging

## Theme 1: Diagnostic Accuracy

Deep learning models have achieved radiologist-level accuracy in multiple
diagnostic tasks. For pneumonia detection, CheXNet achieved 0.927 AUC,
comparable to radiologists' 0.923 [Rajpurkar et al., 2017, Nature].
Similarly, in diabetic retinopathy screening, models reached 0.99 sensitivity
and 0.98 specificity [Gulshan et al., 2016, JAMA].

However, performance varies by disease prevalence. Low-prevalence conditions
show reduced accuracy: brain tumor detection achieved only 0.87 AUC in
community settings vs 0.94 in specialized centers [Smith et al., 2020,
Radiology].

**Evidence Summary**:
- 3 studies report >0.90 AUC for common conditions
- 2 studies show degradation in low-prevalence settings
- All studies use retrospective data (no prospective validation yet)

---

## Theme 2: Generalization Challenges

Models trained on one institution often fail to generalize. Cross-institution
validation showed AUC drops of 0.15-0.25 points [Zhang et al., 2019, Nature Med].
Primary factors include:

1. **Scanner Variation** [Chen et al., 2020, Medical Imaging]:
   - GE vs Siemens scanners: 0.18 AUC drop
   - Mitigation: Domain adaptation reduces gap to 0.07

2. **Population Differences** [Lee et al., 2021, AI in Medicine]:
   - Asian vs Western datasets: 0.22 AUC drop
   - Diverse training data essential

**Evidence Summary**:
- 5 studies document generalization failures
- 2 studies propose mitigation strategies (domain adaptation, diverse data)
- No studies achieve zero performance degradation across institutions

---

## Evidence Database

| Claim | Source | Type | Worker |
|-------|--------|------|--------|
| CheXNet: 0.927 AUC pneumonia detection | Rajpurkar et al., 2017, Nature | Diagnostic Accuracy | Worker 2 |
| Radiologist: 0.923 AUC pneumonia detection | Rajpurkar et al., 2017, Nature | Diagnostic Accuracy | Worker 2 |
| Diabetic retinopathy: 0.99 sensitivity | Gulshan et al., 2016, JAMA | Diagnostic Accuracy | Worker 1 |
| Brain tumor: 0.87 AUC (community) | Smith et al., 2020, Radiology | Prevalence Effect | Worker 3 |
| Brain tumor: 0.94 AUC (specialized) | Smith et al., 2020, Radiology | Prevalence Effect | Worker 3 |
| Cross-institution drop: 0.15-0.25 AUC | Zhang et al., 2019, Nature Med | Generalization | Worker 4 |
| Scanner variation: 0.18 AUC drop | Chen et al., 2020, Medical Imaging | Technical Factor | Worker 5 |
| Domain adaptation: 0.07 AUC gap | Chen et al., 2020, Medical Imaging | Mitigation | Worker 5 |
| Population difference: 0.22 AUC drop | Lee et al., 2021, AI in Medicine | Demographic Factor | Worker 4 |

**Citation Integrity**: All 9 claims traced to original sources with worker attribution.
```

---

## Strategy Comparison

| Strategy | Parallelization | Citation Tracking | Consensus Building | Use Case |
|----------|----------------|-------------------|-------------------|----------|
| **Aggregation** | High | Low | None | Independent analyses |
| **Consensus** | High | Medium | High | Multiple perspectives on same content |
| **Iterative** | None | Medium | Low | Sequential pipelines |
| **Evidence DB** | High | Very High | Medium | Citation-heavy research |

---

## Synthesis Best Practices

### 1. Respect Worker Quality Scores
- Only use ACCEPT (>80) and FLAG (60-80) workers
- Exclude REJECT (<60) workers
- Weight higher-quality outputs more in consensus

### 2. Maintain Traceability
- Always attribute findings to specific workers
- Preserve worker IDs in synthesis
- Enable readers to trace back to sources

### 3. Avoid Information Loss
- Unique insights from single workers still valuable
- Don't discard minority perspectives without justification
- Flag disagreements rather than hiding them

### 4. Use AI for Complex Synthesis
- Delegate synthesis to high-complexity worker AI
- Provide complete context (all worker outputs + strategy)
- Request structured output format

### 5. Quality Check Synthesis
- Ensure no hallucinations introduced during synthesis
- Verify all citations from workers preserved
- Check for logical contradictions

### 6. Provide Synthesis Metadata
- Document which strategy was used and why
- Report how many workers contributed
- Note any excluded workers and reasons

---

## Common Synthesis Anti-Patterns

### Anti-Pattern 1: Ignoring Quality Scores
**Bad**: Include all worker outputs regardless of quality
**Good**: Filter to accept/flag only, weight by quality scores

### Anti-Pattern 2: Cherry-Picking Evidence
**Bad**: Select only evidence supporting desired conclusion
**Good**: Represent all findings, note contradictions

### Anti-Pattern 3: Losing Attribution
**Bad**: "The analysis shows that..."
**Good**: "Worker 3 found that... while Worker 5 noted..."

### Anti-Pattern 4: Wrong Strategy for Task
**Bad**: Use aggregation for overlapping analyses (should use consensus)
**Good**: Select strategy based on task characteristics

---

## Synthesis Workflow Summary

```
1. Filter workers by quality gate (exclude rejected)
2. Select synthesis strategy (automated based on task)
3. Extract relevant information (claims, citations, themes)
4. Combine according to strategy
5. Generate synthesis output
6. Quality check (no hallucinations, citations preserved)
7. Add synthesis metadata
8. Return final integrated result
```

This ensures high-quality synthesis that preserves information while creating coherent, actionable outputs.
