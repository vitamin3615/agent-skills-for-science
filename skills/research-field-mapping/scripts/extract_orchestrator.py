#!/usr/bin/env python3
"""
Survey Extraction Orchestrator

Coordinates worker AI extraction of structured survey data from PubMed chunks
for review paper writing. Extracts: topic, focus, findings, details.

Usage:
    # Extract with research question context
    python extract_orchestrator.py extract --chunks-dir Temp/chunks --research-question Temp/research_question.yaml

    # Extract with default worker (gemini)
    python extract_orchestrator.py extract --chunks-dir Temp/chunks --worker gemini

    # Resume interrupted extraction
    python extract_orchestrator.py extract --resume

    # Check status
    python extract_orchestrator.py status

    # Reset state
    python extract_orchestrator.py extract --reset
"""

import argparse
import subprocess
import json
import time
import random
import yaml
import sys
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add agent-orchestrator utils to path for WorkerSpawner
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'agent-orchestrator' / 'scripts'))
from utils.worker_spawner import WorkerSpawner

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds


def clean_jsonl_output(raw_output: str) -> str:
    """Clean AI worker output to ensure valid JSONL format.
    
    AI workers may return:
    - Markdown code fences: ```json ... ```
    - Conversational text mixed with JSONL
    - Empty lines
    - MCP server initialization messages
    - Multiple JSON objects concatenated on a single line
    
    This function:
    1. Removes markdown code fences
    2. Filters out MCP server messages
    3. Handles concatenated JSON objects on the same line
    4. Filters to only dict objects with 'pmid' field
    5. Returns clean JSONL (one JSON object per line)
    """
    import json
    
    # Filter out common MCP initialization noise
    mcp_noise_patterns = [
        'Loaded cached credentials',
        'Server \'',
        'supports tool updates',
        'Listening for changes',
    ]
    
    valid_lines = []
    decoder = json.JSONDecoder()
    
    for line in raw_output.split('\n'):
        line = line.strip()
        
        # Skip MCP initialization messages
        if any(pattern in line for pattern in mcp_noise_patterns):
            continue
        
        # Skip markdown code fence markers
        if line.startswith('```'):
            continue
            
        # Skip empty lines
        if not line:
            continue
        
        # Try to parse as single JSON object first (fast path)
        try:
            data = json.loads(line)
            if isinstance(data, dict) and 'pmid' in data:
                valid_lines.append(json.dumps(data))
            continue
        except json.JSONDecodeError:
            pass
        
        # Handle concatenated JSON objects on the same line
        # e.g., {"pmid":"1"...}{"pmid":"2"...}
        idx = 0
        while idx < len(line):
            # Skip whitespace
            while idx < len(line) and line[idx].isspace():
                idx += 1
            if idx >= len(line):
                break
            
            try:
                obj, end_idx = decoder.raw_decode(line, idx)
                if isinstance(obj, dict) and 'pmid' in obj:
                    valid_lines.append(json.dumps(obj))
                idx += end_idx
            except json.JSONDecodeError:
                # Not valid JSON from this position, skip this line
                break
    
    return '\n'.join(valid_lines)


