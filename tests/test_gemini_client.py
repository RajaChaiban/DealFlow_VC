"""
Tests for the GeminiClient wrapper.

Tests cover:
- Basic text generation
- Vision analysis (mocked)
- Structured JSON output
- Error handling
- Retry logic
- Token counting
- Health checks

Run with: pytest tests/test_gemini_client.py -v
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.core.gemini_client import GeminiClient, get_gemini_client
from app.utils.exceptions import AnalysisError, APIError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_key() -> str:
    """Provide a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_settings(mock_api_key: str):
    """Mock the settings module."""
    with patch("app.core.gemini_client.settings") as mock_settings:
        mock_settings.google_api_key = mock_api_key
        mock_settings.max_tokens = 2048
        mock_settings.default_temperature = 0.3
        yield mock_settings


@pytest.fixture
def mock_genai():
    """Mock the google.generativeai module."""
    with patch("app.core.gemini_client.genai") as mock_genai:
        yield mock_genai


@pytest.fixture
def client(mock_settings, mock_genai, mock_api_key: str) -> GeminiClient:
    """Create a GeminiClient with mocked dependencies."""
    return GeminiClient(api_key=mock_api_key)


@pytest.fixture
def mock_response():
    """Create a mock Gemini API response."""
    response = MagicMock()
    response.text = "This is a test response."
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = 10
    response.usage_metadata.candidates_token_count = 20
    return response


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample image for vision tests."""
    return Image.new("RGB", (100, 100), color="blue")


# =============================================================================
# Initialization Tests
# =============================================================================


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    def test_init_with_api_key(self, mock_genai, mock_settings):
        """Test initialization with explicit API key."""
        client = GeminiClient(api_key="explicit-key")
        assert client.api_key == "explicit-key"
        mock_genai.configure.assert_called_once_with(api_key="explicit-key")

    def test_init_without_api_key_uses_settings(self, mock_genai, mock_settings):
        """Test initialization uses settings when no API key provided."""
        mock_settings.google_api_key = "settings-key"
        client = GeminiClient()
        assert client.api_key == "settings-key"

    def test_init_raises_error_when_no_api_key(self, mock_genai):
        """Test initialization raises error when no API key available."""
        with patch("app.core.gemini_client.settings") as mock_settings:
            mock_settings.google_api_key = ""
            with pytest.raises(APIError) as exc_info:
                GeminiClient()
            assert exc_info.value.error_code == "GEMINI_NO_API_KEY"

    def test_init_default_model(self, mock_genai, mock_settings):
        """Test default model is set correctly."""
        client = GeminiClient(api_key="test-key", default_model="flash")
        assert client.default_model == "flash"

    def test_init_default_temperature(self, mock_genai, mock_settings):
        """Test default temperature is set correctly."""
        client = GeminiClient(api_key="test-key", default_temperature=0.5)
        assert client.default_temperature == 0.5


# =============================================================================
# Model Name Tests
# =============================================================================


class TestModelNames:
    """Tests for model name resolution."""

    def test_get_model_name_pro(self, client: GeminiClient):
        """Test 'pro' resolves to correct model name."""
        assert client._get_model_name("pro") == "gemini-1.5-pro-latest"

    def test_get_model_name_flash(self, client: GeminiClient):
        """Test 'flash' resolves to correct model name."""
        assert client._get_model_name("flash") == "gemini-1.5-flash-latest"

    def test_get_model_name_custom(self, client: GeminiClient):
        """Test custom model name passes through."""
        assert client._get_model_name("custom-model") == "custom-model"


# =============================================================================
# Text Generation Tests
# =============================================================================


class TestGenerate:
    """Tests for text generation."""

    @pytest.mark.asyncio
    async def test_generate_basic(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
    ):
        """Test basic text generation."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.generate("Test prompt")

        assert result == "This is a test response."
        mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_model_parameter(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
    ):
        """Test generation with specific model."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        await client.generate("Test prompt", model="flash")

        mock_genai.GenerativeModel.assert_called_once()
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        assert call_kwargs["model_name"] == "gemini-1.5-flash-latest"

    @pytest.mark.asyncio
    async def test_generate_with_system_instruction(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
    ):
        """Test generation with system instruction."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        await client.generate(
            "Test prompt",
            system_instruction="You are a helpful assistant",
        )

        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        assert call_kwargs["system_instruction"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_generate_empty_response_raises_error(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that empty response raises AnalysisError."""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(AnalysisError) as exc_info:
            await client.generate("Test prompt")

        assert exc_info.value.error_code == "GEMINI_EMPTY_RESPONSE"


# =============================================================================
# Vision Analysis Tests
# =============================================================================


class TestAnalyzeWithVision:
    """Tests for vision analysis."""

    @pytest.mark.asyncio
    async def test_analyze_single_image(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
        sample_image: Image.Image,
    ):
        """Test analysis with single image."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.analyze_with_vision(
            images=[sample_image],
            text="Company context",
            prompt="Analyze this image",
        )

        assert result == "This is a test response."
        mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_multiple_images(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
        sample_image: Image.Image,
    ):
        """Test analysis with multiple images."""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        images = [sample_image, sample_image, sample_image]

        result = await client.analyze_with_vision(
            images=images,
            text="Multiple slides",
            prompt="Analyze these slides",
        )

        assert result == "This is a test response."

        # Verify content parts include images
        call_args = mock_model.generate_content.call_args[0][0]
        # Should have 3 images + 1 text prompt
        assert len(call_args) == 4

    @pytest.mark.asyncio
    async def test_analyze_vision_empty_response(
        self,
        client: GeminiClient,
        mock_genai,
        sample_image: Image.Image,
    ):
        """Test that empty vision response raises error."""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(AnalysisError) as exc_info:
            await client.analyze_with_vision(
                images=[sample_image],
                text="Context",
                prompt="Analyze",
            )

        assert exc_info.value.error_code == "GEMINI_EMPTY_VISION_RESPONSE"


# =============================================================================
# Structured Output Tests
# =============================================================================


class TestGenerateStructured:
    """Tests for structured JSON generation."""

    @pytest.mark.asyncio
    async def test_generate_structured_basic(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test basic structured output generation."""
        mock_response = MagicMock()
        mock_response.text = '{"name": "TechCorp", "revenue": 1000000}'
        mock_response.usage_metadata = None
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "revenue": {"type": "number"},
            },
        }

        result = await client.generate_structured(
            prompt="Extract company info",
            response_schema=schema,
        )

        assert result["name"] == "TechCorp"
        assert result["revenue"] == 1000000

    @pytest.mark.asyncio
    async def test_generate_structured_with_markdown_wrapper(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test extraction of JSON from markdown code blocks."""
        mock_response = MagicMock()
        mock_response.text = '''Here is the JSON:
```json
{"company": "Acme Inc", "industry": "Technology"}
```'''
        mock_response.usage_metadata = None
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        schema = {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "industry": {"type": "string"},
            },
        }

        result = await client.generate_structured(
            prompt="Extract info",
            response_schema=schema,
        )

        assert result["company"] == "Acme Inc"
        assert result["industry"] == "Technology"

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json_retries(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that invalid JSON triggers retry."""
        # First response is invalid, second is valid
        invalid_response = MagicMock()
        invalid_response.text = "This is not JSON"
        invalid_response.usage_metadata = None

        valid_response = MagicMock()
        valid_response.text = '{"status": "ok"}'
        valid_response.usage_metadata = None

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [invalid_response, valid_response]
        mock_genai.GenerativeModel.return_value = mock_model

        schema = {"type": "object", "properties": {"status": {"type": "string"}}}

        result = await client.generate_structured(
            prompt="Get status",
            response_schema=schema,
        )

        assert result["status"] == "ok"
        assert mock_model.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_structured_all_retries_fail(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that all failed retries raises error."""
        mock_response = MagicMock()
        mock_response.text = "Never valid JSON"
        mock_response.usage_metadata = None
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        schema = {"type": "object", "properties": {"data": {"type": "string"}}}

        with pytest.raises(AnalysisError) as exc_info:
            await client.generate_structured(
                prompt="Get data",
                response_schema=schema,
                max_retries=2,
            )

        assert exc_info.value.error_code == "GEMINI_INVALID_JSON"


# =============================================================================
# JSON Extraction Tests
# =============================================================================


class TestExtractJsonFromResponse:
    """Tests for JSON extraction from various response formats."""

    def test_extract_plain_json(self, client: GeminiClient):
        """Test extraction of plain JSON."""
        text = '{"key": "value"}'
        result = client._extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_extract_json_from_markdown_block(self, client: GeminiClient):
        """Test extraction from ```json block."""
        text = '''Some text before
```json
{"name": "Test"}
```
Some text after'''
        result = client._extract_json_from_response(text)
        assert result == {"name": "Test"}

    def test_extract_json_from_generic_code_block(self, client: GeminiClient):
        """Test extraction from ``` block without json specifier."""
        text = '''```
{"data": 123}
```'''
        result = client._extract_json_from_response(text)
        assert result == {"data": 123}

    def test_extract_json_object_from_mixed_text(self, client: GeminiClient):
        """Test extraction of JSON object from mixed text."""
        text = 'The result is {"result": "success"} as expected.'
        result = client._extract_json_from_response(text)
        assert result == {"result": "success"}

    def test_extract_nested_json(self, client: GeminiClient):
        """Test extraction of nested JSON."""
        text = '{"outer": {"inner": {"value": 42}}}'
        result = client._extract_json_from_response(text)
        assert result["outer"]["inner"]["value"] == 42

    def test_extract_json_with_array(self, client: GeminiClient):
        """Test extraction of JSON with arrays."""
        text = '{"items": [1, 2, 3], "names": ["a", "b"]}'
        result = client._extract_json_from_response(text)
        assert result["items"] == [1, 2, 3]
        assert result["names"] == ["a", "b"]

    def test_extract_json_array_wraps_in_dict(self, client: GeminiClient):
        """Test that standalone arrays are wrapped in dict."""
        text = '[{"id": 1}, {"id": 2}]'
        result = client._extract_json_from_response(text)
        assert "items" in result
        assert len(result["items"]) == 2

    def test_extract_invalid_json_raises_error(self, client: GeminiClient):
        """Test that invalid JSON raises JSONDecodeError."""
        text = "This is not JSON at all"
        with pytest.raises(json.JSONDecodeError):
            client._extract_json_from_response(text)


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
    ):
        """Test retry on rate limit (429) error."""
        from google.api_core import exceptions as google_exceptions

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            google_exceptions.ResourceExhausted("Rate limited"),
            mock_response,
        ]
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.generate("Test prompt")

        assert result == "This is a test response."
        assert mock_model.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_server_error(
        self,
        client: GeminiClient,
        mock_genai,
        mock_response,
    ):
        """Test retry on server error (500)."""
        from google.api_core import exceptions as google_exceptions

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            google_exceptions.InternalServerError("Server error"),
            mock_response,
        ]
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.generate("Test prompt")

        assert result == "This is a test response."

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that max retries raises APIError."""
        from google.api_core import exceptions as google_exceptions

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = google_exceptions.ResourceExhausted(
            "Always rate limited"
        )
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(APIError) as exc_info:
                await client.generate("Test prompt")

        assert exc_info.value.error_code == "GEMINI_MAX_RETRIES_EXCEEDED"

    @pytest.mark.asyncio
    async def test_no_retry_on_permission_denied(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that permission denied doesn't retry."""
        from google.api_core import exceptions as google_exceptions

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = google_exceptions.PermissionDenied(
            "Bad API key"
        )
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(APIError) as exc_info:
            await client.generate("Test prompt")

        assert exc_info.value.error_code == "GEMINI_PERMISSION_DENIED"
        # Should only be called once (no retry)
        assert mock_model.generate_content.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_invalid_argument(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test that invalid argument doesn't retry."""
        from google.api_core import exceptions as google_exceptions

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = google_exceptions.InvalidArgument(
            "Bad request"
        )
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(APIError) as exc_info:
            await client.generate("Test prompt")

        assert exc_info.value.error_code == "GEMINI_INVALID_ARGUMENT"
        assert mock_model.generate_content.call_count == 1


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_response.usage_metadata = None
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.health_check()

        assert result["healthy"] is True
        assert "latency_ms" in result
        assert result["response"] == "OK"

    @pytest.mark.asyncio
    async def test_health_check_failure(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test health check failure."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Connection failed")
        mock_genai.GenerativeModel.return_value = mock_model

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.health_check()

        assert result["healthy"] is False
        assert "error" in result


# =============================================================================
# Token Counting Tests
# =============================================================================


class TestTokenCounting:
    """Tests for token counting."""

    @pytest.mark.asyncio
    async def test_count_tokens(
        self,
        client: GeminiClient,
        mock_genai,
    ):
        """Test token counting."""
        mock_token_result = MagicMock()
        mock_token_result.total_tokens = 42

        mock_model = MagicMock()
        mock_model.count_tokens.return_value = mock_token_result
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.count_tokens("Hello, world!")

        assert result == 42


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestGetGeminiClient:
    """Tests for the get_gemini_client factory function."""

    def test_get_gemini_client_creates_instance(self, mock_genai, mock_settings):
        """Test that factory creates a GeminiClient instance."""
        mock_settings.google_api_key = "test-key"
        mock_settings.default_temperature = 0.3

        client = get_gemini_client()

        assert isinstance(client, GeminiClient)
        assert client.api_key == "test-key"
        assert client.default_temperature == 0.3


# =============================================================================
# Integration Test (Skipped by Default)
# =============================================================================


@pytest.mark.skip(reason="Requires valid API key - run manually")
class TestGeminiIntegration:
    """Integration tests with real Gemini API."""

    @pytest.mark.asyncio
    async def test_real_generate(self):
        """Test real generation with Gemini API."""
        # Set GOOGLE_API_KEY environment variable to run
        client = get_gemini_client()
        result = await client.generate(
            "Say 'Hello, pytest!' and nothing else",
            model="flash",
            temperature=0.0,
        )
        assert "Hello" in result or "pytest" in result

    @pytest.mark.asyncio
    async def test_real_health_check(self):
        """Test real health check."""
        client = get_gemini_client()
        result = await client.health_check()
        assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_real_structured_output(self):
        """Test real structured output."""
        client = get_gemini_client()
        schema = {
            "type": "object",
            "properties": {
                "greeting": {"type": "string"},
                "language": {"type": "string"},
            },
        }
        result = await client.generate_structured(
            prompt="Return a greeting in English",
            response_schema=schema,
            model="flash",
        )
        assert "greeting" in result
