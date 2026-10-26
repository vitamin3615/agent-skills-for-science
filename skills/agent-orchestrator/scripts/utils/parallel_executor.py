"""
Parallel Executor for Agent Orchestrator
Manages concurrent worker execution with fault tolerance.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path


class ParallelExecutor:
    """Executes workers in parallel with fault tolerance."""

    def __init__(self, max_workers: int = 5, timeout: int = 600):
        """
        Initialize ParallelExecutor.

        Args:
            max_workers: Maximum number of parallel workers
            timeout: Timeout per worker in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout

    def execute_workers(self,
                       worker_prompts: List[Dict[str, Any]],
                       worker_spawner,
                       state_manager=None,
                       work_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Execute workers in parallel (or sequentially for Gemini due to Docker container conflicts).

        Phase 4: Parallel Worker Execution

        Args:
            worker_prompts: List of worker prompt configurations
            worker_spawner: WorkerSpawner instance
            state_manager: Optional StateManager for resumability
            work_dir: Optional working directory for outputs

        Returns:
            List of worker results
        """
        # CRITICAL FIX: Gemini CLI uses static Docker container names (sandbox-X.X.X-0)
        # which cannot be customized. Running multiple Gemini workers in parallel causes
        # container name conflicts. Force sequential execution for Gemini workers.
        force_sequential = (
            hasattr(worker_spawner, 'worker_type') and
            worker_spawner.worker_type == 'gemini'
        )

        if force_sequential:
            print("⚠ Gemini workers detected - forcing sequential execution to prevent Docker conflicts")
            # Clean up any stale containers before starting
            if hasattr(worker_spawner, '_cleanup_docker_containers'):
                worker_spawner._cleanup_docker_containers()
            # Route all workers to sequential execution
            return self._execute_sequential(
                worker_prompts,
                worker_spawner,
                state_manager,
                work_dir
            )

        parallel_workers = [w for w in worker_prompts if w.get("group", 0) >= 0]
        sequential_workers = [w for w in worker_prompts if w.get("group", -1) < 0]

        results = []

        if parallel_workers:
            print(f"Executing {len(parallel_workers)} workers in parallel...")
            parallel_results = self._execute_parallel(
                parallel_workers,
                worker_spawner,
                state_manager,
                work_dir
            )
            results.extend(parallel_results)

        if sequential_workers:
            print(f"Executing {len(sequential_workers)} workers sequentially...")
            sequential_results = self._execute_sequential(
                sequential_workers,
                worker_spawner,
                state_manager,
                work_dir
            )
            results.extend(sequential_results)

        return results

    def _execute_parallel(self,
                         worker_prompts: List[Dict[str, Any]],
                         worker_spawner,
                         state_manager,
                         work_dir: Optional[Path]) -> List[Dict[str, Any]]:
        """Execute workers in parallel using ThreadPoolExecutor."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_worker = {
                executor.submit(
                    self._execute_single_worker,
                    worker_config,
                    worker_spawner,
                    work_dir
                ): worker_config
                for worker_config in worker_prompts
            }

            for future in as_completed(future_to_worker, timeout=self.timeout * len(worker_prompts)):
                worker_config = future_to_worker[future]
                worker_id = worker_config.get("worker_id", "unknown")

                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)

                    if state_manager:
                        state_manager.add_worker_result(worker_id, result)

                    print(f"✓ Worker {worker_id} completed")

                except Exception as e:
                    error_result = {
                        "worker_id": worker_id,
                        "task_id": worker_config.get("task_id", ""),
                        "output": f"ERROR: {str(e)}",
                        "status": "failed",
                        "error": str(e)
                    }
                    results.append(error_result)

                    if state_manager:
                        state_manager.log_error(f"Worker {worker_id} failed: {e}")

                    print(f"✗ Worker {worker_id} failed: {e}")

        return results

    def _execute_sequential(self,
                           worker_prompts: List[Dict[str, Any]],
                           worker_spawner,
                           state_manager,
                           work_dir: Optional[Path]) -> List[Dict[str, Any]]:
        """Execute workers sequentially."""
        results = []
        is_gemini = hasattr(worker_spawner, 'worker_type') and worker_spawner.worker_type == 'gemini'

        for worker_config in worker_prompts:
            worker_id = worker_config.get("worker_id", "unknown")

            # Clean up Docker containers before each Gemini worker to prevent conflicts
            if is_gemini and hasattr(worker_spawner, '_cleanup_docker_containers'):
                worker_spawner._cleanup_docker_containers()

            try:
                result = self._execute_single_worker(
                    worker_config,
                    worker_spawner,
                    work_dir
                )
                results.append(result)

                if state_manager:
                    state_manager.add_worker_result(worker_id, result)

                print(f"✓ Worker {worker_id} completed")

            except Exception as e:
                error_result = {
                    "worker_id": worker_id,
                    "task_id": worker_config.get("task_id", ""),
                    "output": f"ERROR: {str(e)}",
                    "status": "failed",
                    "error": str(e)
                }
                results.append(error_result)

                if state_manager:
                    state_manager.log_error(f"Worker {worker_id} failed: {e}")

                print(f"✗ Worker {worker_id} failed: {e}")

        return results

    def _execute_single_worker(self,
                              worker_config: Dict[str, Any],
                              worker_spawner,
                              work_dir: Optional[Path]) -> Dict[str, Any]:
        """
        Execute a single worker with adaptive timeout support.

        Args:
            worker_config: Worker configuration with prompt
            worker_spawner: WorkerSpawner instance
            work_dir: Working directory for output

        Returns:
            Worker result
        """
        worker_id = worker_config.get("worker_id", "unknown")
        task_id = worker_config.get("task_id", "unknown")
        prompt = worker_config.get("prompt", "")
        complexity = worker_config.get("complexity", "medium")

        # Support adaptive timeout from worker configuration
        # If not provided, use class default or calculate adaptively
        timeout = worker_config.get("timeout", self.timeout)

        start_time = time.time()

        output = worker_spawner.call_worker(
            prompt=prompt,
            complexity=complexity,
            context=f"Worker {worker_id}",
            timeout=timeout,  # Pass adaptive timeout
            worker_id=worker_id  # Enable workspace isolation for parallel execution
        )

        execution_time = time.time() - start_time

        if work_dir:
            output_file = work_dir / "worker_results" / f"{worker_id}.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(f"Worker: {worker_id}\n")
                f.write(f"Task: {task_id}\n")
                f.write(f"Complexity: {complexity}\n")
                f.write(f"Execution Time: {execution_time:.2f}s\n")
                f.write(f"\n{'='*60}\n\n")
                f.write(output)

        return {
            "worker_id": worker_id,
            "task_id": task_id,
            "output": output,
            "status": "success",
            "execution_time": execution_time,
            "complexity": complexity
        }

    def execute_with_retry(self,
                          worker_prompts: List[Dict[str, Any]],
                          worker_spawner,
                          max_retries: int = 2,
                          state_manager=None,
                          work_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Execute workers with automatic retry on failure.

        Args:
            worker_prompts: Worker configurations
            worker_spawner: WorkerSpawner instance
            max_retries: Maximum retry attempts
            state_manager: StateManager for state persistence
            work_dir: Working directory

        Returns:
            Worker results
        """
        results = self.execute_workers(
            worker_prompts,
            worker_spawner,
            state_manager,
            work_dir
        )

        failed_workers = [r for r in results if r.get("status") == "failed"]

        retry_count = 0
        while failed_workers and retry_count < max_retries:
            retry_count += 1
            print(f"\nRetrying {len(failed_workers)} failed workers (attempt {retry_count}/{max_retries})...")

            retry_prompts = [
                wp for wp in worker_prompts
                if wp.get("worker_id") in [fw.get("worker_id") for fw in failed_workers]
            ]

            retry_results = self.execute_workers(
                retry_prompts,
                worker_spawner,
                state_manager,
                work_dir
            )

            for r in results:
                if r.get("status") == "failed":
                    retry_result = next(
                        (rr for rr in retry_results if rr.get("worker_id") == r.get("worker_id")),
                        None
                    )
                    if retry_result and retry_result.get("status") == "success":
                        r.update(retry_result)

            failed_workers = [r for r in results if r.get("status") == "failed"]

        if failed_workers:
            print(f"\nWARNING: {len(failed_workers)} workers failed after {max_retries} retries")
            for fw in failed_workers:
                print(f"  - {fw.get('worker_id')}: {fw.get('error', 'Unknown error')}")

        return results


def main():
    """CLI for testing parallel executor."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from worker_spawner import WorkerSpawner

    print("Testing ParallelExecutor...")

    skill_dir = Path(__file__).parent.parent.parent
    worker_spawner = WorkerSpawner(skill_dir)
    executor = ParallelExecutor(max_workers=3)

    test_prompts = [
        {
            "worker_id": "worker_1",
            "task_id": "task_1",
            "prompt": "Explain the concept of parallel processing in 50 words.",
            "complexity": "low",
            "group": 0
        },
        {
            "worker_id": "worker_2",
            "task_id": "task_2",
            "prompt": "Explain the concept of concurrent programming in 50 words.",
            "complexity": "low",
            "group": 0
        },
        {
            "worker_id": "worker_3",
            "task_id": "task_3",
            "prompt": "Explain the concept of asynchronous execution in 50 words.",
            "complexity": "low",
            "group": 0
        }
    ]

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        results = executor.execute_workers(
            test_prompts,
            worker_spawner,
            work_dir=work_dir
        )

        print(f"\nCompleted {len(results)} workers")
        for result in results:
            print(f"\n{result['worker_id']}: {result['status']}")
            print(f"Output preview: {result['output'][:100]}...")


if __name__ == '__main__':
    main()
