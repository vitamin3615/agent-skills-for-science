"""
Task Analyzer for Agent Orchestrator
Uses AI-powered sequential thinking for intelligent task decomposition and planning.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class TaskAnalyzer:
    """Analyzes requests and decomposes tasks using AI-powered sequential thinking."""

    def __init__(self, skill_dir: Path, worker_spawner=None):
        """
        Initialize TaskAnalyzer.

        Args:
            skill_dir: Path to skill root directory
            worker_spawner: Optional WorkerSpawner instance for sequential thinking
        """
        self.skill_dir = skill_dir
        self.worker_spawner = worker_spawner

    def _call_sequential_thinking(self, prompt: str, worker_spawner=None, timeout: int = 600) -> str:
        """
        Call worker AI for sequential thinking.

        Args:
            prompt: Prompt for reasoning
            worker_spawner: WorkerSpawner instance
            timeout: Timeout in seconds (default: 600s / 10 min for complex reasoning)

        Returns:
            Reasoning output
        """
        spawner = worker_spawner or self.worker_spawner
        if not spawner:
            raise RuntimeError("WorkerSpawner required for sequential thinking")

        sequential_thinking_prompt = f"""You are an expert at systematic, step-by-step reasoning.

TASK: {prompt}

INSTRUCTIONS:
Think through this problem systematically using a step-by-step approach:
1. Break down the problem into components
2. Analyze each component methodically
3. Reason through relationships and dependencies
4. Synthesize findings into a coherent conclusion

Provide your detailed reasoning followed by your final answer.
"""

        result = spawner.spawn(
            prompt=sequential_thinking_prompt,
            complexity="high",
            timeout=timeout,
            system_prompt="Sequential reasoning and analysis"
        )

        if result['success']:
            return result['output']
        else:
            raise RuntimeError(f"Sequential thinking failed: {result.get('error', 'Unknown error')}")

    def analyze_request(self, user_request: str, worker_spawner=None) -> Dict[str, Any]:
        """
        Analyze user request using AI-powered sequential thinking.

        Phase 0: Request Understanding

        Args:
            user_request: User's request text
            worker_spawner: Optional WorkerSpawner instance

        Returns:
            Dictionary with request analysis
        """
        prompt = f"""Analyze this user request and extract key components:

REQUEST: {user_request}

TASK: Perform systematic analysis to understand:
1. Core Goal: What is the user trying to achieve?
2. Success Criteria: How will we know the task is complete?
3. Requirements: What are the explicit and implicit requirements?
4. Constraints: Are there time, resource, or quality constraints?
5. Expected Output: What form should the final result take?
6. Context Clues: Any domain-specific context (e.g., book comparison, code analysis)?

