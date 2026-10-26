# Quick Start Guide

Get started with Agent-Orchestrator in 5 minutes.

## 1. Install Prerequisites (2 minutes)

### Required
```bash
# Install at least one AI CLI
pip install gemini-cli          # Recommended

# Verify Docker (required for Gemini)
docker --version
```

### Optional Pre-pull (saves time on first run)
```bash
docker pull us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox:0.23.0
```

## 2. Verify Installation (30 seconds)

```bash
cd .claude/skills/agent-orchestrator
gemini --version
python scripts/orchestrator.py --help
```

## 3. Run Your First Task (2 minutes)

### Example: Analyze multiple files in parallel

```bash
python scripts/orchestrator.py \
  --request "Analyze security vulnerabilities in auth.py, database.py, and api.py"
```

**What happens:**
1. Orchestrator analyzes your request (Phase 0)
2. Breaks it into 3 subtasks (Phase 1-2)
3. Spawns 3 parallel workers (Phase 4)
4. Evaluates quality (Phase 5)
5. Synthesizes results (Phase 6)
6. Generates final report (Phase 8)

**Output location:** `<project_root>/Temp/agent-orchestrator/`

**Check results:**
```bash
cat ./Temp/agent-orchestrator/synthesis_result.md
```

## 4. Choose Your Tier

### When to use which tier?

**Use Tier 4 (Full Orchestrator)** - *Current default, works now:*
```bash
python scripts/orchestrator.py --request "Your complex analysis task"
```
- ✅ Complex analysis with unclear decomposition
- ✅ Need intelligent synthesis and quality control
- ✅ High-stakes decisions requiring iteration

**Use Tier 1 (Simple Parallel)** - *In development:*
> ⚠️ **Note**: `simple_parallel.py` not yet implemented. Use Tier 4 instead.

For straightforward parallel tasks once available:
```bash
python scripts/simple_parallel.py --tasks "task1, task2, task3"
```

**Quick Decision:**
```
Can you list all subtasks clearly? → NO: Use Tier 4 ✓
Need intelligent synthesis? → YES: Use Tier 4 ✓
High-stakes critical decision? → YES: Use Tier 4 ✓
```

## 5. Monitor Progress

### Check current state
```bash
python scripts/state_manager.py --action status
```

### View detailed phase outputs
```bash
ls -lh ./Temp/agent-orchestrator/
cat ./Temp/agent-orchestrator/.orchestrator_state.json
```

### View worker outputs
```bash
ls ./Temp/agent-orchestrator/worker_results/
```

## Common First-Time Issues

### Issue: "Worker timeout after 180s"
**Cause:** Docker image pull on first run
**Solution:** Wait 5-10 minutes or pre-pull image (see step 1)

### Issue: "No workers available"
**Cause:** AI CLI not installed
**Solution:** Install gemini CLI: `pip install gemini-cli`

### Issue: "Docker not found"
**Cause:** Docker not installed
**Solution:** Install Docker Desktop from docker.com

## Next Steps

### Learn more about the full workflow
- **[SKILL.md](../SKILL.md)** - Complete skill reference and tier selection
- **[orchestration-methodology.md](orchestration-methodology.md)** - Deep dive into 9-phase workflow

### See practical examples
- **[examples/book-comparison-example.md](examples/book-comparison-example.md)** - 10-book comparison
- **[examples/parallel-analysis-example.md](examples/parallel-analysis-example.md)** - Code security analysis
- **[examples/sequential-synthesis-example.md](examples/sequential-synthesis-example.md)** - Sequential dependencies

### Explore advanced features
- **[meta-cognitive-iteration.md](meta-cognitive-iteration.md)** - Automatic quality improvement
- **[synthesis-methods.md](synthesis-methods.md)** - Advanced result combination
- **[delegation-strategies.md](delegation-strategies.md)** - Worker selection optimization

## Troubleshooting

For detailed troubleshooting, see **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

**Quick fixes:**
```bash
# Clear state and start fresh
python scripts/state_manager.py --action clear

# Check Docker status
docker ps

# Test worker directly
echo "Test prompt" | gemini
```

## Cost Estimation

**Typical orchestration (5 workers):**
- Gemini: ~$0.005-0.05 per orchestration
- Claude: ~$0.05-0.50 per orchestration
- Average: ~$0.25 per orchestration

See [SKILL.md Limitations](../SKILL.md#limitations) for detailed cost breakdown.

---

**Ready to start?** Run your first analysis:

```bash
python scripts/orchestrator.py \
  --request "Summarize the key features of this codebase"
```

Results will be in `./Temp/agent-orchestrator/synthesis_result.md`
