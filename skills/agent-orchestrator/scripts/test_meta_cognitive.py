#!/usr/bin/env python3
"""
Unit Tests for Meta-Cognitive Iteration Framework
Tests the meta_cognitive_reviewer, iteration strategies, and state management.
"""

import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from meta_cognitive_reviewer import MetaCognitiveReviewer


class TestMetaCognitiveReviewer(unittest.TestCase):
    """Test meta-cognitive reviewer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.reviewer = MetaCognitiveReviewer()

    def test_information_loss_detection(self):
        """Verify pre-caution mechanism detects missing citations."""
        worker_results = [
            {
                "worker_id": "w1",
                "status": "success",
                "output": "Finding 1 [1]. Finding 2 [2]. Finding 3 [3]."
            },
            {
                "worker_id": "w2",
                "status": "success",
                "output": "Analysis A [4]. Analysis B [5]."
            }
        ]

        synthesis_result = {
            "synthesis_output": "Summary without citations."
        }

        info_loss = self.reviewer.detect_information_loss(
            worker_results,
            synthesis_result
        )

        self.assertTrue(info_loss["trigger_iteration"])
        self.assertLess(info_loss["evidence"]["preservation_ratio"], 0.5)
        self.assertEqual(info_loss["evidence"]["worker_citations"], 5)
        self.assertEqual(info_loss["evidence"]["synthesis_citations"], 0)

    def test_quality_degradation_detection(self):
        """Verify post-diagnosis identifies failure patterns."""
        evaluation_results = {
            "total_workers": 10,
            "failed_workers": 4,
            "passed_workers": 3,
            "flagged_workers": 3,
            "overall_quality": {"average_score": 65},
            "individual_evaluations": {
                "w1": {"score": 45, "quality_gate": "reject", "issues": ["missing citations"]},
                "w2": {"score": 50, "quality_gate": "reject", "issues": ["vague claims"]},
                "w3": {"score": 55, "quality_gate": "reject", "issues": ["incomplete"]},
                "w4": {"score": 58, "quality_gate": "reject", "issues": ["missing structure"]},
                "w5": {"score": 75, "quality_gate": "flag", "issues": []},
                "w6": {"score": 72, "quality_gate": "flag", "issues": []},
                "w7": {"score": 70, "quality_gate": "flag", "issues": []},
                "w8": {"score": 85, "quality_gate": "accept", "issues": []},
                "w9": {"score": 88, "quality_gate": "accept", "issues": []},
                "w10": {"score": 82, "quality_gate": "accept", "issues": []}
            }
        }

        quality_degradation = self.reviewer.detect_quality_degradation(
            evaluation_results
        )

        self.assertTrue(quality_degradation["trigger_iteration"])
        self.assertEqual(quality_degradation["evidence"]["failure_rate"], 0.4)
        self.assertEqual(quality_degradation["evidence"]["average_quality"], 65)

    def test_iteration_decision_accept_high_quality(self):
        """Verify decision to accept when quality is excellent."""
        quality_analysis = {
            "overall_score": 88,
            "dimensions": {
                "information_completeness": {"score": 90, "trigger_iteration": False, "issues": []},
                "quality_assessment": {"score": 85, "trigger_iteration": False, "issues": []},
                "synthesis_coherence": {"score": 88, "trigger_iteration": False, "issues": []},
                "goal_fulfillment": {"score": 90, "trigger_iteration": False, "issues": []}
            },
            "confidence": "high"
        }

        decision, strategy, confidence, reasoning = self.reviewer.make_iteration_decision(
            quality_analysis,
            current_iteration=0,
            max_iterations=3
        )

        self.assertEqual(decision, "accept")
        self.assertIsNone(strategy)
        self.assertEqual(confidence, "high")
        self.assertIn("Excellent quality", reasoning)

    def test_iteration_decision_bounded_acceptance(self):
        """Verify bounded acceptance at max iterations."""
        quality_analysis = {
            "overall_score": 72,
            "dimensions": {
                "information_completeness": {"score": 70, "trigger_iteration": True, "issues": ["Some loss"]},
                "quality_assessment": {"score": 75, "trigger_iteration": False, "issues": []},
                "synthesis_coherence": {"score": 70, "trigger_iteration": False, "issues": []},
                "goal_fulfillment": {"score": 72, "trigger_iteration": False, "issues": []}
            },
            "confidence": "medium"
        }

        decision, strategy, confidence, reasoning = self.reviewer.make_iteration_decision(
            quality_analysis,
            current_iteration=3,
            max_iterations=3
        )

        self.assertEqual(decision, "accept")
        self.assertEqual(strategy, "bounded_acceptance")
        self.assertIn("Max iterations", reasoning)

    def test_iteration_decision_stagnation(self):
        """Verify stagnation detection stops iteration."""
        quality_analysis = {
            "overall_score": 73,
            "dimensions": {
                "information_completeness": {"score": 70, "trigger_iteration": True, "issues": ["Minor loss"]},
                "quality_assessment": {"score": 75, "trigger_iteration": False, "issues": []},
                "synthesis_coherence": {"score": 72, "trigger_iteration": False, "issues": []},
                "goal_fulfillment": {"score": 75, "trigger_iteration": False, "issues": []}
            },
            "confidence": "medium"
        }

        decision, strategy, confidence, reasoning = self.reviewer.make_iteration_decision(
            quality_analysis,
            current_iteration=1,
            max_iterations=3,
            previous_quality=70  # Only 3 point improvement
        )

        self.assertEqual(decision, "accept")
        self.assertEqual(strategy, "stagnation_detected")
        self.assertIn("stagnated", reasoning)

    def test_iteration_strategy_selection_information_loss(self):
        """Verify correct strategy for information loss."""
        triggers = [
            ("information_completeness", {
                "score": 50,
                "trigger_iteration": True,
                "issues": ["Severe citation loss"],
                "evidence": {"preservation_ratio": 0.25}
            })
        ]

        quality_analysis = {
            "overall_score": 65,
            "dimensions": {
                "information_completeness": triggers[0][1]
            }
        }

        strategy, confidence, reasoning = self.reviewer._select_iteration_strategy(
            triggers,
            quality_analysis,
            current_iteration=0
        )

        self.assertEqual(strategy, "re_extract_synthesis")
        self.assertEqual(confidence, "high")
        self.assertIn("citation loss", reasoning.lower())

    def test_iteration_strategy_selection_failed_workers(self):
        """Verify correct strategy for quality degradation."""
        triggers = [
            ("quality_assessment", {
                "score": 50,
                "trigger_iteration": True,
                "issues": ["High failure rate"],
                "evidence": {"failure_rate": 0.4}
            })
        ]

        quality_analysis = {
            "overall_score": 60,
            "dimensions": {
                "quality_assessment": triggers[0][1]
            }
        }

        strategy, confidence, reasoning = self.reviewer._select_iteration_strategy(
            triggers,
            quality_analysis,
            current_iteration=0
        )

        self.assertEqual(strategy, "re_execute_failed_workers")
        self.assertEqual(confidence, "high")
        self.assertIn("failure rate", reasoning.lower())

    def test_citation_counting(self):
        """Test citation counting accuracy."""
        text_with_citations = """
        Finding 1 [1,2,3]. Finding 2 (p. 45). Finding 3 (line 100).
        Finding 4 [4]. Finding 5 (p. 78).
        """

        count = self.reviewer._count_citations(text_with_citations)
        self.assertEqual(count, 5)

    def test_missing_key_findings_detection(self):
        """Test detection of missing key findings."""
        worker_results = [
            {
                "worker_id": "w1",
                "status": "success",
                "output": "# Important Finding\n\nThis is critical information."
            },
            {
                "worker_id": "w2",
                "status": "success",
                "output": "# Another Key Point\n\nThis should be included."
            }
        ]

        synthesis_output = "Some summary text without key findings."

        missing = self.reviewer._detect_missing_key_findings(
            worker_results,
            synthesis_output
        )

        self.assertGreater(missing, 0)

    def test_confidence_calculation(self):
        """Test confidence level calculation."""
        high_quality_dimensions = [
            {"score": 85},
            {"score": 90},
            {"score": 88},
            {"score": 87}
        ]

        confidence = self.reviewer._calculate_confidence(high_quality_dimensions)
        self.assertEqual(confidence, "high")

        low_quality_dimensions = [
            {"score": 45},
            {"score": 50},
            {"score": 48},
            {"score": 52}
        ]

        confidence = self.reviewer._calculate_confidence(low_quality_dimensions)
        self.assertEqual(confidence, "low")


class TestStateManagement(unittest.TestCase):
    """Test iteration state management."""

    def setUp(self):
        """Set up test fixtures."""
        from state_manager import StateManager
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = StateManager(work_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_iteration_state_initialization(self):
        """Test iteration state is properly initialized."""
        state = self.state_manager.state

        self.assertIn("iteration_state", state)
        self.assertEqual(state["iteration_state"]["current_iteration"], 0)
        self.assertEqual(state["iteration_state"]["max_iterations"], 3)
        self.assertEqual(state["iteration_state"]["best_quality_score"], 0)

    def test_increment_iteration(self):
        """Test iteration increment."""
        self.state_manager.increment_iteration()

        self.assertEqual(self.state_manager.get_current_iteration(), 1)
        self.assertEqual(
            self.state_manager.state["metadata"]["total_iterations"],
            1
        )

    def test_record_iteration_decision(self):
        """Test recording iteration decisions."""
        decision_metadata = {
            "hypothesis": "Test hypothesis",
            "evidence": ["Evidence 1", "Evidence 2"],
            "confidence": "high",
            "decision": "iterate",
            "strategy": "re_extract_synthesis",
            "reasoning": "Test reasoning",
            "quality_score": 72
        }

        self.state_manager.record_iteration_decision(decision_metadata)

        iteration_key = "iteration_0"
        self.assertIn(iteration_key, self.state_manager.state["iteration_state"]["iteration_decisions"])

        decision = self.state_manager.state["iteration_state"]["iteration_decisions"][iteration_key]
        self.assertEqual(decision["hypothesis"], "Test hypothesis")
        self.assertEqual(decision["strategy"], "re_extract_synthesis")

    def test_record_iteration_result(self):
        """Test recording iteration results."""
        self.state_manager.record_iteration_result(
            iteration=1,
            trigger="information_completeness",
            strategy="re_extract_synthesis",
            quality_before=72,
            quality_after=87,
            decision="accept"
        )

        history = self.state_manager.state["iteration_state"]["iteration_history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["improvement"], 15)

    def test_best_synthesis_tracking(self):
        """Test best synthesis result tracking."""
        synthesis_1 = {"output": "Result 1"}
        synthesis_2 = {"output": "Result 2"}

        self.state_manager.update_best_synthesis(synthesis_1, 75)
        self.assertEqual(self.state_manager.state["iteration_state"]["best_quality_score"], 75)

        self.state_manager.update_best_synthesis(synthesis_2, 88)
        self.assertEqual(self.state_manager.state["iteration_state"]["best_quality_score"], 88)

        best = self.state_manager.get_best_synthesis()
        self.assertEqual(best["output"], "Result 2")

    def test_iteration_trajectory(self):
        """Test iteration trajectory tracking."""
        self.state_manager.record_iteration_result(
            iteration=1,
            trigger="test",
            strategy="test_strategy",
            quality_before=70,
            quality_after=80,
            decision="iterate"
        )

        self.state_manager.record_iteration_result(
            iteration=2,
            trigger="test",
            strategy="test_strategy",
            quality_before=80,
            quality_after=88,
            decision="accept"
        )

        trajectory = self.state_manager.get_iteration_trajectory()
        self.assertEqual(len(trajectory), 2)
        self.assertEqual(trajectory[0]["quality_score"], 80)
        self.assertEqual(trajectory[1]["quality_score"], 88)


if __name__ == '__main__':
    unittest.main()
