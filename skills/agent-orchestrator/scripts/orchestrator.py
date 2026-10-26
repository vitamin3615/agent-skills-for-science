#!/usr/bin/env python3
"""
Multi-Agent Orchestrator
Main CLI for coordinating multi-agent task execution.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from state_manager import StateManager
from task_analyzer import TaskAnalyzer
from delegation_engine import DelegationEngine
from response_evaluator import ResponseEvaluator
from result_synthesizer import ResultSynthesizer
from meta_cognitive_reviewer import MetaCognitiveReviewer
from utils.worker_spawner import WorkerSpawner
from utils.parallel_executor import ParallelExecutor
from utils.meta_actions_handler import MetaActionsHandler


class AgentOrchestrator:
    """Main orchestrator for multi-agent task execution."""

    def __init__(self, work_dir: str = None):
        """
        Initialize AgentOrchestrator.

        Args:
            work_dir: Working directory for outputs. If None, uses ./Temp/agent-orchestrator under the current directory
        """
        if work_dir is None:
            project_root = Path.cwd()
            work_dir = project_root / "Temp" / "agent-orchestrator"

        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.skill_dir = Path(__file__).parent.parent
        self.state_manager = StateManager(work_dir=str(self.work_dir))
        self.worker_spawner = WorkerSpawner(worker_type='gpt', custom_model='gpt-5-mini')
        self.task_analyzer = TaskAnalyzer(self.skill_dir, self.worker_spawner)
        self.delegation_engine = DelegationEngine(self.skill_dir)
        self.response_evaluator = ResponseEvaluator(self.skill_dir)
        self.result_synthesizer = ResultSynthesizer(self.skill_dir)
        self.meta_cognitive_reviewer = MetaCognitiveReviewer()
        self.parallel_executor = ParallelExecutor(max_workers=5)

    def run(self, user_request: str, resume: bool = False) -> str:
        """
        Execute full orchestration workflow.

        Args:
            user_request: User's request
            resume: Whether to resume from saved state

        Returns:
            Path to final report
        """
        start_time = time.time()

        if resume:
            if not self.state_manager.load_state():
                print("No saved state found. Starting fresh.")
                resume = False

        if not resume:
            session_id = self.state_manager.start_session()
            print(f"Started new session: {session_id}")
            self.state_manager.state["metadata"]["user_request"] = user_request

        current_phase = self.state_manager.state["current_phase"]
        print(f"\nResuming from {current_phase}" if resume else "\nStarting orchestration...")

        if current_phase == "phase_0" or not self.state_manager.state["phase_complete"]["phase_0"]:
            request_analysis = self.phase_0_request_understanding(user_request)
        else:
            with open(self.work_dir / "request_analysis.json", 'r') as f:
                request_analysis = json.load(f)

        if current_phase in ["phase_0", "phase_1"] or not self.state_manager.state["phase_complete"]["phase_1"]:
            task_plan = self.phase_1_task_decomposition(request_analysis, user_request)
        else:
            with open(self.work_dir / "task_plan.json", 'r') as f:
                task_plan = json.load(f)

        if current_phase in ["phase_0", "phase_1", "phase_2"] or not self.state_manager.state["phase_complete"]["phase_2"]:
            parallelization = self.phase_2_parallelization_strategy(task_plan)
        else:
            parallelization = self.state_manager.state["parallelization"]

        if current_phase in ["phase_0", "phase_1", "phase_2", "phase_3"] or not self.state_manager.state["phase_complete"]["phase_3"]:
            worker_prompts = self.phase_3_worker_prompt_generation(
                task_plan, parallelization, request_analysis
            )
        else:
            with open(self.work_dir / "worker_prompts.json", 'r') as f:
                worker_prompts = json.load(f)

        if current_phase in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"] or not self.state_manager.state["phase_complete"]["phase_4"]:
            worker_results = self.phase_4_parallel_execution(worker_prompts)
        else:
            with open(self.work_dir / "worker_results.json", 'r') as f:
                worker_results = json.load(f)

        if current_phase in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4", "phase_5"] or not self.state_manager.state["phase_complete"]["phase_5"]:
            evaluation_results = self.phase_5_response_evaluation(
                worker_results, task_plan, request_analysis
            )
        else:
            with open(self.work_dir / "evaluation_results.json", 'r') as f:
                evaluation_results = json.load(f)

        if current_phase in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6"] or not self.state_manager.state["phase_complete"]["phase_6"]:
            synthesis_result = self.phase_6_result_synthesis(
                worker_results, evaluation_results, task_plan, request_analysis
            )
        else:
            with open(self.work_dir / "synthesis_result.json", 'r') as f:
                synthesis_result = json.load(f)

        if current_phase in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7"] or not self.state_manager.state["phase_complete"]["phase_7"]:
            meta_review = self.phase_7_meta_review(
                task_plan, worker_results, evaluation_results, synthesis_result, request_analysis
            )
        else:
            with open(self.work_dir / "meta_review.json", 'r') as f:
                meta_review = json.load(f)

        final_report_path = self.phase_8_final_report(
            request_analysis,
            task_plan,
            parallelization,
            worker_results,
            evaluation_results,
            synthesis_result,
            meta_review
        )

        total_time = time.time() - start_time
        self.state_manager.state["metadata"]["total_execution_time"] = total_time

        # Cleanup workspace directories (prevents disk space accumulation)
        try:
            self.worker_spawner.cleanup_workspaces()
            print("✓ Cleaned up temporary workspaces")
        except Exception as e:
            print(f"⚠ Warning: Workspace cleanup failed: {e}")

        print(f"\n{'='*60}")
        print(f"Orchestration Complete!")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Final Report: {final_report_path}")
        print(f"{'='*60}")

        return str(final_report_path)

    def phase_0_request_understanding(self, user_request: str) -> dict:
        """Phase 0: Request Understanding."""
        print("\n[Phase 0] Request Understanding...")

        request_analysis = self.task_analyzer.analyze_request(user_request)

        output_file = self.work_dir / "request_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(request_analysis, f, indent=2)

        self.state_manager.add_file("request_analysis", str(output_file))
        self.state_manager.complete_phase("phase_0")

        print(f"  Goal: {request_analysis.get('goal', 'N/A')}")
        print(f"  Task Type: {request_analysis.get('task_type', 'N/A')}")
        print(f"  Complexity: {request_analysis.get('complexity', 'N/A')}")

        return request_analysis

    def phase_1_task_decomposition(self, request_analysis: dict, user_request: str) -> dict:
        """Phase 1: Task Decomposition & Planning."""
        print("\n[Phase 1] Task Decomposition...")

        task_plan = self.task_analyzer.decompose_task(
            request_analysis, user_request, self.worker_spawner
        )

        output_file = self.work_dir / "task_plan.json"
        with open(output_file, 'w') as f:
            json.dump(task_plan, f, indent=2)

        self.state_manager.add_file("task_plan", str(output_file))
        self.state_manager.state["task_plan"] = task_plan
        self.state_manager.state["metadata"]["task_count"] = len(task_plan.get("subtasks", []))
        self.state_manager.complete_phase("phase_1")

        print(f"  Subtasks: {len(task_plan.get('subtasks', []))}")

        return task_plan

    def phase_2_parallelization_strategy(self, task_plan: dict) -> dict:
        """Phase 2: Parallelization Strategy."""
        print("\n[Phase 2] Parallelization Strategy...")

        parallelization = self.task_analyzer.determine_parallelization(task_plan)

        self.state_manager.state["parallelization"] = parallelization
        self.state_manager.state["metadata"]["worker_count"] = parallelization["worker_count"]
        self.state_manager.complete_phase("phase_2")

        print(f"  Worker Count: {parallelization['worker_count']}")
        print(f"  Parallel Tasks: {parallelization['parallel_tasks_count']}")
        print(f"  Sequential Tasks: {parallelization['sequential_tasks_count']}")

        return parallelization

    def phase_3_worker_prompt_generation(self,
                                        task_plan: dict,
                                        parallelization: dict,
                                        request_analysis: dict) -> list:
        """Phase 3: Worker Prompt Generation."""
        print("\n[Phase 3] Worker Prompt Generation...")

        # Defensive parsing of optional meta_actions embedded in request/task
        meta_actions_raw = None
        if isinstance(request_analysis, dict):
            meta_actions_raw = request_analysis.get("meta_actions")
        elif isinstance(task_plan, dict):
            meta_actions_raw = task_plan.get("meta_actions")

        try:
            parsed_meta = MetaActionsHandler.parse(meta_actions_raw)
            if parsed_meta:
                # Register parsed meta-actions in state for downstream phases
                self.state_manager.state["meta_actions"] = parsed_meta
                print(f"  Meta-actions registered: {len(parsed_meta)}")
        except Exception as e:
            print(f"  ⚠ meta_actions parse failed: {e}")

        worker_prompts = self.delegation_engine.generate_worker_prompts(
            task_plan, parallelization, request_analysis
        )

        output_file = self.work_dir / "worker_prompts.json"
        with open(output_file, 'w') as f:
            json.dump(worker_prompts, f, indent=2)

        self.state_manager.add_file("worker_prompts", str(output_file))
        self.state_manager.complete_phase("phase_3")

        print(f"  Generated {len(worker_prompts)} worker prompts")

        return worker_prompts

    def phase_4_parallel_execution(self, worker_prompts: list) -> list:
        """Phase 4: Parallel Worker Execution."""
        print("\n[Phase 4] Parallel Worker Execution...")

        worker_results = self.parallel_executor.execute_with_retry(
            worker_prompts,
            self.worker_spawner,
            max_retries=2,
            state_manager=self.state_manager,
            work_dir=self.work_dir
        )

        output_file = self.work_dir / "worker_results.json"
        with open(output_file, 'w') as f:
            json.dump(worker_results, f, indent=2)

        failed_count = len([r for r in worker_results if r.get("status") == "failed"])
        self.state_manager.state["metadata"]["failed_workers"] = failed_count
        self.state_manager.add_file("worker_results", str(output_file))
        self.state_manager.complete_phase("phase_4")

        print(f"  Completed: {len(worker_results) - failed_count}/{len(worker_results)}")
        if failed_count > 0:
            print(f"  Failed: {failed_count}")

        return worker_results

    def phase_5_response_evaluation(self,
                                    worker_results: list,
                                    task_plan: dict,
                                    request_analysis: dict) -> dict:
        """Phase 5: Response Evaluation."""
        print("\n[Phase 5] Response Evaluation...")

        evaluation_results = self.response_evaluator.evaluate_responses(
            worker_results,
            task_plan,
            request_analysis,
            use_ai_evaluation=False,
            worker_spawner=self.worker_spawner
        )

        output_file = self.work_dir / "evaluation_results.json"
        with open(output_file, 'w') as f:
            json.dump(evaluation_results, f, indent=2)

        self.state_manager.add_file("evaluation_report", str(output_file))
        self.state_manager.complete_phase("phase_5")

        print(f"  Average Quality: {evaluation_results['overall_quality']['average_score']}/100")
        print(f"  Accepted: {evaluation_results['passed_workers']}")
        print(f"  Flagged: {evaluation_results['flagged_workers']}")
        print(f"  Rejected: {evaluation_results['failed_workers']}")

        return evaluation_results

    def phase_6_result_synthesis(self,
                                worker_results: list,
                                evaluation_results: dict,
                                task_plan: dict,
                                request_analysis: dict) -> dict:
        """Phase 6: Result Synthesis."""
        print("\n[Phase 6] Result Synthesis...")

        synthesis_result = self.result_synthesizer.synthesize_results(
            worker_results,
            evaluation_results,
            task_plan,
            request_analysis,
            self.worker_spawner
        )

        output_file = self.work_dir / "synthesis_result.json"
        with open(output_file, 'w') as f:
            json.dump(synthesis_result, f, indent=2)

        synthesis_md = self.work_dir / "synthesis_result.md"
        with open(synthesis_md, 'w') as f:
            f.write(synthesis_result.get("synthesis_output", ""))

        self.state_manager.state["metadata"]["synthesis_strategy"] = synthesis_result.get("strategy_used", "unknown")
        self.state_manager.add_file("synthesis_result", str(synthesis_md))
        self.state_manager.complete_phase("phase_6")

        print(f"  Strategy: {synthesis_result.get('strategy_used', 'unknown')}")
        print(f"  Sources Included: {synthesis_result.get('accepted_workers', 0)}")

        return synthesis_result

    def phase_7_meta_review(self,
                           task_plan: dict,
                           worker_results: list,
                           evaluation_results: dict,
                           synthesis_result: dict,
                           request_analysis: dict) -> dict:
        """Phase 7: Enhanced Meta-Cognitive Review with Iteration."""
        print("\n[Phase 7] Meta-Cognitive Review with Iteration...")

        iteration_complete = False
        max_iterations = 3
        previous_quality = None

        while not iteration_complete:
            current_iter = self.state_manager.get_current_iteration()
            print(f"  Iteration {current_iter + 1}/{max_iterations}")

            quality_analysis = self.meta_cognitive_reviewer.analyze_quality(
                worker_results,
                evaluation_results,
                synthesis_result,
                request_analysis
            )

            self.state_manager.record_quality_analysis(quality_analysis)

            print(f"    Quality Score: {quality_analysis['overall_score']}/100")
            print(f"    Confidence: {quality_analysis['confidence']}")

            decision, strategy, confidence, reasoning = \
                self.meta_cognitive_reviewer.make_iteration_decision(
                    quality_analysis,
                    current_iteration=current_iter,
                    max_iterations=max_iterations,
                    previous_quality=previous_quality
                )

            self.state_manager.record_iteration_decision({
                "hypothesis": self._extract_hypothesis(quality_analysis, strategy),
                "evidence": self._extract_evidence(quality_analysis),
                "confidence": confidence,
                "decision": decision,
                "strategy": strategy,
                "reasoning": reasoning,
                "quality_score": quality_analysis["overall_score"]
            })

            print(f"    Decision: {decision}")
            if strategy:
                print(f"    Strategy: {strategy}")
            print(f"    Reasoning: {reasoning}")

            self.state_manager.update_best_synthesis(
                synthesis_result,
                quality_analysis["overall_score"]
            )

            if decision == "accept":
                iteration_complete = True
                meta_review = self._build_meta_review(
                    quality_analysis,
                    decision,
                    task_plan,
                    worker_results,
                    evaluation_results
                )

            elif decision == "fail":
                iteration_complete = True
                meta_review = self._build_failure_report(
                    quality_analysis,
                    reasoning
                )

            elif decision == "iterate":
                if current_iter >= max_iterations - 1:
                    iteration_complete = True
                    best_synthesis = self.state_manager.get_best_synthesis()
                    if best_synthesis:
                        synthesis_result = best_synthesis
                    meta_review = self._build_bounded_acceptance(
                        quality_analysis,
                        current_iter + 1
                    )
                else:
                    quality_before = quality_analysis["overall_score"]

                    print(f"    Executing iteration strategy: {strategy}")
                    synthesis_result, worker_results, evaluation_results = \
                        self._execute_iteration_strategy(
                            strategy,
                            task_plan,
                            request_analysis,
                            quality_analysis,
                            worker_results,
                            evaluation_results,
                            synthesis_result
                        )

                    quality_analysis_after = self.meta_cognitive_reviewer.analyze_quality(
                        worker_results,
                        evaluation_results,
                        synthesis_result,
                        request_analysis
                    )
                    quality_after = quality_analysis_after["overall_score"]

                    self.state_manager.record_iteration_result(
                        iteration=current_iter + 1,
                        trigger=self._extract_trigger(quality_analysis),
                        strategy=strategy,
                        quality_before=quality_before,
                        quality_after=quality_after,
                        decision="iterate"
                    )

                    print(f"    Quality improved: {quality_before:.1f} → {quality_after:.1f}")

                    previous_quality = quality_before
                    self.state_manager.increment_iteration()

        output_file = self.work_dir / "meta_review.json"
        with open(output_file, 'w') as f:
            json.dump(meta_review, f, indent=2)

        self.state_manager.add_file("meta_review", str(output_file))
        self.state_manager.state["metadata"]["final_quality_score"] = quality_analysis["overall_score"]
        self.state_manager.complete_phase("phase_7")

        print(f"  Final Decision: {meta_review['decision']}")
        print(f"  Total Iterations: {self.state_manager.get_current_iteration()}")
        print(f"  Final Quality: {quality_analysis['overall_score']}/100")

        return meta_review

    def _execute_iteration_strategy(self,
                                    strategy: str,
                                    task_plan: dict,
                                    request_analysis: dict,
                                    quality_analysis: dict,
                                    worker_results: list,
                                    evaluation_results: dict,
                                    synthesis_result: dict) -> tuple:
        """
        Execute iteration strategy.

        Args:
            strategy: Strategy to execute
            task_plan: Task plan
            request_analysis: Request analysis
            quality_analysis: Quality analysis
            worker_results: Worker results
            evaluation_results: Evaluation results
            synthesis_result: Current synthesis result

        Returns:
            (new_synthesis_result, worker_results, evaluation_results)
        """
        if strategy == "re_extract_synthesis":
            return self._strategy_re_extract_synthesis(
                worker_results, evaluation_results, task_plan, request_analysis
            )

        elif strategy == "re_execute_failed_workers":
            return self._strategy_re_execute_failed_workers(
                worker_results, evaluation_results, task_plan, request_analysis
            )

        elif strategy == "refine_synthesis_weights":
            return self._strategy_refine_synthesis_weights(
                worker_results, evaluation_results, task_plan, request_analysis
            )

        elif strategy == "re_synthesize_new_strategy":
            return self._strategy_re_synthesize_new_strategy(
                worker_results, evaluation_results, task_plan, request_analysis, synthesis_result
            )

        elif strategy == "re_plan_decomposition":
            return self._strategy_re_plan_decomposition(
                task_plan, request_analysis, worker_results, evaluation_results
            )

        else:
            return synthesis_result, worker_results, evaluation_results

    def _strategy_re_extract_synthesis(self,
                                       worker_results: list,
                                       evaluation_results: dict,
                                       task_plan: dict,
                                       request_analysis: dict) -> tuple:
        """Re-run Phase 6 with evidence_database strategy to prevent information loss."""
        print("      Strategy: Re-extracting synthesis with evidence_database")

        original_strategy = self.result_synthesizer._select_synthesis_strategy(
            worker_results, task_plan, request_analysis
        )

        task_plan_modified = task_plan.copy()
        request_analysis_modified = request_analysis.copy()
        request_analysis_modified["task_type"] = "comparison"

        synthesis_result = self.result_synthesizer._evidence_database_strategy(
            worker_results,
            evaluation_results,
            self.worker_spawner
        )
        synthesis_result["strategy_used"] = "evidence_db"
        synthesis_result["previous_strategy"] = original_strategy
        synthesis_result["iteration_reason"] = "information_loss_prevention"

        return synthesis_result, worker_results, evaluation_results

    def _strategy_re_execute_failed_workers(self,
                                           worker_results: list,
                                           evaluation_results: dict,
                                           task_plan: dict,
                                           request_analysis: dict) -> tuple:
        """Re-execute failed workers with refined prompts."""
        print("      Strategy: Re-executing failed workers")

        failed_workers = [
            r for r in worker_results
            if evaluation_results["individual_evaluations"].get(
                r.get("worker_id"), {}
            ).get("quality_gate") == "reject"
        ]

        if not failed_workers:
            return self._strategy_refine_synthesis_weights(
                worker_results, evaluation_results, task_plan, request_analysis
            )

        print(f"      Re-executing {len(failed_workers)} failed workers")

        new_worker_results = []
        for result in worker_results:
            worker_id = result.get("worker_id")
            quality_gate = evaluation_results["individual_evaluations"].get(
                worker_id, {}
            ).get("quality_gate")

            if quality_gate == "reject":
                task_id = result.get("task_id")
                prompt = result.get("prompt", "")

                refined_prompt = f"""{prompt}

