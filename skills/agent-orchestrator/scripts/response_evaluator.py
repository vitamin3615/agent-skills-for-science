"""
Response Evaluator for Agent Orchestrator
4-layer quality control system for worker outputs.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class ResponseEvaluator:
    """Evaluates worker responses with multi-layer quality control."""

    def __init__(self, skill_dir: Path):
        """
        Initialize ResponseEvaluator.

        Args:
            skill_dir: Path to skill root directory
        """
        self.skill_dir = skill_dir

    def evaluate_responses(self,
                          worker_results: List[Dict[str, Any]],
                          task_plan: Dict[str, Any],
                          request_analysis: Dict[str, Any],
                          use_ai_evaluation: bool = False,
                          worker_spawner=None) -> Dict[str, Any]:
        """
        Evaluate all worker responses.

        Phase 5: Response Evaluation

        Args:
            worker_results: List of worker results
            task_plan: Original task plan
            request_analysis: Request analysis
            use_ai_evaluation: Whether to use AI for Layer 4 evaluation
            worker_spawner: WorkerSpawner for AI evaluation

        Returns:
            Evaluation report with scores and quality gates
        """
        evaluation_results = {}

        for result in worker_results:
            worker_id = result.get("worker_id", "unknown")
            output = result.get("output", "")
            task_id = result.get("task_id", "")

            task_config = self._find_task_config(task_id, task_plan)

            score = self._evaluate_worker_output(
                worker_id=worker_id,
                output=output,
                task_config=task_config,
                request_analysis=request_analysis,
                use_ai_evaluation=use_ai_evaluation,
                worker_spawner=worker_spawner
            )

            quality_gate = self._apply_quality_gate(score)

            evaluation_results[worker_id] = {
                "score": score["total"],
                "layer_scores": score["layers"],
                "quality_gate": quality_gate,
                "issues": score["issues"],
                "recommendation": score["recommendation"]
            }

        overall_quality = self._calculate_overall_quality(evaluation_results)

        return {
            "individual_evaluations": evaluation_results,
            "overall_quality": overall_quality,
            "passed_workers": sum(1 for e in evaluation_results.values() if e["quality_gate"] == "accept"),
            "flagged_workers": sum(1 for e in evaluation_results.values() if e["quality_gate"] == "flag"),
            "failed_workers": sum(1 for e in evaluation_results.values() if e["quality_gate"] == "reject"),
            "total_workers": len(evaluation_results)
        }

    def _evaluate_worker_output(self,
                                worker_id: str,
                                output: str,
                                task_config: Optional[Dict[str, Any]],
                                request_analysis: Dict[str, Any],
                                use_ai_evaluation: bool,
                                worker_spawner) -> Dict[str, Any]:
        """
        Multi-layer evaluation of worker output.

        Layers:
        1. Structural checks (format compliance)
        2. Completeness validation
        3. Hallucination detection heuristics
        4. Optional AI evaluation

        Returns:
            Comprehensive score dictionary
        """
        layer1 = self._layer1_structural_check(output)
        layer2 = self._layer2_completeness_check(output, task_config, request_analysis)
        layer3 = self._layer3_hallucination_detection(output)

        layers = {
            "layer1_structural": layer1,
            "layer2_completeness": layer2,
            "layer3_hallucination": layer3
        }

        if use_ai_evaluation and worker_spawner:
            layer4 = self._layer4_ai_evaluation(output, task_config, worker_spawner)
            layers["layer4_ai"] = layer4
            total = (layer1["score"] * 0.2 + layer2["score"] * 0.3 +
                    layer3["score"] * 0.2 + layer4["score"] * 0.3)
        else:
            total = (layer1["score"] * 0.25 + layer2["score"] * 0.45 +
                    layer3["score"] * 0.3)

        all_issues = (layer1["issues"] + layer2["issues"] + layer3["issues"])
        if use_ai_evaluation and "layer4_ai" in layers:
            all_issues += layers["layer4_ai"]["issues"]

        recommendation = self._generate_recommendation(total, all_issues)

        return {
            "total": round(total, 1),
            "layers": layers,
            "issues": all_issues,
            "recommendation": recommendation
        }

    def _layer1_structural_check(self, output: str) -> Dict[str, Any]:
        """
        Layer 1: Structural checks (format compliance).

        Checks:
        - Non-empty output
        - Reasonable length (not too short)
        - Has structure (headers, lists, etc.)
        """
        issues = []
        score = 100

        if not output or len(output.strip()) == 0:
            issues.append("Empty output")
            return {"score": 0, "issues": issues}

        if len(output) < 100:
            issues.append("Output too short (< 100 chars)")
            score -= 40

        has_headers = bool(re.search(r'^#+\s+', output, re.MULTILINE))
        has_lists = bool(re.search(r'^\s*[-*]\s+', output, re.MULTILINE))
        has_structure = has_headers or has_lists

        if not has_structure:
            issues.append("Lacks clear structure (no headers or lists)")
            score -= 30

        lines = output.split('\n')
        if len(lines) < 5:
            issues.append("Minimal content (< 5 lines)")
            score -= 20

        return {"score": max(0, score), "issues": issues}

    def _layer2_completeness_check(self,
                                   output: str,
                                   task_config: Optional[Dict[str, Any]],
                                   request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Layer 2: Completeness validation.

        Checks:
        - Required sections present
        - Success criteria addressed
        - Task requirements met
        """
        issues = []
        score = 100

        if not task_config:
            return {"score": 80, "issues": ["No task config for validation"]}

        task_desc = task_config.get("description", "").lower()
        output_lower = output.lower()

        expected_keywords = self._extract_keywords(task_desc)
        missing_keywords = [kw for kw in expected_keywords if kw not in output_lower]

        if len(missing_keywords) > len(expected_keywords) * 0.5:
            issues.append(f"Missing key topics: {', '.join(missing_keywords[:3])}")
            score -= 40

        success_criteria = request_analysis.get("success_criteria", [])
        for criterion in success_criteria[:3]:
            criterion_keywords = self._extract_keywords(criterion)
            if not any(kw in output_lower for kw in criterion_keywords):
                issues.append(f"Success criterion not addressed: {criterion[:50]}")
                score -= 15

        output_format = task_config.get("output_format", "")
        if "json" in output_format.lower() and "{" not in output:
            issues.append("Expected JSON format but not found")
            score -= 30
        elif "markdown" in output_format.lower() and not re.search(r'^#+\s+', output, re.MULTILINE):
            issues.append("Expected markdown format but no headers found")
            score -= 20

        return {"score": max(0, score), "issues": issues}

    def _layer3_hallucination_detection(self, output: str) -> Dict[str, Any]:
        """
        Layer 3: Hallucination detection heuristics.

        Heuristics:
        - Vague claims without evidence
        - Missing citations where expected
        - Overconfident language without support
        - Inconsistencies in statements
        """
        issues = []
        score = 100

        vague_patterns = [
            r'\b(many|some|several|various|numerous)\s+\w+\s+(?:show|indicate|suggest|demonstrate)',
            r'\b(it is well known|obviously|clearly|certainly)\b',
            r'\b(always|never|all|none|everyone|no one)\b'
        ]

        vague_count = 0
        for pattern in vague_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            vague_count += len(matches)

        if vague_count > 5:
            issues.append(f"Excessive vague claims ({vague_count} instances)")
            score -= 25

        has_citations = bool(re.search(r'\[[\d,\s]+\]|\(p\.\s*\d+\)|\(line\s+\d+\)', output))
        words_count = len(output.split())

        if words_count > 200 and not has_citations:
            issues.append("Long output without citations")
            score -= 30

        comparative_without_baseline = re.findall(
            r'\b(better|worse|faster|slower|more|less)\s+\w+',
            output,
            re.IGNORECASE
        )
        if len(comparative_without_baseline) > 3:
            issues.append("Comparative claims without baseline")
            score -= 15

        contradictions = self._detect_simple_contradictions(output)
        if contradictions:
            issues.append(f"Possible contradiction: {contradictions[0][:60]}")
            score -= 20

        return {"score": max(0, score), "issues": issues}

    def _layer4_ai_evaluation(self,
                             output: str,
                             task_config: Optional[Dict[str, Any]],
                             worker_spawner) -> Dict[str, Any]:
        """
        Layer 4: AI-powered evaluation.

        Uses worker AI to assess:
        - Reasoning quality
        - Evidence strength
        - Logical consistency
        - Task fulfillment
        """
        evaluation_prompt = f"""Evaluate this AI worker output for quality.

TASK: {task_config.get('description', 'Unknown') if task_config else 'Unknown'}

OUTPUT:
{output[:2000]}

EVALUATION CRITERIA:
1. Reasoning Quality (0-25): Is the reasoning clear and logical?
2. Evidence Strength (0-25): Are claims supported by evidence?
3. Logical Consistency (0-25): Are there contradictions?
4. Task Fulfillment (0-25): Does it address the task?

OUTPUT JSON:
{{
  "reasoning_quality": <0-25>,
  "evidence_strength": <0-25>,
  "logical_consistency": <0-25>,
  "task_fulfillment": <0-25>,
  "total": <0-100>,
  "issues": ["issue 1", "issue 2"],
  "justification": "Brief explanation"
}}"""

        try:
            result = worker_spawner.call_worker(
                prompt=evaluation_prompt,
                complexity="medium",
                context="Quality evaluation"
            )

            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                evaluation = json.loads(json_str)
                return {
                    "score": evaluation.get("total", 70),
                    "issues": evaluation.get("issues", []),
                    "justification": evaluation.get("justification", "")
                }
        except Exception as e:
            return {"score": 70, "issues": [f"AI evaluation failed: {str(e)}"], "justification": ""}

        return {"score": 70, "issues": [], "justification": "Default score"}

    def _apply_quality_gate(self, score: Dict[str, Any]) -> str:
        """
        Apply quality gate thresholds.

        Gates:
        - <60: reject (re-execute)
        - 60-80: flag (review)
        - >80: accept

        Args:
            score: Score dictionary

        Returns:
            Quality gate decision
        """
        total = score["total"]

        if total < 60:
            return "reject"
        elif total < 80:
            return "flag"
        else:
            return "accept"

    def _calculate_overall_quality(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        if not evaluation_results:
            return {"average_score": 0, "quality": "poor"}

        scores = [e["score"] for e in evaluation_results.values()]
        avg_score = sum(scores) / len(scores)

        quality_level = "excellent" if avg_score >= 80 else \
                       "good" if avg_score >= 70 else \
                       "acceptable" if avg_score >= 60 else \
                       "poor"

        return {
            "average_score": round(avg_score, 1),
            "quality": quality_level,
            "min_score": min(scores),
            "max_score": max(scores)
        }

    def _find_task_config(self, task_id: str, task_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find task configuration by ID."""
        for task in task_plan.get("subtasks", []):
            if task.get("id") == task_id:
                return task
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text."""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'have', 'has'}

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]

        return list(set(keywords))[:10]

    def _detect_simple_contradictions(self, output: str) -> List[str]:
        """Simple contradiction detection."""
        sentences = re.split(r'[.!?]\s+', output)
        contradictions = []

        positive_negative_pairs = [
            (r'\bis\b', r'\bis not\b'),
            (r'\bcan\b', r'\bcannot\b'),
            (r'\bwill\b', r'\bwill not\b'),
            (r'\bhas\b', r'\bhas no\b')
        ]

        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:i+3]:
                for pos, neg in positive_negative_pairs:
                    if re.search(pos, sent1, re.IGNORECASE) and re.search(neg, sent2, re.IGNORECASE):
                        subject1 = sent1[:50]
                        subject2 = sent2[:50]
                        if self._similar_subjects(subject1, subject2):
                            contradictions.append(f"{subject1}... vs {subject2}...")
                            break

        return contradictions[:2]

    def _similar_subjects(self, text1: str, text2: str) -> bool:
        """Check if two texts discuss similar subjects."""
        words1 = set(re.findall(r'\b\w{4,}\b', text1.lower()))
        words2 = set(re.findall(r'\b\w{4,}\b', text2.lower()))

        overlap = len(words1 & words2)
        return overlap >= 2

    def _generate_recommendation(self, total_score: float, issues: List[str]) -> str:
        """Generate recommendation based on score and issues."""
        if total_score >= 80:
            return "Accept output. High quality."
        elif total_score >= 60:
            return f"Flag for review. Issues: {'; '.join(issues[:2])}"
        else:
            return f"Reject and re-execute. Critical issues: {'; '.join(issues[:3])}"

    def extract_quality_patterns(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patterns across worker evaluations for meta-cognitive review.

        Returns:
            {
                "failure_rate": 0.2,
                "failure_patterns": ["hallucination", "incomplete"],
                "quality_distribution": {"reject": 2, "flag": 3, "accept": 5},
                "common_issues": ["missing citations", "vague claims"],
                "score_statistics": {"mean": 72.5, "std": 15.2, "min": 45, "max": 95}
            }
        """
        total_workers = evaluation_results.get("total_workers", 0)
        if total_workers == 0:
            return {
                "failure_rate": 0.0,
                "failure_patterns": [],
                "quality_distribution": {"reject": 0, "flag": 0, "accept": 0},
                "common_issues": [],
                "score_statistics": {"mean": 0, "std": 0, "min": 0, "max": 0}
            }

        failed_workers = evaluation_results.get("failed_workers", 0)
        failure_rate = failed_workers / total_workers

        quality_distribution = {
            "reject": failed_workers,
            "flag": evaluation_results.get("flagged_workers", 0),
            "accept": evaluation_results.get("passed_workers", 0)
        }

        individual_evals = evaluation_results.get("individual_evaluations", {})

        all_issues = []
        all_scores = []
        failure_issues = []

        for worker_id, eval_data in individual_evals.items():
            score = eval_data.get("score", 0)
            all_scores.append(score)

            issues = eval_data.get("issues", [])
            all_issues.extend(issues)

            quality_gate = eval_data.get("quality_gate", "accept")
            if quality_gate in ["reject", "flag"]:
                failure_issues.extend(issues)

        issue_keywords = {}
        for issue in all_issues:
            words = re.findall(r'\b\w{4,}\b', issue.lower())
            for word in words:
                if word not in {'output', 'worker', 'result', 'issue', 'found', 'detected'}:
                    issue_keywords[word] = issue_keywords.get(word, 0) + 1

        sorted_keywords = sorted(
            issue_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )
        common_issues = [kw for kw, count in sorted_keywords[:10] if count >= 2]

        failure_keywords = {}
        for issue in failure_issues:
            words = re.findall(r'\b\w{4,}\b', issue.lower())
            for word in words:
                if word not in {'output', 'worker', 'result', 'issue', 'found', 'detected'}:
                    failure_keywords[word] = failure_keywords.get(word, 0) + 1

        sorted_failure_keywords = sorted(
            failure_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )
        failure_patterns = [kw for kw, count in sorted_failure_keywords[:5] if count >= 2]

        score_stats = {
            "mean": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            "std": round(self._calculate_std(all_scores), 1) if all_scores else 0,
            "min": min(all_scores) if all_scores else 0,
            "max": max(all_scores) if all_scores else 0
        }

        return {
            "failure_rate": round(failure_rate, 2),
            "failure_patterns": failure_patterns,
            "quality_distribution": quality_distribution,
            "common_issues": common_issues,
            "score_statistics": score_stats
        }

    def _calculate_std(self, scores: List[float]) -> float:
        """Calculate standard deviation of scores."""
        if not scores:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance ** 0.5


def main():
    """CLI for testing response evaluator."""
    import argparse

    parser = argparse.ArgumentParser(description='Response Evaluator Test')
    parser.add_argument('--output', required=True, help='Path to worker output file')

    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    evaluator = ResponseEvaluator(skill_dir)

    with open(args.output, 'r') as f:
        output = f.read()

    task_config = {"description": "Test task", "output_format": "markdown"}
    request_analysis = {"success_criteria": ["Complete analysis"]}

    score = evaluator._evaluate_worker_output(
        worker_id="test_worker",
        output=output,
        task_config=task_config,
        request_analysis=request_analysis,
        use_ai_evaluation=False,
        worker_spawner=None
    )

    print(json.dumps(score, indent=2))


if __name__ == '__main__':
    main()
