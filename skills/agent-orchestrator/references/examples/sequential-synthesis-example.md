# Example: Sequential Research Pipeline with Dependencies

This example demonstrates sequential task execution where each worker depends on the output of the previous worker, using iterative integration synthesis.

## User Request

```
"Conduct a market analysis for a new SaaS product:
1. First, identify market size and growth trends
2. Then, analyze competitive landscape using the market data
3. Finally, develop go-to-market recommendations based on the analysis"
```

## Phase 0: Request Understanding

**Sequential-Thinking Analysis**:
```json
{
  "goal": "Comprehensive market analysis leading to GTM strategy",
  "success_criteria": [
    "Market size and trends quantified",
    "Competitive positioning identified",
    "Actionable GTM recommendations provided",
    "Each stage builds on previous findings"
  ],
  "requirements": [
    "Multi-stage analysis (market → competition → strategy)",
    "Sequential dependency (each needs previous output)",
    "Quantitative data where possible",
    "Strategic recommendations"
  ],
  "constraints": [
    "3-stage pipeline",
    "Each stage depends on previous"
  ],
  "output_format": "Integrated strategic report",
  "task_type": "analysis",
  "complexity": "high"
}
```

## Phase 1: Task Decomposition

**AI-Generated Task Plan**:
```json
{
  "subtasks": [
    {
      "id": "market_analysis",
      "description": "Identify market size, growth trends, and key segments for project management SaaS",
      "complexity": "high",
      "output_format": "Quantitative market report with segments, size, growth rates",
      "worker_type": "analysis",
      "data_context": "Project management SaaS market, 2024",
      "success_criteria": [
        "Total addressable market (TAM) calculated",
        "Growth rate with 3-year projection",
        "Market segmentation by company size/industry",
        "Key market gaps identified"
      ]
    },
    {
      "id": "competitive_analysis",
      "description": "Analyze competitive landscape using market segments from stage 1",
      "complexity": "high",
      "output_format": "Competitive positioning analysis with differentiation opportunities",
      "worker_type": "analysis",
      "data_context": "Major players in identified market segments",
      "dependencies": ["market_analysis"],
      "success_criteria": [
        "Top 3-5 competitors identified per segment",
        "Competitive positioning mapped",
        "Differentiation opportunities found",
        "White space analysis"
      ]
    },
    {
      "id": "gtm_strategy",
      "description": "Develop go-to-market strategy based on market and competitive analysis",
      "complexity": "high",
      "output_format": "Strategic GTM plan with timeline, budget, channels",
      "worker_type": "synthesis",
      "data_context": "Market data + competitive analysis from stages 1-2",
      "dependencies": ["market_analysis", "competitive_analysis"],
      "success_criteria": [
        "Target segment selected with justification",
        "Positioning strategy defined",
        "GTM tactics with timeline",
        "Budget allocation recommendations"
      ]
    }
  ],
  "dependencies": {
    "competitive_analysis": ["market_analysis"],
    "gtm_strategy": ["market_analysis", "competitive_analysis"]
  },
  "execution_order": ["market_analysis", "competitive_analysis", "gtm_strategy"],
  "reasoning": "Sequential pipeline: each stage builds on previous. Market data → Competitive context → Strategic recommendations."
}
```

## Phase 2: Parallelization Strategy

**Algorithm Application**:
```python
parallel_tasks = 0  # All tasks have dependencies
sequential_tasks = 3
has_heavy_dependencies = True  # 3 tasks with sequential chain

# Apply algorithm:
# has_dependencies = True → return 1 (sequential execution)

worker_count = 1
```

**Parallelization Config**:
```json
{
  "worker_count": 1,
  "parallel_groups": [],
  "sequential_tasks": [
    "market_analysis",
    "competitive_analysis",
    "gtm_strategy"
  ],
  "parallel_tasks_count": 0,
  "sequential_tasks_count": 3,
  "avg_complexity": "high"
}
```

**Note**: Sequential execution required due to dependencies.

## Phase 3: Worker Prompt Generation

**Prompt for Worker 1 - Stage 1** (market_analysis):

```
=== SYSTEM CONTEXT ===
You are Worker 1 in a sequential 3-stage market research pipeline.

Your role: Conduct foundational market analysis for project management SaaS.

Coordination mode: SEQUENTIAL (Stage 1 of 3)
- Your output will be used by Worker 2 (Competitive Analysis)
- Worker 2 will use your market segments and gap analysis
- Worker 3 will build GTM strategy on your + Worker 2's findings

Total orchestration goal: Develop comprehensive GTM strategy from market data

=== TASK DEFINITION ===
TASK ID: market_analysis
DESCRIPTION: Identify market size, growth trends, and key segments

COMPLEXITY: High (requires market research, quantitative analysis, trend forecasting)

EXPECTED OUTPUT FOR DOWNSTREAM WORKERS:
- Total Addressable Market (TAM) in $ with methodology
- Market segmentation (by company size, industry, use case)
- Growth projections (3-year CAGR with justification)
- Market gaps/opportunities requiring minimal competition
[... rest of prompt ...]
```

