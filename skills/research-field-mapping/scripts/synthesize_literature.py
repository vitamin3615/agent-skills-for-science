#!/usr/bin/env python3
"""
Literature Synthesis Orchestrator

Transforms extracted JSONL survey data into expert-level review manuscript organization.
Implements 4-pass architecture with validation.

Usage:
    python synthesize_literature.py \\
        --input combined.jsonl \\
        --research-question Temp/research_question.yaml \\
        --output literature_review.md \\
        --worker gemini
"""

import json
import re
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict
from datetime import datetime
import logging

try:
    from .utils.worker_spawner import WorkerSpawner
except ImportError:
    from utils.worker_spawner import WorkerSpawner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiteratureSynthesizer:
    """Orchestrates intelligent literature aggregation into review structure"""
    
    def __init__(
        self,
        jsonl_path: str,
        research_question: str,
        worker: str,
        model: Optional[str] = None,
    ):
        """
        Initialize synthesizer
        
        Args:
            jsonl_path: Path to combined JSONL file with extracted papers
            research_question: Main research question for the review
            worker: External AI worker CLI to use
            model: Optional explicit model; otherwise use provider configuration
        """
        self.jsonl_path = Path(jsonl_path)
        self.research_question = research_question
        self.worker = worker
        self.worker_spawner = WorkerSpawner(worker_type=worker, custom_model=model)
        self.papers = self.load_and_dedupe(jsonl_path)
        self.pmid_registry = set(p["pmid"] for p in self.papers)
        self.metrics = {
            "preprocessing_time": 0,
            "pass1_time": 0,
            "pass2_time": 0,
            "pass2_5_time": 0,
            "pass3_time": 0,
            "pass4_time": 0,
            "total_ai_calls": 0
        }
        
        logger.info(f"Initialized with {len(self.papers)} papers ({len(self.pmid_registry)} unique PMIDs)")
    
    def load_and_dedupe(self, jsonl_path: str) -> List[Dict]:
        """Load JSONL and deduplicate by PMID"""
        papers = []
        seen_pmids = set()
        
        with open(jsonl_path, 'r') as f:
            for line in f:
                if line.strip():
                    paper = json.loads(line)
                    pmid = paper.get("pmid")
                    if pmid and pmid not in seen_pmids:
                        papers.append(paper)
                        seen_pmids.add(pmid)
                    elif pmid in seen_pmids:
                        logger.warning(f"Duplicate PMID {pmid} skipped")
        
        return papers
    
    def run_pipeline(self) -> str:
        """
        Execute the full 4-pass synthesis pipeline
        
        Returns:
            Markdown review document
        """
        import time
        
        logger.info("=== STARTING LITERATURE SYNTHESIS PIPELINE ===")
        
        # PREPROCESSING: Extract finding categories (rule-based, no AI)
        logger.info("PREPROCESSING: Extracting finding categories")
        start = time.time()
        self.preprocess_finding_categories()
        self.metrics["preprocessing_time"] = time.time() - start
        logger.info(f"Preprocessing complete in {self.metrics['preprocessing_time']:.2f}s")
        
        # Pass 1: Extract scopes + finding categories
        logger.info("PASS 1: Extracting scopes and categories")
        start = time.time()
        scopes = self.pass1_extract_scopes_and_categories()
        self.metrics["pass1_time"] = time.time() - start
        logger.info(f"Pass 1 complete in {self.metrics['pass1_time']:.2f}s - {len(scopes['scopes'])} scopes identified")
        
        # Pass 2: Build taxonomy from scopes (IMPLEMENTS Stage 0 axis selection)
        logger.info("PASS 2: Building taxonomy with axis selection")
        start = time.time()
        taxonomy = self.pass2_build_taxonomy(scopes)
        self.metrics["pass2_time"] = time.time() - start
        logger.info(f"Pass 2 complete in {self.metrics['pass2_time']:.2f}s - Axis: {taxonomy['primary_axis']}")
        
        # Pass 2.5: Validate taxonomy can accommodate findings
        logger.info("PASS 2.5: Validating taxonomy coverage")
        start = time.time()
        taxonomy = self.pass2_5_validate_taxonomy(taxonomy, scopes)
        self.metrics["pass2_5_time"] = time.time() - start
        logger.info(f"Pass 2.5 complete in {self.metrics['pass2_5_time']:.2f}s - Status: {taxonomy.get('validation_status', 'N/A')}")
        
        # Pass 3: Map findings (CHUNKED by section)
        logger.info("PASS 3: Mapping findings (chunked by section)")
        start = time.time()
        organized_sections = []
        for i, section in enumerate(taxonomy["sections"], 1):
            logger.info(f"  Processing section {i}/{len(taxonomy['sections'])}: {section['question'][:60]}...")
            section_output = self.pass3_map_section_findings(section, taxonomy)
            organized_sections.append(section_output)
        
        # Merge section outputs
        organized = self.merge_sections(organized_sections, taxonomy)
        self.metrics["pass3_time"] = time.time() - start
        logger.info(f"Pass 3 complete in {self.metrics['pass3_time']:.2f}s")
        
        # Pass 3.5: Add catchall section for unmapped high-relevance papers
        logger.info("PASS 3.5: Creating catchall section for unmapped papers")
        start = time.time()
        organized = self.pass3_5_add_catchall(organized, taxonomy)
        self.metrics["pass3_5_time"] = time.time() - start
        logger.info(f"Pass 3.5 complete in {self.metrics['pass3_5_time']:.2f}s")
        
        # Pass 4: Validate & generate report
        logger.info("PASS 4: Validating and generating report")
        start = time.time()
        report = self.pass4_validate_and_generate(organized, taxonomy)
        self.metrics["pass4_time"] = time.time() - start
        logger.info(f"Pass 4 complete in {self.metrics['pass4_time']:.2f}s")
        
        # Log metrics
        total_time = sum(self.metrics[k] for k in self.metrics if k.endswith('_time'))
        logger.info(f"\n=== PIPELINE COMPLETE ===")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Total AI calls: {self.metrics['total_ai_calls']}")
        
        return report
    
    # ==================== PREPROCESSING ====================
    
    def preprocess_finding_categories(self):
        """
        Extract one-line categories from full findings (RULE-BASED).
        Augments each paper with 'finding_categories' field.
        """
        for paper in self.papers:
            categories = []
            for finding in paper.get("findings", []):
                category = self.extract_category_from_finding(finding)
                categories.append(category)
            paper["finding_categories"] = categories
    
    def extract_category_from_finding(self, finding_text: str) -> str:
        """
        Rule-based category extraction (no AI call).
        Template: "[entity] [direction] in [context]"
        """
        # Extract first sentence
        first_sent = finding_text.split('.')[0] if '.' in finding_text else finding_text
        
        # Detect direction
        direction = "modification of"
        if any(word in finding_text.lower() for word in ['increase', 'enhance', 'upregulate', 'elevate', 'higher', 'elevated']):
            direction = "upregulation of"
        elif any(word in finding_text.lower() for word in ['decrease', 'reduce', 'downregulate', 'diminish', 'lower', 'reduced']):
            direction = "downregulation of"
        elif any(word in finding_text.lower() for word in ['accumulate', 'deposit', 'accumulation']):
            direction = "accumulation of"
        elif any(word in finding_text.lower() for word in ['impair', 'disrupt', 'dysfunction']):
            direction = "dysfunction of"
        
        # Extract entities (capitalized words, gene names)
        entities = re.findall(r'\b[A-Z][A-Z0-9]+\b', first_sent)  # APOE4, IL6
        if not entities:
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', first_sent)  # Multi-word
        
        # Extract cell type context
        cell_types = ['microglia', 'astrocyte', 'neuron', 'oligodendrocyte', 'endothelial', 'pericyte']
        context = next((ct for ct in cell_types if ct in finding_text.lower()), "cells")
        
        # Generate category
        entity = entities[0] if entities else "protein"
        return f"{entity} {direction} {context}"
    
    # ==================== PASS 1 ====================
    
    def pass1_extract_scopes_and_categories(self) -> Dict:
        """
        Extract scopes and finding categories from papers
        
        Returns:
            Dict with scopes and categories
        """
        # Prepare input for AI
        papers_summary = []
        for paper in self.papers:
            papers_summary.append({
                "pmid": paper["pmid"],
                "topic": paper.get("topic", ""),
                "focus": paper.get("focus", ""),
                "finding_categories": paper.get("finding_categories", [])
            })
        
        prompt = self._build_pass1_prompt(papers_summary)
        response = self.call_ai(prompt, "Pass 1")
        
        return self.parse_json_response(response)
    
    def _build_pass1_prompt(self, papers_summary: List[Dict]) -> str:
        """Build Pass 1 prompt"""
        papers_json = json.dumps(papers_summary, indent=2)
        
        return f"""## Pass 1 Prompt: Scope & Category Extraction

Given these {len(papers_summary)} papers with their topics and finding previews:

{papers_json}

**Finding categories** = one-line summaries of what each finding addresses (already extracted)

Your task is to:
1. **Extract unique scopes** from topics (high-level research areas)
2. **For each scope, identify finding sub-categories** from the categories
   - e.g., Scope="Microglia" → categories=["lipid droplets", "phagocytosis", "inflammatory states"]
3. **Group papers under scopes + categories**

Output **ONLY** valid JSON in this exact format:
{{
  "scopes": [
    {{
      "scope_id": "S1", 
      "name": "Microglial Dysfunction",
      "categories": [
        {{"cat_id": "S1.1", "name": "Lipid Droplet Accumulation", "pmids": ["12345", "67890"]}},
        {{"cat_id": "S1.2", "name": "Phagocytic Clearance Defects", "pmids": ["11111"]}}
      ]
    }},
    ...
  ],
  "clustering_rationale": "Rationale for grouping..."
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
    
    # ==================== PASS 2 ====================
    
    def pass2_build_taxonomy(self, scopes: Dict) -> Dict:
        """
        Build taxonomy with axis selection from scopes
        
        Args:
            scopes: Output from Pass 1
            
        Returns:
            Taxonomy with sections and subsections
        """
        prompt = self._build_pass2_prompt(scopes)
        response = self.call_ai(prompt, "Pass 2")
        
        return self.parse_json_response(response)
    
    def _build_pass2_prompt(self, scopes: Dict) -> str:
        """Build Pass 2 prompt"""
        scopes_json = json.dumps(scopes, indent=2)
        
        return f"""## Pass 2 Prompt: Corpus-Grounded Structure