def load_research_question(filepath: str) -> Dict:
    """Load research question from YAML file."""
    path = Path(filepath)
    if not path.exists():
        print(f"⚠ Research question file not found: {filepath}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"✓ Loaded research question: {config.get('question', 'N/A')[:60]}...")
        return config
    except yaml.YAMLError as e:
        print(f"⚠ Invalid YAML in research question file: {e}")
        return {}


def load_prompt(research_question: Dict = None) -> str:
    """
    Load survey extraction prompt with research question context.
    """
    script_dir = Path(__file__).parent
    prompt_path = script_dir.parent / 'references' / 'survey_prompt.md'

    try:
        template = prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"⚠ Survey prompt not found: {prompt_path}")
        # Fallback embedded prompt
        template = """Extract source-traceable abstract data for a research field map.

## RESEARCH CONTEXT
{{research_question}}

## OUTPUT FORMAT
Use only supplied abstract information. Output raw JSONL:
{{"pmid":"X","relevance":1.0,"inclusion_reason":"Direct evidence","topic":"Topic","focus":"Focus","findings":["Explicit abstract finding"],"source_level":"abstract","confidence":{{"level":"medium","reason":"Abstract-only evidence"}}}}

---
{{chunk_content}}
"""

    # Build research question context
    if research_question:
        parts = [
            f"**Research Question**: {research_question.get('question', 'Not specified')}",
            f"**Focus Entities**: {', '.join(research_question.get('focus_entities', []))}",
            f"**Relevance Threshold**: {research_question.get('relevance_threshold', 0.5)}",
        ]
        if research_question.get('context'):
            parts.append(f"**Context**: {research_question['context']}")

        # Comparisons
        comparisons = research_question.get('comparisons', [])
        if comparisons:
            parts.append("\n### Explicit Comparisons (look for these contrasts)")
            for c in comparisons:
                parts.append(f"- {c}")

        # Evidence types
        evidence_types = research_question.get('evidence_types', [])
        if evidence_types:
            parts.append("\n### Valid Evidence Types")
            for e in evidence_types:
                parts.append(f"- {e}")

        # Modalities
        modalities = research_question.get('modalities', [])
        if modalities:
            parts.append("\n### In-Scope Modalities")
            for m in modalities:
                if isinstance(m, dict):
                    parts.append(f"- **{m.get('name', '')}**: {m.get('look_for', '')}")
                else:
                    parts.append(f"- {m}")

        # Inclusion criteria
        inclusion = research_question.get('inclusion_criteria', [])
        if inclusion:
            parts.append("\n### Inclusion Criteria (paper MUST meet)")
            for i in inclusion:
                parts.append(f"- {i}")

        # Exclusion criteria
        exclusion = research_question.get('exclusion_criteria', [])
        if exclusion:
            parts.append("\n### Exclusion Criteria (REJECT if)")
            for x in exclusion:
                parts.append(f"- {x}")

        rq_text = '\n'.join(parts)
    else:
        rq_text = "No specific research question provided. Extract general survey data."

    return template.replace('{{research_question}}', rq_text)


