"""
Meta-Cognitive Reviewer for Agent Orchestrator
Implements hypothesis-verification decision framework for iterative refinement.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class MetaCognitiveReviewer:
    """Meta-cognitive engine for quality analysis and iteration decisions."""

    def __init__(self):
        """Initialize MetaCognitiveReviewer."""
        self.quality_thresholds = {
            "information_loss": 0.3,
            "failure_rate": 0.3,
            "min_quality": 70,
            "high_quality": 80,
            "improvement_threshold": 5
        }

    def analyze_quality(self,
                       worker_results: List[Dict[str, Any]],
                       evaluation_results: Dict[str, Any],
                       synthesis_result: Dict[str, Any],
                       request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        4-dimensional quality analysis with confidence scoring.

        Dimensions:
        1. Information completeness (pre-caution)
        2. Quality degradation (post-diagnosis)
        3. Synthesis coherence (post-diagnosis)
        4. Goal fulfillment (meta-decision)

        Args:
            worker_results: List of worker outputs
            evaluation_results: Evaluation results
            synthesis_result: Synthesis output
            request_analysis: Original request analysis

        Returns:
            Quality analysis with confidence scores
        """
        info_loss = self.detect_information_loss(worker_results, synthesis_result)
        quality_degradation = self.detect_quality_degradation(evaluation_results)
        synthesis_coherence = self.verify_synthesis_coherence(
            synthesis_result,
            evaluation_results
        )
        goal_fulfillment = self.verify_goal_fulfillment(
            synthesis_result,
            request_analysis
        )

        overall_score = (
            info_loss["score"] * 0.25 +
            quality_degradation["score"] * 0.25 +
            synthesis_coherence["score"] * 0.25 +
            goal_fulfillment["score"] * 0.25
        )

        return {
            "overall_score": round(overall_score, 1),
            "dimensions": {
                "information_completeness": info_loss,
                "quality_assessment": quality_degradation,
                "synthesis_coherence": synthesis_coherence,
                "goal_fulfillment": goal_fulfillment
            },
            "confidence": self._calculate_confidence([
                info_loss, quality_degradation,
                synthesis_coherence, goal_fulfillment
            ])
        }

    def detect_information_loss(self,
                                worker_results: List[Dict[str, Any]],
                                synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-caution: Check if synthesis lost critical information.

        Detects:
        - Citation loss from high-quality workers
        - Key findings missing from synthesis
        - Information completeness ratio

        Args:
            worker_results: List of worker outputs
            synthesis_result: Synthesis output

        Returns:
            Information loss analysis
        """
        synthesis_output = synthesis_result.get("synthesis_output", "")

        worker_citations = []
        for result in worker_results:
            if result.get("status") == "success":
                output = result.get("output", "")
                citations = self._count_citations(output)
                worker_citations.append({
                    "worker_id": result.get("worker_id"),
                    "citations": citations,
                    "output_length": len(output)
                })

        synthesis_citations = self._count_citations(synthesis_output)
        total_worker_citations = sum(w["citations"] for w in worker_citations)

        citation_preservation_ratio = (
            synthesis_citations / total_worker_citations
            if total_worker_citations > 0 else 1.0
        )

        key_findings_loss = self._detect_missing_key_findings(
            worker_results,
            synthesis_output
        )

        issues = []
        score = 100

        if citation_preservation_ratio < 0.3:
            issues.append(
                f"Severe citation loss: {total_worker_citations} → "
                f"{synthesis_citations} ({citation_preservation_ratio:.1%})"
            )
            score -= 40
        elif citation_preservation_ratio < 0.5:
            issues.append(
                f"Moderate citation loss: {citation_preservation_ratio:.1%}"
            )
            score -= 20

        if key_findings_loss > 0:
            issues.append(f"{key_findings_loss} key findings missing from synthesis")
            score -= min(30, key_findings_loss * 10)

        return {
            "score": max(0, score),
            "issues": issues,
            "evidence": {
                "worker_citations": total_worker_citations,
                "synthesis_citations": synthesis_citations,
                "preservation_ratio": round(citation_preservation_ratio, 2),
                "key_findings_lost": key_findings_loss
            },
            "trigger_iteration": citation_preservation_ratio < 0.5 or key_findings_loss > 0
        }

    def detect_quality_degradation(self,
                                   evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-diagnosis: Analyze quality patterns and failures.

        Detects:
        - High worker failure rate
        - Low average quality scores
        - Quality distribution patterns

        Args:
            evaluation_results: Evaluation results

        Returns:
            Quality degradation analysis
        """
        total_workers = evaluation_results.get("total_workers", 0)
        failed_workers = evaluation_results.get("failed_workers", 0)
        avg_score = evaluation_results.get("overall_quality", {}).get("average_score", 70)

        failure_rate = failed_workers / total_workers if total_workers > 0 else 0

        quality_distribution = {
            "accept": evaluation_results.get("passed_workers", 0),
            "flag": evaluation_results.get("flagged_workers", 0),
            "reject": failed_workers
        }

        issues = []
        score = 100

        if failure_rate > self.quality_thresholds["failure_rate"]:
            issues.append(
                f"High failure rate: {failure_rate:.1%} "
                f"({failed_workers}/{total_workers} workers)"
            )
            score -= 40

        if avg_score < self.quality_thresholds["min_quality"]:
            issues.append(f"Low average quality: {avg_score}/100")
            score -= 30

        failure_patterns = self._extract_failure_patterns(evaluation_results)
        if failure_patterns:
            issues.append(f"Common issues: {', '.join(failure_patterns[:3])}")
            score -= 15

        return {
            "score": max(0, score),
            "issues": issues,
            "evidence": {
                "failure_rate": round(failure_rate, 2),
                "average_quality": avg_score,
                "quality_distribution": quality_distribution,
                "failure_patterns": failure_patterns
            },
            "trigger_iteration": (
                failure_rate > self.quality_thresholds["failure_rate"] or
                avg_score < self.quality_thresholds["min_quality"]
            )
        }

    def verify_synthesis_coherence(self,
                                   synthesis_result: Dict[str, Any],
                                   evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-diagnosis: Check strategy appropriateness.

        Verifies:
        - Synthesis strategy matches task characteristics
        - Quality weighting applied appropriately
        - Output coherence and structure

        Args:
            synthesis_result: Synthesis output
            evaluation_results: Evaluation results

        Returns:
            Synthesis coherence analysis
        """
        strategy = synthesis_result.get("strategy_used", "unknown")
        synthesis_output = synthesis_result.get("synthesis_output", "")

        issues = []
        score = 100

        if len(synthesis_output) < 200:
            issues.append("Synthesis output too short")
            score -= 30

        has_structure = bool(re.search(r'^#+\s+', synthesis_output, re.MULTILINE))
        if not has_structure:
            issues.append("Synthesis lacks clear structure")
            score -= 20

        sources_included = synthesis_result.get("sources_included", 0)
        total_workers = evaluation_results.get("total_workers", 0)

        if sources_included < total_workers * 0.5:
            issues.append(
                f"Low source inclusion: {sources_included}/{total_workers}"
            )
            score -= 25

        strategy_mismatch = self._detect_strategy_mismatch(
            synthesis_result,
            evaluation_results
        )
        if strategy_mismatch:
            issues.append(strategy_mismatch)
            score -= 20

        return {
            "score": max(0, score),
            "issues": issues,
            "evidence": {
                "strategy": strategy,
                "output_length": len(synthesis_output),
                "sources_included": sources_included,
                "has_structure": has_structure
            },
            "trigger_iteration": score < 60
        }

    def verify_goal_fulfillment(self,
                               synthesis_result: Dict[str, Any],
                               request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Meta-decision: Compare outputs to original goals.

        Verifies:
        - Success criteria addressed
        - Output format matches expectations
        - Request goals met

        Args:
            synthesis_result: Synthesis output
            request_analysis: Original request analysis

        Returns:
            Goal fulfillment analysis
        """
        synthesis_output = synthesis_result.get("synthesis_output", "")
        success_criteria = request_analysis.get("success_criteria", [])
        output_format = request_analysis.get("output_format", "")

        issues = []
        score = 100

        criteria_met = 0
        for criterion in success_criteria:
            if self._criterion_addressed(criterion, synthesis_output):
                criteria_met += 1

        if success_criteria:
            criteria_ratio = criteria_met / len(success_criteria)
            if criteria_ratio < 0.5:
                issues.append(
                    f"Few success criteria met: {criteria_met}/{len(success_criteria)}"
                )
                score -= 40
            elif criteria_ratio < 0.8:
                issues.append(
                    f"Some success criteria unmet: {criteria_met}/{len(success_criteria)}"
                )
                score -= 20

        if output_format:
            if "json" in output_format.lower() and "{" not in synthesis_output:
                issues.append("Expected JSON format not found")
                score -= 30
            elif "markdown" in output_format.lower() and not re.search(r'^#+\s+', synthesis_output, re.MULTILINE):
                issues.append("Expected markdown headers not found")
                score -= 20

        return {
            "score": max(0, score),
            "issues": issues,
            "evidence": {
                "criteria_met": criteria_met,
                "total_criteria": len(success_criteria),
                "criteria_ratio": round(criteria_met / len(success_criteria), 2) if success_criteria else 1.0,
                "format_match": bool(output_format)
            },
            "trigger_iteration": score < 70
        }

    def make_iteration_decision(self,
                               quality_analysis: Dict[str, Any],
                               current_iteration: int = 0,
                               max_iterations: int = 3,
                               previous_quality: Optional[float] = None) -> Tuple[str, str, str, str]:
        """
        Hypothesis-verification-based decision with explicit reasoning.

        Args:
            quality_analysis: Quality analysis results
            current_iteration: Current iteration number
            max_iterations: Maximum allowed iterations
            previous_quality: Previous iteration quality score

        Returns:
            (decision, strategy, confidence, reasoning)
            decision: "accept" | "iterate" | "fail"
            strategy: iteration strategy to use
            confidence: "high" | "medium" | "low"
            reasoning: explanation of decision
        """
        overall_score = quality_analysis["overall_score"]
        dimensions = quality_analysis["dimensions"]

        if current_iteration >= max_iterations:
            return (
                "accept",
                "bounded_acceptance",
                "high",
                f"Max iterations ({max_iterations}) reached. Accepting best result."
            )

        if previous_quality is not None:
            improvement = overall_score - previous_quality
            if improvement < self.quality_thresholds["improvement_threshold"]:
                return (
                    "accept",
                    "stagnation_detected",
                    "high",
                    f"Quality stagnated (improvement: {improvement:.1f}). Accepting current result."
                )

        if overall_score >= 85:
            return (
                "accept",
                None,
                "high",
                f"Excellent quality achieved ({overall_score}/100). No iteration needed."
            )

        triggers = []
        for dim_name, dim_data in dimensions.items():
            if dim_data.get("trigger_iteration", False):
                triggers.append((dim_name, dim_data))

        if not triggers:
            return (
                "accept",
                None,
                "high",
                f"Acceptable quality ({overall_score}/100). No critical issues detected."
            )

        strategy, confidence, reasoning = self._select_iteration_strategy(
            triggers,
            quality_analysis,
            current_iteration
        )

        if strategy:
            return ("iterate", strategy, confidence, reasoning)
        else:
            return (
                "accept",
                None,
                "medium",
                f"Quality acceptable ({overall_score}/100) despite minor issues."
            )

    def _select_iteration_strategy(self,
                                   triggers: List[Tuple[str, Dict[str, Any]]],
                                   quality_analysis: Dict[str, Any],
                                   current_iteration: int) -> Tuple[str, str, str]:
        """
        Select optimal iteration strategy based on triggers.

        Strategies:
        1. re_extract_synthesis - Pre-caution: information loss
        2. re_execute_failed_workers - Post-diagnosis: quality degradation
        3. refine_synthesis_weights - Post-diagnosis: unbalanced synthesis
        4. re_synthesize_new_strategy - Post-diagnosis: strategy mismatch
        5. re_plan_decomposition - Meta-decision: fundamental planning issue

        Args:
            triggers: List of dimension triggers
            quality_analysis: Full quality analysis
            current_iteration: Current iteration number

        Returns:
            (strategy, confidence, reasoning)
        """
        trigger_names = [t[0] for t in triggers]
        dimensions = quality_analysis["dimensions"]

        if "information_completeness" in trigger_names:
            info_loss = dimensions["information_completeness"]
            preservation_ratio = info_loss["evidence"]["preservation_ratio"]

            if preservation_ratio < 0.3:
                return (
                    "re_extract_synthesis",
                    "high",
                    f"Severe citation loss detected ({preservation_ratio:.1%}). "
                    "Re-extracting synthesis with evidence_database strategy."
                )

        if "quality_assessment" in trigger_names:
            quality_deg = dimensions["quality_assessment"]
            failure_rate = quality_deg["evidence"]["failure_rate"]

            if failure_rate > 0.3:
                return (
                    "re_execute_failed_workers",
                    "high",
                    f"High worker failure rate ({failure_rate:.1%}). "
                    "Re-executing failed workers with refined prompts."
                )

        if "synthesis_coherence" in trigger_names:
            coherence = dimensions["synthesis_coherence"]
            strategy_issue = any(
                "strategy" in issue.lower() or "mismatch" in issue.lower()
                for issue in coherence["issues"]
            )

            if strategy_issue:
                return (
                    "re_synthesize_new_strategy",
                    "medium",
                    "Synthesis strategy mismatch detected. Re-synthesizing with alternative strategy."
                )
            else:
                return (
                    "refine_synthesis_weights",
                    "medium",
                    "Synthesis coherence issues detected. Applying quality-weighted synthesis."
                )

        if "goal_fulfillment" in trigger_names and current_iteration == 0:
            fulfillment = dimensions["goal_fulfillment"]
            criteria_ratio = fulfillment["evidence"]["criteria_ratio"]

            if criteria_ratio < 0.3:
                return (
                    "re_plan_decomposition",
                    "low",
                    f"Fundamental goal misalignment ({criteria_ratio:.1%} criteria met). "
                    "Re-planning task decomposition."
                )

        if len(triggers) >= 2:
            return (
                "re_extract_synthesis",
                "medium",
                f"Multiple quality issues detected ({len(triggers)} dimensions). "
                "Re-synthesizing with enhanced extraction."
            )

        return (None, "low", "Issues detected but no clear iteration strategy.")

    def _count_citations(self, text: str) -> int:
        """Count citations in text."""
        bracket_citations = len(re.findall(r'\[[\d,\s]+\]', text))
        page_citations = len(re.findall(r'\(p\.\s*\d+\)', text))
        line_citations = len(re.findall(r'\(line\s+\d+\)', text))

        return bracket_citations + page_citations + line_citations

    def _detect_missing_key_findings(self,
                                    worker_results: List[Dict[str, Any]],
                                    synthesis_output: str) -> int:
        """Detect key findings missing from synthesis."""
        missing_count = 0
        synthesis_lower = synthesis_output.lower()

        for result in worker_results:
            if result.get("status") == "success":
                output = result.get("output", "")
                headers = re.findall(r'^#+\s+(.+)$', output, re.MULTILINE)

                for header in headers[:3]:
                    header_keywords = set(re.findall(r'\b\w{4,}\b', header.lower()))

                    if not any(kw in synthesis_lower for kw in header_keywords):
                        missing_count += 1

        return missing_count

    def _extract_failure_patterns(self,
                                  evaluation_results: Dict[str, Any]) -> List[str]:
        """Extract common failure patterns from evaluations."""
        patterns = []
        individual_evals = evaluation_results.get("individual_evaluations", {})

        all_issues = []
        for eval_data in individual_evals.values():
            if eval_data.get("quality_gate") in ["reject", "flag"]:
                all_issues.extend(eval_data.get("issues", []))

        issue_keywords = {}
        for issue in all_issues:
            keywords = re.findall(r'\b\w+\b', issue.lower())
            for kw in keywords:
                if len(kw) > 4:
                    issue_keywords[kw] = issue_keywords.get(kw, 0) + 1

        sorted_keywords = sorted(
            issue_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [kw for kw, count in sorted_keywords[:5] if count > 1]

    def _detect_strategy_mismatch(self,
                                 synthesis_result: Dict[str, Any],
                                 evaluation_results: Dict[str, Any]) -> Optional[str]:
        """Detect if synthesis strategy was inappropriate."""
        strategy = synthesis_result.get("strategy_used", "")

        if strategy == "consensus":
            accepted = evaluation_results.get("passed_workers", 0)
            total = evaluation_results.get("total_workers", 0)

            if total > 0 and accepted / total < 0.5:
                return "Consensus strategy used but low agreement among workers"

        return None

    def _criterion_addressed(self, criterion: str, output: str) -> bool:
        """Check if success criterion is addressed in output."""
        criterion_keywords = set(re.findall(r'\b\w{4,}\b', criterion.lower()))
        output_lower = output.lower()

        matches = sum(1 for kw in criterion_keywords if kw in output_lower)
        return matches >= len(criterion_keywords) * 0.5

    def _calculate_confidence(self, dimensions: List[Dict[str, Any]]) -> str:
        """Calculate confidence level based on dimension scores."""
        scores = [d["score"] for d in dimensions]
        avg_score = sum(scores) / len(scores) if scores else 50

        if avg_score >= 80:
            return "high"
        elif avg_score >= 60:
            return "medium"
        else:
            return "low"
