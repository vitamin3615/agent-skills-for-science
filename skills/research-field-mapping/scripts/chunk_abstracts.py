#!/usr/bin/env python3
"""
PubMed Abstract Chunking for Question Extraction

Splits large PubMed markdown files into processable chunks while preserving
abstract boundaries and PMID associations.

Usage:
    python chunk_abstracts.py pubmed_results.md \\
        --output-dir Temp/chunks \\
        --abstracts-per-chunk 20 \\
        --max-tokens 10000
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: ~4 chars per token)."""
    return len(text) // 4


def detect_abstract_boundaries(content: str) -> List[Tuple[int, int, str]]:
    """
    Detect abstract boundaries in PubMed markdown.

    Returns: List of (start_line, end_line, pmid) tuples
    """
    lines = content.split('\n')
    boundaries = []
    current_start = 0
    current_pmid = None

    for i, line in enumerate(lines):
        # Detect abstract start: ### [Title] or PMID: pattern
        if line.startswith('### ') or re.match(r'^PMID:\s*\d+', line):
            # Save previous abstract if exists
            if current_start < i:
                boundaries.append((current_start, i - 1, current_pmid))
            current_start = i

            # Extract PMID if present
            pmid_match = re.search(r'PMID:\s*(\d+)', line)
            if pmid_match:
                current_pmid = pmid_match.group(1)

        # Detect abstract separator: ---
        elif line.strip() == '---' and i > current_start + 5:
            boundaries.append((current_start, i - 1, current_pmid))
            current_start = i + 1
            current_pmid = None

    # Add final abstract
    if current_start < len(lines):
        boundaries.append((current_start, len(lines) - 1, current_pmid))

    return boundaries


def chunk_abstracts(
    source_file: str,
    output_dir: str,
    abstracts_per_chunk: int = 20,
    max_tokens: int = 10000
) -> Dict:
    """
    Chunk PubMed markdown file into processable pieces.

    Returns: Metadata dictionary with chunking stats
    """
    content = Path(source_file).read_text(encoding='utf-8')
    lines = content.split('\n')

    # Detect abstract boundaries
    boundaries = detect_abstract_boundaries(content)
    total_abstracts = len(boundaries)

    if total_abstracts == 0:
        print("⚠ No abstracts detected. Check file format.")
        return {}

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Chunk abstracts
    chunks = []
    current_chunk_abstracts = []
    current_chunk_lines = []
    current_chunk_tokens = 0
    chunk_num = 1

    for start, end, pmid in boundaries:
        abstract_lines = lines[start:end + 1]
        abstract_text = '\n'.join(abstract_lines)
        abstract_tokens = estimate_tokens(abstract_text)

        # Check if adding this abstract would exceed limits
        would_exceed_abstracts = len(current_chunk_abstracts) >= abstracts_per_chunk
        would_exceed_tokens = current_chunk_tokens + abstract_tokens > max_tokens

        if current_chunk_abstracts and (would_exceed_abstracts or would_exceed_tokens):
            # Write current chunk
            chunk_file = output_path / f"chunk_{chunk_num:03d}.md"
            chunk_content = '\n'.join(current_chunk_lines)
            chunk_file.write_text(chunk_content, encoding='utf-8')

            chunks.append({
                'file': str(chunk_file),
                'abstracts': len(current_chunk_abstracts),
                'tokens': current_chunk_tokens,
                'pmids': current_chunk_abstracts
            })

            # Reset for next chunk
            chunk_num += 1
            current_chunk_abstracts = []
            current_chunk_lines = []
            current_chunk_tokens = 0

        # Add abstract to current chunk
        current_chunk_abstracts.append(pmid or f"abstract_{start}")
        current_chunk_lines.extend(abstract_lines)
        current_chunk_tokens += abstract_tokens

    # Write final chunk
    if current_chunk_abstracts:
        chunk_file = output_path / f"chunk_{chunk_num:03d}.md"
        chunk_content = '\n'.join(current_chunk_lines)
        chunk_file.write_text(chunk_content, encoding='utf-8')

        chunks.append({
            'file': str(chunk_file),
            'abstracts': len(current_chunk_abstracts),
            'tokens': current_chunk_tokens,
            'pmids': current_chunk_abstracts
        })

    # Create state file
    state = {
        'input_file': source_file,
        'total_abstracts': total_abstracts,
        'total_chunks': len(chunks),
        'abstracts_per_chunk_target': abstracts_per_chunk,
        'max_tokens_target': max_tokens,
        'created': datetime.now().isoformat(),
        'chunks': chunks
    }

    state_file = output_path / '.extraction_state.json'
    state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

    return state


def print_summary(state: Dict):
    """Print token-efficient summary table."""
    if not state:
        return

    chunks = state.get('chunks', [])
    total_abstracts = state.get('total_abstracts', 0)
    total_chunks = len(chunks)

    if total_chunks == 0:
        return

    # Calculate ranges
    abstracts_counts = [c['abstracts'] for c in chunks]
    tokens_counts = [c['tokens'] for c in chunks]

    abstracts_min = min(abstracts_counts)
    abstracts_max = max(abstracts_counts)
    tokens_min = min(tokens_counts)
    tokens_max = max(tokens_counts)

    print("\n" + "=" * 60)
    print("CHUNKING SUMMARY")
    print("=" * 60)
    print(f"Total Abstracts:      {total_abstracts}")
    print(f"Total Chunks:         {total_chunks}")
    print(f"Abstracts per Chunk:  {abstracts_min}-{abstracts_max}")
    print(f"Tokens per Chunk:     {tokens_min:,}-{tokens_max:,}")
    print(f"State File:           {Path(state.get('input_file', '')).parent}/chunks/.extraction_state.json")
    print("=" * 60)
    print("\n✓ Chunking complete. Ready for extraction.")
    print(f"  Next: python scripts/extract_orchestrator.py extract --chunks-dir {Path(chunks[0]['file']).parent}")


def main():
    parser = argparse.ArgumentParser(
        description='Chunk PubMed abstracts for L1/L2/L3 question extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python chunk_abstracts.py pubmed_results.md --output-dir Temp/chunks

    # Custom chunk size
    python chunk_abstracts.py pubmed_results.md -o Temp/chunks \\
        --abstracts-per-chunk 15 --max-tokens 8000

    # Larger chunks for faster processing
    python chunk_abstracts.py pubmed_results.md -o Temp/chunks \\
        --abstracts-per-chunk 25 --max-tokens 12000

Output:
    - chunk_001.md, chunk_002.md, ... (chunk files)
    - .extraction_state.json (metadata and resume state)
    - Summary table (token-efficient for Claude to read)
"""
    )

    parser.add_argument('file', help='PubMed markdown file')
    parser.add_argument('-o', '--output-dir', default='Temp/chunks',
                       help='Output directory for chunks (default: Temp/chunks)')
    parser.add_argument('--abstracts-per-chunk', type=int, default=20,
                       help='Target abstracts per chunk (default: 20)')
    parser.add_argument('--max-tokens', type=int, default=10000,
                       help='Maximum tokens per chunk (default: 10000)')
    parser.add_argument('--json', action='store_true',
                       help='Output JSON format for programmatic use')

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1

    # Chunk the file
    state = chunk_abstracts(
        args.file,
        args.output_dir,
        args.abstracts_per_chunk,
        args.max_tokens
    )

    if not state:
        return 1

    # Output results
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print_summary(state)

    return 0


if __name__ == '__main__':
    exit(main())
