"""
State Management for Agent Orchestrator
Handles workflow state persistence, resumability, and recovery.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class StateManager:
    """Manages workflow state for resumability and error recovery."""

    def __init__(self, work_dir: str = None,
                 state_file: str = ".orchestrator_state.json",
                 enable_backup: bool = True,
                 max_backups: int = 5):
        """
        Initialize StateManager.

        Args:
            work_dir: Working directory for outputs. If None, uses ./Temp/agent-orchestrator under the current directory
            state_file: State file name
            enable_backup: Enable automatic backups
            max_backups: Maximum number of backup files to keep
        """
        if work_dir is None:
            project_root = Path.cwd()
            work_dir = str(project_root / "Temp" / "agent-orchestrator")

        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.work_dir / state_file
        self.enable_backup = enable_backup
        self.max_backups = max_backups
        self.state = self._initialize_state()

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize default state structure."""
        return {
            "version": "1.1",
            "session_id": None,
            "created_at": None,
            "updated_at": None,
            "phase_complete": {
                "phase_0": False,  # Request Understanding
                "phase_1": False,  # Task Decomposition
                "phase_2": False,  # Parallelization Strategy
                "phase_3": False,  # Worker Prompt Generation
                "phase_4": False,  # Parallel Worker Execution
                "phase_5": False,  # Response Evaluation
                "phase_6": False,  # Result Synthesis
                "phase_7": False,  # Meta-Review
                "phase_8": False   # Final Report
            },
            "current_phase": "phase_0",
            "files": {
                "request_analysis": None,
                "task_plan": None,
                "worker_prompts": [],
                "worker_results": [],
                "evaluation_report": None,
                "synthesis_result": None,
                "meta_review": None,
                "final_report": None
            },
            "task_plan": None,
            "parallelization": {
                "worker_count": 0,
                "parallel_groups": [],
                "sequential_tasks": []
            },
            "worker_results": {},
            "evaluation_scores": {},
            "iteration_state": {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            },
            "meta_cognitive_trace": {
                "quality_analyses": [],
                "decisions_made": [],
                "improvement_trajectory": []
            },
            "metadata": {
                "user_request": None,
                "task_count": 0,
                "worker_count": 0,
                "failed_workers": 0,
                "synthesis_strategy": None,
                "total_execution_time": None,
                "total_iterations": 0,
                "final_quality_score": None
            },
            "errors": [],
            "recovery_attempts": 0
        }

    def load_state(self) -> bool:
        """
        Load state from file if exists.

        Returns:
            True if state loaded, False if starting fresh
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"WARNING: Corrupted state file: {e}")
            return self._attempt_recovery()
        except Exception as e:
            print(f"ERROR loading state: {e}")
            return False

    def save_state(self, backup: bool = True) -> bool:
        """
        Save current state to file.

        Args:
            backup: Create backup before saving

        Returns:
            True if successful
        """
        self.state["updated_at"] = datetime.now().isoformat()

        if backup and self.enable_backup:
            self._create_backup()

        try:
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)

            with open(temp_file, 'r') as f:
                json.load(f)

            shutil.move(str(temp_file), str(self.state_file))
            return True
        except Exception as e:
            print(f"ERROR saving state: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    def _create_backup(self):
        """Create timestamped backup of state file."""
        if not self.state_file.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.state_file.with_suffix(f'.{timestamp}.backup')

        try:
            shutil.copy2(self.state_file, backup_file)
            self._cleanup_old_backups()
        except Exception as e:
            print(f"WARNING: Backup creation failed: {e}")

    def _cleanup_old_backups(self):
        """Remove old backups exceeding max_backups limit."""
        backups = sorted(self.work_dir.glob('.orchestrator_state.*.backup'))

        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
            except Exception as e:
                print(f"WARNING: Could not delete old backup {oldest}: {e}")

    def _attempt_recovery(self) -> bool:
        """Attempt to recover from corrupted state file."""
        print("Attempting state recovery...")

        backups = sorted(self.work_dir.glob('.orchestrator_state.*.backup'), reverse=True)
        for backup in backups:
            try:
                with open(backup, 'r') as f:
                    self.state = json.load(f)
                print(f"✓ Recovered from backup: {backup.name}")
                return True
            except Exception:
                continue

        print("No valid backups. Reconstructing from output files...")
        return self._reconstruct_from_files()

    def _reconstruct_from_files(self) -> bool:
        """Reconstruct state from existing output files."""
        reconstructed = self._initialize_state()

        request_file = self.work_dir / "request_analysis.json"
        task_plan_file = self.work_dir / "task_plan.json"
        synthesis_file = self.work_dir / "synthesis_result.md"
        report_file = self.work_dir / "final_report.md"

        if request_file.exists():
            reconstructed["phase_complete"]["phase_0"] = True
            reconstructed["files"]["request_analysis"] = str(request_file)
            reconstructed["current_phase"] = "phase_1"

        if task_plan_file.exists():
            reconstructed["phase_complete"]["phase_1"] = True
            reconstructed["files"]["task_plan"] = str(task_plan_file)
            reconstructed["current_phase"] = "phase_2"

        worker_results = list(self.work_dir.glob("worker_results/worker_*.json"))
        if worker_results:
            reconstructed["phase_complete"]["phase_4"] = True
            reconstructed["files"]["worker_results"] = [str(f) for f in worker_results]
            reconstructed["current_phase"] = "phase_5"

        if synthesis_file.exists():
            reconstructed["phase_complete"]["phase_6"] = True
            reconstructed["files"]["synthesis_result"] = str(synthesis_file)
            reconstructed["current_phase"] = "phase_7"

        if report_file.exists():
            reconstructed["phase_complete"]["phase_8"] = True
            reconstructed["files"]["final_report"] = str(report_file)

        if reconstructed["phase_complete"]["phase_0"]:
            self.state = reconstructed
            print("✓ State reconstructed from output files")
            self.save_state(backup=False)
            return True

        print("✗ Reconstruction failed: No output files found")
        return False

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start new orchestration session.

        Args:
            session_id: Optional custom session ID

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.state["session_id"] = session_id
        self.state["created_at"] = datetime.now().isoformat()
        self.save_state(backup=False)
        return session_id

    def complete_phase(self, phase: str):
        """Mark phase as complete and advance to next phase."""
        phase_key = f"phase_{phase}" if not phase.startswith("phase_") else phase
        self.state["phase_complete"][phase_key] = True

        phase_order = ["phase_0", "phase_1", "phase_2", "phase_3",
                      "phase_4", "phase_5", "phase_6", "phase_7", "phase_8"]
        current_idx = phase_order.index(phase_key)
        if current_idx < len(phase_order) - 1:
            self.state["current_phase"] = phase_order[current_idx + 1]

        self.save_state()

    def add_file(self, file_type: str, file_path: str):
        """
        Register output file in state.

        Args:
            file_type: Type of file
            file_path: Path to file
        """
        if file_type in ["worker_prompts", "worker_results"]:
            if file_path not in self.state["files"][file_type]:
                self.state["files"][file_type].append(file_path)
        else:
            self.state["files"][file_type] = file_path
        self.save_state()

    def add_worker_result(self, worker_id: str, result: Dict[str, Any]):
        """Store worker result in state."""
        self.state["worker_results"][worker_id] = result
        self.save_state()

    def add_evaluation_score(self, worker_id: str, score: int):
        """Store evaluation score for worker."""
        self.state["evaluation_scores"][worker_id] = score
        self.save_state()

    def log_error(self, error: str, phase: Optional[str] = None):
        """
        Log error to state.

        Args:
            error: Error message
            phase: Phase where error occurred
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase or self.state["current_phase"],
            "error": error
        }
        self.state["errors"].append(error_entry)
        self.state["recovery_attempts"] += 1
        self.save_state()

    def get_resumption_info(self) -> Dict[str, Any]:
        """
        Get information for resuming interrupted workflow.

        Returns:
            Dictionary with resumption details
        """
        info = {
            "can_resume": self.state["phase_complete"]["phase_0"],
            "session_id": self.state["session_id"],
            "current_phase": self.state["current_phase"],
            "completed_phases": [p for p, done in self.state["phase_complete"].items() if done],
            "pending_phases": [p for p, done in self.state["phase_complete"].items() if not done],
            "files_available": {k: v for k, v in self.state["files"].items() if v},
            "worker_count": self.state["metadata"]["worker_count"],
            "failed_workers": self.state["metadata"]["failed_workers"],
            "last_updated": self.state["updated_at"],
            "errors": len(self.state["errors"])
        }
        return info

    def clear_state(self):
        """Clear state and start fresh."""
        self.state = self._initialize_state()
        if self.state_file.exists():
            self.state_file.unlink()

    def get_current_iteration(self) -> int:
        """Get current iteration number."""
        if "iteration_state" not in self.state:
            self.state["iteration_state"] = {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            }
        return self.state["iteration_state"]["current_iteration"]

    def increment_iteration(self):
        """Increment iteration counter and save state."""
        if "iteration_state" not in self.state:
            self.state["iteration_state"] = {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            }

        self.state["iteration_state"]["current_iteration"] += 1
        self.state["metadata"]["total_iterations"] = self.state["iteration_state"]["current_iteration"]
        self.save_state()

    def record_iteration_decision(self, decision_metadata: Dict[str, Any]):
        """
        Record iteration decision with hypothesis-evidence-reasoning trace.

        Args:
            decision_metadata: Decision information including hypothesis, evidence,
                             confidence, decision, and reasoning
        """
        if "iteration_state" not in self.state:
            self.state["iteration_state"] = {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            }

        if "meta_cognitive_trace" not in self.state:
            self.state["meta_cognitive_trace"] = {
                "quality_analyses": [],
                "decisions_made": [],
                "improvement_trajectory": []
            }

        iteration = self.state["iteration_state"]["current_iteration"]
        iteration_key = f"iteration_{iteration}"

        self.state["iteration_state"]["iteration_decisions"][iteration_key] = {
            "hypothesis": decision_metadata.get("hypothesis", ""),
            "evidence": decision_metadata.get("evidence", []),
            "confidence": decision_metadata.get("confidence", ""),
            "decision": decision_metadata.get("decision", ""),
            "strategy": decision_metadata.get("strategy", ""),
            "reasoning": decision_metadata.get("reasoning", ""),
            "timestamp": datetime.now().isoformat()
        }

        self.state["meta_cognitive_trace"]["decisions_made"].append({
            "iteration": iteration,
            "decision": decision_metadata.get("decision", ""),
            "strategy": decision_metadata.get("strategy", ""),
            "quality_score": decision_metadata.get("quality_score", 0),
            "timestamp": datetime.now().isoformat()
        })

        self.save_state()

    def record_iteration_result(self,
                               iteration: int,
                               trigger: str,
                               strategy: str,
                               quality_before: float,
                               quality_after: float,
                               decision: str):
        """
        Record iteration execution result.

        Args:
            iteration: Iteration number
            trigger: What triggered the iteration
            strategy: Strategy used
            quality_before: Quality score before iteration
            quality_after: Quality score after iteration
            decision: Final decision (accept/iterate/fail)
        """
        if "iteration_state" not in self.state:
            self.state["iteration_state"] = {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            }

        iteration_record = {
            "iteration": iteration,
            "trigger": trigger,
            "strategy": strategy,
            "quality_before": quality_before,
            "quality_after": quality_after,
            "improvement": quality_after - quality_before,
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        }

        self.state["iteration_state"]["iteration_history"].append(iteration_record)

        if "meta_cognitive_trace" not in self.state:
            self.state["meta_cognitive_trace"] = {
                "quality_analyses": [],
                "decisions_made": [],
                "improvement_trajectory": []
            }

        self.state["meta_cognitive_trace"]["improvement_trajectory"].append({
            "iteration": iteration,
            "quality_score": quality_after,
            "improvement": quality_after - quality_before
        })

        if quality_after > self.state["iteration_state"]["best_quality_score"]:
            self.state["iteration_state"]["best_quality_score"] = quality_after

        self.save_state()

    def record_quality_analysis(self, quality_analysis: Dict[str, Any]):
        """
        Record quality analysis for meta-cognitive trace.

        Args:
            quality_analysis: Quality analysis results
        """
        if "meta_cognitive_trace" not in self.state:
            self.state["meta_cognitive_trace"] = {
                "quality_analyses": [],
                "decisions_made": [],
                "improvement_trajectory": []
            }

        self.state["meta_cognitive_trace"]["quality_analyses"].append({
            "iteration": self.get_current_iteration(),
            "overall_score": quality_analysis.get("overall_score", 0),
            "dimensions": quality_analysis.get("dimensions", {}),
            "timestamp": datetime.now().isoformat()
        })

        self.save_state()

    def get_iteration_trajectory(self) -> List[Dict[str, Any]]:
        """
        Get quality improvement trajectory across iterations.

        Returns:
            List of iteration results with quality scores
        """
        if "meta_cognitive_trace" not in self.state:
            return []

        return self.state["meta_cognitive_trace"].get("improvement_trajectory", [])

    def update_best_synthesis(self, synthesis_result: Dict[str, Any], quality_score: float):
        """
        Update best synthesis result if current is better.

        Args:
            synthesis_result: Synthesis result
            quality_score: Quality score
        """
        if "iteration_state" not in self.state:
            self.state["iteration_state"] = {
                "current_iteration": 0,
                "max_iterations": 3,
                "iteration_history": [],
                "iteration_decisions": {},
                "best_quality_score": 0,
                "best_synthesis_result": None
            }

        if quality_score > self.state["iteration_state"]["best_quality_score"]:
            self.state["iteration_state"]["best_quality_score"] = quality_score
            self.state["iteration_state"]["best_synthesis_result"] = synthesis_result
            self.save_state()

    def get_best_synthesis(self) -> Optional[Dict[str, Any]]:
        """Get best synthesis result across all iterations."""
        if "iteration_state" not in self.state:
            return None

        return self.state["iteration_state"].get("best_synthesis_result")

    def __str__(self) -> str:
        """String representation of current state."""
        return json.dumps(self.get_resumption_info(), indent=2)


def main():
    """CLI interface for state management."""
    import argparse

    parser = argparse.ArgumentParser(description='Agent Orchestrator State Manager')
    parser.add_argument('--action', choices=['status', 'clear', 'recover'],
                       required=True, help='Action to perform')
    parser.add_argument('--work-dir', default=None,
                       help='Working directory (default: <project_root>/Temp/agent-orchestrator)')

    args = parser.parse_args()

    manager = StateManager(work_dir=args.work_dir)

    if args.action == 'status':
        if manager.load_state():
            print("Current State:")
            print(manager)
        else:
            print("No active session found")

    elif args.action == 'clear':
        manager.clear_state()
        print("✓ State cleared")

    elif args.action == 'recover':
        if manager._attempt_recovery():
            print("✓ Recovery successful")
            print(manager)
        else:
            print("✗ Recovery failed")


if __name__ == '__main__':
    main()
