"""Validate Study state and render or export portable learning artifacts."""

## Imports
## Use standard-library data, path, and atomic-write support.
from __future__ import annotations

import copy
import csv
import io
import json
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .review_scheduler import (
    build_review_schedule,
    review_cards_to_csv,
    review_schedule_to_csv,
)


## State contract
## Mirror required top-level fields used by cross-object validation.
REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "session_id",
    "state_version",
    "learning_target",
    "anchor_question",
    "learner_goal",
    "learner_profile",
    "time_budget",
    "mode",
    "phase",
    "interaction_status",
    "current_zoom_level",
    "current_node_id",
    "current_edge_id",
    "current_question_id",
    "current_location_path",
    "route",
    "nodes",
    "edges",
    "map_views",
    "questions",
    "prerequisite_frontier",
    "question_frontier",
    "unresolved_questions",
    "mastery_by_node",
    "mastery_by_edge",
    "evidence",
    "known_misconceptions",
    "examples_seen",
    "representations_used",
    "review_queue",
    "sources",
    "source_references",
    "generated_artifacts",
    "session_summary",
    "next_recommended_route",
    "revision_log",
    "extensions",
)

GENERIC_EDGE_LABELS = {
    "related",
    "related to",
    "relates to",
    "connected",
    "connected to",
    "associated",
    "associated with",
}

MASTERY_CAPABILITY_CEILINGS = {
    "misconception_evidence": 0,
    "recognition": 1,
    "cued_explanation": 2,
    "independent_explanation": 3,
    "familiar_application": 4,
    "transfer": 5,
    "comparison": 5,
    "prediction": 5,
    "teaching": 5,
    "limit_recognition": 5,
}
MASTERY_OUTCOME_CEILINGS = {
    "incorrect": 0,
    "inconclusive": 0,
    "not_attempted": 0,
    "partially_correct": 2,
    "correct": 5,
}
MASTERY_SUPPORT_CEILINGS = {
    "full": 1,
    "substantial": 2,
    "light": 2,
    "none": 5,
}
LIVE_REVIEW_STATUSES = {"active", "queued", "scheduled", "due"}
LIVE_QUESTION_STATUSES = {"open", "active", "deferred"}
LIVE_MISCONCEPTION_STATUSES = {"suspected", "confirmed", "repairing", "monitoring"}


