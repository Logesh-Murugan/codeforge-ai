"""
HuggingFaceEmbeddings — cloud embedding provider via the HuggingFace
Inference API.

Calls ``https://api-inference.huggingface.co/pipeline/feature-extraction/``
with a Bearer token.  No heavy ``sentence-transformers`` dependency is
required.  The only runtime dependency is ``httpx``.

Environment variables
---------------------
HF_API_TOKEN          HuggingFace API token  (required for cloud mode)
HF_EMBED_MODEL        Model ID               (default: sentence-transformers/all-MiniLM-L6-v2)
HF_EMBED_TIMEOUT      HTTP timeout seconds   (default: 30)

Model dimension reference
--------------------------
all-MiniLM-L6-v2            384
all-mpnet-base-v2           768
paraphrase-multilingual     768
"""
import logging
from typing import List

import httpx

from memory.interfaces.embedding import EmbeddingProviderInterface

logger = logging.getLogger(__name__)

_HF_INFERENCE_URL = (
    "https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
)

_MODEL_DIMENSIONS: dict[str, int] = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
}


class HuggingFaceEmbeddings(EmbeddingProviderInterface):
    """
    Cloud embedding provider backed by the HuggingFace Inference API.

    Args:
        api_token: HuggingFace Bearer token.
        model:     HF model repository ID.
        timeout:   HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_token: str,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        timeout: int = 30,
    ) -> None:
        if not api_token:
            raise ValueError(
                "HuggingFaceEmbeddings requires a valid HF_API_TOKEN. "
                "Set the HF_API_TOKEN environment variable."
            )
        self._api_token = api_token
        self._model = model
        self._timeout = timeout
        self._dimension: int = _MODEL_DIMENSIONS.get(model, 384)
        self._url = _HF_INFERENCE_URL.format(model=model)

    # ------------------------------------------------------------------
    # EmbeddingProviderInterface
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def provider_name(self) -> str:
        return "huggingface"

    def health_check(self) -> bool:
        """Probe the HF Inference API with a trivial request."""
        try:
            vec = self.embed_query("ping")
            return len(vec) > 0
        except Exception as exc:
            logger.debug("[HF] Health check failed: %s", exc)
            return False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of documents.

        The HF Inference API accepts a list of strings in the
        ``inputs`` field and returns a list of float vectors.
        """
        return self._call_api(texts)

    def embed_query(self, text: str) -> List[float]:
        result = self._call_api([text])
        return result[0]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """
        POST to the HF Inference feature-extraction endpoint.

        Raises:
            RuntimeError: On HTTP or structural errors.
        """
        headers = {"Authorization": f"Bearer {self._api_token}"}
        payload = {"inputs": texts, "options": {"wait_for_model": True}}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(self._url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # HF may return a list-of-lists (batch) or a single list (single text).
            if isinstance(data, list) and data and isinstance(data[0], float):
                # Single text → wrap in outer list
                data = [data]

            if not isinstance(data, list) or not all(
                isinstance(v, list) for v in data
            ):
                raise ValueError(
                    f"Unexpected HF response structure. "
                    f"Expected list-of-lists, got: {type(data)}"
                )

            # Update dimension from first real response
            first_vec = data[0]
            if self._dimension != len(first_vec):
                logger.debug(
                    "[HF] Updating dimension from %d → %d for model '%s'",
                    self._dimension,
                    len(first_vec),
                    self._model,
                )
                self._dimension = len(first_vec)

            return data
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"HuggingFace API HTTP error {exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"HuggingFace API connection error: {exc}"
            ) from exc
