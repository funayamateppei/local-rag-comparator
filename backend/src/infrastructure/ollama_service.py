"""Ollama-based LLM and Embedding service implementations."""

import httpx
from src.application.interfaces import IEmbeddingService, ILLMService


class OllamaLLMService(ILLMService):
    """ILLMService implementation using Ollama REST API.

    Communicates with Ollama's /api/generate endpoint.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:14b") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json()["response"]


class OllamaEmbeddingService(IEmbeddingService):
    """IEmbeddingService implementation using Ollama REST API.

    Communicates with Ollama's /api/embed endpoint using bge-m3.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "bge-m3") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient() as client:
            embeddings = []
            for text in texts:
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": text},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embeddings"][0])
            return embeddings
