#!/usr/bin/env python3
"""
Research Question Definition Tool

Creates and validates research_question.yaml for survey extraction.
Supports both simple questions and fully decomposed operationalized specs.

Usage:
    python define_question.py --question "How does APOE4 affect AD?"
    python define_question.py --from-yaml structured_question.yaml
    python define_question.py --validate research_question.yaml
"""

import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def create_question_file(
    question: str,
    entities: list = None,
    threshold: float = 0.5,
    context: str = '',
    comparisons: list = None,
    evidence_types: list = None,
    modalities: list = None,
    inclusion_criteria: list = None,
    exclusion_criteria: list = None,
    output: str = 'Temp/research_question.yaml'
) -> Path:
    """Create research_question.yaml from inputs."""
    config = {
        'question': question,
        'focus_entities': entities or [],
        'relevance_threshold': threshold,
        'context': context
    }

    if comparisons:
        config['comparisons'] = comparisons
    if evidence_types:
        config['evidence_types'] = evidence_types
    if modalities:
        config['modalities'] = modalities
    if inclusion_criteria:
        config['inclusion_criteria'] = inclusion_criteria
    if exclusion_criteria:
        config['exclusion_criteria'] = exclusion_criteria

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, width=120)

    print(f"✓ Created: {output_path}")
    print(f"  Question: {question}")
    if entities:
        print(f"  Focus entities: {', '.join(entities)}")
    print(f"  Relevance threshold: {threshold}")
    if comparisons:
        print(f"  Comparisons: {len(comparisons)} defined")
    if modalities:
        print(f"  Modalities: {len(modalities)} defined")
    if evidence_types:
        print(f"  Evidence types: {len(evidence_types)} defined")

    return output_path


def load_from_yaml(filepath: str, output: str) -> Path:
    """Load a structured question YAML and save to output path."""
    path = Path(filepath)
    if not path.exists():
        print(f"✗ File not found: {filepath}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"✗ Invalid YAML: {e}")
        return None

    if not config.get('question'):
        print("✗ Missing required field: 'question'")
        return None

    config.setdefault('focus_entities', [])
    config.setdefault('relevance_threshold', 0.5)
    config.setdefault('context', '')

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, width=120)

    print(f"✓ Loaded structured question from: {filepath}")
    print(f"  Saved to: {output_path}")
    print(f"  Question: {config['question'][:80]}...")
    for key in ['comparisons', 'evidence_types', 'modalities', 'inclusion_criteria', 'exclusion_criteria']:
        if config.get(key):
            print(f"  {key}: {len(config[key])} items")

    return output_path


def validate_question_file(filepath: str) -> dict:
    """Validate research_question.yaml structure."""
    path = Path(filepath)
    if not path.exists():
        print(f"✗ File not found: {filepath}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"✗ Invalid YAML: {e}")
        return None

    if not config.get('question'):
        print("✗ Missing required field: 'question'")
        return None

    config.setdefault('focus_entities', [])
    config.setdefault('relevance_threshold', 0.5)
    config.setdefault('context', '')

    print(f"✓ Valid: {filepath}")
    print(f"  Question: {config['question'][:80]}...")

    # Report decomposition completeness
    decomposed = 0
    for key in ['comparisons', 'evidence_types', 'modalities', 'inclusion_criteria', 'exclusion_criteria']:
        if config.get(key):
            decomposed += 1
            print(f"  ✓ {key}: {len(config[key])} items")
        else:
            print(f"  - {key}: not defined")

    if decomposed >= 3:
        print(f"\n  Decomposition: {decomposed}/5 dimensions defined (well-operationalized)")
    elif decomposed > 0:
        print(f"\n  Decomposition: {decomposed}/5 dimensions defined (partially operationalized)")
    else:
        print(f"\n  Decomposition: basic question only (consider adding comparisons, evidence_types, modalities)")

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Define research question for survey extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Simple question
    python define_question.py --question "How does APOE4 affect AD?" \\
        --entities "APOE4,metabol*,lipi*"

    # With explicit comparisons and evidence types
    python define_question.py --question "How does APOE genotype affect AD omics?" \\
        --entities "APOE4,APOE2,APOE3" \\
        --comparisons "APOE4/4 vs APOE3/3,APOE4 carriers vs non-carriers" \\
        --evidence-types "Genotype-stratified differential analysis,eQTL/pQTL mapping"

    # Load fully structured YAML
    python define_question.py --from-yaml my_detailed_question.yaml

    # Validate existing file
    python define_question.py --validate research_question.yaml
"""
    )

    parser.add_argument('--question', '-q', help='Research question text')
    parser.add_argument('--entities', '-e', help='Focus entities (comma-separated)')
    parser.add_argument('--threshold', '-t', type=float, default=0.5,
                        help='Relevance threshold 0.0-1.0 (default: 0.5)')
    parser.add_argument('--context', '-c', help='Additional context')
    parser.add_argument('--comparisons', help='Explicit comparisons (comma-separated)')
    parser.add_argument('--evidence-types', help='Evidence types (comma-separated)')
    parser.add_argument('--inclusion', help='Inclusion criteria (comma-separated)')
    parser.add_argument('--exclusion', help='Exclusion criteria (comma-separated)')
    parser.add_argument('--output', '-o', default='Temp/research_question.yaml',
                        help='Output file path')
    parser.add_argument('--from-yaml', help='Load structured question from YAML file')
    parser.add_argument('--validate', '-v', help='Validate existing YAML file')

    args = parser.parse_args()

    if args.validate:
        result = validate_question_file(args.validate)
        return 0 if result else 1

    if args.from_yaml:
        result = load_from_yaml(args.from_yaml, args.output)
        return 0 if result else 1

    if args.question:
        entities = [e.strip() for e in args.entities.split(',')] if args.entities else []
        comparisons = [c.strip() for c in args.comparisons.split(',')] if args.comparisons else None
        evidence_types = [e.strip() for e in args.evidence_types.split(',')] if args.evidence_types else None
        inclusion = [i.strip() for i in args.inclusion.split(',')] if args.inclusion else None
        exclusion = [x.strip() for x in args.exclusion.split(',')] if args.exclusion else None

        create_question_file(
            args.question,
            entities,
            args.threshold,
            args.context or '',
            comparisons=comparisons,
            evidence_types=evidence_types,
            inclusion_criteria=inclusion,
            exclusion_criteria=exclusion,
            output=args.output
        )
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    exit(main())
