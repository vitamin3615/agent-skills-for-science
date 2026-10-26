"""Optional external worker-CLI adapter with bounded retry logic."""

import subprocess
import time
import random
import logging
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkerSpawner:
    """
    Spawns explicitly selected CLI-based workers using a configured model or the
    provider CLI default.

    Supports: gemini, claude, codex, copilot
    Features:
    - Optional explicit/environment model configuration
    - Exponential backoff retry (3 attempts per model)
    - Configurable timeouts
    - Graceful error handling with fatal error detection
    """

    # Versioned model names age quickly. Use an explicit model supplied by the
    # caller, an environment override, or the provider CLI's configured default.
    MODEL_ENV_VARS = {
        'gemini': 'FIELD_MAPPING_GEMINI_MODEL',
        'claude': 'FIELD_MAPPING_CLAUDE_MODEL',
        'codex': 'FIELD_MAPPING_CODEX_MODEL',
        'copilot': 'FIELD_MAPPING_COPILOT_MODEL',
        'gpt': 'FIELD_MAPPING_GPT_MODEL',
    }

    def __init__(self, worker_type: str = 'gemini', custom_model: Optional[str] = None):
        """
        Initialize worker spawner.

        Args:
            worker_type: Type of worker (gemini|claude|codex|copilot|gpt)
            custom_model: Override automatic model selection
        """
        if worker_type not in ['gemini', 'claude', 'codex', 'copilot', 'gpt']:
            raise ValueError(f"Invalid worker type: {worker_type}")

        self.worker_type = worker_type
        self.custom_model = custom_model
        self._workspace_cleanup = []  # Track workspaces for cleanup
        logger.info(f"Initialized {worker_type} worker spawner")

    def _create_isolated_workspace(self, worker_id: str) -> Path:
        """
        Create isolated workspace directory for worker.

        This prevents Docker container conflicts when running multiple
        Gemini workers in parallel by giving each worker a unique mount point.

        Args:
            worker_id: Unique worker identifier

        Returns:
            Path to isolated workspace directory
        """
        workspace = Path(tempfile.mkdtemp(prefix=f"gemini_worker_{worker_id}_"))
        self._workspace_cleanup.append(workspace)
        logger.info(f"Created isolated workspace for {worker_id}: {workspace}")
        return workspace

    def cleanup_workspaces(self):
        """
        Clean up all temporary workspace directories.

        Call this after all workers have completed to free disk space.
        """
        for workspace in self._workspace_cleanup:
            try:
                if workspace.exists():
                    shutil.rmtree(workspace)
                    logger.info(f"Cleaned up workspace: {workspace}")
            except Exception as e:
                logger.warning(f"Failed to cleanup workspace {workspace}: {e}")

        self._workspace_cleanup.clear()

    def _cleanup_docker_containers(self):
        """Report a Docker conflict without deleting containers."""
        logger.warning(
            "Docker conflict detected. Automatic container deletion is disabled; "
            "inspect and resolve the specific container outside this worker."
        )

    def _select_model(self, complexity: str) -> Optional[str]:
        """
        Select model based on complexity level.

        Args:
            complexity: low|medium|high

        Returns:
            Model identifier string
        """
        if self.custom_model:
            return self.custom_model

        return os.environ.get(self.MODEL_ENV_VARS[self.worker_type])

    def _get_fallback_sequence(self, complexity: str) -> list:
        """
        Return the single explicitly configured or provider-default model.

        Args:
            complexity: low|medium|high

        Returns:
            List of models to try in order
        """
        if self.custom_model:
            return [self.custom_model]

        return [self._select_model(complexity)]

    def _is_rate_limit_error(self, result) -> bool:
        """
        Check if subprocess result indicates rate limiting.

        Args:
            result: subprocess.CompletedProcess result

        Returns:
            True if rate limited, False otherwise
        """
        if not hasattr(result, 'stderr') or not result.stderr:
            return False

        error_text = result.stderr.lower()
        rate_limit_indicators = [
            'rate limit',
            'too many requests',
            'quota exceeded',
            '429',
            'throttled',
            'rate_limit_exceeded'
        ]

        return any(indicator in error_text for indicator in rate_limit_indicators)

    def _is_docker_conflict_error(self, result) -> bool:
        """
        Check if subprocess result indicates Docker container name conflict.

        Args:
            result: subprocess.CompletedProcess result

        Returns:
            True if Docker conflict, False otherwise
        """
        if not hasattr(result, 'stderr') or not result.stderr:
            return False

        error_text = result.stderr.lower()
        docker_conflict_indicators = [
            'container name',
            'is already in use',
            'conflict',
            'error response from daemon',
            'container with the same name exists'
        ]

        return any(indicator in error_text for indicator in docker_conflict_indicators)

    def _build_command(self, model: Optional[str], prompt: str, system_prompt: Optional[str] = None) -> list:
        """
        Build CLI command for worker subprocess.

        Args:
            model: Model identifier
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Command list for subprocess
        """
        if self.worker_type == 'gemini':
            cmd = ['gemini']
            if model:
                cmd.extend(['-m', model])
            # NOTE: gemini's -s flag is --sandbox alias, NOT system prompt.
            # Use -p for non-interactive mode (required v0.33+); prepend system_prompt.
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            cmd.extend(['-p', full_prompt])

        elif self.worker_type == 'claude':
            cmd = ['claude', '-p']
            if model:
                cmd.extend(['--model', model])
            if system_prompt:
                cmd.extend(['--system-prompt', system_prompt])
            cmd.append(prompt)

        elif self.worker_type == 'codex':
            cmd = ['codex', 'exec']
            if model:
                cmd.extend(['-m', model])
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            cmd.append(full_prompt)

        elif self.worker_type == 'copilot':
            # Copilot doesn't have --system, so prepend the system prompt.
            full_prompt = f"{system_prompt} | {prompt}" if system_prompt else prompt
            full_prompt = full_prompt.replace('\n', ' ').replace('\r', ' ')
            cmd = ['copilot']
            if model:
                cmd.extend(['--model', model])
            cmd.extend(['-p', full_prompt])

        elif self.worker_type == 'gpt':
            # GPT uses the Copilot CLI in the same format.
            full_prompt = f"{system_prompt} | {prompt}" if system_prompt else prompt
            full_prompt = full_prompt.replace('\n', ' ').replace('\r', ' ')
            cmd = ['copilot']
            if model:
                cmd.extend(['--model', model])
            cmd.extend(['-p', full_prompt])

        return cmd

    def _execute_with_retry(
        self,
        cmd: list,
        timeout: int = 120,
        max_attempts: int = 3,
        progressive_timeout: bool = True
    ) -> Dict[str, Any]:
        """
        Execute command with exponential backoff retry and progressive timeout escalation.

        Args:
            cmd: Command list
            timeout: Base timeout in seconds
            max_attempts: Maximum retry attempts
            progressive_timeout: Enable progressive timeout escalation (increases timeout on retry)

        Returns:
            Dict with success status, output, and error info
        """
        base_delay = 2  # Start with 2 seconds

        for attempt in range(1, max_attempts + 1):
            result = None
            # Progressive timeout escalation: 1x, 1.5x, 2x
            if progressive_timeout and attempt > 1:
                escalation_factor = 1.0 + ((attempt - 1) * 0.5)
                current_timeout = min(int(timeout * escalation_factor), 5400)  # Max 90 min
                logger.info(f"Progressive timeout escalation: {timeout}s → {current_timeout}s (attempt {attempt})")
            else:
                current_timeout = timeout
            try:
                logger.info(f"Attempt {attempt}/{max_attempts}: {' '.join(cmd[:3])}...")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=current_timeout,
                    check=False
                )

                if result.returncode == 0:
                    logger.info(f"Worker completed successfully on attempt {attempt}")
                    return {
                        'success': True,
                        'output': result.stdout.strip(),
                        'error': None,
                        'attempts': attempt
                    }
                else:
                    logger.warning(f"Worker failed with code {result.returncode}: {result.stderr[:200]}")

                    # Check for Docker container conflicts (retry with longer delay)
                    if self._is_docker_conflict_error(result):
                        logger.warning(
                            "Docker container conflict detected; automatic cleanup is disabled"
                        )
                        # Report the conflict without mutating Docker state.
                        self._cleanup_docker_containers()
                        # Continue to exponential backoff below

                    # Don't retry on certain fatal error types
                    elif "invalid model" in result.stderr.lower() or "authentication" in result.stderr.lower():
                        return {
                            'success': False,
                            'output': None,
                            'error': result.stderr.strip(),
                            'attempts': attempt,
                            'fatal': True
                        }

            except subprocess.TimeoutExpired:
                logger.error(f"Worker timeout after {current_timeout}s on attempt {attempt}")
                if attempt == max_attempts:
                    return {
                        'success': False,
                        'output': None,
                        'error': f"Timeout after {current_timeout}s (progressive escalation from {timeout}s base)" if progressive_timeout and attempt > 1 else f"Timeout after {current_timeout}s",
                        'attempts': attempt
                    }

            except Exception as e:
                logger.error(f"Worker exception on attempt {attempt}: {e}")
                if attempt == max_attempts:
                    return {
                        'success': False,
                        'output': None,
                        'error': str(e),
                        'attempts': attempt
                    }

            # Exponential backoff with jitter
            # For Docker conflicts, add extra delay to allow containers to clean up
            if attempt < max_attempts:
                delay = (base_delay ** attempt) + random.uniform(0, 1)

                # Extra delay for Docker conflicts (prevents rapid retries on container issues)
                if result is not None and result.returncode != 0 and self._is_docker_conflict_error(result):
                    extra_docker_delay = random.uniform(2, 5)
                    delay += extra_docker_delay
                    logger.info(f"Docker conflict: adding extra {extra_docker_delay:.1f}s delay")

                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)

        return {
            'success': False,
            'output': None,
            'error': "Max retry attempts exceeded",
            'attempts': max_attempts
        }

    def spawn(
        self,
        prompt: str,
        complexity: str = 'medium',
        timeout: int = 180,
        system_prompt: Optional[str] = None,
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Spawn a worker AI process with bounded retry.

        Supports workspace isolation for Gemini workers to prevent Docker
        container conflicts when running multiple workers in parallel.

        Args:
            prompt: User prompt for the AI
            complexity: low|medium|high (affects model selection)
            timeout: Timeout in seconds (default: 180s)
            system_prompt: Optional system prompt
            worker_id: Optional worker identifier for workspace isolation (Gemini only)

        Returns:
            Dict with success status, output, metadata, and model_used
        """
        # Workspace isolation for Gemini workers (prevents container conflicts)
        use_workspace_isolation = (self.worker_type == 'gemini' and worker_id is not None)

        if use_workspace_isolation:
            workspace = self._create_isolated_workspace(worker_id)
            original_cwd = os.getcwd()
            logger.info(f"Using workspace isolation for {worker_id}: {workspace}")

            try:
                # Change to isolated workspace
                os.chdir(workspace)

                # Execute worker in isolated workspace
                result = self._spawn_in_workspace(
                    prompt, complexity, timeout, system_prompt, worker_id
                )

                return result

            finally:
                # Always restore original directory
                os.chdir(original_cwd)
                logger.debug(f"Restored working directory for {worker_id}")

        else:
            # Normal execution without workspace isolation
            return self._spawn_in_workspace(
                prompt, complexity, timeout, system_prompt, worker_id
            )

    def _spawn_in_workspace(
        self,
        prompt: str,
        complexity: str,
        timeout: int,
        system_prompt: Optional[str],
        worker_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Internal method to spawn worker (extracted for workspace isolation logic).

        Args:
            prompt: User prompt
            complexity: Complexity level
            timeout: Timeout in seconds
            system_prompt: Optional system prompt
            worker_id: Optional worker identifier

        Returns:
            Dict with success status and output
        """
        fallback_models = self._get_fallback_sequence(complexity)

        logger.info(f"Spawning {self.worker_type} worker (complexity={complexity}, worker_id={worker_id}, fallback sequence: {fallback_models})")

        # Try each model in fallback sequence
        last_result = None
        for model_index, model in enumerate(fallback_models):
            logger.info(f"Trying model {model_index + 1}/{len(fallback_models)}: {model}")

            cmd = self._build_command(model, prompt, system_prompt)
            result = self._execute_with_retry(cmd, timeout)

            # Success - return immediately
            if result['success']:
                result['model_used'] = model or 'provider-default'
                result['worker_id'] = worker_id
                logger.info(f"Successfully used model: {model} (worker_id={worker_id})")
                return result

            # Check if it was a rate limit error
            last_result = result
            if result.get('fatal'):
                # Fatal error (auth, invalid model) - don't try fallbacks
                logger.error(f"Fatal error with {model}, stopping fallback sequence")
                result['model_used'] = model or 'provider-default'
                result['worker_id'] = worker_id
                return result

            # If we have more models to try, continue
            if model_index < len(fallback_models) - 1:
                logger.warning(f"Model {model} failed, trying next fallback model")
                continue
            else:
                logger.error(f"All fallback models exhausted for complexity={complexity}")

        # All models failed
        if last_result:
            last_result['error'] = f"All models exhausted. Last error: {last_result.get('error', 'Unknown')}"
            last_result['models_tried'] = fallback_models
            last_result['worker_id'] = worker_id
            return last_result

        return {
            'success': False,
            'output': None,
            'error': 'No models available',
            'attempts': 0,
            'models_tried': fallback_models,
            'worker_id': worker_id
        }

    def call_worker(
        self,
        prompt: str,
        complexity: str = 'medium',
        context: Optional[str] = None,
        timeout: int = 180,
        worker_id: Optional[str] = None
    ) -> str:
        """
        Convenience method to call worker and return output directly.

        Args:
            prompt: User prompt for the AI
            complexity: low|medium|high
            context: Optional context description (used as system prompt)
            timeout: Timeout in seconds
            worker_id: Optional worker identifier for workspace isolation

        Returns:
            Worker output string

        Raises:
            RuntimeError: If worker fails
        """
        system_prompt = context if context else None
        result = self.spawn(prompt, complexity, timeout, system_prompt, worker_id)

        if result['success']:
            return result['output']
        else:
            raise RuntimeError(f"Worker failed: {result.get('error', 'Unknown error')}")

    def check_available(self) -> bool:
        """
        Check if worker CLI tool is available.

        Returns:
            True if worker is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.worker_type, '--version'],
                capture_output=True,
                timeout=5,
                check=False
            )
            available = result.returncode == 0
            if available:
                logger.info(f"{self.worker_type} worker is available")
            else:
                logger.warning(f"{self.worker_type} worker is not available")
            return available
        except FileNotFoundError:
            logger.warning(f"{self.worker_type} CLI tool not found")
            return False
        except Exception as e:
            logger.error(f"Error checking {self.worker_type} availability: {e}")
            return False


def find_available_worker(preferred: Optional[str] = None) -> Optional[str]:
    """
    Find an available worker CLI tool.

    Args:
        preferred: Preferred worker type

    Returns:
        Available worker type or None
    """
    workers = ['gemini', 'claude', 'codex', 'copilot']

    # Try preferred first
    if preferred and preferred in workers:
        spawner = WorkerSpawner(preferred)
        if spawner.check_available():
            return preferred

    # Try others
    for worker in workers:
        if worker != preferred:
            spawner = WorkerSpawner(worker)
            if spawner.check_available():
                return worker

    return None
