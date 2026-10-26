"""Tests for Study state, rendering, export, and review helpers."""

## Imports
## Load sample state and exercise only deterministic package behavior.
from __future__ import annotations

import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


## Package setup
## Make the skill root importable without installing a Python package.
SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.study_artifacts import (  # noqa: E402
    export_artifacts,
    lesson_notes,
    public_graph,
    render_mermaid,
    render_text_map,
    validate_state,
)
import scripts.study_artifacts as study_artifacts  # noqa: E402
from scripts.review_scheduler import (  # noqa: E402
    build_review_schedule,
    review_cards_to_csv,
    review_schedule_to_csv,
)


## Utility behavior
## Verify schema fidelity, semantic maps, cross-references, and portable output.
class StudyUtilityTests(unittest.TestCase):
    """Exercise deterministic helpers against the canonical sample state."""

    def setUp(self) -> None:
        """Load a fresh sample state and its schema for every test."""
        self.state = json.loads(
            (SKILL_ROOT / "assets" / "session_state.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.schema = json.loads(
            (SKILL_ROOT / "references" / "session-state.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_sample_matches_json_schema(self) -> None:
        """Confirm the schema is valid Draft 2020-12 and accepts the sample."""
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema is optional and not installed")

        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator(self.schema).validate(self.state)

    def test_sample_passes_cross_object_validation(self) -> None:
        """Confirm all sample identifiers, views, evidence, and revisions agree."""
        self.assertEqual(validate_state(self.state), [])

    def test_generic_edge_label_is_rejected(self) -> None:
        """Ensure a topic-list-style generic edge fails semantic validation."""
        broken_state = copy.deepcopy(self.state)
        broken_state["edges"][0]["label"] = "related to"
        errors = validate_state(broken_state)
        self.assertTrue(any("generic label" in error for error in errors))

    def test_dangling_endpoint_is_rejected(self) -> None:
        """Ensure an edge cannot reference a node absent from canonical state."""
        broken_state = copy.deepcopy(self.state)
        broken_state["edges"][0]["target_node_id"] = "n_missing"
        errors = validate_state(broken_state)
        self.assertTrue(any("missing target_node_id" in error for error in errors))

    def test_mastery_requires_evidence(self) -> None:
        """Ensure positive node or edge mastery cannot exist without evidence."""
        broken_state = copy.deepcopy(self.state)
        broken_state["mastery_by_edge"]["e_learning_rate_scales_update"]["evidence_ids"] = []
        errors = validate_state(broken_state)
        self.assertIn(
            "edge mastery e_learning_rate_scales_update exceeds zero without evidence",
            errors,
        )

    def test_mastery_evidence_must_target_the_exact_object(self) -> None:
        """Reject an existing evidence ID that supports a different node or edge."""
        broken_state = copy.deepcopy(self.state)
        broken_state["mastery_by_node"]["n_optimization"] = copy.deepcopy(
            broken_state["mastery_by_node"]["n_gradient"]
        )
        broken_state["mastery_by_edge"]["e_parameters_configure_model"] = copy.deepcopy(
            broken_state["mastery_by_edge"]["e_derivative_prerequisite_gradient"]
        )
        errors = validate_state(broken_state)
        self.assertTrue(
            any(
                "node mastery n_optimization cites evidence ev_gradient_retrieval that does not target"
                in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "edge mastery e_parameters_configure_model cites evidence ev_gradient_retrieval "
                "that does not target"
                in error
                for error in errors
            )
        )

    def test_mastery_level_must_fit_evidence_metadata(self) -> None:
        """Use evidence metadata as an upper-bound check without inferring mastery."""
        broken_state = copy.deepcopy(self.state)
        broken_state["mastery_by_node"]["n_gradient"]["level"] = 4
        broken_state["mastery_by_edge"]["e_learning_rate_scales_update"]["level"] = 3
        errors = validate_state(broken_state)
        self.assertIn(
            "node mastery n_gradient level 4 exceeds the directly targeted evidence "
            "compatibility ceiling 3",
            errors,
        )
        self.assertIn(
            "edge mastery e_learning_rate_scales_update level 3 exceeds the directly "
            "targeted evidence compatibility ceiling 2",
            errors,
        )

    def test_merged_alias_cannot_remain_in_live_canonical_state(self) -> None:
        """Reject stale mastery, views, frontiers, paths, reviews, aliases, and history."""
        broken_state = copy.deepcopy(self.state)
        alias = next(node for node in broken_state["nodes"] if node["id"] == "n_step_size")
        alias["lifecycle"] = "merged"
        alias["merged_into_node_id"] = "n_learning_rate"
        survivor = next(
            node for node in broken_state["nodes"] if node["id"] == "n_learning_rate"
        )
        survivor["aliases"] = []
        broken_state["current_location_path"].append("n_step_size")
        broken_state["prerequisite_frontier"].append(
            {
                "node_id": "n_step_size",
                "blocking_question_id": None,
                "reason": "Stale alias frontier.",
                "priority": 1,
                "status": "open",
                "extensions": {},
            }
        )
        errors = validate_state(broken_state)
        expected_fragments = (
            "term 'Step size' is not retained by survivor n_learning_rate",
            "merged node n_step_size retains canonical mastery",
            "live review item review_learning_rate_edge targets non-active node n_step_size",
            "question_frontier question q_learning_rate_contrast targets merged node n_step_size",
            "prerequisite frontier contains merged node n_step_size",
            "map view core contains non-active node n_step_size",
            "current_location_path contains non-active node n_step_size",
            "merged node n_step_size lacks a node merge revision change",
        )
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in error for error in errors), fragment)

    def test_live_routes_and_misconceptions_reject_merged_targets(self) -> None:
        """Prevent repaired merge history from leaving live stale references."""
        broken_state = copy.deepcopy(self.state)
        alias = next(node for node in broken_state["nodes"] if node["id"] == "n_step_size")
        alias["lifecycle"] = "merged"
        alias["merged_into_node_id"] = "n_learning_rate"
        survivor = next(
            node for node in broken_state["nodes"] if node["id"] == "n_learning_rate"
        )
        survivor["aliases"] = ["Step size", "Step size (learner wording)"]
        broken_state["mastery_by_node"].pop("n_step_size")
        for view in ("context", "core", "neighborhood"):
            broken_state["map_views"][view]["visible_node_ids"] = [
                node_id
                for node_id in broken_state["map_views"][view]["visible_node_ids"]
                if node_id != "n_step_size"
            ]
            broken_state["map_views"][view]["collapsed_node_ids"] = [
                node_id
                for node_id in broken_state["map_views"][view]["collapsed_node_ids"]
                if node_id != "n_step_size"
            ]
        alias_edge = next(
            edge
            for edge in broken_state["edges"]
            if edge["id"] == "e_step_size_duplicate_learning_rate"
        )
        alias_edge["lifecycle"] = "archived"
        broken_state["mastery_by_edge"].pop(alias_edge["id"])
        broken_state["review_queue"] = []
        broken_state["question_frontier"] = ["q_anchor"]
        broken_state["unresolved_questions"] = ["q_anchor"]
        broken_state["route"]["planned_question_ids"] = ["q_learning_rate_contrast"]
        broken_state["revision_log"][-1]["changes"].append(
            {
                "operation": "merge",
                "entity_type": "node",
                "entity_id": "n_step_size",
                "summary": "Merged the learner alias into learning rate.",
                "extensions": {},
            }
        )
        errors = validate_state(broken_state)
        self.assertTrue(
            any(
                "route-planned question q_learning_rate_contrast targets non-active node n_step_size"
                in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "live misconception m_learning_rate_sets_direction implicates non-active node n_step_size"
                in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "live misconception m_learning_rate_sets_direction implicates non-active edge "
                "e_step_size_duplicate_learning_rate" in error
                for error in errors
            )
        )

    def test_source_reference_must_bind_to_its_owner(self) -> None:
        """Reject a source reference attached to a different node than it supports."""
        broken_state = copy.deepcopy(self.state)
        broken_state["sources"].append({"id": "source_test"})
        broken_state["source_references"].append(
            {
                "id": "source_ref_test",
                "source_id": "source_test",
                "locator": {"section": "1", "extensions": {}},
                "supported_entity_type": "node",
                "supported_entity_id": "n_learning_rate",
            }
        )
        broken_state["nodes"][0]["source_reference_ids"] = ["source_ref_test"]
        errors = validate_state(broken_state)
        self.assertTrue(any("bound to node n_learning_rate" in error for error in errors))

    def test_visible_records_must_be_active(self) -> None:
        """Reject archived graph records that remain exposed in a map view."""
        broken_state = copy.deepcopy(self.state)
        target_node = next(
            node for node in broken_state["nodes"] if node["id"] == "n_learning_rate"
        )
        target_node["lifecycle"] = "archived"
        errors = validate_state(broken_state)
        self.assertIn(
            "map view neighborhood contains non-active node n_learning_rate", errors
        )

    def test_prerequisite_frontier_uses_blocking_question_id(self) -> None:
        """Accept the schema's nullable blocking-question reference when valid."""
        state_with_prerequisite = copy.deepcopy(self.state)
        state_with_prerequisite["prerequisite_frontier"].append(
            {
                "node_id": "n_derivative",
                "blocking_question_id": "q_numeric_updates",
                "reason": "The numerical update question may expose a chain-rule gap.",
                "priority": 3,
                "status": "open",
                "extensions": {},
            }
        )
        self.assertEqual(validate_state(state_with_prerequisite), [])

    def test_renderers_use_visible_semantic_view(self) -> None:
        """Render the neighborhood with semantic labels and collapsed nodes hidden."""
        mermaid = render_mermaid(self.state, zoom="neighborhood")
        text_map = render_text_map(self.state, zoom="neighborhood")
        self.assertIn('N1 -->|"scales the magnitude of"| N2', mermaid)
        self.assertIn("Learning rate --scales the magnitude of--> Parameter update", text_map)
        self.assertNotIn("Step size (learner wording)", mermaid)
        self.assertIn("class N1 current", mermaid)
        self.assertIn(
            "Here: Optimization > Gradient descent > Objective function > Gradient > "
            "Parameter update > Learning rate",
            text_map,
        )
        self.assertIn(
            "Focus question: Two runs have the same positive gradient", text_map
        )
        self.assertIn(
            "Focus relationship: Learning rate --scales the magnitude of--> Parameter update",
            text_map,
        )

        bidirectional_state = copy.deepcopy(self.state)
        bidirectional_edge = next(
            edge
            for edge in bidirectional_state["edges"]
            if edge["id"] == "e_learning_rate_scales_update"
        )
        bidirectional_edge["directionality"] = "bidirectional"
        self.assertIn(
            "Learning rate <--scales the magnitude of--> Parameter update",
            render_text_map(bidirectional_state, zoom="neighborhood"),
        )

    def test_public_graph_omits_focus_outside_exported_view(self) -> None:
        """Keep core graph focus IDs local while retaining its relevant question."""
        neighborhood_state = copy.deepcopy(self.state)
        neighborhood_state["current_node_id"] = "n_overshooting"
        neighborhood_state["current_edge_id"] = "e_overshooting_limits_convergence"
        neighborhood_state["current_question_id"] = "q_learning_rate_transfer"
        self.assertEqual(validate_state(neighborhood_state), [])

        graph = public_graph(neighborhood_state, zoom="core")
        self.assertIsNone(graph["current_node_id"])
        self.assertIsNone(graph["current_edge_id"])
        self.assertEqual(graph["current_question_id"], "q_learning_rate_transfer")

    def test_interactive_viewer_uses_canonical_state_fields(self) -> None:
        """Keep the optional HTML viewer aligned with the portable state schema."""
        viewer = (SKILL_ROOT / "assets" / "interactive-map.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("state.map_views?.[zoom]", viewer)
        self.assertIn("learningState.current_node_id", viewer)
        self.assertIn("node.epistemic_status?.kind", viewer)
        self.assertNotIn("node.visibility", viewer)
        self.assertNotIn("edge.visibility", viewer)

    def test_review_schedule_preserves_mixed_queue(self) -> None:
        """Schedule existing review content without reducing it to definitions."""
        rows = build_review_schedule(self.state, start_date=date(2026, 9, 10))
        kinds = {row["kind"] for row in rows}
        self.assertIn("edge_explanation", kinds)
        self.assertIn("misconception_check", kinds)
        self.assertIn("transfer_problem", kinds)
        self.assertEqual(rows, sorted(rows, key=lambda row: (row["due_date"], row["review_id"])))

        schedule_csv = review_schedule_to_csv(rows)
        parsed_schedule = list(csv.DictReader(io.StringIO(schedule_csv)))
        self.assertEqual(len(parsed_schedule), len(rows))

        cards_csv = review_cards_to_csv(self.state["review_queue"])
        parsed_cards = list(csv.DictReader(io.StringIO(cards_csv)))
        self.assertEqual(len(parsed_cards), len(self.state["review_queue"]))

    def test_export_writes_coherent_versioned_artifacts(self) -> None:
        """Export six files whose state revision and artifact records remain valid."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = export_artifacts(
                self.state,
                Path(temporary_directory),
                start_date=date(2026, 9, 10),
            )
            self.assertEqual(
                [path.name for path in paths],
                [
                    "session_state.json",
                    "map.json",
                    "map.mmd",
                    "lesson_notes.md",
                    "review_cards.csv",
                    "review_schedule.csv",
                ],
            )
            self.assertTrue(all(path.is_file() for path in paths))

            exported_state = json.loads(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(exported_state["state_version"], self.state["state_version"] + 1)
            self.assertEqual(validate_state(exported_state), [])
            self.assertEqual(
                exported_state["revision_log"][-1]["kind"], "artifact_update"
            )
            self.assertEqual(len(exported_state["generated_artifacts"]), 6)
            self.assertTrue(
                all(record["validated"] for record in exported_state["generated_artifacts"])
            )

            try:
                from jsonschema import Draft202012Validator
            except ImportError:
                return
            Draft202012Validator(self.schema).validate(exported_state)

    def test_lesson_notes_handle_an_unanswered_anchor(self) -> None:
        """Keep notes exportable when every nullable summary text is absent."""
        early_state = copy.deepcopy(self.state)
        early_state["session_summary"]["current_anchor_answer"] = None
        early_state["session_summary"]["synthesis_task"] = None
        early_state["session_summary"]["transfer_task"] = None
        early_state["session_summary"]["notes"] = None
        notes = lesson_notes(early_state)
        self.assertIn("Not yet synthesized.", notes)
        self.assertIn("No synthesis task has been set.", notes)
        self.assertIn("No transfer task has been set.", notes)
        self.assertIn("No additional session notes.", notes)

    def test_export_rejects_invalid_generated_content_before_writing(self) -> None:
        """Do not mark or write a bundle whose generated Mermaid is invalid."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            with patch.object(study_artifacts, "render_mermaid", return_value="not mermaid\n"):
                with self.assertRaisesRegex(ValueError, "Invalid generated artifacts"):
                    export_artifacts(self.state, output_directory)
            self.assertEqual(list(output_directory.iterdir()), [])


## Test entrypoint
## Support direct local execution as well as unittest discovery.
if __name__ == "__main__":
    unittest.main()
