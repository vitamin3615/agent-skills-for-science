#!/usr/bin/env python3
"""
PubMed Abstract Cleanup

Removes metadata and boilerplate from PubMed markdown to save tokens:
- Author affiliations (numbered superscripts)
- Funding statements
- Keywords/MeSH terms
- Copyright notices
- Journal metadata
- DOI/URL links

Preserves: Title, PMID, Author names (without affiliations), Abstract text

Usage:
    # Preview what will be removed
    python cleanup_abstracts.py pubmed_results.md --dry-run --verbose

    # Clean and save
    python cleanup_abstracts.py pubmed_results.md -o pubmed_cleaned.md

    # Aggressive mode (remove more)
    python cleanup_abstracts.py pubmed_results.md -o cleaned.md --aggressive
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple


# Patterns for metadata to remove
REMOVAL_PATTERNS = {
    'affiliations': [
        r'^\d+\s*[A-Z][^.]+\.\s*$',  # Lines starting with numbers (affiliations)
        r'^[¹²³⁴⁵⁶⁷⁸⁹⁰]+\s*.+$',  # Unicode superscript affiliations
        r'^\*\s*[A-Z][^.]+\.\s*$',  # Asterisk affiliations
    ],
    'funding': [
        r'^Funding:.*$',
        r'^Grant support:.*$',
        r'^Financial disclosure:.*$',
        r'^This work was supported by.*$',
        r'^Supported by.*$',
    ],
    'keywords': [
        r'^Keywords?:.*$',
        r'^MeSH [Tt]erms:.*$',
        r'^Index terms:.*$',
    ],
    'copyright': [
        r'^Copyright ©.*$',
        r'^©\s*\d{4}.*$',
        r'^\(c\)\s*\d{4}.*$',
        r'^All rights reserved\.*$',
    ],
    'journal_meta': [
        r'^DOI:.*$',
        r'^\*\*DOI:\*\*.*$',
        r'^10\.\d{4,}.*$',  # DOI values (10.xxxx/...)
        r'^PMCID:.*$',
        r'^Published:.*$',
        r'^Available online:.*$',
        r'^Received:.*Accepted:.*$',
        r'^\[Epub ahead of print\].*$',
        r'^\*\*Volume/Issue:\*\*.*$',
        r'^Volume:.*Issue:.*$',
        r'^\*\*Publication Date:\*\*.*$',
        r'^\d{4}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*$',  # Date values
        r'^\*\*Journal:\*\*.*$',
        r'^# PubMed Search Results:.*$',  # Search header
        r'^## Search Information.*$',  # Search section
        r'^\*\*Search Date:\*\*.*$',
        r'^\*\*Results Found:\*\*.*$',
        r'^## Detailed Article Information.*$',
    ],
    'authors': [
        r'^\*\*Authors:\*\*.*$',  # Authors header
        r'^[A-Z][a-z]+ [A-Z](?:,\s*[A-Z][a-z]+ [A-Z])+.*$',  # Author list lines (Name X, Name Y, ...)
    ],
    'links': [
        r'^https?://.*$',
        r'^www\..*$',
    ],
}

# Aggressive patterns (only used with --aggressive flag)
AGGRESSIVE_PATTERNS = {
    'conflict': [
        r'^Conflict of interest:.*$',
        r'^Competing interests:.*$',
        r'^The authors declare.*$',
    ],
    'acknowledgments': [
        r'^Acknowledgments?:.*$',
        r'^We thank.*$',
    ],
    'supplementary': [
        r'^Supplementary [Mm]aterial:.*$',
        r'^Data availability:.*$',
    ],
}


def should_remove_line(line: str, aggressive: bool = False) -> Tuple[bool, str]:
    """
    Check if line matches removal patterns.

    Returns: (should_remove, reason)
    """
    line_stripped = line.strip()

    if not line_stripped:
        return False, ''

    # Check standard patterns
    for category, patterns in REMOVAL_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                return True, category

    # Check aggressive patterns if enabled
    if aggressive:
        for category, patterns in AGGRESSIVE_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    return True, f'aggressive:{category}'

    return False, ''


def clean_author_line(line: str) -> str:
    """
    Clean author line: remove affiliation superscripts but keep names.

    Example:
        "Authors: Smith J¹², Jones K³, Lee M⁴"
        → "Authors: Smith J, Jones K, Lee M"
    """
    if not line.lower().startswith('author'):
        return line

    # Remove Unicode superscripts
    cleaned = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+', '', line)
    # Remove numeric superscripts
    cleaned = re.sub(r'\d+(?=,|\s|$)', '', cleaned)
    # Remove asterisks
    cleaned = re.sub(r'\*+', '', cleaned)
    # Clean up extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)

    return cleaned.strip()


def cleanup_abstracts(
    content: str,
    aggressive: bool = False
) -> Tuple[str, dict]:
    """
    Clean PubMed markdown content.

    Returns: (cleaned_content, stats)
    """
    lines = content.split('\n')
    cleaned_lines = []
    stats = {
        'total_lines': len(lines),
        'removed_lines': 0,
        'removed_by_category': {},
        'kept_lines': 0,
    }

    for line in lines:
        should_remove, reason = should_remove_line(line, aggressive)

        if should_remove:
            stats['removed_lines'] += 1
            stats['removed_by_category'][reason] = stats['removed_by_category'].get(reason, 0) + 1
        else:
            cleaned_lines.append(line)
            stats['kept_lines'] += 1

    cleaned_content = '\n'.join(cleaned_lines)

    # Collapse consecutive blank lines (3+ blank lines → 2 blank lines)
    cleaned_content = re.sub(r'\n\n\n+', '\n\n', cleaned_content)

    # Calculate token estimate
    stats['original_tokens'] = len(content) // 4
    stats['cleaned_tokens'] = len(cleaned_content) // 4
    stats['token_reduction'] = stats['original_tokens'] - stats['cleaned_tokens']
    stats['reduction_percent'] = (stats['token_reduction'] / stats['original_tokens'] * 100) if stats['original_tokens'] > 0 else 0

    return cleaned_content, stats


def print_stats(stats: dict, verbose: bool = False):
    """Print cleanup statistics."""
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Total Lines:       {stats['total_lines']}")
    print(f"Removed Lines:     {stats['removed_lines']} ({stats['removed_lines']/stats['total_lines']*100:.1f}%)")
    print(f"Kept Lines:        {stats['kept_lines']}")
    print()
    print(f"Original Tokens:   ~{stats['original_tokens']:,}")
    print(f"Cleaned Tokens:    ~{stats['cleaned_tokens']:,}")
    print(f"Token Reduction:   ~{stats['token_reduction']:,} ({stats['reduction_percent']:.1f}%)")
    print("=" * 60)

    if verbose and stats['removed_by_category']:
        print("\nRemoved by Category:")
        for category, count in sorted(stats['removed_by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category:20s}: {count:4d} lines")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Clean PubMed abstracts by removing metadata and boilerplate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview what will be removed
    python cleanup_abstracts.py pubmed_results.md --dry-run --verbose

    # Clean and save
    python cleanup_abstracts.py pubmed_results.md -o pubmed_cleaned.md

    # Aggressive mode (removes more)
    python cleanup_abstracts.py pubmed_results.md -o cleaned.md --aggressive

Removal categories (standard):
    - affiliations: Author institution lines
    - funding: Grant and support statements
    - keywords: MeSH terms and keyword lists
    - copyright: Copyright notices
    - journal_meta: DOI, publication dates
    - links: URLs

Additional removal (--aggressive):
    - conflict: Conflict of interest statements
    - acknowledgments: Acknowledgment sections
    - supplementary: Data availability statements
"""
    )

    parser.add_argument('file', help='PubMed markdown file to clean')
    parser.add_argument('-o', '--output', help='Output file (default: print to stdout)')
    parser.add_argument('--aggressive', action='store_true',
                       help='Remove additional metadata (conflicts, acknowledgments)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be removed without saving')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed removal statistics')

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1

    # Read and clean
    content = Path(args.file).read_text(encoding='utf-8')
    cleaned_content, stats = cleanup_abstracts(
        content,
        aggressive=args.aggressive
    )

    # Print stats
    print_stats(stats, args.verbose)

    if args.dry_run:
        print("\n✓ Dry run complete. No files written.")
        print(f"  Run without --dry-run to save cleaned file.")
        return 0

    # Save or print
    if args.output:
        Path(args.output).write_text(cleaned_content, encoding='utf-8')
        print(f"\n✓ Cleaned file saved: {args.output}")
        print(f"\n  Next: python scripts/chunk_abstracts.py {args.output} --output-dir Temp/chunks")
    else:
        print("\n" + "=" * 60)
        print("CLEANED CONTENT (first 1000 chars)")
        print("=" * 60)
        print(cleaned_content[:1000])
        print("...")
        print("\nUse -o/--output to save to file.")

    return 0


if __name__ == '__main__':
    exit(main())
