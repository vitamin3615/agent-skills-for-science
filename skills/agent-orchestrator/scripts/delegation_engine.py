"""
Delegation Engine for Agent Orchestrator
Generates optimal worker prompts using hierarchical structure.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class DelegationEngine:
    """Generates optimized worker prompts for task delegation."""

    def __init__(self, skill_dir: Path):
        """
        Initialize DelegationEngine.

        Args:
            skill_dir: Path to skill root directory
        """
        self.skill_dir = skill_dir
        self.prompts_dir = skill_dir / "worker_prompts"
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load all worker prompt templates."""
        templates = {}
        template_files = {
            "comparison": "comparison_worker.txt",
            "analysis": "analysis_worker.txt",
            "synthesis": "synthesis_worker.txt",
            "evaluation": "evaluation_worker.txt",
            "meta": "meta_orchestrator.txt"
        }

        for task_type, filename in template_files.items():
            template_path = self.prompts_dir / filename
            if template_path.exists():
                with open(template_path, 'r') as f:
                    templates[task_type] = f.read()
            else:
                templates[task_type] = self._get_default_template(task_type)

        return templates

    def generate_worker_prompts(self,
                                task_plan: Dict[str, Any],
                                parallelization: Dict[str, Any],
                                request_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate optimized prompts for all workers.

        Phase 3: Worker Prompt Generation

        Args:
            task_plan: Task decomposition plan
            parallelization: Parallelization configuration
            request_analysis: Original request analysis

        Returns:
            List of worker prompt configurations
        """
        worker_prompts = []
        worker_id = 0

        for group_idx, group in enumerate(parallelization["parallel_groups"]):
            for task in group:
                worker_id += 1
                prompt = self._build_hierarchical_prompt(
                    worker_id=worker_id,
                    task=task,
                    total_workers=parallelization["worker_count"],
                    group_idx=group_idx,
                    request_analysis=request_analysis,
                    task_plan=task_plan
                )

                worker_prompts.append({
                    "worker_id": f"worker_{worker_id}",
                    "task_id": task.get("id", f"task_{worker_id}"),
                    "prompt": prompt,
                    "complexity": task.get("complexity", "medium"),
                    "worker_type": task.get("worker_type", "analysis"),
                    "group": group_idx
                })

        for task in parallelization["sequential_tasks"]:
            worker_id += 1
            prompt = self._build_hierarchical_prompt(
                worker_id=worker_id,
                task=task,
                total_workers=1,
                group_idx=-1,
                request_analysis=request_analysis,
                task_plan=task_plan
            )

            worker_prompts.append({
                "worker_id": f"worker_{worker_id}",
                "task_id": task.get("id", f"task_{worker_id}"),
                "prompt": prompt,
                "complexity": task.get("complexity", "medium"),
                "worker_type": task.get("worker_type", "analysis"),
                "group": -1
            })

        return worker_prompts

    def _build_hierarchical_prompt(self,
                                   worker_id: int,
                                   task: Dict[str, Any],
                                   total_workers: int,
                                   group_idx: int,
                                   request_analysis: Dict[str, Any],
                                   task_plan: Dict[str, Any]) -> str:
        """
        Build hierarchical prompt structure.

        Hierarchy:
        1. SYSTEM CONTEXT (Role & Purpose)
        2. TASK DEFINITION (Clear goal)
        3. METHODOLOGY (How to approach)
        4. DATA/CONTENT (What to analyze)
        5. OUTPUT FORMAT (Exact structure)
        6. QUALITY CRITERIA (Requirements)
        7. CRITICAL CONSTRAINTS (Must-dos)

        Args:
            worker_id: Worker ID
            task: Task configuration
            total_workers: Total number of workers
            group_idx: Parallel group index (-1 for sequential)
            request_analysis: Request analysis
            task_plan: Task plan

        Returns:
            Optimized prompt
        """
        worker_type = task.get("worker_type", "analysis")
        template = self.templates.get(worker_type, self.templates["analysis"])

        is_parallel = group_idx >= 0
        coordination_context = self._generate_coordination_context(
            worker_id, total_workers, is_parallel, group_idx
        )

        prompt_parts = []

        prompt_parts.append(f"# 1. SYSTEM CONTEXT")
        prompt_parts.append(f"You are Worker AI #{worker_id} in a multi-agent orchestration system.")
        prompt_parts.append(coordination_context)
        prompt_parts.append("")

        prompt_parts.append(f"# 2. TASK DEFINITION")
        prompt_parts.append(f"**Task ID**: {task.get('id', f'task_{worker_id}')}")
        prompt_parts.append(f"**Description**: {task.get('description', 'No description')}")
        prompt_parts.append(f"**Complexity**: {task.get('complexity', 'medium')}")
        prompt_parts.append("")

        prompt_parts.append(f"# 3. METHODOLOGY")
        methodology = self._extract_methodology(template, worker_type)
        prompt_parts.append(methodology)
        prompt_parts.append("")

        prompt_parts.append(f"# 4. DATA/CONTENT")
        data_context = task.get("data_context", "No specific data provided")
        # Handle different data_context types (list, dict, or string)
        if isinstance(data_context, list):
            prompt_parts.append("Files to analyze:\n" + "\n".join(f"- {item}" for item in data_context))
        elif isinstance(data_context, dict):
            prompt_parts.append("Data context:\n" + "\n".join(f"- {k}: {v}" for k, v in data_context.items()))
        else:
            prompt_parts.append(str(data_context))
        prompt_parts.append("")

        prompt_parts.append(f"# 5. OUTPUT FORMAT")
        output_format = task.get("output_format", "Structured markdown report")
        prompt_parts.append(output_format)
        prompt_parts.append("")

        prompt_parts.append(f"# 6. QUALITY CRITERIA")
        quality_criteria = self._generate_quality_criteria(task, request_analysis)
        prompt_parts.append(quality_criteria)
        prompt_parts.append("")

        prompt_parts.append(f"# 7. CRITICAL CONSTRAINTS")
        constraints = self._generate_constraints(task, request_analysis)
        prompt_parts.append(constraints)
        prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _generate_coordination_context(self,
                                      worker_id: int,
                                      total_workers: int,
                                      is_parallel: bool,
                                      group_idx: int) -> str:
        """Generate cross-worker coordination context."""
        if is_parallel and total_workers > 1:
            return f"""**Coordination Mode**: Parallel execution
**Your Role**: Worker {worker_id} of {total_workers}
**Group**: Parallel Group {group_idx + 1}
**Independence**: Your task is independent of other workers. Results will be synthesized separately.
**Focus**: Concentrate solely on your assigned task. Do not attempt to coordinate with other workers."""
        elif total_workers > 1:
            return f"""**Coordination Mode**: Sequential execution
**Your Role**: Worker {worker_id} in sequential pipeline
**Dependencies**: Your output may be used by subsequent workers.
**Quality**: Ensure outputs are well-structured for downstream consumption."""
        else:
            return f"""**Coordination Mode**: Single-worker execution
**Your Role**: Sole worker for this task
**Responsibility**: Complete analysis independently."""

    def _extract_methodology(self, template: str, worker_type: str) -> str:
        """Extract methodology section from template."""
        if "FRAMEWORK:" in template or "METHODOLOGY:" in template:
            start_marker = "FRAMEWORK:" if "FRAMEWORK:" in template else "METHODOLOGY:"
            start = template.find(start_marker)
            end_markers = ["OUTPUT FORMAT:", "CRITICAL:", "QUALITY:"]

            end = len(template)
            for marker in end_markers:
                pos = template.find(marker, start)
                if pos != -1:
                    end = min(end, pos)

            return template[start:end].strip()
        else:
            return self._get_default_methodology(worker_type)

    def _get_default_methodology(self, worker_type: str) -> str:
        """Get default methodology for worker type."""
        methodologies = {
            "comparison": """**FRAMEWORK**:
1. Identify claims/elements in target document
2. Find corresponding content in source
3. Assess alignment: ALIGNED | PARTIAL | MISSING | CONTRADICTORY
4. Extract verbatim evidence with citations
5. Note novel additions or differences""",

            "analysis": """**FRAMEWORK**:
1. Understand the context and requirements
2. Identify key components to analyze
3. Apply systematic analysis methodology
4. Extract insights and patterns
5. Formulate conclusions with evidence""",

            "synthesis": """**FRAMEWORK**:
1. Review all input sources
2. Identify common themes and patterns
3. Resolve conflicts and contradictions
4. Integrate insights into coherent whole
5. Highlight key findings and recommendations""",

            "evaluation": """**FRAMEWORK**:
1. Define evaluation criteria
2. Assess completeness and correctness
3. Check evidence quality and citations
4. Identify hallucinations or unsupported claims
5. Assign quality score with justification"""
        }
        return methodologies.get(worker_type, methodologies["analysis"])

    def _generate_quality_criteria(self,
                                   task: Dict[str, Any],
                                   request_analysis: Dict[str, Any]) -> str:
        """Generate quality criteria for task."""
        criteria = []
        criteria.append("**Completeness**: Address all aspects of the task")
        criteria.append("**Evidence**: Support claims with specific evidence")
        criteria.append("**Accuracy**: Ensure factual correctness")
        criteria.append("**Clarity**: Use clear, unambiguous language")

        success_criteria = request_analysis.get("success_criteria", [])
        if success_criteria:
            criteria.append("\n**Task-Specific Criteria**:")
            for criterion in success_criteria:
                criteria.append(f"- {criterion}")

        return "\n".join(criteria)

    def _generate_constraints(self,
                             task: Dict[str, Any],
                             request_analysis: Dict[str, Any]) -> str:
        """Generate critical constraints."""
        constraints = []
        constraints.append("**NO HALLUCINATION**: Only make claims supported by evidence")
        constraints.append("**EXACT CITATIONS**: Provide precise references (page numbers, line numbers, etc.)")
        constraints.append("**STAY ON TASK**: Focus only on your assigned task")

        user_constraints = request_analysis.get("constraints", [])
        if user_constraints:
            constraints.append("\n**User Constraints**:")
            for constraint in user_constraints:
                constraints.append(f"- {constraint}")

        return "\n".join(constraints)

    def _get_default_template(self, task_type: str) -> str:
        """Get default template if file not found."""
        return f"""Worker template for {task_type} task.

FRAMEWORK:
1. Understand the task
2. Apply appropriate methodology
3. Generate results
4. Format output

OUTPUT FORMAT:
Structured markdown with clear sections

CRITICAL CONSTRAINTS:
- No hallucination
- Provide evidence
- Stay on task"""


def main():
    """CLI for testing delegation engine."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Delegation Engine Test')
    parser.add_argument('--task-plan', required=True, help='Path to task plan JSON')
    parser.add_argument('--parallelization', required=True, help='Path to parallelization JSON')
    parser.add_argument('--request-analysis', required=True, help='Path to request analysis JSON')

    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    engine = DelegationEngine(skill_dir)

    with open(args.task_plan, 'r') as f:
        task_plan = json.load(f)
    with open(args.parallelization, 'r') as f:
        parallelization = json.load(f)
    with open(args.request_analysis, 'r') as f:
        request_analysis = json.load(f)

    prompts = engine.generate_worker_prompts(task_plan, parallelization, request_analysis)

    print(f"Generated {len(prompts)} worker prompts")
    for prompt_config in prompts:
        print(f"\n{'='*60}")
        print(f"Worker: {prompt_config['worker_id']}")
        print(f"Task: {prompt_config['task_id']}")
        print(f"Type: {prompt_config['worker_type']}")
        print(f"Complexity: {prompt_config['complexity']}")
        print(f"\nPrompt:\n{prompt_config['prompt'][:500]}...")


if __name__ == '__main__':
    main()
