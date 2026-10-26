"""
Result Synthesizer for Agent Orchestrator
Multiple synthesis strategies for combining worker outputs.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ResultSynthesizer:
    """Synthesizes results from multiple workers using context-dependent strategies."""

    def __init__(self, skill_dir: Path):
        """
        Initialize ResultSynthesizer.

        Args:
            skill_dir: Path to skill root directory
        """
        self.skill_dir = skill_dir

    def synthesize_results(self,
                          worker_results: List[Dict[str, Any]],
                          evaluation_results: Dict[str, Any],
                          task_plan: Dict[str, Any],
                          request_analysis: Dict[str, Any],
                          worker_spawner) -> Dict[str, Any]:
        """
        Synthesize worker results using appropriate strategy.

        Phase 6: Result Synthesis

        Args:
            worker_results: List of worker outputs
            evaluation_results: Evaluation results
            task_plan: Task plan
            request_analysis: Request analysis
            worker_spawner: WorkerSpawner for delegating synthesis

        Returns:
            Synthesis result
        """
        strategy = self._select_synthesis_strategy(
            worker_results,
            task_plan,
            request_analysis
        )

        print(f"Selected synthesis strategy: {strategy}")

        if strategy == "aggregation":
            synthesis = self._aggregation_strategy(
                worker_results, evaluation_results, worker_spawner
            )
        elif strategy == "consensus":
            synthesis = self._consensus_strategy(
                worker_results, evaluation_results, worker_spawner
            )
        elif strategy == "iterative":
            synthesis = self._iterative_integration_strategy(
                worker_results, evaluation_results, worker_spawner
            )
        elif strategy == "evidence_db":
            synthesis = self._evidence_database_strategy(
                worker_results, evaluation_results, worker_spawner
            )
        else:
            synthesis = self._aggregation_strategy(
                worker_results, evaluation_results, worker_spawner
            )

        synthesis["strategy_used"] = strategy
        synthesis["total_workers"] = len(worker_results)
        synthesis["accepted_workers"] = len([
            r for r in worker_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") == "accept"
        ])

        return synthesis

    def _select_synthesis_strategy(self,
                                   worker_results: List[Dict[str, Any]],
                                   task_plan: Dict[str, Any],
                                   request_analysis: Dict[str, Any]) -> str:
        """
        Select appropriate synthesis strategy based on task characteristics.

        Strategies:
        - aggregation: Independent tasks (e.g., book comparison)
        - consensus: Overlapping analysis requiring agreement
        - iterative: Sequential dependencies
        - evidence_db: Citation-heavy tasks

        Args:
            worker_results: Worker outputs
            task_plan: Task plan
            request_analysis: Request analysis

        Returns:
            Strategy name
        """
        task_type = request_analysis.get("task_type", "mixed")
        subtasks = task_plan.get("subtasks", [])
        dependencies = task_plan.get("dependencies", {})

        has_heavy_deps = sum(len(deps) for deps in dependencies.values()) > len(subtasks) * 0.3

        if has_heavy_deps:
            return "iterative"

        if task_type == "comparison":
            citation_count = sum(
                result.get("output", "").count("[") +
                result.get("output", "").count("(p.")
                for result in worker_results
            )
            if citation_count > len(worker_results) * 5:
                return "evidence_db"
            else:
                return "aggregation"

        if len(worker_results) > 3 and task_type in ["analysis", "evaluation"]:
            return "consensus"

        return "aggregation"

    def _aggregation_strategy(self,
                             worker_results: List[Dict[str, Any]],
                             evaluation_results: Dict[str, Any],
                             worker_spawner) -> Dict[str, Any]:
        """
        Aggregation strategy for independent tasks.

        Best for: Book comparison, parallel independent analyses

        Approach:
        - Collect all worker outputs
        - Organize by worker/task
        - Delegate to synthesis worker AI for integration
        """
        accepted_results = [
            r for r in worker_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") in ["accept", "flag"]
        ]

        synthesis_prompt = self._build_aggregation_prompt(accepted_results)

        synthesis_output = worker_spawner.call_worker(
            prompt=synthesis_prompt,
            complexity="high",
            context="Result aggregation synthesis"
        )

        return {
            "synthesis_output": synthesis_output,
            "method": "aggregation",
            "sources_included": len(accepted_results),
            "sources_excluded": len(worker_results) - len(accepted_results)
        }

    def _consensus_strategy(self,
                           worker_results: List[Dict[str, Any]],
                           evaluation_results: Dict[str, Any],
                           worker_spawner) -> Dict[str, Any]:
        """
        Consensus strategy for overlapping analyses.

        Best for: Multiple workers analyzing same content

        Approach:
        - Identify common findings
        - Resolve conflicts
        - Weight by quality scores
        """
        accepted_results = [
            r for r in worker_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") in ["accept", "flag"]
        ]

        scores = {
            r.get("worker_id"): evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("score", 70)
            for r in accepted_results
        }

        synthesis_prompt = self._build_consensus_prompt(accepted_results, scores)

        synthesis_output = worker_spawner.call_worker(
            prompt=synthesis_prompt,
            complexity="high",
            context="Consensus building synthesis"
        )

        return {
            "synthesis_output": synthesis_output,
            "method": "consensus",
            "sources_included": len(accepted_results),
            "quality_weighted": True
        }

    def _iterative_integration_strategy(self,
                                       worker_results: List[Dict[str, Any]],
                                       evaluation_results: Dict[str, Any],
                                       worker_spawner) -> Dict[str, Any]:
        """
        Iterative integration for sequential dependencies.

        Best for: Tasks with dependency chains

        Approach:
        - Process results in dependency order
        - Each iteration builds on previous
        - Final integrated output
        """
        sorted_results = sorted(
            worker_results,
            key=lambda r: r.get("task_id", "")
        )

        accepted_results = [
            r for r in sorted_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") in ["accept", "flag"]
        ]

        integrated = ""
        for i, result in enumerate(accepted_results):
            synthesis_prompt = self._build_iterative_prompt(
                current_result=result,
                previous_integration=integrated,
                step=i+1,
                total_steps=len(accepted_results)
            )

            integrated = worker_spawner.call_worker(
                prompt=synthesis_prompt,
                complexity="high",
                context=f"Iterative integration step {i+1}"
            )

        return {
            "synthesis_output": integrated,
            "method": "iterative_integration",
            "integration_steps": len(accepted_results)
        }

    def _evidence_database_strategy(self,
                                   worker_results: List[Dict[str, Any]],
                                   evaluation_results: Dict[str, Any],
                                   worker_spawner) -> Dict[str, Any]:
        """
        Evidence database strategy for citation-heavy tasks.

        Best for: Literature reviews, fact-checking, novelty analysis

        Approach:
        - Extract all evidence with citations
        - Build evidence database
        - Generate synthesis from evidence
        """
        accepted_results = [
            r for r in worker_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") in ["accept", "flag"]
        ]

        evidence_db = self._extract_evidence_database(accepted_results)

        synthesis_prompt = self._build_evidence_db_prompt(evidence_db, accepted_results)

        synthesis_output = worker_spawner.call_worker(
            prompt=synthesis_prompt,
            complexity="high",
            context="Evidence-based synthesis"
        )

        return {
            "synthesis_output": synthesis_output,
            "method": "evidence_database",
            "evidence_count": len(evidence_db),
            "sources_included": len(accepted_results)
        }

    def _build_aggregation_prompt(self, worker_results: List[Dict[str, Any]]) -> str:
        """Build prompt for aggregation synthesis."""
        worker_outputs = "\n\n---\n\n".join([
            f"**Worker {r.get('worker_id')}** (Task: {r.get('task_id')})\n\n{r.get('output', '')}"
            for r in worker_results
        ])

        return f"""You are synthesizing results from {len(worker_results)} independent workers.