You have identified these scopes from the literature:
{scopes_json}

Research Question: "{self.research_question}"

Choose the simplest organizational axis, or hybrid, that represents the observed
corpus and answers the research question. Let the evidence determine the number,
form, and order of sections. Do not force a fixed section count, interrogative
headings, or a foundational-to-therapeutic narrative. Allow secondary assignments
when a scope materially informs more than one section.

Output **ONLY** valid JSON in this exact format:
{{
  "reasoning_trace": "Concise organization rationale",
  "primary_axis": "By Process",
  "secondary_axis": "By Cell Type",
  "sections": [
    {{
      "section_id": 1,
      "question": "How does lipid metabolism become dysregulated?",
      "subsections": [
        {{"question": "What cellular mechanisms drive lipid accumulation?", "scope_ids": ["S1", "S3"]}},
        {{"question": "How do different cell types respond?", "scope_ids": ["S2"]}}
      ]
    }}
  ],
  "scope_to_section_map": {{"S1": 1, "S2": 1, "S3": 2}}
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
    
    # ==================== PASS 2.5 ====================
    
    def pass2_5_validate_taxonomy(self, taxonomy: Dict, scopes: Dict) -> Dict:
        """
        Validate taxonomy can accommodate all findings
        
        Args:
            taxonomy: Output from Pass 2
            scopes: Output from Pass 1
            
        Returns:
            Validated (possibly revised) taxonomy
        """
        # Extract all finding categories from scopes
        all_categories = []
        for scope in scopes["scopes"]:
            for cat in scope.get("categories", []):
                all_categories.append(cat["name"])
        
        prompt = self._build_pass2_5_prompt(taxonomy, all_categories)
        response = self.call_ai(prompt, "Pass 2.5")
        result = self.parse_json_response(response)
        
        # If revised, use revised taxonomy
        if result.get("validation_status") == "REVISED":
            logger.warning(f"Taxonomy revised: {result.get('coverage_pct', 0)*100:.0f}% coverage")
            return result.get("revised_taxonomy", taxonomy)
        
        return taxonomy
    
    def _build_pass2_5_prompt(self, taxonomy: Dict, all_categories: List[str]) -> str:
        """Build Pass 2.5 prompt"""
        taxonomy_json = json.dumps(taxonomy, indent=2)
        categories_json = json.dumps(all_categories, indent=2)
        
        return f"""## Pass 2.5 Prompt: Taxonomy Coverage Check

You have created this taxonomy:
{taxonomy_json}

Here is a QUICK SCAN of all finding categories:
{categories_json}

### Your task:

1. **Coverage check**: For each finding category, identify which subsection it maps to
   - If no clear destination → flag as "UNMAPPED"

2. **Threshold check**: 
   - If <10% unmapped → APPROVE taxonomy
   - If ≥10% unmapped → REVISE taxonomy (add missing subsections)

3. **Revise if needed**:
   - Add subsections for unmapped categories
   - OR merge categories that are too granular
   - Maintain consistency with primary/secondary axis

Output **ONLY** valid JSON in this exact format:
{{
  "validation_status": "APPROVED",
  "coverage_pct": 0.95,
  "unmapped_categories": [],
  "revised_taxonomy": null
}}

OR if revising:
{{
  "validation_status": "REVISED",
  "coverage_pct": 0.85,
  "unmapped_categories": ["category1", "category2"],
  "revised_taxonomy": {{...complete revised taxonomy...}}
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
    
    # ==================== PASS 3 ====================
    
    def pass3_map_section_findings(self, section: Dict, taxonomy: Dict) -> Dict:
        """
        Map findings to subsections within one section
        
        Args:
            section: One section from taxonomy
            taxonomy: Full taxonomy for context
            
        Returns:
            Organized findings for this section
        """
        # Collect findings for this section
        section_findings = self._collect_section_findings(section, taxonomy)
        
        prompt = self._build_pass3_prompt(section, section_findings)
        response = self.call_ai(prompt, "Pass 3")
        
        return self.parse_json_response(response)
    
    def _collect_section_findings(self, section: Dict, taxonomy: Dict) -> List[Dict]:
        """Collect all findings assigned to this section, prioritizing by relevance"""
        section_id = section["section_id"]
        scope_ids = set()
        
        # Collect all scope IDs for this section
        for subsection in section["subsections"]:
            scope_ids.update(subsection.get("scope_ids", []))
        
        # Find papers and prioritize by relevance
        findings = []
        for paper in self.papers:
            # Filter: only include papers with findings and relevance >= 0.5
            if not paper.get("findings") or paper.get("relevance", 0) < 0.5:
                continue
                
            for finding_idx, finding in enumerate(paper.get("findings", [])):
                findings.append({
                    "text": finding,
                    "pmid": paper["pmid"],
                    "relevance": paper.get("relevance", 0),
                    "category": paper.get("finding_categories", [])[finding_idx] if finding_idx < len(paper.get("finding_categories", [])) else ""
                })
        
        # Sort by relevance (highest first) to prioritize in truncation
        findings.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return findings
    
    def _build_pass3_prompt(self, section: Dict, findings: List[Dict]) -> str:
        """Build Pass 3 prompt"""
        section_id = section["section_id"]
        section_question = section["question"]
        subsections = section["subsections"]
        
        # Since we've filtered by relevance >= 0.5, we can use more findings
        # Use up to 400 findings (already sorted by relevance, so highest priority first)
        max_findings = min(400, len(findings))
        findings_json = json.dumps(findings[:max_findings], indent=2)
        subsections_json = json.dumps(subsections, indent=2)
        
        if len(findings) > max_findings:
            logger.info(f"    Truncated to {max_findings}/{len(findings)} findings (relevance-sorted)")
        
        return f"""## Pass 3 Prompt: Section Finding Mapping

You are organizing findings for SECTION {section_id}: "{section_question}"

Subsections in this section:
{subsections_json}

Here are findings assigned to this section:
{findings_json}

### Your task:

1. **Map each finding** to the appropriate subsection
   - A finding may map to multiple subsections within THIS section
   - Flag findings that don't fit any subsection

2. **Consolidate redundant findings** (same observation):
   - Merge: "APOE4 disrupts lipid metabolism (PMID:123, mouse; PMID:456, human)"
   - Rules: Same = same cell type + molecule + direction
   - Contradict: "However, X found opposite (PMID:789)"

3. **Order within subsection**:
   - Phenomenon/observation first
   - Mechanism second
   - Context (cell type, model, sex) third

Output **ONLY** valid JSON in this exact format:
{{
  "section_id": {section_id},
  "subsections": [
    {{
      "subsection_id": "1.1",
      "findings": [
        {{
          "text": "Finding text here",
          "pmids": ["123", "456"],
          "evidence_type": "iPSC_derived",
          "context": "despite elevated cholesterol"
        }}
      ]
    }}
  ],
  "unmapped_findings": [],
  "pmids_in_section": ["123", "456"]
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
    
    # ==================== PASS 3.5 ====================
    
    def pass3_5_add_catchall(self, organized: Dict, taxonomy: Dict) -> Dict:
        """
        Add catchall section for unmapped high-relevance papers
        """
        # Get all mapped PMIDs
        mapped_pmids = set()
        for section in organized.get("sections", []):
            for subsection in section.get("subsections", []):
                for finding in subsection.get("findings", []):
                    mapped_pmids.update(finding.get("pmids", []))
        
        # Find unmapped papers with relevance >= 0.5 (matching our filter threshold)
        unmapped_relevant = []
        for paper in self.papers:
            if paper["pmid"] not in mapped_pmids and paper.get("relevance", 0) >= 0.5:
                if paper.get("findings"):
                    unmapped_relevant.append(paper)
        
        if not unmapped_relevant:
            logger.info("  No relevant unmapped papers to add")
            return organized
        
        logger.info(f"  Adding {len(unmapped_relevant)} relevant unmapped papers to catchall section")
        
        # Sort by relevance (highest first) and group by topic
        unmapped_relevant.sort(key=lambda p: p.get("relevance", 0), reverse=True)
        
        topic_groups = {}
        for paper in unmapped_relevant:
            topic = paper.get("topic", "Other")
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(paper)
        
        # Create catchall section
        catchall_section = {
            "section_id": len(organized["sections"]) + 1,
            "subsections": []
        }
        
        # Create subsections by topic
        for subsection_idx, (topic, papers) in enumerate(sorted(topic_groups.items()), 1):
            subsection = {
                "subsection_id": f"{catchall_section['section_id']}.{subsection_idx}",
                "question": f"Additional findings: {topic}",
                "findings": []
            }
            
            for paper in papers:
                for finding in paper.get("findings", []):
                    subsection["findings"].append({
                        "text": finding,
                        "pmids": [paper["pmid"]],
                        "relevance": paper.get("relevance", 0)
                    })
            
            catchall_section["subsections"].append(subsection)
        
        # Add to organized structure
        organized["sections"].append(catchall_section)
        
        # Update taxonomy to include catchall section
        organized["taxonomy"]["sections"].append({
            "section_id": catchall_section["section_id"],
            "question": "Other Relevant Findings (Unmapped High-Relevance Papers)",
            "subsections": [
                {"question": ss["question"]} for ss in catchall_section["subsections"]
            ]
        })
        
        return organized
    
    # ==================== HELPER METHODS ====================
    
    def merge_sections(self, organized_sections: List[Dict], taxonomy: Dict) -> Dict:
        """Merge all section outputs into one structure"""
        return {
            "taxonomy": taxonomy,
            "sections": organized_sections
        }
    
    def call_ai(self, prompt: str, pass_name: str, max_retries: int = 3) -> str:
        """Call the explicitly selected external worker."""
        self.metrics["total_ai_calls"] += 1
        result = self.worker_spawner.spawn(
            prompt=prompt,
            complexity='high',
            timeout=300,
        )
        if result.get('success') and result.get('output'):
            return result['output']
        logger.error(f"{pass_name}: AI call failed - {result.get('error', 'unknown error')}")
        return "{\"error\": \"AI call failed\"}"
    
    def parse_json_response(self, response_text: str) -> Dict:
        """
        Extract JSON from AI response (handles markdown wrapping)
        
        Args:
            response_text: Raw AI response
            
        Returns:
            Parsed JSON dict
        """
        # Try direct parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Extract from code block
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from code block: {e}")
                raise
        
        # Last resort: find first { to last }
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response_text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract valid JSON from response: {response_text[:200]}...")
    
    # ==================== PASS 4 ====================
    
    def pass4_validate_and_generate(self, organized: Dict, taxonomy: Dict) -> str:
        """
        Validate completeness and generate markdown report
        
        Args:
            organized: Organized findings from Pass 3
            taxonomy: Taxonomy structure
            
        Returns:
            Markdown report
        """
        # 1. PMID Completeness Check
        covered_pmids = self._extract_covered_pmids(organized)
        missing = self.pmid_registry - covered_pmids
        
        if missing:
            coverage = len(covered_pmids) / len(self.pmid_registry) * 100
            logger.warning(f"⚠ MISSING {len(missing)} PMIDs ({coverage:.1f}% coverage)")
            # Note: Low coverage may indicate mapping issues, but we'll proceed to generate report
        
        logger.info(f"✓ PMID completeness: {len(covered_pmids)}/{len(self.pmid_registry)}")
        
        # 2. Placement Sanity Check
        misplaced = self.check_placement_quality(organized)
        if misplaced:
            logger.warning(f"⚠ {len(misplaced)} potentially misplaced findings")
        
        # 3. Cross-Section Deduplication Check
        duplicates = self.deduplicate_cross_section(organized)
        if duplicates:
            logger.warning(f"⚠ {len(duplicates)} findings appear in multiple sections")
        
        # 4. Generate markdown report
        report = self.render_markdown(organized, taxonomy)
        
        # 5. Append appendices
        report += self.generate_appendix_a(covered_pmids)
        report += self.generate_appendix_c(misplaced)
        report += self.generate_appendix_d(duplicates)
        
        return report
    
    def _extract_covered_pmids(self, organized: Dict) -> Set[str]:
        """Extract all PMIDs from organized findings"""
        covered = set()
        for section in organized.get("sections", []):
            for subsection in section.get("subsections", []):
                for finding in subsection.get("findings", []):
                    covered.update(finding.get("pmids", []))
        return covered
    
    def check_placement_quality(self, organized: Dict) -> List[Dict]:
        """Check if findings match their section topics"""
        misplaced = []
        for section in organized.get("sections", []):
            section_id = section.get("section_id")
            # Get section question from taxonomy
            section_keywords = set()  # Simplified for now
            
            for subsection in section.get("subsections", []):
                for finding in subsection.get("findings", []):
                    finding_keywords = self.extract_keywords(finding.get("text", ""))
                    overlap = len(section_keywords & finding_keywords)
                    if overlap < 2 and section_keywords:  # Weak match
                        misplaced.append({
                            "finding": finding.get("text", "")[:100],
                            "section": section_id,
                            "pmids": finding.get("pmids", [])
                        })
        
        return misplaced
    
    def extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords for semantic matching"""
        # Extract capitalized entities (APOE4, IL-6, etc.)
        entities = set(re.findall(r'\b[A-Z][A-Z0-9-]+\b', text))
        
        # Extract multi-word terms
        bio_terms = set(re.findall(
            r'\b(?:lipid|protein|immune|inflammatory|synaptic|mitochondrial|lysosomal)\s+\w+\b', 
            text.lower()
        ))
        
        # Extract cell types
        cell_types = set(re.findall(
            r'\b(?:microglia|astrocyte|neuron|oligodendrocyte)s?\b', 
            text.lower()
        ))
        
        # Combine all
        keywords = entities | bio_terms | cell_types
        
        # Remove stopwords
        stopwords = {'How', 'Does', 'What', 'Why', 'The', 'This', 'These', 'That'}
        keywords = {k for k in keywords if k not in stopwords}
        
        return keywords
    
    def deduplicate_cross_section(self, organized: Dict) -> Dict[str, List[Dict]]:
        """Find findings appearing in multiple sections"""
        finding_map = defaultdict(list)
        
        for section in organized.get("sections", []):
            section_id = section.get("section_id")
            for subsection in section.get("subsections", []):
                subsection_id = subsection.get("subsection_id", "?")
                for finding in subsection.get("findings", []):
                    # Normalize text for comparison
                    key = finding.get("text", "").lower().strip()[:100]
                    finding_map[key].append({
                        "section": section_id,
                        "subsection": subsection_id,
                        "full_text": finding.get("text", ""),
                        "pmids": finding.get("pmids", [])
                    })
        
        # Return only duplicates
        duplicates = {k: v for k, v in finding_map.items() if len(v) > 1}
        return duplicates
    
    def render_markdown(self, organized: Dict, taxonomy: Dict) -> str:
        """Generate markdown report"""
        md = []
        
        # Header
        md.append(f"# Literature Review: {self.research_question}")
        md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d')} | {len(self.papers)} papers*\n")
        
        # Central Thesis (TODO: extract from taxonomy)
        md.append("## Central Thesis\n")
        md.append("[To be synthesized from findings]\n")
        
        # Build taxonomy lookup for questions
        taxonomy_sections = {s['section_id']: s for s in taxonomy.get('sections', [])}
        
        # Sections
        for section in organized.get("sections", []):
            section_id = section.get("section_id")
            # Get question from taxonomy
            tax_section = taxonomy_sections.get(section_id, {})
            section_q = tax_section.get('question', f"Section {section_id}")
            md.append(f"## {section_id}. {section_q}\n")
            
            # Build subsection lookup by subsection_id from taxonomy
            tax_subsections = tax_section.get('subsections', [])
            subsection_questions = {}
            for idx, ss in enumerate(tax_subsections):
                # Try to match by index since subsection_id format is like "1.1", "1.2"
                subsection_questions[idx] = ss.get('question', '[Question]')
            
            for subsection in section.get("subsections", []):
                subsection_id = subsection.get("subsection_id", "?")
                # Try to get question from subsection data or taxonomy
                subsection_q = subsection.get("question")
                
                # If not in data, try to match from taxonomy by subsection index
                if not subsection_q or subsection_q == "[Question]":
                    # Extract subsection index from ID like "1.1" -> 0, "1.2" -> 1
                    try:
                        if '.' in str(subsection_id):
                            idx = int(str(subsection_id).split('.')[-1]) - 1
                            subsection_q = subsection_questions.get(idx, '[Question]')
                        else:
                            subsection_q = '[Question]'
                    except:
                        subsection_q = '[Question]'
                
                md.append(f"### {subsection_id} {subsection_q}\n")
                
                md.append("**Evidence:**\n")
                for finding in subsection.get("findings", []):
                    pmids = ", ".join(f"PMID:{p}" for p in finding.get("pmids", []))
                    md.append(f"- {finding.get('text', '')} ({pmids})\n")
                
                md.append("")
        
        return "\n".join(md)
    
    def generate_appendix_a(self, covered_pmids: Set[str]) -> str:
        """Generate paper index appendix"""
        md = ["\n---\n", "## Appendix A: Complete Paper Index\n"]
        
        missing_pmids = self.pmid_registry - covered_pmids
        coverage = len(covered_pmids) / len(self.pmid_registry) * 100 if self.pmid_registry else 0
        
        md.append(f"**Coverage Summary**: {len(covered_pmids)}/{len(self.pmid_registry)} PMIDs ({coverage:.1f}%)\n")
        
        if missing_pmids:
            md.append(f"\n### Missing Papers ({len(missing_pmids)} papers)\n")
            md.append("The following papers were not mapped to the taxonomy (likely due to low relevance or niche findings):\n")
            md.append("| PMID | Topic | Relevance |")
            md.append("|------|-------|-----------|")
            for pmid in sorted(missing_pmids)[:50]:  # Show first 50
                paper = next((p for p in self.papers if p["pmid"] == pmid), None)
                topic = paper.get("topic", "")[:50] if paper else ""
                relevance = paper.get("relevance", 0) if paper else 0
                md.append(f"| {pmid} | {topic} | {relevance:.2f} |")
            if len(missing_pmids) > 50:
                md.append(f"\n*...and {len(missing_pmids) - 50} more*\n")
        
        md.append(f"\n### Included Papers ({len(covered_pmids)} papers)\n")
        md.append("| PMID | Topic | Status |")
        md.append("|------|-------|--------|")
        
        for pmid in sorted(covered_pmids):
            paper = next((p for p in self.papers if p["pmid"] == pmid), None)
            topic = paper.get("topic", "")[:50] if paper else ""
            md.append(f"| {pmid} | {topic} | ✓ |")
        
        return "\n".join(md)
    
    def generate_appendix_c(self, misplaced: List[Dict]) -> str:
        """Generate placement warnings appendix"""
        if not misplaced:
            return ""
        
        md = ["\n## Appendix C: Placement Quality Check\n"]
        md.append(f"⚠️ Flagged {len(misplaced)} findings (weak keyword match with section):\n")
        
        for item in misplaced[:10]:  # Limit to 10
            md.append(f"- Finding: \"{item['finding']}...\" (PMIDs: {', '.join(item['pmids'])}) in Section {item['section']}")
        
        return "\n".join(md)
    
    def generate_appendix_d(self, duplicates: Dict[str, List[Dict]]) -> str:
        """Generate cross-section duplicates appendix"""
        if not duplicates:
            return ""
        
        md = ["\n## Appendix D: Findings Appearing in Multiple Sections\n"]
        md.append(f"The following {len(duplicates)} findings appear in 2+ sections (may indicate bridging concepts):\n")
        
        for key, instances in list(duplicates.items())[:10]:  # Limit to 10
            md.append(f"\n- Finding: \"{instances[0]['full_text'][:80]}...\"")
            for inst in instances:
                md.append(f"  - Section {inst['section']} / Subsection {inst['subsection']}")
        
        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Synthesize literature into review structure")
    parser.add_argument("--input", required=True, help="Path to combined JSONL file")
    parser.add_argument("--research-question", required=True, help="Main research question")
    parser.add_argument("--output", required=True, help="Output markdown file path")
    parser.add_argument("--worker", required=True, choices=["gemini", "claude", "codex", "copilot"], help="External worker CLI to use; select deliberately")
    parser.add_argument("--model", help="Explicit model override; otherwise use the provider CLI default")
    
    args = parser.parse_args()
    
    # Load research question if it's a YAML file
    if args.research_question.endswith(('.yaml', '.yml')):
        with open(args.research_question) as f:
            rq_data = yaml.safe_load(f)
            research_question = rq_data.get("question", "Unknown")
    else:
        research_question = args.research_question
    
    # Run synthesis
    synthesizer = LiteratureSynthesizer(
        jsonl_path=args.input,
        research_question=research_question,
        worker=args.worker,
        model=args.model,
    )
    
    report = synthesizer.run_pipeline()
    
    # Write output
    output_path = Path(args.output)
    output_path.write_text(report)
    
    logger.info(f"✓ Report written to {output_path}")
    logger.info(f"✓ Synthesis complete!")


if __name__ == "__main__":
    main()