OUTPUT FORMAT (JSON):
{{
  "goal": "Clear statement of goal",
  "success_criteria": ["criterion 1", "criterion 2"],
  "requirements": ["req 1", "req 2"],
  "constraints": ["constraint 1"],
  "output_format": "Description of expected output",
  "task_type": "comparison|analysis|synthesis|evaluation|mixed",
  "complexity": "low|medium|high",
  "reasoning": "Your step-by-step reasoning"
}}"""

        reasoning_output = self._call_sequential_thinking(prompt, worker_spawner)

        try:
            start_idx = reasoning_output.find('{')
            end_idx = reasoning_output.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = reasoning_output[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "goal": "Parse user request",
                    "success_criteria": ["Complete task"],
                    "requirements": [user_request],
                    "constraints": [],
                    "output_format": "Report",
                    "task_type": "mixed",
                    "complexity": "medium",
                    "reasoning": reasoning_output
                }
        except json.JSONDecodeError:
            analysis = {
                "goal": "Parse user request",
                "success_criteria": ["Complete task"],
                "requirements": [user_request],
                "constraints": [],
                "output_format": "Report",
                "task_type": "mixed",
                "complexity": "medium",
                "reasoning": reasoning_output
            }

        return analysis

    def decompose_task(self, request_analysis: Dict[str, Any],
                      user_request: str,
                      worker_spawner) -> Dict[str, Any]:
        """
        Decompose task into subtasks using worker AI.

        Phase 1: Task Decomposition & Planning

        Args:
            request_analysis: Output from analyze_request
            user_request: Original user request
            worker_spawner: WorkerSpawner instance for delegating to AI

        Returns:
            Task plan with subtasks and dependencies
        """
        meta_prompt_template = self.skill_dir / "worker_prompts" / "meta_orchestrator.txt"

        if meta_prompt_template.exists():
            with open(meta_prompt_template, 'r') as f:
                template = f.read()
        else:
            template = self._get_default_meta_prompt()

        prompt = template.format(
            user_request=user_request,
            goal=request_analysis.get("goal", ""),
            requirements="\n".join(f"- {r}" for r in request_analysis.get("requirements", [])),
            task_type=request_analysis.get("task_type", "mixed"),
            complexity=request_analysis.get("complexity", "medium")
        )

        result = worker_spawner.call_worker(
            prompt=prompt,
            complexity="high",
            context="Task decomposition and planning"
        )

        try:
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                task_plan = json.loads(json_str)
            else:
                task_plan = self._create_fallback_plan(request_analysis, user_request)
        except json.JSONDecodeError:
            task_plan = self._create_fallback_plan(request_analysis, user_request)

        return task_plan

    def determine_parallelization(self, task_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine optimal parallelization strategy.

        Phase 2: Parallelization Strategy

        Args:
            task_plan: Task plan from decompose_task

        Returns:
            Parallelization configuration
        """
        subtasks = task_plan.get("subtasks", [])
        dependencies = task_plan.get("dependencies", {})

        parallel_tasks = []
        sequential_tasks = []

        for task in subtasks:
            task_id = task.get("id", "")
            has_deps = task_id in dependencies and len(dependencies[task_id]) > 0

            if has_deps:
                sequential_tasks.append(task)
            else:
                parallel_tasks.append(task)

        avg_complexity = self._calculate_avg_complexity(subtasks)
        has_heavy_dependencies = len(sequential_tasks) > len(parallel_tasks)

        worker_count = self._determine_worker_count(
            len(parallel_tasks),
            avg_complexity,
            has_heavy_dependencies
        )

        parallel_groups = self._create_parallel_groups(parallel_tasks, worker_count)

        return {
            "worker_count": worker_count,
            "parallel_groups": parallel_groups,
            "sequential_tasks": sequential_tasks,
            "avg_complexity": avg_complexity,
            "total_tasks": len(subtasks),
            "parallel_tasks_count": len(parallel_tasks),
            "sequential_tasks_count": len(sequential_tasks)
        }

    def _determine_worker_count(self, parallel_tasks: int,
                               avg_complexity: str,
                               has_dependencies: bool) -> int:
        """
        Intelligent worker allocation (not hardcoded).

        Args:
            parallel_tasks: Number of parallel tasks
            avg_complexity: Average complexity (low/medium/high)
            has_dependencies: Whether there are heavy dependencies

        Returns:
            Optimal worker count (1-7)
        """
        if has_dependencies:
            return 1

        if parallel_tasks <= 2:
            return min(2, parallel_tasks)
        elif parallel_tasks <= 5 and avg_complexity == "low":
            return min(5, parallel_tasks)
        elif avg_complexity == "high":
            return min(3, parallel_tasks)
        else:
            return min(5, parallel_tasks)

    def _calculate_avg_complexity(self, subtasks: List[Dict[str, Any]]) -> str:
        """Calculate average complexity of subtasks."""
        complexities = {"low": 0, "medium": 0, "high": 0}

        for task in subtasks:
            complexity = task.get("complexity", "medium")
            if complexity in complexities:
                complexities[complexity] += 1

        total = sum(complexities.values())
        if total == 0:
            return "medium"

        if complexities["high"] / total > 0.5:
            return "high"
        elif complexities["low"] / total > 0.5:
            return "low"
        else:
            return "medium"

    def _create_parallel_groups(self, parallel_tasks: List[Dict[str, Any]],
                               worker_count: int) -> List[List[Dict[str, Any]]]:
        """Create parallel execution groups."""
        if worker_count <= 1 or not parallel_tasks:
            return [parallel_tasks] if parallel_tasks else []

        groups = [[] for _ in range(worker_count)]
        for i, task in enumerate(parallel_tasks):
            groups[i % worker_count].append(task)

        return [g for g in groups if g]

    def _create_fallback_plan(self, request_analysis: Dict[str, Any],
                             user_request: str) -> Dict[str, Any]:
        """Create simple fallback plan if AI decomposition fails."""
        return {
            "subtasks": [
                {
                    "id": "task_1",
                    "description": user_request,
                    "complexity": request_analysis.get("complexity", "medium"),
                    "output_format": "Detailed analysis"
                }
            ],
            "dependencies": {},
            "execution_order": ["task_1"],
            "reasoning": "Fallback: Single-task plan"
        }

    def _get_default_meta_prompt(self) -> str:
        """Default meta orchestrator prompt if template not found."""
        return """You are analyzing a user request to create a task execution plan.

USER REQUEST: {user_request}

GOAL: {goal}

REQUIREMENTS:
{requirements}

TASK TYPE: {task_type}
COMPLEXITY: {complexity}

STEP-BY-STEP REASONING:
1. Goal Identification: What is the user trying to achieve?
2. Task Decomposition: What distinct subtasks are needed?
3. Dependency Analysis: Which tasks can run in parallel?
4. Parallelization Strategy: How many workers? How to group?
5. Checkpoint Identification: Where are high-risk decisions?
6. Execution Plan: Generate JSON task plan

OUTPUT JSON:
{{
  "subtasks": [
    {{
      "id": "task_1",
      "description": "Clear description",
      "complexity": "low|medium|high",
      "output_format": "Expected output",
      "worker_type": "comparison|analysis|synthesis|evaluation"
    }}
  ],
  "dependencies": {{
    "task_2": ["task_1"]
  }},
  "execution_order": ["task_1", "task_2"],
  "reasoning": "Your reasoning"
}}"""


def main():
    """CLI for testing task analyzer."""
    import argparse
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent / "utils"))
    from worker_spawner import WorkerSpawner

    parser = argparse.ArgumentParser(description='Task Analyzer')
    parser.add_argument('--request', required=True, help='User request')
    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    analyzer = TaskAnalyzer(skill_dir)

    print("Phase 0: Analyzing request...")
    request_analysis = analyzer.analyze_request(args.request)
    print(json.dumps(request_analysis, indent=2))

    print("\nPhase 1: Decomposing task...")
    spawner = WorkerSpawner(skill_dir)
    task_plan = analyzer.decompose_task(request_analysis, args.request, spawner)
    print(json.dumps(task_plan, indent=2))

    print("\nPhase 2: Determining parallelization...")
    parallelization = analyzer.determine_parallelization(task_plan)
    print(json.dumps(parallelization, indent=2))


if __name__ == '__main__':
    main()
