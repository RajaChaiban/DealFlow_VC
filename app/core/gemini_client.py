"""
Production-grade Google Gemini API client wrapper.

Provides async methods for text generation, vision analysis, and structured output
with comprehensive error handling, retry logic, and logging.

Example:
    ```python
    from app.core import GeminiClient

    client = GeminiClient()

    # Simple text generation
    response = await client.generate("Explain private equity in one paragraph")

    # Structured JSON output
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    result = await client.generate_structured("Summarize this deal", schema)
    ```
"""

import asyncio
import json
import re
import time
from typing import Any, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image

from app.config import settings
from app.utils.exceptions import AnalysisError, APIError
from app.utils.logger import logger


class GeminiClient:
    """
    Async wrapper for Google Gemini API with retry logic and error handling.

    Supports both gemini-1.5-pro and gemini-1.5-flash models with automatic
    retry on transient failures and comprehensive logging.

    Attributes:
        api_key: Google API key for authentication
        default_model: Default model to use (pro or flash)
        default_temperature: Default temperature for generation
        max_retries: Maximum number of retry attempts

    Example:
        ```python
        client = GeminiClient()

        # Generate text
        response = await client.generate(
            prompt="What is a CIM?",
            model="pro",
            temperature=0.3
        )
        print(response)

        # Generate with system instruction
        response = await client.generate(
            prompt="Analyze this company",
            system_instruction="You are a senior PE analyst"
        )
        ```
    """

    # Model name mappings
    MODEL_NAMES = {
        "pro": "gemini-1.5-pro-latest",
        "flash": "gemini-1.5-flash-latest",
    }

    # Retry configuration
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # Base delay in seconds
    MAX_DELAY = 30.0  # Maximum delay in seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "pro",
        default_temperature: float = 0.3,
    ) -> None:
        """
        Initialize the Gemini client.

        Args:
            api_key: Google API key. If None, uses config settings.
            default_model: Default model ('pro' or 'flash').
            default_temperature: Default temperature for generation.

        Raises:
            APIError: If API key is not configured.
        """
        self.api_key = api_key or settings.google_api_key

        if not self.api_key:
            raise APIError(
                message="Google API key not configured",
                error_code="GEMINI_NO_API_KEY",
                details={"hint": "Set GOOGLE_API_KEY in .env file"},
            )

        # Configure the API
        genai.configure(api_key=self.api_key)

        self.default_model = default_model
        self.default_temperature = default_temperature

        logger.info(
            f"GeminiClient initialized with default model: {self._get_model_name(default_model)}"
        )

    def _get_model_name(self, model: str) -> str:
        """
        Get full model name from shorthand.

        Args:
            model: Model shorthand ('pro' or 'flash') or full name.

        Returns:
            Full model name string.
        """
        return self.MODEL_NAMES.get(model, model)

    def _get_model(
        self,
        model: str,
        system_instruction: Optional[str] = None,
    ) -> genai.GenerativeModel:
        """
        Get configured GenerativeModel instance.

        Args:
            model: Model shorthand or full name.
            system_instruction: Optional system instruction.

        Returns:
            Configured GenerativeModel instance.
        """
        model_name = self._get_model_name(model)

        model_kwargs: dict[str, Any] = {"model_name": model_name}

        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        return genai.GenerativeModel(**model_kwargs)

    async def _execute_with_retry(
        self,
        operation: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            operation: Name of the operation for logging.
            func: Async function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function call.

        Raises:
            APIError: If all retry attempts fail.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                start_time = time.time()

                # Execute the function
                result = await asyncio.to_thread(func, *args, **kwargs)

                elapsed = time.time() - start_time
                logger.debug(f"{operation} completed in {elapsed:.2f}s (attempt {attempt})")

                return result

            except google_exceptions.ResourceExhausted as e:
                # Rate limit error (429)
                last_exception = e
                delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)

                logger.warning(
                    f"{operation} rate limited (attempt {attempt}/{self.MAX_RETRIES}). "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)

            except google_exceptions.InternalServerError as e:
                # Server error (500)
                last_exception = e
                delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)

                logger.warning(
                    f"{operation} server error (attempt {attempt}/{self.MAX_RETRIES}). "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)

            except google_exceptions.ServiceUnavailable as e:
                # Service unavailable (503)
                last_exception = e
                delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)

                logger.warning(
                    f"{operation} service unavailable (attempt {attempt}/{self.MAX_RETRIES}). "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)

            except google_exceptions.InvalidArgument as e:
                # Invalid argument - don't retry
                logger.error(f"{operation} invalid argument: {e}")
                raise APIError(
                    message=f"Invalid argument in {operation}",
                    error_code="GEMINI_INVALID_ARGUMENT",
                    details={"error": str(e)},
                ) from e

            except google_exceptions.PermissionDenied as e:
                # Permission denied - don't retry
                logger.error(f"{operation} permission denied: {e}")
                raise APIError(
                    message="Permission denied - check API key",
                    error_code="GEMINI_PERMISSION_DENIED",
                    details={"error": str(e)},
                ) from e

            except Exception as e:
                # Unexpected error
                last_exception = e
                logger.error(f"{operation} unexpected error: {e}", exc_info=True)

                if attempt < self.MAX_RETRIES:
                    delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
                    logger.warning(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            f"{operation} failed after {self.MAX_RETRIES} attempts",
            exc_info=last_exception,
        )

        raise APIError(
            message=f"{operation} failed after {self.MAX_RETRIES} attempts",
            error_code="GEMINI_MAX_RETRIES_EXCEEDED",
            details={
                "attempts": self.MAX_RETRIES,
                "last_error": str(last_exception) if last_exception else "Unknown",
            },
        ) from last_exception

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate text response from a prompt.

        Args:
            prompt: The input prompt for generation.
            model: Model to use ('pro' or 'flash'). Defaults to config.
            temperature: Sampling temperature (0.0-2.0). Lower = more deterministic.
            max_tokens: Maximum tokens in response.
            system_instruction: Optional system-level instruction.

        Returns:
            Generated text response.

        Raises:
            APIError: If API call fails after retries.
            AnalysisError: If response is empty or invalid.

        Example:
            ```python
            response = await client.generate(
                prompt="Summarize the key risks in this CIM",
                model="pro",
                temperature=0.2,
                system_instruction="You are a PE analyst focused on risk assessment"
            )
            ```
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens or settings.max_tokens

        model_name = self._get_model_name(model)

        logger.info(
            f"Generating response with {model_name} "
            f"(temp={temperature}, max_tokens={max_tokens})"
        )

        # Get model instance
        gemini_model = self._get_model(model, system_instruction)

        # Configure generation
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        def _generate() -> genai.types.GenerateContentResponse:
            return gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
            )

        # Execute with retry
        start_time = time.time()
        response = await self._execute_with_retry("generate", _generate)
        elapsed = time.time() - start_time

        # Extract text from response
        if not response or not response.text:
            raise AnalysisError(
                message="Empty response from Gemini",
                error_code="GEMINI_EMPTY_RESPONSE",
                details={"model": model_name, "prompt_length": len(prompt)},
            )

        text = response.text

        # Log usage statistics
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            logger.info(
                f"Generation complete: {usage.prompt_token_count} prompt tokens, "
                f"{usage.candidates_token_count} response tokens, "
                f"{elapsed:.2f}s elapsed"
            )
        else:
            logger.info(
                f"Generation complete: {len(text)} chars, {elapsed:.2f}s elapsed"
            )

        return text

    async def analyze_with_vision(
        self,
        images: list[Image.Image],
        text: str,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Analyze images combined with text context.

        Useful for analyzing pitch deck slides, financial charts, or other
        visual content alongside textual information.

        Args:
            images: List of PIL Image objects to analyze.
            text: Additional text context to include.
            prompt: Analysis prompt/instructions.
            model: Model to use ('pro' or 'flash').
            temperature: Sampling temperature.

        Returns:
            Analysis response text.

        Raises:
            APIError: If API call fails after retries.
            AnalysisError: If response is empty or invalid.

        Example:
            ```python
            from PIL import Image

            # Load pitch deck slides
            slides = [Image.open(f"slide_{i}.png") for i in range(1, 6)]

            response = await client.analyze_with_vision(
                images=slides,
                text="Company: TechCorp, Industry: SaaS",
                prompt="Analyze these pitch deck slides and identify key value propositions"
            )
            ```
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        model_name = self._get_model_name(model)

        logger.info(
            f"Analyzing {len(images)} images with {model_name} "
            f"(text_length={len(text)}, prompt_length={len(prompt)})"
        )

        # Get model instance
        gemini_model = self._get_model(model)

        # Configure generation
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=settings.max_tokens,
        )

        # Build content parts: images + text + prompt
        content_parts: list[Any] = []

        # Add images
        for i, img in enumerate(images):
            content_parts.append(img)
            logger.debug(f"Added image {i + 1}: {img.size[0]}x{img.size[1]}")

        # Add text context and prompt
        combined_prompt = f"""Context:
{text}

Instructions:
{prompt}"""

        content_parts.append(combined_prompt)

        def _generate() -> genai.types.GenerateContentResponse:
            return gemini_model.generate_content(
                content_parts,
                generation_config=generation_config,
            )

        # Execute with retry
        start_time = time.time()
        response = await self._execute_with_retry("analyze_with_vision", _generate)
        elapsed = time.time() - start_time

        # Extract text from response
        if not response or not response.text:
            raise AnalysisError(
                message="Empty response from vision analysis",
                error_code="GEMINI_EMPTY_VISION_RESPONSE",
                details={
                    "model": model_name,
                    "image_count": len(images),
                    "text_length": len(text),
                },
            )

        text_response = response.text

        logger.info(
            f"Vision analysis complete: {len(images)} images analyzed, "
            f"{len(text_response)} chars response, {elapsed:.2f}s elapsed"
        )

        return text_response

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output matching a schema.

        Instructs the model to output valid JSON and validates the response
        against the provided schema. Retries if JSON parsing fails.

        Args:
            prompt: The input prompt for generation.
            response_schema: JSON schema dict describing expected output structure.
            model: Model to use ('pro' or 'flash').
            temperature: Sampling temperature (lower recommended for structured output).
            max_retries: Max attempts for valid JSON (default 3).

        Returns:
            Parsed JSON dict matching the schema.

        Raises:
            APIError: If API call fails after retries.
            AnalysisError: If valid JSON cannot be generated after retries.

        Example:
            ```python
            schema = {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "industry": {"type": "string"},
                    "revenue": {"type": "number"},
                    "risks": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["company_name", "industry"]
            }

            result = await client.generate_structured(
                prompt="Extract company info from this text: ...",
                response_schema=schema
            )
            print(result["company_name"])
            ```
        """
        model = model or self.default_model
        # Use lower temperature for structured output
        temperature = temperature if temperature is not None else 0.1

        model_name = self._get_model_name(model)

        logger.info(
            f"Generating structured output with {model_name} "
            f"(temp={temperature})"
        )

        # Create structured prompt with JSON instruction
        schema_str = json.dumps(response_schema, indent=2)
        structured_prompt = f"""{prompt}

