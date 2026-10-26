"""
Minimal meta-actions parser for orchestration phases.

This module provides defensive parsing and validation for a lightweight
"meta_actions" structure that can be embedded in request_analysis or
task_plan to trigger cross-phase orchestrator behaviors.

Structure expected:
{
  "actions": [
    {"phase": 3, "action": "increase_workers", "params": {...}},
    {"phase": 7, "action": "re_execute_failed_workers"}
  ]
}

The parser returns a normalized list of actions or an empty list when
no meta_actions are provided. It raises ValueError on malformed inputs.
"""
from typing import Any, Dict, List, Optional


class MetaActionsHandler:
    """Handle parsing and validation of meta_actions payloads."""

    @staticmethod
    def parse(meta_actions: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate a meta_actions mapping.

        Args:
            meta_actions: Mapping or None

        Returns:
            Normalized list of action dicts (may be empty)

        Raises:
            ValueError: If the structure is present but malformed
        """
        if not meta_actions:
            return []

        if not isinstance(meta_actions, dict):
            raise ValueError("meta_actions must be a dict with key 'actions'")

        actions = meta_actions.get("actions")
        if actions is None:
            raise ValueError("meta_actions missing 'actions' key")
        if not isinstance(actions, list):
            raise ValueError("meta_actions['actions'] must be a list")

        normalized: List[Dict[str, Any]] = []
        for idx, act in enumerate(actions):
            if not isinstance(act, dict):
                raise ValueError(f"action at index {idx} is not a dict")

            phase = act.get("phase")
            name = act.get("action")
            params = act.get("params", {})

            if not isinstance(phase, int) or phase < 0 or phase > 10:
                raise ValueError(f"action.phase must be int between 0 and 10 (got {phase})")

            if not isinstance(name, str) or not name:
                raise ValueError("action.action must be a non-empty string")

            if params is None:
                params = {}

            normalized.append({"phase": phase, "action": name, "params": params})

        return normalized