IMPORTANT: Previous attempt failed quality checks. Please ensure:
1. Include specific evidence and citations
2. Maintain clear structure with headers
3. Avoid vague claims without support
4. Double-check for contradictions"""

                try:
                    output = self.worker_spawner.call_worker(
                        prompt=refined_prompt,
                        complexity="high",
                        context=f"Re-execution: {task_id}"
                    )

                    new_worker_results.append({
                        "worker_id": worker_id,
                        "task_id": task_id,
                        "output": output,
                        "status": "success",
                        "prompt": refined_prompt,
                        "iteration": "re_executed"
                    })
                except Exception as e:
                    print(f"        Re-execution failed for {worker_id}: {e}")
                    new_worker_results.append(result)
            else:
                new_worker_results.append(result)

        new_evaluation_results = self.response_evaluator.evaluate_responses(
            new_worker_results,
            task_plan,
            request_analysis,
            use_ai_evaluation=False,
            worker_spawner=self.worker_spawner
        )

        new_synthesis_result = self.result_synthesizer.synthesize_results(
            new_worker_results,
            new_evaluation_results,
            task_plan,
            request_analysis,
            self.worker_spawner
        )
        new_synthesis_result["iteration_reason"] = "re_executed_failed_workers"

        return new_synthesis_result, new_worker_results, new_evaluation_results

    def _strategy_refine_synthesis_weights(self,
                                          worker_results: list,
                                          evaluation_results: dict,
                                          task_plan: dict,
                                          request_analysis: dict) -> tuple:
        """Apply quality-weighted synthesis."""
        print("      Strategy: Applying quality-weighted synthesis")

        synthesis_result = self.result_synthesizer.synthesize_with_quality_weights(
            worker_results,
            evaluation_results,
            self.worker_spawner,
            task_plan,
            request_analysis
        )
        synthesis_result["iteration_reason"] = "quality_weighted_refinement"

        return synthesis_result, worker_results, evaluation_results

    def _strategy_re_synthesize_new_strategy(self,
                                            worker_results: list,
                                            evaluation_results: dict,
                                            task_plan: dict,
                                            request_analysis: dict,
                                            current_synthesis: dict) -> tuple:
        """Override synthesis strategy and retry."""
        print("      Strategy: Re-synthesizing with alternative strategy")

        current_strategy = current_synthesis.get("strategy_used", "aggregation")

        strategy_alternatives = {
            "aggregation": "consensus",
            "consensus": "iterative",
            "iterative": "evidence_db",
            "evidence_db": "aggregation"
        }

        new_strategy = strategy_alternatives.get(current_strategy, "consensus")

        print(f"        Changing from {current_strategy} to {new_strategy}")

        if new_strategy == "consensus":
            synthesis_result = self.result_synthesizer._consensus_strategy(
                worker_results, evaluation_results, self.worker_spawner
            )
        elif new_strategy == "iterative":
            synthesis_result = self.result_synthesizer._iterative_integration_strategy(
                worker_results, evaluation_results, self.worker_spawner
            )
        elif new_strategy == "evidence_db":
            synthesis_result = self.result_synthesizer._evidence_database_strategy(
                worker_results, evaluation_results, self.worker_spawner
            )
        else:
            synthesis_result = self.result_synthesizer._aggregation_strategy(
                worker_results, evaluation_results, self.worker_spawner
            )

        synthesis_result["strategy_used"] = new_strategy
        synthesis_result["previous_strategy"] = current_strategy
        synthesis_result["iteration_reason"] = "strategy_mismatch_correction"

        return synthesis_result, worker_results, evaluation_results

    def _strategy_re_plan_decomposition(self,
                                       task_plan: dict,
                                       request_analysis: dict,
                                       worker_results: list,
                                       evaluation_results: dict) -> tuple:
        """Re-run Phase 1 with feedback from execution."""
        print("      Strategy: Re-planning task decomposition (COMPLEX - using current results)")

        synthesis_result = self.result_synthesizer.synthesize_with_quality_weights(
            worker_results,
            evaluation_results,
            self.worker_spawner,
            task_plan,
            request_analysis
        )
        synthesis_result["iteration_reason"] = "re_planning_attempted_using_best_available"

        return synthesis_result, worker_results, evaluation_results

    def _build_meta_review(self,
                          quality_analysis: dict,
                          decision: str,
                          task_plan: dict,
                          worker_results: list,
                          evaluation_results: dict) -> dict:
        """Build meta-review for accept decision."""
        return {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "quality_score": quality_analysis["overall_score"],
            "confidence": quality_analysis["confidence"],
            "dimensions": quality_analysis["dimensions"],
            "task_plan_quality": "good" if len(task_plan.get("subtasks", [])) > 0 else "poor",
            "worker_performance": {
                "total": len(worker_results),
                "successful": len([r for r in worker_results if r.get("status") == "success"]),
                "failed": len([r for r in worker_results if r.get("status") == "failed"])
            },
            "quality_assessment": evaluation_results.get("overall_quality", {}),
            "iterations": self.state_manager.get_current_iteration(),
            "iteration_history": self.state_manager.state.get("iteration_state", {}).get("iteration_history", [])
        }

    def _build_failure_report(self,
                             quality_analysis: dict,
                             reasoning: str) -> dict:
        """Build meta-review for fail decision."""
        return {
            "timestamp": datetime.now().isoformat(),
            "decision": "fail",
            "quality_score": quality_analysis["overall_score"],
            "confidence": quality_analysis["confidence"],
            "reasoning": reasoning,
            "dimensions": quality_analysis["dimensions"],
            "iterations": self.state_manager.get_current_iteration()
        }

    def _build_bounded_acceptance(self,
                                  quality_analysis: dict,
                                  iterations: int) -> dict:
        """Build meta-review for bounded acceptance."""
        return {
            "timestamp": datetime.now().isoformat(),
            "decision": "accept",
            "acceptance_type": "bounded",
            "quality_score": quality_analysis["overall_score"],
            "confidence": quality_analysis["confidence"],
            "reasoning": f"Max iterations ({iterations}) reached. Accepting best result.",
            "dimensions": quality_analysis["dimensions"],
            "iterations": iterations,
            "iteration_history": self.state_manager.state.get("iteration_state", {}).get("iteration_history", [])
        }

    def _extract_hypothesis(self, quality_analysis: dict, strategy: str) -> str:
        """Extract hypothesis from quality analysis."""
        dimensions = quality_analysis["dimensions"]

        if strategy == "re_extract_synthesis":
            info_loss = dimensions.get("information_completeness", {})
            if info_loss.get("issues"):
                return info_loss["issues"][0]
            return "Information loss detected in synthesis"

        elif strategy == "re_execute_failed_workers":
            quality_deg = dimensions.get("quality_assessment", {})
            if quality_deg.get("issues"):
                return quality_deg["issues"][0]
            return "High worker failure rate"

        elif strategy == "refine_synthesis_weights":
            return "Quality weighting will improve synthesis"

        elif strategy == "re_synthesize_new_strategy":
            coherence = dimensions.get("synthesis_coherence", {})
            if coherence.get("issues"):
                return coherence["issues"][0]
            return "Synthesis strategy mismatch"

        else:
            return "Quality improvement needed"

    def _extract_evidence(self, quality_analysis: dict) -> list:
        """Extract evidence from quality analysis."""
        evidence = []
        dimensions = quality_analysis["dimensions"]

        for dim_name, dim_data in dimensions.items():
            if dim_data.get("issues"):
                evidence.extend(dim_data["issues"])

        return evidence[:5]

    def _extract_trigger(self, quality_analysis: dict) -> str:
        """Extract trigger from quality analysis."""
        dimensions = quality_analysis["dimensions"]

        for dim_name, dim_data in dimensions.items():
            if dim_data.get("trigger_iteration", False):
                return dim_name

        return "quality_threshold"

    def phase_8_final_report(self,
                            request_analysis: dict,
                            task_plan: dict,
                            parallelization: dict,
                            worker_results: list,
                            evaluation_results: dict,
                            synthesis_result: dict,
                            meta_review: dict) -> Path:
        """Phase 8: Final Report Generation."""
        print("\n[Phase 8] Final Report Generation...")

        report_path = self.work_dir / "final_report.md"

        with open(report_path, 'w') as f:
            f.write("# Multi-Agent Orchestration Report\n\n")

            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Session ID**: {self.state_manager.state['session_id']}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"**Goal**: {request_analysis.get('goal', 'N/A')}\n\n")
            f.write(f"**Task Type**: {request_analysis.get('task_type', 'N/A')}\n\n")
            f.write(f"**Workers**: {len(worker_results)}\n\n")
            f.write(f"**Quality Score**: {evaluation_results['overall_quality']['average_score']}/100\n\n")
            f.write(f"**Synthesis Strategy**: {synthesis_result.get('strategy_used', 'unknown')}\n\n")

            f.write("## Methodology\n\n")
            f.write(f"### Task Decomposition\n\n")
            f.write(f"- Subtasks: {len(task_plan.get('subtasks', []))}\n")
            f.write(f"- Parallelization: {parallelization['worker_count']} workers\n")
            f.write(f"- Strategy: {synthesis_result.get('strategy_used', 'unknown')}\n\n")

            f.write("## Synthesis Results\n\n")
            f.write(synthesis_result.get("synthesis_output", "No synthesis output"))
            f.write("\n\n")

            iteration_state = self.state_manager.state.get("iteration_state", {})
            total_iterations = iteration_state.get("current_iteration", 0)

            if total_iterations > 0:
                f.write("## Iteration Summary\n\n")
                f.write(f"- **Total Iterations**: {total_iterations}\n")

                final_quality = self.state_manager.state.get("metadata", {}).get("final_quality_score", 0)
                best_quality = iteration_state.get("best_quality_score", 0)
                f.write(f"- **Final Quality**: {final_quality}/100\n")
                f.write(f"- **Best Quality Achieved**: {best_quality}/100\n\n")

                iteration_history = iteration_state.get("iteration_history", [])
                if iteration_history:
                    f.write("### Iteration Details\n\n")
                    for iter_record in iteration_history:
                        iter_num = iter_record.get("iteration", 0)
                        trigger = iter_record.get("trigger", "unknown")
                        strategy = iter_record.get("strategy", "unknown")
                        quality_before = iter_record.get("quality_before", 0)
                        quality_after = iter_record.get("quality_after", 0)
                        improvement = iter_record.get("improvement", 0)

                        f.write(f"#### Iteration {iter_num}\n\n")
                        f.write(f"- **Trigger**: {trigger}\n")
                        f.write(f"- **Strategy**: {strategy}\n")
                        f.write(f"- **Quality Before**: {quality_before}/100\n")
                        f.write(f"- **Quality After**: {quality_after}/100\n")
                        f.write(f"- **Improvement**: {improvement:+.1f}\n\n")

                iteration_decisions = iteration_state.get("iteration_decisions", {})
                if iteration_decisions:
                    f.write("### Decision Trace\n\n")
                    for iter_key in sorted(iteration_decisions.keys()):
                        decision_data = iteration_decisions[iter_key]
                        hypothesis = decision_data.get("hypothesis", "")
                        evidence = decision_data.get("evidence", [])
                        confidence = decision_data.get("confidence", "")
                        decision = decision_data.get("decision", "")
                        reasoning = decision_data.get("reasoning", "")

                        f.write(f"**{iter_key.replace('_', ' ').title()}**\n\n")
                        f.write(f"- **Hypothesis**: {hypothesis}\n")
                        if evidence:
                            f.write(f"- **Evidence**: {evidence[0]}\n")
                        f.write(f"- **Confidence**: {confidence}\n")
                        f.write(f"- **Decision**: {decision}\n")
                        f.write(f"- **Reasoning**: {reasoning}\n\n")

            f.write("## Quality Assessment\n\n")
            f.write(f"- Average Score: {evaluation_results['overall_quality']['average_score']}/100\n")
            f.write(f"- Accepted Workers: {evaluation_results['passed_workers']}\n")
            f.write(f"- Flagged Workers: {evaluation_results['flagged_workers']}\n")
            f.write(f"- Rejected Workers: {evaluation_results['failed_workers']}\n\n")

            f.write("## Worker Contributions\n\n")
            for result in worker_results:
                worker_id = result.get("worker_id", "unknown")
                task_id = result.get("task_id", "unknown")
                status = result.get("status", "unknown")
                eval_score = evaluation_results["individual_evaluations"].get(
                    worker_id, {}
                ).get("score", 0)

                f.write(f"### {worker_id}\n\n")
                f.write(f"- **Task**: {task_id}\n")
                f.write(f"- **Status**: {status}\n")
                f.write(f"- **Quality Score**: {eval_score}/100\n\n")

            f.write("## Appendices\n\n")
            f.write(f"### A. Task Plan\n\n")
            f.write(f"```json\n{json.dumps(task_plan, indent=2)}\n```\n\n")

            f.write(f"### B. State File\n\n")
            f.write(f"State file: `{self.state_manager.state_file}`\n\n")

        self.state_manager.add_file("final_report", str(report_path))
        self.state_manager.complete_phase("phase_8")

        return report_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Multi-Agent Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrator.py --request "Compare document against 10 books"
  python orchestrator.py --resume ~/output/.orchestrator_state.json
        """
    )

    parser.add_argument('--request', type=str, help='User request')
    parser.add_argument('--resume', type=str, help='Path to state file to resume from')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: <project_root>/Temp/agent-orchestrator)')

    args = parser.parse_args()

    if not args.request and not args.resume:
        parser.error("Either --request or --resume is required")

    orchestrator = AgentOrchestrator(work_dir=args.output_dir)

    if args.resume:
        orchestrator.state_manager.state_file = Path(args.resume)
        user_request = orchestrator.state_manager.state.get("metadata", {}).get("user_request", "")
        final_report = orchestrator.run(user_request, resume=True)
    else:
        final_report = orchestrator.run(args.request, resume=False)

    print(f"\nFinal report available at: {final_report}")


if __name__ == '__main__':
    main()
