#!/usr/bin/env python3
"""Comprehensive test of all Copilot-based models in worker_spawner."""

import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from utils.worker_spawner import WorkerSpawner


def test_all_copilot_models():
    """Test all models that use Copilot CLI."""
    
    print("=" * 80)
    print(" COMPREHENSIVE COPILOT MODELS TEST")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}\n")
    
    # Define all models to test
    test_config = {
        'gpt': {
            'models': ['gpt-5-mini', 'gpt-4.1', 'gpt-5.1'],
            'prompt': 'Calculate 50 + 50. Reply with just the number.',
            'expected': '100'
        },
        'copilot': {
            'models': ['claude-haiku-4.5', 'claude-sonnet-4', 'claude-sonnet-4.6'],
            'prompt': 'What is 25 * 4? Reply with just the number.',
            'expected': '100'
        }
    }
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'details': []
    }
    
    # Test each worker type and model
    for worker_type, config in test_config.items():
        print(f"\n{'=' * 80}")
        print(f" Testing {worker_type.upper()} Worker Type")
        print(f"{'=' * 80}\n")
        
        for model in config['models']:
            results['total_tests'] += 1
            test_name = f"{worker_type}/{model}"
            
            print(f"[{results['total_tests']}] Testing: {test_name}")
            print(f"    Prompt: {config['prompt'][:60]}...")
            
            test_result = {
                'test': test_name,
                'worker_type': worker_type,
                'model': model,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                # Initialize worker with specific model
                worker = WorkerSpawner(worker_type=worker_type, custom_model=model)
                
                # Execute test
                result = worker.spawn(
                    prompt=config['prompt'],
                    complexity='low',
                    timeout=45
                )
                
                if result['success']:
                    output = result['output'].strip()
                    
                    # Check if expected value is in output
                    if config['expected'] in output:
                        print(f"    ✓ PASSED")
                        print(f"      Output: {output[:80]}")
                        print(f"      Model Used: {result.get('model_used', 'unknown')}")
                        print(f"      Attempts: {result.get('attempts', 0)}")
                        results['passed'] += 1
                        test_result['status'] = 'passed'
                        test_result['output'] = output[:200]
                    else:
                        print(f"    ⚠ PARTIAL - Response received but unexpected")
                        print(f"      Expected: {config['expected']}")
                        print(f"      Got: {output[:80]}")
                        results['failed'] += 1
                        test_result['status'] = 'partial'
                        test_result['output'] = output[:200]
                        test_result['note'] = f"Expected '{config['expected']}' not found"
                else:
                    print(f"    ✗ FAILED")
                    print(f"      Error: {result.get('error', 'unknown')}")
                    results['failed'] += 1
                    test_result['status'] = 'failed'
                    test_result['error'] = result.get('error', 'unknown')
                
                test_result['model_used'] = result.get('model_used', 'unknown')
                test_result['attempts'] = result.get('attempts', 0)
                
            except Exception as e:
                print(f"    ✗ EXCEPTION")
                print(f"      Error: {str(e)}")
                results['failed'] += 1
                test_result['status'] = 'exception'
                test_result['error'] = str(e)
            
            results['details'].append(test_result)
            print()
    
    # Summary
    print("=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)
    print(f"\nTotal Tests: {results['total_tests']}")
    print(f"Passed:      {results['passed']} ({results['passed']/results['total_tests']*100:.1f}%)")
    print(f"Failed:      {results['failed']} ({results['failed']/results['total_tests']*100:.1f}%)")
    
    print("\nDetailed Results:")
    print("-" * 80)
    for detail in results['details']:
        status_icon = {
            'passed': '✓',
            'partial': '⚠',
            'failed': '✗',
            'exception': '✗'
        }.get(detail['status'], '?')
        print(f"{status_icon} {detail['test']:<30} {detail['status'].upper():<10} "
              f"({detail.get('model_used', 'N/A')})")
    
    # Save results
    results_file = Path(__file__).parent.parent / "Temp" / "copilot_models_test.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print("=" * 80)
    
    return results['passed'] == results['total_tests']


if __name__ == "__main__":
    success = test_all_copilot_models()
    sys.exit(0 if success else 1)
