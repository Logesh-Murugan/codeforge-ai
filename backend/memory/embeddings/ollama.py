"""
OllamaEmbeddings — local-first embedding provider via the Ollama REST API.

Calls the ``/api/embeddings`` endpoint on a locally running Ollama
server.  Default model: ``nomic-embed-text`` (768 dimensions).

Environment variables
---------------------
OLLAMA_BASE_URL       Base URL of the Ollama server  (default: http://localhost:11434)
OLLAMA_EMBED_MODEL    Model to use for embeddings    (default: nomic-embed-text)
OLLAMA_TIMEOUT        HTTP timeout in seconds        (default: 30)

No vendor SDK is required.  The only runtime dependency is ``httpx``,
which is already in requirements.txt.
"""
import logging
from typing import List

import httpx

from memory.interfaces.embedding import EmbeddingProviderInterface

logger = logging.getLogger(__name__)

# Dimension map for known Ollama embedding models.
# Extend as new models are pulled into a deployment.
_MODEL_DIMENSIONS: dict[str, int] = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "snowflake-arctic-embed": 1024,
}


class OllamaEmbeddings(EmbeddingProviderInterface):
    """
    Embedding provider that calls a locally running Ollama server.

    Args:
        base_url: Ollama server base URL.
        model:    Ollama model name (must be pulled on the server).
        timeout:  HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dimension: int = _MODEL_DIMENSIONS.get(model, 768)

    # ------------------------------------------------------------------
    # EmbeddingProviderInterface
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def provider_name(self) -> str:
        return "ollama"

    def health_check(self) -> bool:
        """Verify the Ollama server is reachable."""
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception as exc:
            logger.debug("[OLLAMA] Health check failed: %s", exc)
            return False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of documents via sequential Ollama API calls."""
        results: List[List[float]] = []
        for text in texts:
            results.append(self._call_api(text))
        return results

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a query.

        Uses the ``query: `` instruction prefix for nomic-embed-text to
        improve retrieval quality.
        """
        prefix = "query: " if "nomic" in self._model else ""
        return self._call_api(f"{prefix}{text}")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_api(self, text: str) -> List[float]:
        """
        POST to Ollama /api/embeddings and return the embedding vector.

        Raises:
            RuntimeError: If the request fails or the response is malformed.
        """
        payload = {"model": self._model, "prompt": text}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    f"{self._base_url}/api/embeddings",
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding")
            if not embedding or not isinstance(embedding, list):
                raise ValueError(
                    f"Unexpected Ollama response structure: {list(data.keys())}"
                )
            # Update dimension from first real response (handles unknown models)
            if self._dimension != len(embedding):
                logger.debug(
                    "[OLLAMA] Updating dimension from %d → %d for model '%s'",
                    self._dimension,
                    len(embedding),
                    self._model,
                )
                self._dimension = len(embedding)
            return embedding
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama API HTTP error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Ollama API connection error (is Ollama running at {self._base_url}?): {exc}"
            ) from exc
