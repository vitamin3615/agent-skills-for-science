#!/usr/bin/env python3
"""
Filter Relevant Papers from JSONL

Removes papers marked as irrelevant by worker AI during extraction,
keeping only papers with relevant:true for clustering.

Usage:
    # Filter single file
    python filter_relevant.py extracted_001.jsonl -o relevant.jsonl

    # Filter and combine all extracted files
    python filter_relevant.py Temp/chunks/extracted/*.jsonl -o combined_relevant.jsonl

    # Show statistics only
    python filter_relevant.py extracted_*.jsonl --stats-only
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict


def load_jsonl(file_path: str) -> List[Dict]:
    """Load JSONL file into list of dicts."""
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠ Warning: Invalid JSON at {file_path}:{line_num}: {e}")
    return results


def filter_relevant(data: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Separate relevant and irrelevant papers.

    Returns: (relevant_papers, irrelevant_papers)
    """
    relevant = []
    irrelevant = []

    for entry in data:
        # Check relevance field (default to true if missing for backward compatibility)
        is_relevant = entry.get('relevant', True)

        if is_relevant:
            relevant.append(entry)
        else:
            irrelevant.append(entry)

    return relevant, irrelevant


def save_jsonl(data: List[Dict], output_path: str):
    """Save list of dicts to JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')


def print_stats(relevant: List[Dict], irrelevant: List[Dict], verbose: bool = False):
    """Print filtering statistics."""
    total = len(relevant) + len(irrelevant)

    print("\n" + "=" * 60)
    print("RELEVANCE FILTERING SUMMARY")
    print("=" * 60)
    print(f"Total Papers:      {total}")
    print(f"Relevant Papers:   {len(relevant)} ({len(relevant)/total*100:.1f}%)")
    print(f"Irrelevant Papers: {len(irrelevant)} ({len(irrelevant)/total*100:.1f}%)")
    print(f"Filtering Rate:    {len(irrelevant)/total*100:.1f}% removed")
    print("=" * 60)

    if verbose and irrelevant:
        print("\nIrrelevant Papers (Reasons):")
        print("-" * 60)
        # Group by reason
        reasons = {}
        for entry in irrelevant:
            reason = entry.get('reason', 'No reason provided')
            pmid = entry.get('pmid', 'unknown')
            if reason not in reasons:
                reasons[reason] = []
            reasons[reason].append(pmid)

        for reason, pmids in sorted(reasons.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n{reason}")
            print(f"  PMIDs ({len(pmids)}): {', '.join(pmids[:10])}")
            if len(pmids) > 10:
                print(f"  ... and {len(pmids) - 10} more")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Filter relevant papers from extraction JSONL files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Filter single file
    python filter_relevant.py extracted_001.jsonl -o relevant.jsonl

    # Filter and combine all extracted files
    python filter_relevant.py Temp/chunks/extracted/*.jsonl -o combined_relevant.jsonl

    # Show statistics without saving
    python filter_relevant.py extracted_*.jsonl --stats-only

    # Verbose mode (show irrelevant papers and reasons)
    python filter_relevant.py extracted_*.jsonl -o relevant.jsonl --verbose

Workflow:
    After extraction (Step 2), filter before clustering (Step 3):

    1. Extract with relevance filtering enabled (default)
    2. Filter relevant papers:
       python filter_relevant.py Temp/chunks/extracted/*.jsonl -o combined_relevant.jsonl
    3. Cluster using combined_relevant.jsonl (Step 3)
    4. Format (Step 4)

Benefits:
    - Saves tokens in clustering (only process relevant papers)
    - Improves quality (no irrelevant papers in output)
    - Faster clustering (fewer papers to analyze)
    - Typical filtering: 20-40% of papers removed in broad searches
"""
    )

    parser.add_argument('files', nargs='+', help='JSONL file(s) to filter')
    parser.add_argument('-o', '--output', help='Output file for relevant papers')
    parser.add_argument('--irrelevant-output', help='Optional output file for irrelevant papers')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show statistics without saving files')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed irrelevant paper reasons')

    args = parser.parse_args()

    # Load all input files
    all_data = []
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"⚠ Warning: File not found: {file_path}")
            continue
        data = load_jsonl(file_path)
        all_data.extend(data)

    if not all_data:
        print("Error: No data loaded from input files")
        return 1

    # Filter
    relevant, irrelevant = filter_relevant(all_data)

    # Print stats
    print_stats(relevant, irrelevant, args.verbose)

    # Save if requested
    if not args.stats_only:
        if args.output:
            save_jsonl(relevant, args.output)
            print(f"✓ Saved {len(relevant)} relevant papers to: {args.output}")

            if args.irrelevant_output:
                save_jsonl(irrelevant, args.irrelevant_output)
                print(f"✓ Saved {len(irrelevant)} irrelevant papers to: {args.irrelevant_output}")

            print(f"\n  Next: Use {args.output} for clustering (Step 3)")
        else:
            print("⚠ No output file specified. Use -o/--output to save filtered results.")
            print("  Or use --stats-only to just view statistics.")

    return 0


if __name__ == '__main__':
    exit(main())