## Identifier helpers
## Collect stable IDs and report duplicates consistently.
def _record_index(records: Iterable[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Index records by ID and return duplicate identifiers.

    Parameters:
        records: Iterable of mappings expected to contain an `id` field.

    Returns:
        Pair of the last record for each ID and a sorted duplicate-ID list.
    """
    index: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str):
            continue
        if record_id in index:
            duplicates.add(record_id)
        index[record_id] = record
    return index, sorted(duplicates)


def _missing_ids(values: Iterable[str], available: set[str]) -> list[str]:
    """Return sorted referenced identifiers absent from the available set."""
    return sorted({value for value in values if value not in available})


def _non_null_locator_count(locator: dict[str, Any]) -> int:
    """Count meaningful source-locator values, excluding extensions."""
    return sum(
        value not in (None, "", [])
        for key, value in locator.items()
        if key != "extensions"
    )


## Evidence compatibility
## Reject mastery claims contradicted by coarse performance metadata.
def _evidence_mastery_ceiling(evidence: dict[str, Any]) -> int:
    """Return a conservative compatibility ceiling for one evidence record.

    Parameters:
        evidence: Learner evidence with outcome, support, and capabilities.

    Returns:
        Highest mastery level not contradicted by those coarse fields. This is
        only a rejection bound; target-specific quality and context still
        require pedagogical judgment before assigning a level.
    """
    capability_ceiling = max(
        (
            MASTERY_CAPABILITY_CEILINGS.get(capability, 0)
            for capability in evidence.get("demonstrated_capabilities", [])
        ),
        default=0,
    )
    return min(
        capability_ceiling,
        MASTERY_OUTCOME_CEILINGS.get(evidence.get("outcome"), 0),
        MASTERY_SUPPORT_CEILINGS.get(evidence.get("support_level"), 0),
    )


def _source_binding_errors(
    owner_type: str,
    owner_id: str,
    reference_ids: Iterable[str],
    reference_index: dict[str, dict[str, Any]],
) -> list[str]:
    """Validate source references owned by one graph or learning record.

    Parameters:
        owner_type: Entity kind recorded by `supported_entity_type`.
        owner_id: Stable identifier of the record holding the references.
        reference_ids: Source-reference identifiers attached to the record.
        reference_index: All source-reference records indexed by identifier.

    Returns:
        Missing-reference and mismatched-binding errors.
    """
    errors: list[str] = []
    for reference_id in reference_ids:
        reference = reference_index.get(reference_id)
        if reference is None:
            errors.append(f"{owner_type} {owner_id} references missing source reference {reference_id}")
        elif (
            reference.get("supported_entity_type") != owner_type
            or reference.get("supported_entity_id") != owner_id
        ):
            errors.append(
                f"{owner_type} {owner_id} has source reference {reference_id} bound to "
                f"{reference.get('supported_entity_type')} {reference.get('supported_entity_id')}"
            )
    return errors


## Graph-view validation
## Confirm displayed subgraphs remain referentially sound and connected.
def _view_connectivity_errors(
    view_name: str,
    view: dict[str, Any],
    node_index: dict[str, dict[str, Any]],
    edge_index: dict[str, dict[str, Any]],
) -> list[str]:
    """Validate one context, core, or neighborhood view.

    Parameters:
        view_name: View identifier used in error messages.
        view: Map-view record containing visible and collapsed IDs.
        node_index: All graph nodes indexed by stable ID.
        edge_index: All graph edges indexed by stable ID.

    Returns:
        Human-readable invariant violations for this view.
    """
    errors: list[str] = []
    node_ids = set(node_index)
    edge_ids = set(edge_index)
    visible_nodes = set(view.get("visible_node_ids", []))
    visible_edges = set(view.get("visible_edge_ids", []))
    collapsed_nodes = set(view.get("collapsed_node_ids", []))

    for node_id in _missing_ids(visible_nodes | collapsed_nodes, node_ids):
        errors.append(f"map view {view_name} references missing node {node_id}")
    for edge_id in _missing_ids(visible_edges, edge_ids):
        errors.append(f"map view {view_name} references missing edge {edge_id}")
    for node_id in sorted(visible_nodes & collapsed_nodes):
        errors.append(f"map view {view_name} marks node {node_id} both visible and collapsed")

    focus_node_id = view.get("focus_node_id")
    if focus_node_id is not None and focus_node_id not in visible_nodes:
        errors.append(f"map view {view_name} focus node {focus_node_id} is not visible")

    adjacency = {node_id: set() for node_id in visible_nodes if node_id in node_ids}
    for edge_id in sorted(visible_edges & edge_ids):
        edge = edge_index[edge_id]
        if edge.get("lifecycle") != "active":
            errors.append(f"map view {view_name} shows non-active edge {edge_id}")
        source_id = edge.get("source_node_id")
        target_id = edge.get("target_node_id")
        if source_id not in visible_nodes or target_id not in visible_nodes:
            errors.append(
                f"map view {view_name} shows edge {edge_id} without both endpoints"
            )
            continue
        adjacency[source_id].add(target_id)
        adjacency[target_id].add(source_id)

    if len(adjacency) > 1:
        start_id = next(iter(adjacency))
        reached = {start_id}
        pending = [start_id]
        while pending:
            current_id = pending.pop()
            for neighbor_id in adjacency[current_id] - reached:
                reached.add(neighbor_id)
                pending.append(neighbor_id)
        for node_id in sorted(set(adjacency) - reached):
            errors.append(f"map view {view_name} has disconnected visible node {node_id}")

    if view_name == "core" and len(visible_nodes) > 12:
        if not view.get("expanded_by_request") or not view.get("display_limit_override_reason"):
            errors.append("core view exceeds 12 nodes without an explicit learner-request override")

    for node_id in sorted((visible_nodes | collapsed_nodes) & node_ids):
        if node_index[node_id].get("lifecycle") != "active":
            errors.append(f"map view {view_name} contains non-active node {node_id}")

    return errors


## Cross-object validation
## Check semantic and referential invariants beyond JSON Schema shape.
def validate_state(state: dict[str, Any]) -> list[str]:
    """Validate a Study session state's cross-object invariants.

    Parameters:
        state: Parsed state conforming structurally to `session-state.schema.json`.

    Returns:
        Ordered list of human-readable errors. An empty list means all checked
        cross-object invariants pass; it does not replace formal JSON Schema
        validation.
    """
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in state:
            errors.append(f"missing required top-level field {field}")

    if errors:
        return errors

    collections = {
        "node": state["nodes"],
        "edge": state["edges"],
        "question": state["questions"],
        "evidence": state["evidence"],
        "misconception": state["known_misconceptions"],
        "example": state["examples_seen"],
        "representation": state["representations_used"],
        "review item": state["review_queue"],
        "source": state["sources"],
        "source reference": state["source_references"],
        "artifact": state["generated_artifacts"],
        "revision": state["revision_log"],
    }
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    for collection_name, records in collections.items():
        index, duplicates = _record_index(records)
        indexes[collection_name] = index
        for duplicate_id in duplicates:
            errors.append(f"duplicate {collection_name} ID {duplicate_id}")

    node_index = indexes["node"]
    edge_index = indexes["edge"]
    question_index = indexes["question"]
    evidence_index = indexes["evidence"]
    misconception_index = indexes["misconception"]
    example_index = indexes["example"]
    representation_index = indexes["representation"]
    source_index = indexes["source"]
    source_reference_index = indexes["source reference"]
    artifact_index = indexes["artifact"]
    node_ids = set(node_index)
    edge_ids = set(edge_index)
    question_ids = set(question_index)
    evidence_ids = set(evidence_index)
    misconception_ids = set(misconception_index)
    source_ids = set(source_index)
    source_reference_ids = set(source_reference_index)
    artifact_ids = set(artifact_index)
    state_version = state.get("state_version")
    merged_node_ids = {
        node_id
        for node_id, node in node_index.items()
        if node.get("lifecycle") == "merged" or node.get("merged_into_node_id") is not None
    }
    active_node_ids = {
        node_id
        for node_id, node in node_index.items()
        if node.get("lifecycle") == "active" and node.get("merged_into_node_id") is None
    }
    active_edge_ids = {
        edge_id
        for edge_id, edge in edge_index.items()
        if edge.get("lifecycle") == "active"
    }

    for source_id in _missing_ids(state["learning_target"].get("source_ids", []), source_ids):
        errors.append(f"learning target references missing source {source_id}")

    for edge_id, edge in edge_index.items():
        for endpoint_name in ("source_node_id", "target_node_id"):
            endpoint_id = edge.get(endpoint_name)
            if endpoint_id not in node_ids:
                errors.append(f"edge {edge_id} has missing {endpoint_name} {endpoint_id}")
            elif (
                edge.get("lifecycle") == "active"
                and node_index[endpoint_id].get("lifecycle") != "active"
            ):
                errors.append(f"active edge {edge_id} targets non-active node {endpoint_id}")
        normalized_label = " ".join(str(edge.get("label", "")).lower().split())
        if not normalized_label:
            errors.append(f"edge {edge_id} has no semantic label")
        elif normalized_label in GENERIC_EDGE_LABELS:
            errors.append(f"edge {edge_id} uses generic label {normalized_label!r}")
        if edge.get("origin") == "source" and not edge.get("source_reference_ids"):
            errors.append(f"source-origin edge {edge_id} lacks a source reference")
        errors.extend(
            _source_binding_errors(
                "edge", edge_id, edge.get("source_reference_ids", []), source_reference_index
            )
        )
        introduced = edge.get("introduced_at_version")
        updated = edge.get("updated_at_version")
        if isinstance(state_version, int) and (
            not isinstance(introduced, int)
            or not isinstance(updated, int)
            or introduced > updated
            or updated > state_version
        ):
            errors.append(f"edge {edge_id} has inconsistent state-version bounds")

    for node_id, node in node_index.items():
        if node.get("origin") == "source" and not node.get("source_reference_ids"):
            errors.append(f"source-origin node {node_id} lacks a source reference")
        errors.extend(
            _source_binding_errors(
                "node", node_id, node.get("source_reference_ids", []), source_reference_index
            )
        )
        introduced = node.get("introduced_at_version")
        updated = node.get("updated_at_version")
        if isinstance(state_version, int) and (
            not isinstance(introduced, int)
            or not isinstance(updated, int)
            or introduced > updated
            or updated > state_version
        ):
            errors.append(f"node {node_id} has inconsistent state-version bounds")
        merged_into = node.get("merged_into_node_id")
        if merged_into is not None and merged_into not in node_ids:
            errors.append(f"node {node_id} merges into missing node {merged_into}")
        if node.get("lifecycle") == "merged" and not merged_into:
            errors.append(f"merged node {node_id} lacks merged_into_node_id")
        if merged_into == node_id:
            errors.append(f"node {node_id} cannot merge into itself")
        if merged_into is not None and node.get("lifecycle") == "active":
            errors.append(f"node {node_id} has a merge survivor but remains active")
        if merged_into in node_index and merged_into != node_id:
            survivor = node_index[merged_into]
            if survivor.get("lifecycle") != "active":
                errors.append(f"merged node {node_id} has non-active survivor {merged_into}")
            survivor_terms = {
                " ".join(str(term).casefold().split())
                for term in [survivor.get("label"), *survivor.get("aliases", [])]
            }
            for term in [node.get("label"), *node.get("aliases", [])]:
                normalized_term = " ".join(str(term).casefold().split())
                if normalized_term and normalized_term not in survivor_terms:
                    errors.append(
                        f"merged node {node_id} term {term!r} is not retained by "
                        f"survivor {merged_into}"
                    )

    for question_id, question in question_index.items():
        for node_id in _missing_ids(question.get("target_node_ids", []), node_ids):
            errors.append(f"question {question_id} targets missing node {node_id}")
        for edge_id in _missing_ids(question.get("target_edge_ids", []), edge_ids):
            errors.append(f"question {question_id} targets missing edge {edge_id}")
        errors.extend(
            _source_binding_errors(
                "question",
                question_id,
                question.get("source_reference_ids", []),
                source_reference_index,
            )
        )
        for evidence_id in _missing_ids(question.get("answered_by_evidence_ids", []), evidence_ids):
            errors.append(f"question {question_id} cites missing answer evidence {evidence_id}")
        introduced = question.get("introduced_at_version")
        if isinstance(state_version, int) and (
            not isinstance(introduced, int) or introduced > state_version
        ):
            errors.append(f"question {question_id} has inconsistent introduced version")
        if question.get("status") in LIVE_QUESTION_STATUSES:
            for node_id in sorted(
                set(question.get("target_node_ids", [])) - active_node_ids
            ):
                if node_id in node_ids:
                    errors.append(
                        f"live question {question_id} targets non-active node {node_id}"
                    )
            for edge_id in sorted(
                set(question.get("target_edge_ids", [])) - active_edge_ids
            ):
                if edge_id in edge_ids:
                    errors.append(
                        f"live question {question_id} targets non-active edge {edge_id}"
                    )

    for evidence_id, evidence in evidence_index.items():
        question_id = evidence.get("question_id")
        if question_id is not None and question_id not in question_ids:
            errors.append(f"evidence {evidence_id} references missing question {question_id}")
        for node_id in _missing_ids(evidence.get("target_node_ids", []), node_ids):
            errors.append(f"evidence {evidence_id} targets missing node {node_id}")
        for edge_id in _missing_ids(evidence.get("target_edge_ids", []), edge_ids):
            errors.append(f"evidence {evidence_id} targets missing edge {edge_id}")
        for reference_id in _missing_ids(evidence.get("source_reference_ids", []), source_reference_ids):
            errors.append(f"evidence {evidence_id} references missing source reference {reference_id}")

    mastery_groups = (
        ("node", state["mastery_by_node"], node_ids),
        ("edge", state["mastery_by_edge"], edge_ids),
    )
    for target_kind, mastery_records, target_ids in mastery_groups:
        for target_id, record in mastery_records.items():
            if target_id not in target_ids:
                errors.append(f"{target_kind} mastery targets missing {target_kind} {target_id}")
            if target_kind == "node" and target_id in merged_node_ids:
                errors.append(f"merged node {target_id} retains canonical mastery")
            record_evidence_ids = record.get("evidence_ids", [])
            mastery_level = record.get("level", 0)
            if mastery_level > 0 and not record_evidence_ids:
                errors.append(f"{target_kind} mastery {target_id} exceeds zero without evidence")
            for evidence_id in _missing_ids(record_evidence_ids, evidence_ids):
                errors.append(f"{target_kind} mastery {target_id} cites missing evidence {evidence_id}")
            evidence_target_field = f"target_{target_kind}_ids"
            directly_targeted_evidence: list[dict[str, Any]] = []
            for evidence_id in record_evidence_ids:
                evidence = evidence_index.get(evidence_id)
                if evidence is None:
                    continue
                if target_id not in evidence.get(evidence_target_field, []):
                    errors.append(
                        f"{target_kind} mastery {target_id} cites evidence {evidence_id} "
                        f"that does not target that {target_kind}"
                    )
                else:
                    directly_targeted_evidence.append(evidence)
            evidence_ceiling = max(
                (_evidence_mastery_ceiling(evidence) for evidence in directly_targeted_evidence),
                default=0,
            )
            if mastery_level > evidence_ceiling:
                errors.append(
                    f"{target_kind} mastery {target_id} level {mastery_level} exceeds "
                    f"the directly targeted evidence compatibility ceiling {evidence_ceiling}"
                )

    route_revision_index, duplicate_route_revisions = _record_index(
        state["route"].get("revisions", [])
    )
    for duplicate_id in duplicate_route_revisions:
        errors.append(f"duplicate route revision ID {duplicate_id}")
    route_revision_ids = set(route_revision_index)
    route_started_at = state["route"].get("started_at_version")
    if isinstance(state_version, int) and (
        not isinstance(route_started_at, int) or route_started_at > state_version
    ):
        errors.append("route has inconsistent started_at_version")
    for question_id in _missing_ids(state["route"].get("planned_question_ids", []), question_ids):
        errors.append(f"route references missing planned question {question_id}")
    for question_id in state["route"].get("planned_question_ids", []):
        question = question_index.get(question_id)
        if question is None:
            continue
        for node_id in sorted(
            set(question.get("target_node_ids", [])) - active_node_ids
        ):
            if node_id in node_ids:
                errors.append(
                    f"route-planned question {question_id} targets non-active node {node_id}"
                )
        for edge_id in sorted(
            set(question.get("target_edge_ids", [])) - active_edge_ids
        ):
            if edge_id in edge_ids:
                errors.append(
                    f"route-planned question {question_id} targets non-active edge {edge_id}"
                )
    for revision_id, revision in route_revision_index.items():
        for evidence_id in _missing_ids(revision.get("triggering_evidence_ids", []), evidence_ids):
            errors.append(f"route revision {revision_id} cites missing evidence {evidence_id}")
        revision_version = revision.get("state_version")
        if isinstance(state_version, int) and (
            not isinstance(revision_version, int) or revision_version > state_version
        ):
            errors.append(f"route revision {revision_id} has inconsistent state_version")

    for misconception_id, misconception in misconception_index.items():
        for node_id in _missing_ids(misconception.get("implicated_node_ids", []), node_ids):
            errors.append(f"misconception {misconception_id} implicates missing node {node_id}")
        for edge_id in _missing_ids(misconception.get("implicated_edge_ids", []), edge_ids):
            errors.append(f"misconception {misconception_id} implicates missing edge {edge_id}")
        for evidence_id in _missing_ids(misconception.get("evidence_ids", []), evidence_ids):
            errors.append(f"misconception {misconception_id} cites missing evidence {evidence_id}")
        repair_question_id = misconception.get("repair_question_id")
        if repair_question_id is not None and repair_question_id not in question_ids:
            errors.append(f"misconception {misconception_id} references missing repair question {repair_question_id}")
        route_revision_id = misconception.get("route_revision_id")
        if misconception.get("status") in {"confirmed", "repairing", "monitoring", "repaired"}:
            if route_revision_id not in route_revision_ids:
                errors.append(f"misconception {misconception_id} lacks a valid route revision")
        for question_id in _missing_ids(misconception.get("recheck_question_ids", []), question_ids):
            errors.append(f"misconception {misconception_id} references missing recheck question {question_id}")
        resolved_evidence_id = misconception.get("resolved_by_evidence_id")
        if resolved_evidence_id is not None and resolved_evidence_id not in evidence_ids:
            errors.append(f"misconception {misconception_id} cites missing repair evidence {resolved_evidence_id}")
        if misconception.get("status") in LIVE_MISCONCEPTION_STATUSES:
            for node_id in sorted(
                set(misconception.get("implicated_node_ids", [])) - active_node_ids
            ):
                if node_id in node_ids:
                    errors.append(
                        f"live misconception {misconception_id} implicates non-active node {node_id}"
                    )
            for edge_id in sorted(
                set(misconception.get("implicated_edge_ids", [])) - active_edge_ids
            ):
                if edge_id in edge_ids:
                    errors.append(
                        f"live misconception {misconception_id} implicates non-active edge {edge_id}"
                    )

    for example_id, example in example_index.items():
        for node_id in _missing_ids(example.get("target_node_ids", []), node_ids):
            errors.append(f"example {example_id} targets missing node {node_id}")
        for edge_id in _missing_ids(example.get("target_edge_ids", []), edge_ids):
            errors.append(f"example {example_id} targets missing edge {edge_id}")
        evidence_id = example.get("evidence_id")
        if evidence_id is not None and evidence_id not in evidence_ids:
            errors.append(f"example {example_id} references missing evidence {evidence_id}")
        errors.extend(
            _source_binding_errors(
                "example",
                example_id,
                example.get("source_reference_ids", []),
                source_reference_index,
            )
        )

    for representation_id, representation in representation_index.items():
        for node_id in _missing_ids(representation.get("target_node_ids", []), node_ids):
            errors.append(f"representation {representation_id} targets missing node {node_id}")
        for edge_id in _missing_ids(representation.get("target_edge_ids", []), edge_ids):
            errors.append(f"representation {representation_id} targets missing edge {edge_id}")
        artifact_id = representation.get("artifact_id")
        if artifact_id is not None and artifact_id not in artifact_ids:
            errors.append(f"representation {representation_id} references missing artifact {artifact_id}")
        learner_evidence_id = representation.get("learner_evidence_id")
        if learner_evidence_id is not None and learner_evidence_id not in evidence_ids:
            errors.append(f"representation {representation_id} references missing learner evidence {learner_evidence_id}")

    for item_id, item in indexes["review item"].items():
        for node_id in _missing_ids(item.get("target_node_ids", []), node_ids):
            errors.append(f"review item {item_id} targets missing node {node_id}")
        for edge_id in _missing_ids(item.get("target_edge_ids", []), edge_ids):
            errors.append(f"review item {item_id} targets missing edge {edge_id}")
        misconception_id = item.get("misconception_id")
        if misconception_id is not None and misconception_id not in misconception_ids:
            errors.append(f"review item {item_id} references missing misconception {misconception_id}")
        for evidence_id in _missing_ids(item.get("created_from_evidence_ids", []), evidence_ids):
            errors.append(f"review item {item_id} cites missing evidence {evidence_id}")
        for reference_id in _missing_ids(item.get("source_reference_ids", []), source_reference_ids):
            errors.append(f"review item {item_id} references missing source reference {reference_id}")
        if item.get("status") in LIVE_REVIEW_STATUSES:
            for node_id in sorted(
                set(item.get("target_node_ids", [])) - active_node_ids
            ):
                if node_id in node_ids:
                    errors.append(
                        f"live review item {item_id} targets non-active node {node_id}"
                    )
            for edge_id in sorted(
                set(item.get("target_edge_ids", [])) - active_edge_ids
            ):
                if edge_id in edge_ids:
                    errors.append(
                        f"live review item {item_id} targets non-active edge {edge_id}"
                    )

    supported_indexes = {
        "node": node_index,
        "edge": edge_index,
        "question": question_index,
        "example": example_index,
        "representation": representation_index,
    }
    for reference_id, reference in source_reference_index.items():
        source_id = reference.get("source_id")
        if source_id not in source_ids:
            errors.append(f"source reference {reference_id} targets missing source {source_id}")
        if _non_null_locator_count(reference.get("locator", {})) == 0:
            errors.append(f"source reference {reference_id} has no usable locator")
        entity_type = reference.get("supported_entity_type")
        entity_id = reference.get("supported_entity_id")
        if entity_type in supported_indexes and entity_id not in supported_indexes[entity_type]:
            errors.append(f"source reference {reference_id} targets missing {entity_type} {entity_id}")
        if entity_type == "summary" and not state.get("session_summary"):
            errors.append(f"source reference {reference_id} targets missing session summary")

    for frontier_name in ("question_frontier", "unresolved_questions"):
        for question_id in _missing_ids(state[frontier_name], question_ids):
            errors.append(f"{frontier_name} references missing question {question_id}")
        for question_id in state[frontier_name]:
            question = question_index.get(question_id)
            if question is None:
                continue
            for node_id in sorted(set(question.get("target_node_ids", [])) & merged_node_ids):
                errors.append(
                    f"{frontier_name} question {question_id} targets merged node {node_id}"
                )
    for item in state["prerequisite_frontier"]:
        node_id = item.get("node_id")
        question_id = item.get("blocking_question_id")
        if node_id not in node_ids:
            errors.append(f"prerequisite frontier references missing node {node_id}")
        elif node_id in merged_node_ids:
            errors.append(f"prerequisite frontier contains merged node {node_id}")
        if question_id is not None and question_id not in question_ids:
            errors.append(
                f"prerequisite frontier for {node_id} references missing question {question_id}"
            )

    for view_name in ("context", "core", "neighborhood"):
        errors.extend(
            _view_connectivity_errors(
                view_name,
                state["map_views"].get(view_name, {}),
                node_index,
                edge_index,
            )
        )

    current_checks = (
        ("current_node_id", state["current_node_id"], node_ids),
        ("current_edge_id", state["current_edge_id"], edge_ids),
        ("current_question_id", state["current_question_id"], question_ids),
    )
    for field_name, current_id, available_ids in current_checks:
        if current_id is not None and current_id not in available_ids:
            errors.append(f"{field_name} references missing ID {current_id}")
    if state["current_node_id"] in merged_node_ids:
        errors.append(f"current_node_id references merged node {state['current_node_id']}")
    for node_id in _missing_ids(state["current_location_path"], node_ids):
        errors.append(f"current_location_path references missing node {node_id}")
    for node_id in state["current_location_path"]:
        if node_id in node_index and node_index[node_id].get("lifecycle") != "active":
            errors.append(f"current_location_path contains non-active node {node_id}")

    active_view = state["map_views"].get(state["current_zoom_level"], {})
    active_visible_nodes = set(active_view.get("visible_node_ids", []))
    active_visible_edges = set(active_view.get("visible_edge_ids", []))
    if state["current_node_id"] is not None and state["current_node_id"] not in active_visible_nodes:
        errors.append("current node is not visible in the active map view")
    if state["current_edge_id"] is not None and state["current_edge_id"] not in active_visible_edges:
        errors.append("current edge is not visible in the active map view")

    summary = state["session_summary"]
    for edge_id in _missing_ids(summary.get("important_edge_ids", []), edge_ids):
        errors.append(f"session summary references missing important edge {edge_id}")
    for question_id in _missing_ids(summary.get("remaining_question_ids", []), question_ids):
        errors.append(f"session summary references missing question {question_id}")

    recommendation = state.get("next_recommended_route")
    if recommendation:
        for question_id in _missing_ids(recommendation.get("next_question_ids", []), question_ids):
            errors.append(f"next route references missing question {question_id}")
        for node_id in _missing_ids(recommendation.get("next_node_ids", []), node_ids):
            errors.append(f"next route references missing node {node_id}")
        for node_id in sorted(set(recommendation.get("next_node_ids", [])) & merged_node_ids):
            errors.append(f"next route references merged node {node_id}")

    revision_versions = [record.get("state_version") for record in state["revision_log"]]
    if isinstance(state_version, int):
        expected_versions = list(range(1, state_version + 1))
        if revision_versions != expected_versions:
            errors.append(
                f"revision_log versions {revision_versions} do not equal contiguous {expected_versions}"
            )
    for revision_id, revision in indexes["revision"].items():
        for evidence_id in _missing_ids(revision.get("triggering_evidence_ids", []), evidence_ids):
            errors.append(f"revision {revision_id} cites missing evidence {evidence_id}")

    recorded_merge_node_ids = {
        change.get("entity_id")
        for revision in state["revision_log"]
        for change in revision.get("changes", [])
        if change.get("operation") == "merge" and change.get("entity_type") == "node"
    }
    for node_id in sorted(merged_node_ids - recorded_merge_node_ids):
        errors.append(f"merged node {node_id} lacks a node merge revision change")

    return errors


## View selection
## Derive visible records from canonical map-view IDs.
def _records_for_view(
    state: dict[str, Any], zoom: str, include_collapsed: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return graph records displayed at one zoom level.

    Parameters:
        state: Valid Study session state.
        zoom: One of `context`, `core`, or `neighborhood`.
        include_collapsed: Whether to reveal nodes collapsed in this view.

    Returns:
        Pair of ordered node and edge records whose endpoints are included.
    """
    if zoom not in {"context", "core", "neighborhood"}:
        raise ValueError(f"unknown zoom level {zoom!r}")
    view = state["map_views"][zoom]
    selected_node_ids = list(view["visible_node_ids"])
    selected_edge_ids = list(view["visible_edge_ids"])
    if include_collapsed:
        selected_node_ids.extend(view["collapsed_node_ids"])

    node_index, _ = _record_index(state["nodes"])
    edge_index, _ = _record_index(state["edges"])
    selected_node_set = set(selected_node_ids)
    nodes = [node_index[node_id] for node_id in selected_node_ids if node_id in node_index]

    if include_collapsed:
        selected_edge_ids = [
            edge["id"]
            for edge in state["edges"]
            if edge.get("lifecycle") == "active"
            and edge.get("source_node_id") in selected_node_set
            and edge.get("target_node_id") in selected_node_set
        ]
    edges = [edge_index[edge_id] for edge_id in selected_edge_ids if edge_id in edge_index]
    return nodes, edges


def _escape_mermaid(value: Any) -> str:
    """Escape a value for a quoted Mermaid node or edge label."""
    return str(value).replace("\\", "\\\\").replace('"', "&quot;").replace("|", "&#124;")


## Human-readable rendering
## Present the same semantic view as Mermaid or linear text.
def render_mermaid(
    state: dict[str, Any],
    zoom: str | None = None,
    include_collapsed: bool = False,
    direction: str = "LR",
) -> str:
    """Render one Study view as Mermaid flowchart source.

    Parameters:
        state: Valid Study session state.
        zoom: View to render; defaults to the state's current zoom.
        include_collapsed: Reveal this view's collapsed nodes when true.
        direction: Mermaid flow direction, normally `LR` or `TD`.

    Returns:
        Mermaid source with stable ordering, semantic edge labels, and current
        node highlighting.
    """
    selected_zoom = zoom or state["current_zoom_level"]
    nodes, edges = _records_for_view(state, selected_zoom, include_collapsed)
    aliases = {node["id"]: f"N{index}" for index, node in enumerate(nodes)}
    lines = [f"flowchart {direction}"]

    for node in nodes:
        label = _escape_mermaid(node["label"])
        lines.append(f'  {aliases[node["id"]]}["{label}"]')
    for edge in edges:
        source_alias = aliases[edge["source_node_id"]]
        target_alias = aliases[edge["target_node_id"]]
        label = _escape_mermaid(edge["label"])
        arrow = "<-->" if edge.get("directionality") == "bidirectional" else "-->"
        lines.append(f'  {source_alias} {arrow}|"{label}"| {target_alias}')

    current_node_id = state.get("current_node_id")
    if current_node_id in aliases:
        lines.extend(
            [
                "  classDef current fill:#dbeafe,stroke:#1d4ed8,stroke-width:3px,color:#172033",
                f"  class {aliases[current_node_id]} current",
            ]
        )
    return "\n".join(lines) + "\n"


def render_text_map(
    state: dict[str, Any], zoom: str | None = None, include_collapsed: bool = False
) -> str:
    """Render one Study view as an accessible labeled edge list.

    Parameters:
        state: Valid Study session state.
        zoom: View to render; defaults to the current zoom.
        include_collapsed: Reveal this view's collapsed nodes when true.

    Returns:
        Plain text containing the anchor, location, and one semantic relation
        per line.
    """
    selected_zoom = zoom or state["current_zoom_level"]
    nodes, edges = _records_for_view(state, selected_zoom, include_collapsed)
    labels = {node["id"]: node["label"] for node in nodes}
    canonical_labels = {node["id"]: node["label"] for node in state["nodes"]}
    location_labels = [
        canonical_labels.get(node_id, node_id)
        for node_id in state.get("current_location_path", [])
    ]
    lines = [
        f"Anchor: {state['anchor_question']}",
        f"Zoom: {selected_zoom}",
        f"Here: {' > '.join(location_labels)}",
    ]
    question_index, _ = _record_index(state["questions"])
    current_question = question_index.get(state.get("current_question_id"))
    if current_question is not None:
        lines.append(f"Focus question: {current_question['text']}")
    current_edge = next(
        (edge for edge in edges if edge["id"] == state.get("current_edge_id")), None
    )
    if current_edge is not None:
        focus_arrow = (
            "<--{}-->"
            if current_edge.get("directionality") == "bidirectional"
            else "--{}-->"
        )
        lines.append(
            "Focus relationship: "
            f"{labels[current_edge['source_node_id']]} "
            f"{focus_arrow.format(current_edge['label'])} "
            f"{labels[current_edge['target_node_id']]}"
        )
    lines.append("Relationships:")
    for edge in edges:
        arrow = "<--{}-->" if edge.get("directionality") == "bidirectional" else "--{}-->"
        lines.append(
            f"- {labels[edge['source_node_id']]} {arrow.format(edge['label'])} "
            f"{labels[edge['target_node_id']]}. {edge['explanation']}"
        )
    return "\n".join(lines) + "\n"


## Portable artifact content
## Derive public graph and notes from canonical state.
def public_graph(state: dict[str, Any], zoom: str = "core") -> dict[str, Any]:
    """Build a learner-facing graph subset for one zoom level.

    Parameters:
        state: Valid Study session state.
        zoom: Context, core, or neighborhood view to expose.

    Returns:
        JSON-serializable graph containing visible records and separate mastery.
    """
    nodes, edges = _records_for_view(state, zoom, include_collapsed=False)
    node_ids = {node["id"] for node in nodes}
    edge_ids = {edge["id"] for edge in edges}
    return {
        "schema_version": state["schema_version"],
        "state_version": state["state_version"],
        "learning_target": state["learning_target"],
        "anchor_question": state["anchor_question"],
        "zoom": zoom,
        "current_node_id": (
            state["current_node_id"] if state["current_node_id"] in node_ids else None
        ),
        "current_edge_id": (
            state["current_edge_id"] if state["current_edge_id"] in edge_ids else None
        ),
        "current_question_id": state["current_question_id"],
        "nodes": nodes,
        "edges": edges,
        "mastery_by_node": {
            key: value for key, value in state["mastery_by_node"].items() if key in node_ids
        },
        "mastery_by_edge": {
            key: value for key, value in state["mastery_by_edge"].items() if key in edge_ids
        },
        "frontier_question_ids": state["question_frontier"],
    }


def lesson_notes(state: dict[str, Any]) -> str:
    """Create concise anchor-centered Markdown notes from current state.

    Parameters:
        state: Valid Study session state.

    Returns:
        Markdown synthesis containing current answer, core relationships,
        remaining frontier, synthesis task, transfer task, and next route.
    """
    node_index, _ = _record_index(state["nodes"])
    edge_index, _ = _record_index(state["edges"])
    question_index, _ = _record_index(state["questions"])
    summary = state["session_summary"]
    lines = [
        f"# {state['learning_target']['title']}",
        "",
        f"**Anchor question:** {state['anchor_question']}",
        "",
        "## Current answer",
        "",
        summary["current_anchor_answer"] or "Not yet synthesized.",
        "",
        "## Important relationships",
        "",
    ]
    for edge_id in summary["important_edge_ids"]:
        edge = edge_index[edge_id]
        lines.append(
            f"- **{node_index[edge['source_node_id']]['label']}** "
            f"—{edge['label']}→ **{node_index[edge['target_node_id']]['label']}**: "
            f"{edge['explanation']}"
        )
    lines.extend(["", "## Remaining frontier", ""])
    for question_id in summary["remaining_question_ids"]:
        lines.append(f"- {question_index[question_id]['text']}")
    lines.extend(
        [
            "",
            "## Synthesis task",
            "",
            summary["synthesis_task"] or "No synthesis task has been set.",
            "",
            "## Transfer task",
            "",
            summary["transfer_task"] or "No transfer task has been set.",
            "",
            "## Session notes",
            "",
            summary["notes"] or "No additional session notes.",
            "",
            "## Recommended next route",
            "",
            state["next_recommended_route"]["reason"]
            if state.get("next_recommended_route")
            else "No further route is currently recommended.",
            "",
        ]
    )
    return "\n".join(lines)


## Atomic output support
## Write complete artifacts without exposing partial files.
def _write_text_atomic(path: Path, content: str) -> None:
    """Write UTF-8 text atomically to a target path.

    Parameters:
        path: Final output path in an existing or newly created directory.
        content: Complete text to write.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        delete=False,
    ) as temporary_file:
        temporary_file.write(content)
        temporary_path = Path(temporary_file.name)
    temporary_path.replace(path)


def _state_with_export_records(state: dict[str, Any]) -> dict[str, Any]:
    """Return a copied state with one versioned export revision and artifact records."""
    exported_state = copy.deepcopy(state)
    new_version = int(exported_state["state_version"]) + 1
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    artifact_specs = (
        ("session_state", "session_state.json", "Canonical resumable learning state."),
        ("map_json", "map.json", "Learner-facing core semantic graph."),
        ("mermaid", "map.mmd", "Mermaid source for the visible core map."),
        ("lesson_notes", "lesson_notes.md", "Anchor-centered session synthesis."),
        ("review_cards", "review_cards.csv", "Mixed node, edge, mechanism, and transfer review cards."),
        ("review_schedule", "review_schedule.csv", "Portable spaced-review dates."),
    )
    artifact_records = []
    changes = []
    for artifact_type, filename, description in artifact_specs:
        artifact_id = f"artifact_export_{new_version}_{artifact_type}"
        artifact_records.append(
            {
                "id": artifact_id,
                "type": artifact_type,
                "path": filename,
                "description": description,
                "created_from_state_version": new_version,
                "validated": False,
                "extensions": {},
            }
        )
        changes.append(
            {
                "operation": "add",
                "entity_type": "artifact",
                "entity_id": artifact_id,
                "summary": f"Prepared {filename} for content validation.",
                "extensions": {},
            }
        )

    existing_ids = {record["id"] for record in exported_state["generated_artifacts"]}
    exported_state["generated_artifacts"].extend(
        record for record in artifact_records if record["id"] not in existing_ids
    )
    exported_state["state_version"] = new_version
    exported_state["updated_at"] = timestamp
    exported_state["revision_log"].append(
        {
            "id": f"revision_export_{new_version}",
            "state_version": new_version,
            "occurred_at": timestamp,
            "kind": "artifact_update",
            "reason": "Prepared a portable artifact export without changing the learning graph.",
            "triggering_evidence_ids": [],
            "changes": changes,
            "extensions": {},
        }
    )
    return exported_state


## Generated-content validation
## Check each portable serialization before recording successful validation.
def _artifact_content_errors(
    contents: dict[str, str], schedule: list[dict[str, Any]]
) -> list[str]:
    """Validate the six generated artifact strings without writing them.

    Parameters:
        contents: Filename-to-content mapping for one portable export.
        schedule: Review rows used to create the schedule CSV.

    Returns:
        Human-readable parse, structure, and cross-artifact errors.
    """
    errors: list[str] = []
    expected_filenames = {
        "session_state.json",
        "map.json",
        "map.mmd",
        "lesson_notes.md",
        "review_cards.csv",
        "review_schedule.csv",
    }
    if set(contents) != expected_filenames:
        errors.append("artifact bundle does not contain exactly the six portable files")
        return errors

    try:
        parsed_state = json.loads(contents["session_state.json"])
    except (TypeError, json.JSONDecodeError) as error:
        errors.append(f"session_state.json is not valid JSON: {error}")
        return errors
    state_errors = validate_state(parsed_state)
    if state_errors:
        errors.append("session_state.json fails cross-object validation")

    try:
        parsed_graph = json.loads(contents["map.json"])
    except (TypeError, json.JSONDecodeError) as error:
        errors.append(f"map.json is not valid JSON: {error}")
    else:
        expected_graph = public_graph(parsed_state, zoom="core")
        if parsed_graph != expected_graph:
            errors.append("map.json is not the core public graph for session_state.json")
        graph_node_ids = {node.get("id") for node in parsed_graph.get("nodes", [])}
        graph_edge_ids = {edge.get("id") for edge in parsed_graph.get("edges", [])}
        if parsed_graph.get("current_node_id") not in graph_node_ids | {None}:
            errors.append("map.json current_node_id is outside its node subset")
        if parsed_graph.get("current_edge_id") not in graph_edge_ids | {None}:
            errors.append("map.json current_edge_id is outside its edge subset")
        for edge in parsed_graph.get("edges", []):
            if (
                edge.get("source_node_id") not in graph_node_ids
                or edge.get("target_node_id") not in graph_node_ids
            ):
                errors.append(f"map.json edge {edge.get('id')} has an omitted endpoint")

    mermaid = contents["map.mmd"]
    if not mermaid.startswith("flowchart ") or mermaid != render_mermaid(
        parsed_state, zoom="core"
    ):
        errors.append("map.mmd is not the generated core Mermaid flowchart")

    notes = contents["lesson_notes.md"]
    if not notes.strip() or notes != lesson_notes(parsed_state):
        errors.append("lesson_notes.md is empty or inconsistent with session_state.json")

    csv_specs = (
        (
            "review_cards.csv",
            [
                "review_id",
                "kind",
                "prompt",
                "node_ids",
                "edge_ids",
                "misconception_id",
                "success_criteria",
                "source_reference_ids",
            ],
            review_cards_to_csv(parsed_state["review_queue"]),
        ),
        (
            "review_schedule.csv",
            ["review_id", "due_date", "interval_days", "kind", "prompt", "status"],
            review_schedule_to_csv(schedule),
        ),
    )
    for filename, expected_fields, expected_content in csv_specs:
        reader = csv.DictReader(io.StringIO(contents[filename]))
        rows = list(reader)
        if reader.fieldnames != expected_fields or contents[filename] != expected_content:
            errors.append(f"{filename} is not the expected portable CSV")
        if filename == "review_cards.csv" and len(rows) != len(parsed_state["review_queue"]):
            errors.append("review_cards.csv row count does not match the review queue")
        if filename == "review_schedule.csv" and len(rows) != len(schedule):
            errors.append("review_schedule.csv row count does not match the schedule")

    return errors


## Artifact export
## Write a coherent portable bundle after validating canonical state.
def export_artifacts(
    state: dict[str, Any],
    output_directory: Path,
    start_date: date | None = None,
) -> list[Path]:
    """Validate state and export a portable Study artifact set.

    Parameters:
        state: Parsed Study session state.
        output_directory: Caller-selected directory for six portable files.
        start_date: Optional base date for review items lacking a due date.

    Returns:
        Paths written, ordered as state, graph, Mermaid, notes, cards, schedule.

    Raises:
        ValueError: Cross-object state invariants fail before or after export.
    """
    errors = validate_state(state)
    if errors:
        raise ValueError("Invalid Study state:\n- " + "\n- ".join(errors))

    exported_state = _state_with_export_records(state)
    export_errors = validate_state(exported_state)
    if export_errors:
        raise ValueError("Invalid exported Study state:\n- " + "\n- ".join(export_errors))

    schedule = build_review_schedule(exported_state, start_date=start_date)
    contents = {
        "session_state.json": json.dumps(exported_state, indent=2, ensure_ascii=False) + "\n",
        "map.json": json.dumps(public_graph(exported_state, zoom="core"), indent=2, ensure_ascii=False) + "\n",
        "map.mmd": render_mermaid(exported_state, zoom="core"),
        "lesson_notes.md": lesson_notes(exported_state),
        "review_cards.csv": review_cards_to_csv(exported_state["review_queue"]),
        "review_schedule.csv": review_schedule_to_csv(schedule),
    }
    content_errors = _artifact_content_errors(contents, schedule)
    if content_errors:
        raise ValueError("Invalid generated artifacts:\n- " + "\n- ".join(content_errors))

    new_artifact_ids = {
        change["entity_id"]
        for change in exported_state["revision_log"][-1]["changes"]
        if change.get("entity_type") == "artifact"
    }
    artifact_paths: dict[str, str] = {}
    for artifact in exported_state["generated_artifacts"]:
        if artifact["id"] in new_artifact_ids:
            artifact["validated"] = True
            artifact_paths[artifact["id"]] = artifact["path"]
    export_revision = exported_state["revision_log"][-1]
    export_revision["reason"] = (
        "Recorded a content-validated portable artifact export without changing the learning graph."
    )
    for change in export_revision["changes"]:
        artifact_id = change.get("entity_id")
        if artifact_id in artifact_paths:
            change["summary"] = f"Validated {artifact_paths[artifact_id]} for portable export."

    contents["session_state.json"] = (
        json.dumps(exported_state, indent=2, ensure_ascii=False) + "\n"
    )
    final_content_errors = _artifact_content_errors(contents, schedule)
    if final_content_errors:
        raise ValueError(
            "Invalid finalized artifacts:\n- " + "\n- ".join(final_content_errors)
        )

    output_directory = Path(output_directory)
    paths: list[Path] = []
    for filename, content in contents.items():
        path = output_directory / filename
        _write_text_atomic(path, content)
        paths.append(path)
    return paths
