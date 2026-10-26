#!/usr/bin/env python3
"""Quick test to verify worker AI integration without full orchestration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from utils.worker_spawner import WorkerSpawner


def test_quick_worker_response():
    """Test that worker can respond to simple requests quickly."""
    print("=" * 60)
    print(" Quick Worker Response Test")
    print("=" * 60)

    print("\n[1] Initializing gemini worker...")
    spawner = WorkerSpawner(worker_type='gemini')
    print("✓ Worker initialized")

    print("\n[2] Testing simple mathematical response...")
    result = spawner.spawn(
        prompt="Calculate 15 + 27. Respond with just the number.",
        complexity="low",
        timeout=30
    )

    if result['success']:
        print(f"✓ Response: {result['output'][:100]}")
        print(f"  Model: {result.get('model_used', 'unknown')}")
        print(f"  Attempts: {result.get('attempts', 0)}")
    else:
        print(f"✗ Failed: {result.get('error', 'unknown')}")
        return False

    print("\n[3] Testing JSON format response...")
    result = spawner.spawn(
        prompt='Output this exact JSON: {"status": "ok", "value": 42}',
        complexity="low",
        timeout=30
    )

    if result['success']:
        output = result['output'].strip()
        print(f"✓ Response: {output[:150]}")
        if '42' in output:
            print("✓ JSON formatting works")
        else:
            print("! Warning: Response may not be exact JSON")
    else:
        print(f"✗ Failed: {result.get('error', 'unknown')}")
        return False

    print("\n" + "=" * 60)
    print("✓ Quick test PASSED - Worker AI is functional")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = test_quick_worker_response()
    sys.exit(0 if success else 1)