class SurveyExtractor:
    """Orchestrator for survey extraction from PubMed abstracts."""

    def __init__(
        self,
        worker: str = 'gemini',
        max_chars: int = 50000,
        research_question: Dict = None,
        custom_model: str = None
    ):
        self.worker = worker
        self.max_chars = max_chars
        self.script_dir = Path(__file__).parent
        self.state_file: Optional[Path] = None
        self.research_question = research_question or {}
        self.prompt_template = load_prompt(research_question)
        
        # Initialize WorkerSpawner with rate limit fallback
        self.spawner = WorkerSpawner(worker_type=worker, custom_model=custom_model)
        if custom_model:
            logger.info(f"Initialized {worker} worker with custom model: {custom_model}")
        else:
            logger.info(f"Initialized {worker} worker with fallback support")

    def extract_chunk(self, chunk_file: str, chunk_num: int, total: int) -> str:
        """Extract survey data from a single chunk with retry and rate limit fallback."""
        content = Path(chunk_file).read_text(encoding='utf-8')
        original_len = len(content)

        # Truncate with warning if needed
        if original_len > self.max_chars:
            content = content[:self.max_chars]
            print(f"  ⚠ Content truncated: {original_len:,} → {self.max_chars:,} chars")

        # Build prompt from template
        prompt = self.prompt_template.replace('{{chunk_content}}', content)

        # Determine complexity for model selection
        content_len = len(content)
        has_many_abstracts = content.count('###') > 15
        complexity = 'high' if (content_len > 8000 or has_many_abstracts) else 'medium'

        # Use WorkerSpawner with automatic fallback
        worker_id = f"chunk_{chunk_num:03d}"
        result = self.spawner.spawn(
            prompt=prompt,
            complexity=complexity,
            timeout=180,
            worker_id=worker_id
        )

        if result['success']:
            model_used = result.get('model_used', 'unknown')
            attempts = result.get('attempts', 1)
            if attempts > 1 or model_used != self.spawner._select_model(complexity):
                print(f"  ✓ Success with {model_used} (after {attempts} attempts)")
            return result['output']
        else:
            error_msg = result.get('error', 'Unknown error')
            models_tried = result.get('models_tried', [])
            print(f"  ✗ All models failed: {models_tried}")
            print(f"    Last error: {error_msg}")
            return ""

    def _process_chunk(self, chunk_file: Path, chunk_index: int, total: int, out_path: Path) -> dict:
        """Process a single chunk for parallel execution. Thread-safe."""
        spawner = WorkerSpawner(
            worker_type=self.worker,
            custom_model=self.spawner.custom_model
        )
        try:
            content = chunk_file.read_text(encoding='utf-8')
            if len(content) > self.max_chars:
                content = content[:self.max_chars]

            prompt = self.prompt_template.replace('{{chunk_content}}', content)
            complexity = 'high' if (len(content) > 8000 or content.count('###') > 15) else 'medium'

            worker_id = f"chunk_{chunk_index:03d}"
            result = spawner.spawn(prompt=prompt, complexity=complexity, timeout=180, worker_id=worker_id)

            if not result['success']:
                return {'success': False, 'chunk_name': chunk_file.name, 'chunk_index': chunk_index}

            cleaned = clean_jsonl_output(result['output'])
            if not cleaned:
                return {'success': False, 'chunk_name': chunk_file.name, 'chunk_index': chunk_index}

            out_file = out_path / f"survey_{chunk_index:03d}.jsonl"
            out_file.write_text(cleaned, encoding='utf-8')
            line_count = len([l for l in cleaned.split('\n') if l.strip()])

            return {
                'success': True,
                'chunk_name': chunk_file.name,
                'chunk_index': chunk_index,
                'out_file': str(out_file),
                'out_file_name': out_file.name,
                'line_count': line_count
            }
        finally:
            spawner.cleanup_workspaces()

    def load_state(self, chunks_dir: Path) -> Dict:
        """Load extraction state from JSON file."""
        self.state_file = chunks_dir / '.extraction_state.json'
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                print("⚠ Corrupted state file, starting fresh")
        return {}

    def save_state(self, state: Dict):
        """Save extraction state to JSON file."""
        if self.state_file:
            self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def extract_all(
        self,
        chunks_dir: str,
        output_dir: str = None,
        delay: float = 1.0,
        resume: bool = False,
        reset: bool = False,
        sequential: bool = False,
        max_workers: int = 5
    ) -> List[str]:
        """Extract survey data from all chunks with state persistence."""
        chunks_path = Path(chunks_dir)
        chunk_files = sorted(chunks_path.glob('chunk_*.md'))

        if not chunk_files:
            print(f"No chunk files found in {chunks_dir}")
            return []

        out_path = Path(output_dir) if output_dir else chunks_path / 'extracted'
        out_path.mkdir(parents=True, exist_ok=True)

        # Gemini uses static Docker container names - force sequential
        if self.worker == 'gemini' and not sequential:
            print("⚠ Gemini workers use static Docker container names - forcing sequential mode")
            sequential = True

        # State management
        state = {} if reset else self.load_state(chunks_path)
        completed = set(state.get('completed_chunks', []))

        if reset and self.state_file and self.state_file.exists():
            self.state_file.unlink()
            print("🔄 State reset, starting fresh")

        if resume and completed:
            print(f"📂 Resuming: {len(completed)}/{len(chunk_files)} chunks already done")
        elif completed and not resume:
            print(f"⚠ Found existing state ({len(completed)} chunks done).")
            print("   Use --resume to continue or --reset to start fresh.")
            return []

        # Initialize state
        if not state:
            state = {
                'started': datetime.now().isoformat(),
                'worker': self.worker,
                'completed_chunks': [],
                'output_files': [],
                'research_question': self.research_question.get('question', '')
            }
        else:
            state.setdefault('completed_chunks', [])
            state.setdefault('output_files', [])
            state.setdefault('started', datetime.now().isoformat())
            state.setdefault('worker', self.worker)

        results = list(state.get('output_files', []))
        total = len(chunk_files)
        mode = "sequential" if sequential else f"parallel ({max_workers} workers)"

        print(f"\n🔬 Survey Extraction: {total} chunks using {self.worker} [{mode}]")
        if self.research_question:
            print(f"   Research focus: {self.research_question.get('question', 'N/A')[:60]}...")
        print(f"   Output format: JSONL (topic/focus/findings/details)")
        print()

        is_gemini = self.worker == 'gemini'

        if sequential:
            for i, chunk_file in enumerate(chunk_files, 1):
                chunk_name = chunk_file.name

                if chunk_name in completed:
                    print(f"[{i}/{total}] ✓ {chunk_name} (already done)")
                    continue

                # Clean up Docker containers before each Gemini chunk
                if is_gemini and hasattr(self.spawner, '_cleanup_docker_containers'):
                    self.spawner._cleanup_docker_containers()

                print(f"[{i}/{total}] Processing {chunk_name}...")

                output = self.extract_chunk(str(chunk_file), i, total)

                if output:
                    cleaned_output = clean_jsonl_output(output)
                    if not cleaned_output:
                        print(f"  ⚠ No valid JSONL records found in output")
                        continue

                    out_file = out_path / f"survey_{i:03d}.jsonl"
                    out_file.write_text(cleaned_output, encoding='utf-8')
                    results.append(str(out_file))

                    state['completed_chunks'].append(chunk_name)
                    state['output_files'].append(str(out_file))
                    state['last_updated'] = datetime.now().isoformat()
                    self.save_state(state)

                    line_count = len([l for l in cleaned_output.split('\n') if l.strip()])
                    print(f"  ✓ Saved: {out_file.name} ({line_count} abstracts)")
                else:
                    print(f"  ⚠ Empty result (will retry on next --resume)")

                if i < total:
                    time.sleep(delay)
        else:
            # Parallel execution
            state_lock = threading.Lock()
            pending = []
            for i, chunk_file in enumerate(chunk_files, 1):
                if chunk_file.name in completed:
                    print(f"[{i}/{total}] ✓ {chunk_file.name} (already done)")
                    continue
                pending.append((i, chunk_file))

            print(f"Submitting {len(pending)} chunks to {max_workers} workers...\n")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for idx, (i, chunk_file) in enumerate(pending):
                    if delay > 0 and idx > 0:
                        time.sleep(delay)
                    future = executor.submit(self._process_chunk, chunk_file, i, total, out_path)
                    futures[future] = (i, chunk_file.name)

                done_count = len(completed)
                for future in as_completed(futures):
                    i, chunk_name = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        print(f"[{i}/{total}] {chunk_name} - exception: {e}")
                        continue

                    if result['success']:
                        with state_lock:
                            state['completed_chunks'].append(chunk_name)
                            state['output_files'].append(result['out_file'])
                            state['last_updated'] = datetime.now().isoformat()
                            self.save_state(state)
                            results.append(result['out_file'])
                        done_count += 1
                        print(f"[{i}/{total}] ({done_count}/{total}) ✓ {result['out_file_name']} ({result['line_count']} abstracts)")
                    else:
                        print(f"[{i}/{total}] ⚠ {chunk_name} - empty result (retry on --resume)")

        # Cleanup state on completion
        if len(state['completed_chunks']) == total:
            if self.state_file and self.state_file.exists():
                self.state_file.unlink()
            print(f"\n✅ Extracted all {total} chunks to {out_path}/")
            print(f"\n📊 Next steps:")
            print(f"   1. Combine JSONL: cat {out_path}/survey_*.jsonl > combined.jsonl")
            print(f"   2. Review and group by topic for review paper sections")
        else:
            print(f"\n⚠ Extracted {len(state['completed_chunks'])}/{total} chunks.")
            print(f"   Use --resume to continue.")

        return results

    def status(self, chunks_dir: str):
        """Show extraction status."""
        chunks_path = Path(chunks_dir)
        chunk_files = sorted(chunks_path.glob('chunk_*.md'))
        total = len(chunk_files)

        if total == 0:
            print(f"No chunks found in {chunks_dir}")
            return

        state = self.load_state(chunks_path)
        if not state:
            print(f"No extraction in progress.")
            print(f"Found {total} chunks ready for extraction.")
            return

        completed = len(state.get('completed_chunks', []))
        started = state.get('started', 'unknown')
        worker = state.get('worker', 'unknown')
        question = state.get('research_question', 'N/A')

        print(f"\n📊 Survey Extraction Status")
        print(f"=" * 60)
        print(f"Started:    {started}")
        print(f"Worker:     {worker}")
        print(f"Question:   {question[:50]}...")
        print(f"Progress:   {completed}/{total} chunks ({completed/total*100:.1f}%)")
        print(f"Remaining:  {total - completed} chunks")
        print(f"=" * 60)

        if completed < total:
            print(f"\n🔄 To resume: python scripts/extract_orchestrator.py extract --resume")
        else:
            print(f"\n✅ Extraction complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Extract survey data from PubMed chunks for review paper writing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract with research question context
    python extract_orchestrator.py extract --chunks-dir Temp/chunks \\
        --research-question Temp/research_question.yaml

    # Quick extraction without research question
    python extract_orchestrator.py extract --chunks-dir Temp/chunks --worker gemini

    # Resume interrupted extraction
    python extract_orchestrator.py extract --resume

    # Check status
    python extract_orchestrator.py status --chunks-dir Temp/chunks

    # Reset and start fresh
    python extract_orchestrator.py extract --chunks-dir Temp/chunks --reset

Output Format:
    Each JSONL line contains:
    - pmid: PubMed ID
    - relevance: 0.0-1.0 relevance to research question
    - topic: High-level research area (for grouping)
    - focus: Specific aspect studied
    - findings: List of key results
    - details: Sample size, methods, key entities
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # extract command
    extract_p = subparsers.add_parser('extract', help='Extract survey data from chunks')
    extract_p.add_argument('--chunks-dir', help='Directory with chunk files (default: from state)')
    extract_p.add_argument('--worker', required=True,
                          choices=['gemini', 'claude', 'codex', 'copilot'],
                          help='External worker CLI to use; select deliberately')
    extract_p.add_argument('--custom-model',
                          help='Explicit model override; otherwise use provider configuration')
    extract_p.add_argument('--research-question', '-q',
                          help='Path to research_question.yaml')
    extract_p.add_argument('--output-dir', help='Output directory (default: chunks_dir/extracted)')
    extract_p.add_argument('--delay', type=float, default=1.0,
                          help='Delay between chunks in seconds (default: 1.0)')
    extract_p.add_argument('--max-chars', type=int, default=50000,
                          help='Max characters per chunk (default: 50000)')
    extract_p.add_argument('--resume', action='store_true',
                          help='Resume interrupted extraction')
    extract_p.add_argument('--reset', action='store_true',
                          help='Clear state and start fresh')
    extract_p.add_argument('--sequential', action='store_true',
                          help='Disable concurrent chunk execution')
    extract_p.add_argument('--workers', type=int, default=1,
                          help='Maximum concurrent external workers (default: 1)')

    # status command
    status_p = subparsers.add_parser('status', help='Check extraction status')
    status_p.add_argument('--chunks-dir', help='Directory with chunk files')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Auto-detect chunks-dir from state if resuming
    if args.command == 'extract' and args.resume and not args.chunks_dir:
        for state_file in Path('.').rglob('.extraction_state.json'):
            args.chunks_dir = str(state_file.parent)
            print(f"📂 Auto-detected chunks directory: {args.chunks_dir}")
            break

    if not args.chunks_dir:
        print("Error: --chunks-dir is required (or use --resume with existing state)")
        return 1

    if not Path(args.chunks_dir).exists():
        print(f"Error: Directory not found: {args.chunks_dir}")
        return 1

    # Load research question if provided
    research_question = {}
    if args.command == 'extract' and hasattr(args, 'research_question') and args.research_question:
        research_question = load_research_question(args.research_question)

    if args.command == 'extract':
        extractor = SurveyExtractor(
            worker=args.worker,
            max_chars=args.max_chars,
            research_question=research_question,
            custom_model=getattr(args, 'custom_model', None)
        )
        extractor.extract_all(
            args.chunks_dir,
            getattr(args, 'output_dir', None),
            args.delay,
            resume=args.resume,
            reset=args.reset,
            sequential=args.sequential,
            max_workers=args.workers
        )

    elif args.command == 'status':
        extractor = SurveyExtractor()
        extractor.status(args.chunks_dir)

    return 0


if __name__ == '__main__':
    exit(main())
