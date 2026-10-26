#!/usr/bin/env python3
"""Minimal end-to-end test for agent-orchestrator."""

import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from orchestrator import AgentOrchestrator


def test_minimal_orchestration():
    """Test minimal orchestration workflow with a simple request."""
    print("=" * 70)
    print(" Minimal End-to-End Orchestration Test")
    print("=" * 70)

    work_dir = tempfile.mkdtemp(prefix="orchestrator_test_")
    print(f"\nWork directory: {work_dir}")

    try:
        print("\n[1] Initializing orchestrator...")
        orchestrator = AgentOrchestrator(work_dir=work_dir)
        print(f"✓ Initialized with worker: {orchestrator.worker_spawner.worker_type}")

        print("\n[2] Testing Phase 0: Request Understanding...")
        request = "Analyze the difference between lists and tuples in Python"

        try:
            analysis = orchestrator.phase_0_request_understanding(request)
            print(f"✓ Goal: {analysis.get('goal', 'N/A')[:80]}")
            print(f"✓ Task Type: {analysis.get('task_type', 'N/A')}")
            print(f"✓ Complexity: {analysis.get('complexity', 'N/A')}")

            analysis_file = Path(work_dir) / "request_analysis.json"
            if analysis_file.exists():
                print(f"✓ Analysis saved to: {analysis_file}")

        except Exception as e:
            print(f"✗ Phase 0 failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n[3] Testing Phase 1: Task Decomposition...")
        try:
            task_plan = orchestrator.phase_1_task_decomposition(analysis, request)
            subtasks = task_plan.get("subtasks", [])
            print(f"✓ Generated {len(subtasks)} subtask(s)")
            for i, task in enumerate(subtasks[:3], 1):
                print(f"  {i}. {task.get('description', 'N/A')[:70]}")

            plan_file = Path(work_dir) / "task_plan.json"
            if plan_file.exists():
                print(f"✓ Task plan saved to: {plan_file}")

        except Exception as e:
            print(f"✗ Phase 1 failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n[4] Testing Phase 2: Parallelization Strategy...")
        try:
            parallelization = orchestrator.phase_2_parallelization_strategy(task_plan)
            print(f"✓ Worker count: {parallelization['worker_count']}")
            print(f"✓ Parallel tasks: {parallelization['parallel_tasks_count']}")
            print(f"✓ Sequential tasks: {parallelization['sequential_tasks_count']}")

        except Exception as e:
            print(f"✗ Phase 2 failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n" + "=" * 70)
        print("✓ Minimal orchestration test PASSED")
        print("=" * 70)

        print("\nGenerated files:")
        for file in Path(work_dir).glob("*.json"):
            size = file.stat().st_size
            print(f"  - {file.name} ({size:,} bytes)")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\nCleaning up: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == '__main__':
    success = test_minimal_orchestration()
    sys.exit(0 if success else 1)