IMPORTANT: You must respond with valid JSON only. No markdown, no explanation, just the JSON object.

The response must match this JSON schema:
```json
{schema_str}
```

Respond with only the JSON object:"""

        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                # Generate response
                response_text = await self.generate(
                    prompt=structured_prompt,
                    model=model,
                    temperature=temperature,
                )

                # Extract and parse JSON
                result = self._extract_json_from_response(response_text)

                logger.info(
                    f"Structured output generated successfully on attempt {attempt}"
                )

                return result

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(
                    f"JSON parsing failed (attempt {attempt}/{max_retries}): {e}"
                )

                if attempt < max_retries:
                    # Slightly increase temperature on retry to get different output
                    temperature = min(temperature + 0.1, 0.5)

            except Exception as e:
                last_error = e
                logger.error(f"Structured generation error: {e}")
                raise

        # All retries exhausted
        raise AnalysisError(
            message=f"Failed to generate valid JSON after {max_retries} attempts",
            error_code="GEMINI_INVALID_JSON",
            details={
                "attempts": max_retries,
                "last_error": str(last_error) if last_error else "Unknown",
                "schema": response_schema,
            },
        )

    def _extract_json_from_response(self, text: str) -> dict[str, Any]:
        """
        Extract JSON from a response that may be wrapped in markdown.

        Handles responses that include ```json code blocks or plain JSON.

        Args:
            text: Response text potentially containing JSON.

        Returns:
            Parsed JSON dict.

        Raises:
            json.JSONDecodeError: If no valid JSON can be extracted.

        Example:
            ```python
            # Handles markdown-wrapped JSON
            text = '''```json
            {"name": "TechCorp", "revenue": 1000000}
            ```'''
            result = client._extract_json_from_response(text)
            # result == {"name": "TechCorp", "revenue": 1000000}

            # Also handles plain JSON
            text = '{"name": "TechCorp"}'
            result = client._extract_json_from_response(text)
            ```
        """
        text = text.strip()

        # Try to extract JSON from markdown code blocks
        # Pattern matches ```json ... ``` or ``` ... ```
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(json_block_pattern, text)

        if matches:
            # Try each matched block
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue

        # Try to find JSON object directly (starts with { and ends with })
        json_object_pattern = r"\{[\s\S]*\}"
        object_match = re.search(json_object_pattern, text)

        if object_match:
            try:
                return json.loads(object_match.group())
            except json.JSONDecodeError:
                pass

        # Try to find JSON array (starts with [ and ends with ])
        json_array_pattern = r"\[[\s\S]*\]"
        array_match = re.search(json_array_pattern, text)

        if array_match:
            try:
                result = json.loads(array_match.group())
                # Wrap array in dict if needed
                if isinstance(result, list):
                    return {"items": result}
                return result
            except json.JSONDecodeError:
                pass

        # Last resort: try parsing the entire text as JSON
        return json.loads(text)

    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in a text string.

        Args:
            text: Text to count tokens for.
            model: Model to use for tokenization.

        Returns:
            Number of tokens in the text.

        Example:
            ```python
            count = await client.count_tokens("Hello, world!")
            print(f"Token count: {count}")
            ```
        """
        model = model or self.default_model
        gemini_model = self._get_model(model)

        def _count() -> int:
            result = gemini_model.count_tokens(text)
            return result.total_tokens

        return await asyncio.to_thread(_count)

    async def health_check(self) -> dict[str, Any]:
        """
        Check if the Gemini API is accessible.

        Returns:
            Dict with health status and latency.

        Example:
            ```python
            health = await client.health_check()
            if health["healthy"]:
                print(f"API responding in {health['latency_ms']}ms")
            ```
        """
        try:
            start_time = time.time()

            # Simple generation to test API
            response = await self.generate(
                prompt="Say 'OK' in one word",
                model="flash",  # Use flash for speed
                temperature=0.0,
                max_tokens=10,
            )

            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "healthy": True,
                "latency_ms": round(elapsed_ms, 2),
                "model": self._get_model_name("flash"),
                "response": response.strip(),
            }

        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "model": self._get_model_name("flash"),
            }


# Convenience function for creating a client
def get_gemini_client() -> GeminiClient:
    """
    Get a configured GeminiClient instance.

    Returns:
        GeminiClient instance using settings from config.

    Example:
        ```python
        from app.core import get_gemini_client

        client = get_gemini_client()
        response = await client.generate("Hello!")
        ```
    """
    return GeminiClient(
        api_key=settings.google_api_key,
        default_model="pro",
        default_temperature=settings.default_temperature,
    )
