#!/usr/bin/env python3
"""
Model Availability Checker

Diagnoses which AI providers and models are available and working.
Useful for troubleshooting when orchestrator tasks fail.

Usage:
    python check_model_availability.py              # Use cache if fresh
    python check_model_availability.py --force      # Force recheck
    python check_model_availability.py --json       # JSON output only
"""

import sys
import json
import os
import subprocess
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from utils.worker_spawner import WorkerSpawner


class ModelAvailabilityChecker:
    """Check availability of AI models across providers."""
    
    # Test the configured override, or let the installed CLI choose its default.
    # This avoids embedding model versions that become stale.
    TEST_MODELS = {
        'gemini': [os.environ.get('FIELD_MAPPING_GEMINI_MODEL', 'provider-default')],
        'claude': [os.environ.get('FIELD_MAPPING_CLAUDE_MODEL', 'provider-default')],
        'codex': [os.environ.get('FIELD_MAPPING_CODEX_MODEL', 'provider-default')],
        'copilot': [os.environ.get('FIELD_MAPPING_COPILOT_MODEL', 'provider-default')],
        'gpt': [os.environ.get('FIELD_MAPPING_GPT_MODEL', 'provider-default')],
    }
    
    CLI_COMMANDS = {
        'gemini': 'gemini',
        'claude': 'claude',
        'codex': 'codex',
        'copilot': 'copilot',
        'gpt': 'copilot'
    }
    
    def __init__(self, cache_duration: int = 3600):
        """
        Initialize checker.
        
        Args:
            cache_duration: Cache validity in seconds (default 1 hour)
        """
        self.cache_duration = cache_duration
        cache_root = Path(
            os.environ.get(
                'FIELD_MAPPING_CACHE_DIR',
                Path(tempfile.gettempdir()) / 'research-field-mapping'
            )
        )
        self.cache_file = cache_root / "model_availability_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.results = {}
    
    def _check_cli_available(self, cli_name: str) -> Dict[str, Any]:
        """
        Check if CLI tool is installed and accessible.
        
        Args:
            cli_name: Name of CLI command
            
        Returns:
            Dict with status and version info
        """
        try:
            # Try to get version
            result = subprocess.run(
                [cli_name, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                return {
                    'available': True,
                    'version': version[:100] if version else 'unknown',
                    'error': None
                }
            else:
                return {
                    'available': False,
                    'version': None,
                    'error': f'Exit code {result.returncode}'
                }
                
        except FileNotFoundError:
            return {
                'available': False,
                'version': None,
                'error': 'CLI not installed'
            }
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'version': None,
                'error': 'CLI timeout'
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'error': str(e)
            }
    
    def _test_model(self, worker_type: str, model: str) -> Dict[str, Any]:
        """
        Test if specific model works.
        
        Args:
            worker_type: Worker type (gemini, claude, etc.)
            model: Model identifier
            
        Returns:
            Dict with availability status and metrics
        """
        try:
            configured_model = None if model == 'provider-default' else model
            spawner = WorkerSpawner(worker_type=worker_type, custom_model=configured_model)
            
            start_time = time.time()
            result = spawner.spawn(
                prompt='OK',
                complexity='low',
                timeout=15  # Reduced timeout for faster testing
            )
            latency = time.time() - start_time
            
            if result['success']:
                return {
                    'available': True,
                    'latency_ms': int(latency * 1000),
                    'error': None,
                    'response_sample': result['output'][:50]
                }
            else:
                return {
                    'available': False,
                    'latency_ms': None,
                    'error': result.get('error', 'Unknown error'),
                    'response_sample': None
                }
                
        except Exception as e:
            return {
                'available': False,
                'latency_ms': None,
                'error': str(e),
                'response_sample': None
            }
    
    def check_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Check availability of all providers and models.
        
        Args:
            force: Force recheck even if cache is valid
            
        Returns:
            Availability status for all providers
        """
        # Try to load from cache first
        if not force and self._load_cache():
            return self.results
        
        print("Checking model availability...")
        print("Testing the configured or default model across 5 providers...\n")
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'summary': {
                'total_providers': 0,
                'available_providers': 0,
                'total_models': 0,
                'available_models': 0
            }
        }
        
        # Check each provider
        for provider, models in self.TEST_MODELS.items():
            print(f"Checking {provider}...")
            self.results['summary']['total_providers'] += 1
            
            provider_result = {
                'cli': {},
                'models': {},
                'status': 'unknown'
            }
            
            # Check CLI availability (if applicable)
            if provider in self.CLI_COMMANDS:
                cli_check = self._check_cli_available(self.CLI_COMMANDS[provider])
                provider_result['cli'] = cli_check
                
                if not cli_check['available']:
                    provider_result['status'] = 'cli_unavailable'
                    self.results['providers'][provider] = provider_result
                    print(f"  ✗ CLI not available: {cli_check['error']}")
                    continue
                else:
                    print(f"  ✓ CLI available: {cli_check['version'][:50]}")
            
            # Test models
            models_available = 0
            for model in models:
                print(f"    Testing {model}...", end=' ')
                model_result = self._test_model(provider, model)
                provider_result['models'][model] = model_result
                
                if model_result['available']:
                    models_available += 1
                    print(f"✓ ({model_result['latency_ms']}ms)")
                    self.results['summary']['available_models'] += 1
                else:
                    print(f"✗ {model_result['error']}")
                
                self.results['summary']['total_models'] += 1
            
            # Set provider status
            if models_available == len(models):
                provider_result['status'] = 'available'
                self.results['summary']['available_providers'] += 1
            elif models_available > 0:
                provider_result['status'] = 'partial'
                self.results['summary']['available_providers'] += 0.5
            else:
                provider_result['status'] = 'unavailable'
            
            self.results['providers'][provider] = provider_result
            print()
        
        # Save to cache
        self._save_cache()
        
        return self.results
    
    def _load_cache(self) -> bool:
        """
        Load results from cache if valid.
        
        Returns:
            True if cache loaded successfully
        """
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                cached = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                self.results = cached
                age_minutes = int((datetime.now() - cache_time).total_seconds() / 60)
                print(f"Using cached results from {age_minutes} minutes ago")
                print(f"Use --force to recheck\n")
                return True
            
            return False
            
        except Exception:
            return False
    
    def _save_cache(self):
        """Save results to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def print_report(self):
        """Print human-readable availability report."""
        if not self.results:
            print("No results available. Run check_all() first.")
            return
        
        print("=" * 80)
        print(" MODEL AVAILABILITY REPORT")
        print("=" * 80)
        print(f"Timestamp: {self.results['timestamp']}\n")
        
        summary = self.results['summary']
        print(f"Providers: {summary['available_providers']}/{summary['total_providers']} available")
        print(f"Models:    {summary['available_models']}/{summary['total_models']} working\n")
        
        # Detailed provider status
        print("PROVIDER STATUS:")
        print("-" * 80)
        
        for provider, data in self.results['providers'].items():
            status_icon = {
                'available': '✓',
                'partial': '⚠',
                'unavailable': '✗',
                'cli_unavailable': '✗'
            }.get(data['status'], '?')
            
            status_text = {
                'available': 'WORKING',
                'partial': 'PARTIAL',
                'unavailable': 'DOWN',
                'cli_unavailable': 'CLI MISSING'
            }.get(data['status'], 'UNKNOWN')
            
            print(f"{status_icon} {provider.upper():<12} {status_text}")
            
            # Show model details
            for model, model_data in data['models'].items():
                if model_data['available']:
                    print(f"    ✓ {model:<25} {model_data['latency_ms']}ms")
                else:
                    error = model_data['error'][:50]
                    print(f"    ✗ {model:<25} {error}")
        
        print("\n" + "=" * 80)
        
        # Recommendations
        self._print_recommendations()
    
    def _print_recommendations(self):
        """Print recommendations based on availability."""
        print("\nRECOMMENDATIONS:")
        print("-" * 80)
        
        available_providers = []
        unavailable_providers = []
        
        for provider, data in self.results['providers'].items():
            if data['status'] == 'available':
                available_providers.append(provider)
            else:
                unavailable_providers.append(provider)
        
        if not available_providers:
            print("⚠ WARNING: No providers available!")
            print("  - Check internet connection")
            print("  - Verify CLI tools installed (gemini, claude, codex, copilot)")
            print("  - Check API credentials")
        elif len(available_providers) < len(self.TEST_MODELS):
            print(f"✓ {len(available_providers)} provider(s) working: {', '.join(available_providers)}")
            if unavailable_providers:
                print(f"⚠ {len(unavailable_providers)} provider(s) down: {', '.join(unavailable_providers)}")
                print("  Configure worker_type to use available providers")
        else:
            print("✓ All providers working normally")
        
        # Report available choices without assuming a provider or model is best.
        if available_providers:
            print(f"\nAvailable worker types: {', '.join(available_providers)}")
            print("Choose from task requirements and your current provider configuration.")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check AI model availability across providers'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recheck (ignore cache)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON only'
    )
    parser.add_argument(
        '--cache-duration',
        type=int,
        default=3600,
        help='Cache duration in seconds (default: 3600)'
    )
    
    args = parser.parse_args()
    
    checker = ModelAvailabilityChecker(cache_duration=args.cache_duration)
    results = checker.check_all(force=args.force)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        checker.print_report()
    
    # Exit code based on availability
    if results['summary']['available_providers'] == 0:
        sys.exit(1)  # No providers available
    elif results['summary']['available_providers'] < results['summary']['total_providers']:
        sys.exit(2)  # Some providers unavailable
    else:
        sys.exit(0)  # All good


if __name__ == '__main__':
    main()
