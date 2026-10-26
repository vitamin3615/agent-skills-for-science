#!/usr/bin/env python3
"""Test script for WorkerSpawner and basic orchestrator functionality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from utils.worker_spawner import WorkerSpawner, find_available_worker


def test_worker_availability():
    """Test which workers are available."""
    print("=" * 60)
    print("Testing Worker Availability")
    print("=" * 60)

    workers = ['gemini', 'claude', 'codex', 'copilot']
    available = []

    for worker in workers:
        spawner = WorkerSpawner(worker)
        is_available = spawner.check_available()
        status = "✓ Available" if is_available else "✗ Not available"
        print(f"{worker:10s}: {status}")
        if is_available:
            available.append(worker)

    print()
    if not available:
        print("✗ ERROR: No workers available! Install at least one CLI tool.")
        return False
    else:
        print(f"✓ Found {len(available)} available worker(s): {', '.join(available)}")
        return True


def test_worker_spawner_basic():
    """Test basic WorkerSpawner functionality."""
    print("\n" + "=" * 60)
    print("Testing WorkerSpawner Basic Functionality")
    print("=" * 60)

    worker = find_available_worker()
    if not worker:
        print("✗ No available workers found")
        return False

    print(f"Using worker: {worker}")
    spawner = WorkerSpawner(worker)

    print("\nTest 1: Simple prompt")
    result = spawner.spawn(
        prompt="What is 2+2? Respond with just the number.",
        complexity="low",
        timeout=30
    )

    if result['success']:
        print(f"✓ Worker responded: {result['output'][:100]}")
        print(f"  Model used: {result.get('model_used', 'unknown')}")
        print(f"  Attempts: {result.get('attempts', 'unknown')}")
    else:
        print(f"✗ Worker failed: {result.get('error', 'unknown')}")
        return False

    return True


def test_task_analyzer():
    """Test TaskAnalyzer initialization and basic functionality."""
    print("\n" + "=" * 60)
    print("Testing TaskAnalyzer")
    print("=" * 60)

    from task_analyzer import TaskAnalyzer

    worker = find_available_worker()
    if not worker:
        print("✗ No available workers")
        return False

    skill_dir = Path(__file__).parent.parent
    spawner = WorkerSpawner(worker)
    analyzer = TaskAnalyzer(skill_dir, spawner)

    print(f"✓ TaskAnalyzer initialized with {worker}")
    print("✓ No MCP dependency required")

    return True


def test_orchestrator_init():
    """Test AgentOrchestrator initialization."""
    print("\n" + "=" * 60)
    print("Testing AgentOrchestrator Initialization")
    print("=" * 60)

    from orchestrator import AgentOrchestrator

    try:
        orchestrator = AgentOrchestrator(work_dir="/tmp/test_orchestrator")
        print("✓ AgentOrchestrator initialized successfully")
        print(f"  Worker type: {orchestrator.worker_spawner.worker_type}")
        print(f"  Work directory: {orchestrator.work_dir}")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(" Agent Orchestrator Worker Test Suite")
    print("=" * 70 + "\n")

    tests = [
        ("Worker Availability", test_worker_availability),
        ("WorkerSpawner Basic", test_worker_spawner_basic),
        ("TaskAnalyzer", test_task_analyzer),
        ("Orchestrator Init", test_orchestrator_init),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 70)
    print(" Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
