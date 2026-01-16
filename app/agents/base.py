"""
Base Agent class for DealFlow AI Copilot.

Provides common functionality for all specialized agents including
error handling, retry logic, logging, and status tracking.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

from app.core.gemini_client import GeminiClient, get_gemini_client
from app.models.schemas import AgentExecutionStatus, AgentStatus
from app.utils.exceptions import AnalysisError
from app.utils.logger import logger

# Type variable for agent output
T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all DealFlow agents.

    Provides common functionality:
    - Gemini client management
    - Execution status tracking
    - Error handling and retry logic
    - Logging and metrics

    Subclasses must implement:
    - name: Agent identifier
    - execute(): Main execution logic
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        max_retries: int = 3,
        timeout_seconds: int = 120,
    ) -> None:
        """
        Initialize the base agent.

        Args:
            gemini_client: Optional pre-configured Gemini client
            max_retries: Maximum retry attempts on failure
            timeout_seconds: Maximum execution time before timeout
        """
        self.client = gemini_client or get_gemini_client()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        # Execution tracking
        self._status = AgentStatus.PENDING
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._retry_count = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> T:
        """
        Execute the agent's main task.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            Agent-specific result model

        Raises:
            AnalysisError: If execution fails
        """
        pass

    @property
    def status(self) -> AgentStatus:
        """Current execution status."""
        return self._status

    @property
    def execution_status(self) -> AgentExecutionStatus:
        """Get detailed execution status."""
        duration = None
        if self._started_at:
            end_time = self._completed_at or datetime.utcnow()
            duration = (end_time - self._started_at).total_seconds()

        return AgentExecutionStatus(
            agent_name=self.name,
            status=self._status,
            started_at=self._started_at,
            completed_at=self._completed_at,
            duration_seconds=duration,
            error_message=self._error_message,
            retry_count=self._retry_count,
        )

    async def run(self, **kwargs: Any) -> T:
        """
        Run the agent with error handling and retry logic.

        This is the main entry point for agent execution.
        It wraps execute() with status tracking, retries, and timeouts.

        Args:
            **kwargs: Arguments passed to execute()

        Returns:
            Agent result

        Raises:
            AnalysisError: If all retry attempts fail
        """
        self._status = AgentStatus.RUNNING
        self._started_at = datetime.utcnow()
        self._error_message = None
        self._retry_count = 0

        logger.info(f"[{self.name}] Starting execution")

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.execute(**kwargs),
                    timeout=self.timeout_seconds,
                )

                # Success
                self._status = AgentStatus.COMPLETED
                self._completed_at = datetime.utcnow()

                duration = (self._completed_at - self._started_at).total_seconds()
                logger.info(
                    f"[{self.name}] Completed successfully in {duration:.2f}s"
                )

                return result

            except asyncio.TimeoutError:
                last_error = AnalysisError(
                    message=f"{self.name} timed out after {self.timeout_seconds}s",
                    error_code="AGENT_TIMEOUT",
                )
                self._retry_count = attempt
                logger.warning(
                    f"[{self.name}] Timeout on attempt {attempt}/{self.max_retries}"
                )

            except AnalysisError as e:
                last_error = e
                self._retry_count = attempt
                logger.warning(
                    f"[{self.name}] Analysis error on attempt {attempt}/{self.max_retries}: {e.message}"
                )

            except Exception as e:
                last_error = e
                self._retry_count = attempt
                logger.error(
                    f"[{self.name}] Unexpected error on attempt {attempt}/{self.max_retries}",
                    exc_info=True,
                )

            # Retry with backoff
            if attempt < self.max_retries:
                self._status = AgentStatus.RETRYING
                delay = 2 ** attempt  # Exponential backoff
                logger.info(f"[{self.name}] Retrying in {delay}s...")
                await asyncio.sleep(delay)

        # All retries exhausted
        self._status = AgentStatus.FAILED
        self._completed_at = datetime.utcnow()
        self._error_message = str(last_error) if last_error else "Unknown error"

        logger.error(
            f"[{self.name}] Failed after {self.max_retries} attempts: {self._error_message}"
        )

        raise AnalysisError(
            message=f"{self.name} failed after {self.max_retries} attempts",
            error_code="AGENT_MAX_RETRIES",
            details={
                "agent": self.name,
                "attempts": self.max_retries,
                "last_error": self._error_message,
            },
        )

    async def _generate_with_schema(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_instruction: Optional[str] = None,
        model: str = "pro",
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output using Gemini.

        Helper method for agents to get validated JSON responses.

        Args:
            prompt: The prompt to send
            schema: Expected JSON schema
            system_instruction: Optional system prompt
            model: Model to use ('pro' or 'flash')
            temperature: Generation temperature

        Returns:
            Parsed JSON dict
        """
        # Build full prompt with system instruction
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        return await self.client.generate_structured(
            prompt=full_prompt,
            response_schema=schema,
            model=model,
            temperature=temperature,
        )

    async def _generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: str = "pro",
        temperature: float = 0.3,
    ) -> str:
        """
        Generate text response using Gemini.

        Args:
            prompt: The prompt to send
            system_instruction: Optional system prompt
            model: Model to use
            temperature: Generation temperature

        Returns:
            Generated text
        """
        return await self.client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
        )

    def reset(self) -> None:
        """Reset agent state for reuse."""
        self._status = AgentStatus.PENDING
        self._started_at = None
        self._completed_at = None
        self._error_message = None
        self._retry_count = 0


class AgentContext:
    """
    Shared context for agent execution.

    Stores intermediate results and shared data between agents.
    """

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.created_at = datetime.utcnow()

    def set(self, key: str, value: Any) -> None:
        """Store a value in context."""
        self.data[key] = value
        logger.debug(f"Context: Set '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from context."""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return key in self.data

    def clear(self) -> None:
        """Clear all context data."""
        self.data.clear()