**Prompt for Worker 2 - Stage 2** (competitive_analysis):

```
=== SYSTEM CONTEXT ===
You are Worker 2 in a sequential 3-stage market research pipeline.

Your role: Competitive landscape analysis using market data from Worker 1.

Coordination mode: SEQUENTIAL (Stage 2 of 3)
- You are receiving output from Worker 1 (Market Analysis)
- Your output will be used by Worker 3 (GTM Strategy)
- Build on Worker 1's findings, especially market segments and gaps

INPUT FROM PREVIOUS WORKER (Worker 1):
[Market analysis output will be inserted here]

YOUR OUTPUT WILL BE USED BY:
Worker 3 expects competitive positioning analysis that identifies differentiation opportunities within the market segments you identify.
[... rest of prompt ...]
```

**Prompt for Worker 3 - Stage 3** (gtm_strategy):

```
=== SYSTEM CONTEXT ===
You are Worker 3 in a sequential 3-stage market research pipeline.

Your role: Synthesize market + competitive data into GTM strategy.

Coordination mode: SEQUENTIAL (Stage 3 of 3 - FINAL)
- You are receiving outputs from Worker 1 (Market Analysis) and Worker 2 (Competitive Analysis)
- Your output is the final deliverable
- Synthesize all prior findings into actionable GTM plan

INPUT FROM PREVIOUS WORKERS:

**From Worker 1 (Market Analysis)**:
[Market analysis output will be inserted here]

**From Worker 2 (Competitive Analysis)**:
[Competitive analysis output will be inserted here]

YOUR OUTPUT IS THE FINAL SYNTHESIS:
Integrate insights from both previous stages into a cohesive GTM strategy.
[... rest of prompt ...]
```

## Phase 4: Sequential Worker Execution

**Execution Timeline**:
```
T+0s:    Worker 1 starts (market_analysis)
T+87s:   Worker 1 completes
T+87s:   Worker 2 starts (competitive_analysis) - receives Worker 1 output
T+169s:  Worker 2 completes
T+169s:  Worker 3 starts (gtm_strategy) - receives Worker 1 + Worker 2 outputs
T+245s:  Worker 3 completes

Total execution time: 245 seconds (sequential, cannot parallelize)
```

## Phase 5: Response Evaluation

**Worker 1 Evaluation** (market_analysis):
- **Layer 1**: 100/100 (well-structured)
- **Layer 2**: 100/100 (all criteria met)
- **Layer 3**: 95/100 (minor: 1 unsupported comparison)
- **Final**: 98.5/100 → ACCEPT

**Worker 2 Evaluation** (competitive_analysis):
- **Layer 1**: 100/100 (clear structure)
- **Layer 2**: 100/100 (used Worker 1 data effectively)
- **Layer 3**: 100/100 (all claims supported)
- **Final**: 100/100 → ACCEPT

**Worker 3 Evaluation** (gtm_strategy):
- **Layer 1**: 100/100 (professional report format)
- **Layer 2**: 95/100 (minor: budget could be more detailed)
- **Layer 3**: 100/100 (integrated prior findings well)
- **Final**: 97.5/100 → ACCEPT

**Overall Quality**: 98.7/100 (excellent)

## Phase 6: Result Synthesis

**Strategy Selected**: Iterative Integration (sequential dependencies)

**Synthesis Approach**:
The synthesis maintains the logical flow from market data → competitive context → strategic recommendations, integrating outputs while preserving the narrative arc.

**Integrated Output**:

```markdown
# Go-to-Market Strategy: Project Management SaaS

*Integrated analysis synthesizing market research, competitive landscape, and strategic recommendations*

---

## Stage 1: Market Analysis

### Market Size & Opportunity

The global project management SaaS market was valued at **$6.8 billion in 2024**,
growing at a **13% CAGR** with projected value of **$9.6 billion by 2027**.

**Methodology**: Bottom-up analysis
- 14 million companies worldwide use project management software
- Average spend: $485/year per company
- TAM = 14M × $485 = $6.8B

### Market Segmentation

Three distinct segments emerged:

| Segment | Company Size | TAM | Growth | Characteristics |
|---------|--------------|-----|--------|-----------------|
| Enterprise | 1,000+ employees | $3.4B | 8% | Complex workflows, integrations |
| Mid-Market | 100-999 employees | $2.6B | 12% | Scalability + simplicity balance |
| SMB | 10-99 employees | $850M | 22% | Price-sensitive, ease of use critical |

**Key Finding**: SMB segment shows highest growth (22%) but smallest TAM,
suggesting emerging market with significant headroom.

### Market Gaps Identified

1. **Remote-First Optimization** (identified in 42% of buyer interviews)
   - Current tools designed for co-located teams
   - Async collaboration features underdeveloped

2. **Integration Simplicity** (top complaint: 38% of users)
   - Enterprise tools offer 100+ integrations
   - SMBs need 5-10 but simpler setup

3. **Usage-Based Pricing** (requested by 31% of SMB buyers)
   - Per-seat pricing doesn't match usage patterns
   - Pay-per-project model would better align value

---

## Stage 2: Competitive Analysis

*Building on market segments and gaps identified in Stage 1...*

### Competitive Landscape by Segment

Using the market segmentation from Stage 1, competitive analysis reveals distinct
positioning in each segment:

**SMB Segment Analysis** (focus on 22% growth segment):

| Competitor | Market Share | Positioning | Price | Strengths | Gaps |
|------------|--------------|-------------|-------|-----------|------|
| Asana | 28% | All-in-one platform | $13.49/user/mo | Brand, features | Complex for SMBs |
| Monday.com | 22% | Visual workflows | $12/user/mo | UI/UX | Learning curve |
| Trello | 18% | Kanban simplicity | $6/user/mo | Easy to start | Lacks structure |
| ClickUp | 12% | Customization | $9/user/mo | Flexibility | Overwhelming |

**White Space Analysis**:

Mapping competitors against Stage 1 market gaps:

```
           Integration Simplicity
                  Low ←→ High
        ┌─────────────┬─────────────┐
Remote  │             │   ASANA     │
First   │  [GAP]      │   MONDAY    │  High
Focus   │             │   CLICKUP   │
        ├─────────────┼─────────────┤
        │  TRELLO     │             │
        │             │             │  Low
        └─────────────┴─────────────┘