Each worker completed an independent task. Your role is to aggregate their findings into a coherent report.

WORKER OUTPUTS:
{worker_outputs}

SYNTHESIS TASK:
1. Organize findings by worker/task
2. Create clear sections for each worker's contribution
3. Identify any cross-worker patterns or themes
4. Maintain traceability (attribute findings to workers)
5. Generate executive summary

OUTPUT FORMAT:
# Executive Summary
[Brief overview of all findings]

# Detailed Findings

## Worker 1: [Task description]
[Worker 1 findings]

## Worker 2: [Task description]
[Worker 2 findings]

[Continue for all workers...]

# Cross-Worker Insights
[Any patterns or themes across workers]

# Conclusion
[Final synthesis]"""

    def _build_consensus_prompt(self,
                                worker_results: List[Dict[str, Any]],
                                scores: Dict[str, float]) -> str:
        """Build prompt for consensus synthesis."""
        worker_outputs = "\n\n---\n\n".join([
            f"**Worker {r.get('worker_id')}** (Quality Score: {scores.get(r.get('worker_id'), 70)}/100)\n\n{r.get('output', '')}"
            for r in worker_results
        ])

        return f"""You are building consensus from {len(worker_results)} workers who analyzed overlapping content.

Workers may have different perspectives. Your task is to identify common ground and resolve conflicts.

