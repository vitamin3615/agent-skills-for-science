#!/usr/bin/env python3
"""
Hierarchical Markdown Formatter

Converts clustered JSON (from Step 3) to hierarchical markdown for manuscript writing.

Usage:
    python format_output.py \\
        --input Temp/clustered_themes.json \\
        --output Temp/research_questions.md
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def slugify(text: str) -> str:
    """Convert text to anchor-safe slug."""
    return text.lower().replace(' ', '-').replace('?', '').replace(':', '')[:50]


def format_theme(theme: Dict, theme_num: int) -> str:
    """Format a single theme into hierarchical markdown."""
    lines = []
    theme_name = theme.get('name', f'Theme {theme_num}')
    papers = theme.get('papers', [])
    l1_questions = theme.get('l1_questions', [])

    # Theme header
    anchor = f"theme-{theme_num}"
    lines.append(f'<a name="{anchor}"></a>')
    lines.append(f'## Theme {theme_num}: {theme_name}')
    lines.append('')
    lines.append(f'**Papers**: {len(papers)} papers')
    if papers:
        pmid_list = ', '.join([f'PMID:{p}' if str(p).isdigit() else str(p) for p in papers[:20]])
        if len(papers) > 20:
            pmid_list += f', ... ({len(papers) - 20} more)'
        lines.append(f'**PMIDs**: {pmid_list}')
    lines.append('')

    # L1 questions
    for l1_data in l1_questions:
        if isinstance(l1_data, str):
            l1_question = l1_data
            l2_mechanisms = []
        else:
            l1_question = l1_data.get('question', l1_data.get('l1', ''))
            l2_mechanisms = l1_data.get('l2_mechanisms', l1_data.get('l2', []))

        lines.append(f'**L1**: {l1_question}')
        lines.append('')

        # L2 mechanisms
        for l2_data in l2_mechanisms:
            if isinstance(l2_data, str):
                l2_question = l2_data
                l3_details = []
            else:
                l2_question = l2_data.get('question', l2_data.get('l2', ''))
                l3_details = l2_data.get('l3_details', l2_data.get('l3', []))

            lines.append(f'- **L2**: {l2_question}')

            # L3 details (with PMIDs)
            for i, l3 in enumerate(l3_details, 1):
                lines.append(f'  - **L3-Q{i}**: {l3}')

            lines.append('')

    lines.append('---')
    lines.append('')

    return '\n'.join(lines)


def format_markdown(data: Dict) -> str:
    """Format clustered data into complete hierarchical markdown."""
    lines = []

    # Metadata header
    title = data.get('title', 'Research Questions: PubMed Literature Analysis')
    total_papers = data.get('total_papers', 0)
    themes = data.get('themes', [])
    extraction_date = data.get('extraction_date', datetime.now().strftime('%Y-%m-%d'))
    worker = data.get('worker', 'unknown')

    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'**Metadata**:')
    lines.append(f'- Total Papers: {total_papers}')
    lines.append(f'- Themes: {len(themes)}')
    lines.append(f'- Extraction Date: {extraction_date}')
    lines.append(f'- Worker: {worker}')
    lines.append('')

    # Table of Contents
    if themes:
        lines.append('## Table of Contents')
        lines.append('')
        for i, theme in enumerate(themes, 1):
            theme_name = theme.get('name', f'Theme {i}')
            anchor = f"theme-{i}"
            papers_count = len(theme.get('papers', []))
            lines.append(f'{i}. [{theme_name}](#{anchor}) ({papers_count} papers)')
        lines.append('')
        lines.append('---')
        lines.append('')

    # Themes
    for i, theme in enumerate(themes, 1):
        lines.append(format_theme(theme, i))

    # Cross-theme connections (if present)
    connections = data.get('cross_theme_connections', [])
    if connections:
        lines.append('## Cross-Theme Connections')
        lines.append('')
        for conn in connections:
            lines.append(f'**{conn.get("description", "Connection")}**')
            lines.append('')
            conn_l1 = conn.get('l1', conn.get('question', ''))
            if conn_l1:
                lines.append(f'**L1**: {conn_l1}')
                lines.append('')
            for l2 in conn.get('l2', []):
                lines.append(f'- **L2**: {l2}')
            lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Format clustered JSON into hierarchical markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python format_output.py --input clustered.json -o output.md

    # Specify title
    python format_output.py -i clustered.json -o output.md \\
        --title "APOE in Alzheimer's Disease"

Input JSON format:
    {
      "title": "Research Questions: Topic",
      "total_papers": 150,
      "themes": [
        {
          "name": "Theme Name",
          "papers": ["12345", "67890"],
          "l1_questions": [
            {
              "question": "L1 question?",
              "l2_mechanisms": [
                {
                  "question": "L2 question?",
                  "l3_details": ["L3 detail (PMID: 123)", "L3 detail (PMID: 456)"]
                }
              ]
            }
          ]
        }
      ]
    }

Output:
    Hierarchical markdown with:
    - Metadata header
    - Table of contents
    - L1 themes → L2 mechanisms → L3 details
    - PMIDs at L3 level only
"""
    )

    parser.add_argument('-i', '--input', required=True,
                       help='Input JSON file (clustered themes)')
    parser.add_argument('-o', '--output', required=True,
                       help='Output markdown file')
    parser.add_argument('--title',
                       help='Override title in output')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Load JSON
    try:
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return 1

    # Override title if specified
    if args.title:
        data['title'] = args.title

    # Format markdown
    markdown = format_markdown(data)

    # Write output
    Path(args.output).write_text(markdown, encoding='utf-8')

    # Summary
    themes = data.get('themes', [])
    total_papers = data.get('total_papers', 0)
    total_l1 = sum(len(t.get('l1_questions', [])) for t in themes)

    print(f"\n✅ Formatted hierarchical markdown")
    print(f"=" * 60)
    print(f"Output File:    {args.output}")
    print(f"Total Papers:   {total_papers}")
    print(f"Themes:         {len(themes)}")
    print(f"L1 Questions:   {total_l1}")
    print(f"=" * 60)

    return 0


if __name__ == '__main__':
    exit(main())