```

**Key Finding**: No competitor addresses remote-first + integration simplicity
simultaneously. This white space aligns with SMB segment needs from Stage 1.

### Differentiation Opportunity

Based on Stage 1 gaps and competitive positioning:

**Positioning Strategy**: "The project management tool built for async-first remote teams"

**Differentiation Drivers**:
1. **Async-first design** (addresses Stage 1 Gap #1: Remote optimization)
   - No competitor explicitly optimizes for async workflows
   - Aligns with 42% buyer need from market research

2. **Simple integrations** (addresses Stage 1 Gap #2)
   - Focus on top 10 tools (vs 100+ for Asana)
   - One-click setup vs complex configuration

3. **Usage-based pricing** (addresses Stage 1 Gap #3)
   - Pay per active project, not per seat
   - Aligns with 31% SMB buyer request

---

## Stage 3: Go-to-Market Strategy

*Synthesizing market data (Stage 1) and competitive insights (Stage 2)...*

### Target Segment Selection

**Selected Segment**: SMB (10-99 employees), Remote-First Focus

**Justification**:
- **High growth**: 22% CAGR (from Stage 1) vs 8% for Enterprise
- **White space**: No direct competitor (from Stage 2 positioning map)
- **Market size**: $850M TAM provides adequate headroom
- **Alignment**: Gaps #1-3 from Stage 1 all apply to this segment

### Positioning Strategy

**Value Proposition** (derived from competitive differentiation):
"Simple project management designed for distributed teams. Async-first workflows,
essential integrations, and pricing that matches how you work."

**Positioning vs Competitors** (using Stage 2 landscape):
- **vs Asana**: 1/4 the features, 1/2 the price, 10x easier onboarding
- **vs Monday.com**: Async-native vs real-time focus
- **vs Trello**: More structure for distributed teams
- **vs ClickUp**: Less overwhelming, faster time-to-value

### Go-to-Market Tactics

**Phase 1: Beta Launch** (Months 1-3)

*Target*: 50 remote-first companies (10-30 employees)
- **Channel**: Direct outreach to remote-first communities (RemoteOK, We Work Remotely)
- **Offer**: Free beta + feature influence
- **Success Metric**: 70% retention after month 2

*Budget*: $50k
- Community partnerships: $20k
- Beta user incentives: $15k
- Product iteration: $15k

**Phase 2: Product Hunt Launch** (Month 4)

*Target*: 500 signups in week 1
- **Positioning**: Lead with async-first differentiation
- **Pricing**: $10/user/month (middle of $6-13 range from Stage 2 competitive analysis)
- **Success Metric**: 25% conversion to paid

*Budget*: $75k
- Product Hunt sponsorship: $30k
- Launch content creation: $25k
- Early adopter discounts: $20k

**Phase 3: Scale** (Months 5-12)

*Target*: 1,000 paying teams by month 12
- **Channel Mix**:
  - Content marketing: Async work best practices (60% budget)
  - Paid search: "remote project management" (25% budget)
  - Partnerships: Integration partners (15% budget)

- **Expansion Strategy**:
  - Month 6: Introduce usage-based pricing tier (addresses Gap #3)
  - Month 9: Expand integrations to 20 tools based on user data

*Budget*: $275k
- Content marketing: $165k
- Paid acquisition: $69k
- Integration development: $41k

### Budget Summary

**Total Year 1 GTM Budget**: $400k

**Allocation** (informed by $850M TAM from Stage 1):
- Customer acquisition: $284k (71%)
- Product development: $56k (14%)
- Partnerships: $60k (15%)

**CAC Target**: $284k ÷ 1,000 customers = **$284 per customer**
**LTV Estimate**: $10/user × 15 avg users × 24 months = **$3,600**
**LTV:CAC Ratio**: 12.7x (healthy for SaaS)

### Risk Mitigation

**Risk 1: Async-first positioning too narrow**
- *Source*: Stage 1 showed 42% interest, not majority
- *Mitigation*: Position as async-capable, not async-only; support both workflows

**Risk 2: Incumbent response**
- *Source*: Stage 2 revealed Asana/Monday have resources to copy features
- *Mitigation*: Build brand in async/remote community before launch (Phase 1 beta)

**Risk 3: Integration complexity**
- *Source*: Stage 1 Gap #2 is also our differentiator
- *Mitigation*: Launch with 10 integrations proven in beta; add based on data

### Success Metrics

**Month 3** (End of Beta):
- 50 beta users enrolled
- 35+ active users (70% retention)
- Async features validated (70%+ usage)

**Month 6** (Post-Launch):
- 250 paying customers
- $2,500 MRR
- 20% month-over-month growth

**Month 12** (Scale Phase):
- 1,000 paying customers
- $15,000 MRR
- CAC ≤ $284
- Net Promoter Score ≥ 40

---

## Synthesis Notes

This integrated analysis demonstrates sequential dependency resolution:

1. **Stage 1 (Market Analysis)** identified:
   - $850M SMB segment with 22% growth
   - 3 specific market gaps (remote-first, integrations, pricing)

2. **Stage 2 (Competitive Analysis)** used Stage 1 findings to:
   - Map competitors against identified segments
   - Discover white space at intersection of remote-first + simple integrations
   - Validate differentiation opportunities

3. **Stage 3 (GTM Strategy)** synthesized both to:
   - Select target segment (SMB) based on growth + white space
   - Define positioning against specific competitors using gap analysis
   - Allocate budget proportional to TAM
   - Set success metrics grounded in market data

**Integration Quality**: Each stage references and builds upon prior findings,
creating a coherent narrative from market data → competitive context →
strategic recommendations.

**Total Analysis Time**: 245 seconds (3 sequential stages)
**Synthesis Strategy**: Iterative Integration
**Quality**: 98.7/100 (all workers accepted)
```

## Key Takeaways

1. **Sequential Execution**: Required for dependencies (can't parallelize)
2. **Strategy Selection**: Iterative Integration automatically chosen (sequential tasks)
3. **Context Propagation**: Each worker receives previous outputs as input
4. **Narrative Flow**: Synthesis maintains logical progression through stages
5. **Cross-References**: Stage 2 explicitly builds on Stage 1 findings
6. **Coherent Output**: Final report reads as integrated analysis, not disconnected parts
7. **Quality Consistency**: All 3 workers scored >95% (high-quality pipeline)

## Comparison to Parallel Example

| Dimension | Sequential Example | Parallel Example |
|-----------|-------------------|------------------|
| **Worker Count** | 1 (sequential) | 5 (parallel) |
| **Execution Time** | 245s | 134s |
| **Speedup** | None (can't parallelize) | 3.4x |
| **Dependencies** | Heavy (linear chain) | None (independent) |
| **Synthesis** | Iterative Integration | Aggregation |
| **Complexity** | High (each builds on previous) | Medium (independent tasks) |
| **Output Type** | Coherent narrative | Compiled findings |

This example demonstrates how the orchestrator handles sequential dependencies, propagates context between stages, and uses iterative integration synthesis to maintain narrative flow.
