"""Tests for Ollama-based LLM and Embedding service implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from src.application.interfaces import IEmbeddingService, ILLMService
from src.infrastructure.ollama_service import OllamaEmbeddingService, OllamaLLMService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status = MagicMock()
    return response


def _make_error_response(status_code: int = 500) -> MagicMock:
    """Create a mock httpx.Response that raises on raise_for_status."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Internal Server Error",
        request=MagicMock(spec=httpx.Request),
        response=response,
    )
    return response


# ---------------------------------------------------------------------------
# OllamaLLMService
# ---------------------------------------------------------------------------

class TestOllamaLLMServiceInterface:
    """OllamaLLMService should implement ILLMService."""

    def test_implements_illm_service(self):
        service = OllamaLLMService()
        assert isinstance(service, ILLMService)


class TestOllamaLLMServiceGenerate:
    """Tests for OllamaLLMService.generate method."""

    @pytest.mark.asyncio
    async def test_generate_sends_correct_request(self):
        """generate should POST to /api/generate with model, prompt, and stream=False."""
        mock_response = _make_response({"response": "Hello!"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaLLMService()
            await service.generate("Say hello")

        mock_client.post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:14b", "prompt": "Say hello", "stream": False},
            timeout=120.0,
        )

    @pytest.mark.asyncio
    async def test_generate_returns_response_text(self):
        """generate should return the 'response' field from the JSON body."""
        mock_response = _make_response({"response": "The answer is 42."})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaLLMService()
            result = await service.generate("What is the meaning of life?")

        assert result == "The answer is 42."

    @pytest.mark.asyncio
    async def test_generate_with_custom_base_url_and_model(self):
        """generate should use the custom base_url and model provided at init."""
        mock_response = _make_response({"response": "custom response"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaLLMService(base_url="http://host.docker.internal:11434/", model="llama3:8b")
            await service.generate("test prompt")

        mock_client.post.assert_called_once_with(
            "http://host.docker.internal:11434/api/generate",
            json={"model": "llama3:8b", "prompt": "test prompt", "stream": False},
            timeout=120.0,
        )

    @pytest.mark.asyncio
    async def test_generate_raises_on_http_error(self):
        """generate should propagate httpx.HTTPStatusError when the API returns an error."""
        mock_response = _make_error_response(500)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaLLMService()
            with pytest.raises(httpx.HTTPStatusError):
                await service.generate("bad request")


# ---------------------------------------------------------------------------
# OllamaEmbeddingService
# ---------------------------------------------------------------------------

class TestOllamaEmbeddingServiceInterface:
    """OllamaEmbeddingService should implement IEmbeddingService."""

    def test_implements_iembedding_service(self):
        service = OllamaEmbeddingService()
        assert isinstance(service, IEmbeddingService)


class TestOllamaEmbeddingServiceCreateEmbeddings:
    """Tests for OllamaEmbeddingService.create_embeddings method."""

    @pytest.mark.asyncio
    async def test_create_embeddings_returns_correct_vectors(self):
        """create_embeddings should return embedding vectors from the API response."""
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_response = _make_response({"embeddings": [expected_embedding]})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService()
            result = await service.create_embeddings(["hello world"])

        assert result == [expected_embedding]

    @pytest.mark.asyncio
    async def test_create_embeddings_sends_correct_request(self):
        """create_embeddings should POST to /api/embed with model and input."""
        mock_response = _make_response({"embeddings": [[0.1, 0.2]]})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService()
            await service.create_embeddings(["test text"])

        mock_client.post.assert_called_once_with(
            "http://localhost:11434/api/embed",
            json={"model": "bge-m3", "input": "test text"},
            timeout=60.0,
        )

    @pytest.mark.asyncio
    async def test_create_embeddings_handles_multiple_texts(self):
        """create_embeddings should call the API once per text and return all embeddings."""
        responses = [
            _make_response({"embeddings": [[0.1, 0.2, 0.3]]}),
            _make_response({"embeddings": [[0.4, 0.5, 0.6]]}),
            _make_response({"embeddings": [[0.7, 0.8, 0.9]]}),
        ]
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = responses

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService()
            result = await service.create_embeddings(["text1", "text2", "text3"])

        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_create_embeddings_with_empty_list(self):
        """create_embeddings with an empty list should return an empty list without API calls."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService()
            result = await service.create_embeddings([])

        assert result == []
        mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_embeddings_raises_on_http_error(self):
        """create_embeddings should propagate httpx.HTTPStatusError when the API returns an error."""
        mock_response = _make_error_response(500)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService()
            with pytest.raises(httpx.HTTPStatusError):
                await service.create_embeddings(["will fail"])

    @pytest.mark.asyncio
    async def test_create_embeddings_with_custom_base_url_and_model(self):
        """create_embeddings should use the custom base_url and model provided at init."""
        mock_response = _make_response({"embeddings": [[0.1]]})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response

        with patch("src.infrastructure.ollama_service.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            service = OllamaEmbeddingService(base_url="http://host.docker.internal:11434/", model="nomic-embed-text")
            await service.create_embeddings(["test"])

        mock_client.post.assert_called_once_with(
            "http://host.docker.internal:11434/api/embed",
            json={"model": "nomic-embed-text", "input": "test"},
            timeout=60.0,
        )