WORKER OUTPUTS (with quality scores):
{worker_outputs}

CONSENSUS BUILDING:
1. Identify claims made by multiple workers (strong consensus)
2. Identify claims made by single workers (weak consensus)
3. Resolve contradictions (weight by quality scores)
4. Flag unresolved disagreements
5. Generate consensus report

OUTPUT FORMAT:
# Consensus Summary
[What workers agree on]

# Strong Consensus (multiple workers)
[Claims supported by 2+ workers]

# Weak Consensus (single workers)
[Claims from individual workers only]

# Contradictions Resolved
[How conflicts were resolved]

# Unresolved Disagreements
[Any remaining contradictions]"""

    def _build_iterative_prompt(self,
                               current_result: Dict[str, Any],
                               previous_integration: str,
                               step: int,
                               total_steps: int) -> str:
        """Build prompt for iterative integration."""
        return f"""You are performing iterative integration (Step {step} of {total_steps}).

PREVIOUS INTEGRATION:
{previous_integration if previous_integration else "This is the first step."}

CURRENT WORKER OUTPUT:
**Worker {current_result.get('worker_id')}** (Task: {current_result.get('task_id')})

{current_result.get('output', '')}

INTEGRATION TASK:
1. Review previous integrated content
2. Incorporate current worker's output
3. Resolve any conflicts or overlaps
4. Maintain coherent flow
5. Build incrementally toward final synthesis

OUTPUT:
Integrated content combining previous integration with current worker output."""

    def _build_evidence_db_prompt(self,
                                 evidence_db: List[Dict[str, Any]],
                                 worker_results: List[Dict[str, Any]]) -> str:
        """Build prompt for evidence database synthesis."""
        evidence_list = "\n".join([
            f"- {ev['claim']} [{ev['citation']}] (Worker: {ev['worker_id']})"
            for ev in evidence_db[:100]
        ])

        return f"""You are synthesizing findings from an evidence database.

EVIDENCE DATABASE ({len(evidence_db)} entries):
{evidence_list}

WORKER COUNT: {len(worker_results)}

SYNTHESIS TASK:
1. Organize evidence by themes/topics
2. Build arguments from evidence
3. Maintain precise citations
4. Identify evidence clusters
5. Generate evidence-based report

OUTPUT FORMAT:
# Evidence-Based Synthesis

## Theme 1: [Theme name]
- Finding: [finding] [citation] (Worker X)
- Finding: [finding] [citation] (Worker Y)

## Theme 2: [Theme name]
[Continue...]

# Conclusion
[Evidence-based conclusions]"""

    def _extract_evidence_database(self,
                                   worker_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all evidence with citations from worker outputs."""
        import re
        evidence_db = []

        for result in worker_results:
            output = result.get("output", "")
            worker_id = result.get("worker_id", "unknown")

            citation_pattern = r'([^.!?]+)\s*\[([^\]]+)\]'
            matches = re.findall(citation_pattern, output)

            for claim, citation in matches:
                evidence_db.append({
                    "claim": claim.strip(),
                    "citation": citation.strip(),
                    "worker_id": worker_id
                })

            page_pattern = r'([^.!?]+)\s*\(p\.\s*(\d+)\)'
            page_matches = re.findall(page_pattern, output)

            for claim, page in page_matches:
                evidence_db.append({
                    "claim": claim.strip(),
                    "citation": f"p. {page}",
                    "worker_id": worker_id
                })

        return evidence_db

    def synthesize_with_quality_weights(self,
                                       worker_results: List[Dict[str, Any]],
                                       evaluation_results: Dict[str, Any],
                                       worker_spawner,
                                       task_plan: Optional[Dict[str, Any]] = None,
                                       request_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Quality-weighted synthesis excluding low-quality workers.

        Weighting:
        - >80 score: 1.0 weight (full inclusion)
        - 60-80 score: 0.5 weight (partial inclusion)
        - <60 score: 0.0 weight (excluded)

        Args:
            worker_results: List of worker outputs
            evaluation_results: Evaluation results with scores
            worker_spawner: WorkerSpawner for synthesis
            task_plan: Optional task plan
            request_analysis: Optional request analysis

        Returns:
            Synthesis result with quality weighting
        """
        individual_evals = evaluation_results.get("individual_evaluations", {})

        weighted_results = []
        for result in worker_results:
            worker_id = result.get("worker_id")
            eval_data = individual_evals.get(worker_id, {})
            score = eval_data.get("score", 70)

            if score >= 80:
                weight = 1.0
                weight_label = "high"
            elif score >= 60:
                weight = 0.5
                weight_label = "medium"
            else:
                weight = 0.0
                weight_label = "excluded"
                continue

            weighted_results.append({
                "worker_id": worker_id,
                "output": result.get("output", ""),
                "score": score,
                "weight": weight,
                "weight_label": weight_label
            })

        synthesis_prompt = self._build_quality_weighted_prompt(weighted_results)

        synthesis_output = worker_spawner.call_worker(
            prompt=synthesis_prompt,
            complexity="high",
            context="Quality-weighted synthesis"
        )

        return {
            "synthesis_output": synthesis_output,
            "method": "quality_weighted",
            "strategy_used": "quality_weighted",
            "sources_included": len([r for r in weighted_results if r["weight"] > 0]),
            "sources_excluded": len(worker_results) - len(weighted_results),
            "quality_weighting": {
                "high_weight": len([r for r in weighted_results if r["weight"] == 1.0]),
                "medium_weight": len([r for r in weighted_results if r["weight"] == 0.5])
            }
        }

    def _build_quality_weighted_prompt(self,
                                      weighted_results: List[Dict[str, Any]]) -> str:
        """Build prompt for quality-weighted synthesis."""
        worker_outputs = "\n\n---\n\n".join([
            f"**Worker {r['worker_id']}** (Quality: {r['score']}/100, Weight: {r['weight_label'].upper()})\n\n{r['output']}"
            for r in weighted_results
        ])

        return f"""You are synthesizing results from {len(weighted_results)} workers with quality-based weighting.

Workers are weighted by quality:
- HIGH WEIGHT (>80 score): Trust fully, prioritize in synthesis
- MEDIUM WEIGHT (60-80 score): Include but verify against high-weight sources
- LOW WEIGHT (<60 score): Excluded from synthesis

WEIGHTED WORKER OUTPUTS:
{worker_outputs}

SYNTHESIS TASK:
1. Prioritize findings from HIGH WEIGHT workers
2. Use MEDIUM WEIGHT workers to supplement/corroborate
3. When conflicts arise, defer to higher-quality sources
4. Maintain citation traceability
5. Generate quality-weighted synthesis

OUTPUT FORMAT:
# Quality-Weighted Synthesis

## High-Confidence Findings
[From high-weight workers]

## Supporting Evidence
[From medium-weight workers that corroborate]

## Consolidated Analysis
[Integrated synthesis with quality consideration]

# Conclusion
[Quality-weighted conclusions]"""

    def extract_information_coverage(self,
                                    synthesis_output: str,
                                    worker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare synthesis to worker outputs for completeness check.

        Analyzes:
        - Citation preservation (count citations in synthesis vs workers)
        - Key finding coverage (headers/sections from workers in synthesis)
        - Information completeness ratio

        Args:
            synthesis_output: Synthesis output text
            worker_results: List of worker outputs

        Returns:
            Information coverage analysis
        """
        import re

        synthesis_citations = self._count_all_citations(synthesis_output)
        synthesis_headers = self._extract_headers(synthesis_output)
        synthesis_lower = synthesis_output.lower()

        total_worker_citations = 0
        total_worker_headers = []
        missing_findings = []

        for result in worker_results:
            if result.get("status") == "success":
                output = result.get("output", "")
                worker_id = result.get("worker_id", "unknown")

                citations = self._count_all_citations(output)
                total_worker_citations += citations

                headers = self._extract_headers(output)
                total_worker_headers.extend(headers)

                for header in headers[:3]:
                    header_keywords = set(re.findall(r'\b\w{4,}\b', header.lower()))
                    if not any(kw in synthesis_lower for kw in header_keywords):
                        missing_findings.append({
                            "worker_id": worker_id,
                            "header": header,
                            "keywords": list(header_keywords)
                        })

        citation_preservation = (
            synthesis_citations / total_worker_citations
            if total_worker_citations > 0 else 1.0
        )

        header_coverage = (
            (len(total_worker_headers) - len(missing_findings)) / len(total_worker_headers)
            if total_worker_headers else 1.0
        )

        completeness_score = (citation_preservation * 0.6 + header_coverage * 0.4) * 100

        return {
            "synthesis_citations": synthesis_citations,
            "worker_citations": total_worker_citations,
            "citation_preservation_ratio": round(citation_preservation, 2),
            "synthesis_headers": len(synthesis_headers),
            "worker_headers": len(total_worker_headers),
            "header_coverage_ratio": round(header_coverage, 2),
            "missing_findings": missing_findings[:5],
            "completeness_score": round(completeness_score, 1),
            "information_loss_detected": completeness_score < 70
        }

    def _count_all_citations(self, text: str) -> int:
        """Count all types of citations in text."""
        import re
        bracket_citations = len(re.findall(r'\[[\d,\s]+\]', text))
        page_citations = len(re.findall(r'\(p\.\s*\d+\)', text))
        line_citations = len(re.findall(r'\(line\s+\d+\)', text))
        return bracket_citations + page_citations + line_citations

    def _extract_headers(self, text: str) -> List[str]:
        """Extract markdown headers from text."""
        import re
        return re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)


def main():
    """CLI for testing result synthesizer."""
    import argparse

    parser = argparse.ArgumentParser(description='Result Synthesizer Test')
    parser.add_argument('--results', required=True, help='Path to worker results JSON')
    parser.add_argument('--evaluation', required=True, help='Path to evaluation results JSON')

    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    synthesizer = ResultSynthesizer(skill_dir)

    with open(args.results, 'r') as f:
        worker_results = json.load(f)
    with open(args.evaluation, 'r') as f:
        evaluation_results = json.load(f)

    task_plan = {"subtasks": [], "dependencies": {}}
    request_analysis = {"task_type": "comparison"}

    strategy = synthesizer._select_synthesis_strategy(
        worker_results, task_plan, request_analysis
    )

    print(f"Selected strategy: {strategy}")


if __name__ == '__main__':
    main()
