"""
LocalEmbeddings — zero-dependency, build-safe embedding provider.

Produces deterministic, L2-normalised float vectors by projecting
token hash positions into a fixed-width vector.  No GPU, no network,
no heavy dependencies required.  Suitable for development, CI, and
free-tier deployments where Ollama/HuggingFace are unavailable.

Dimension: 1536 (matches text-embedding-3-small for interoperability)
but is overridable via the constructor.
"""
import hashlib
from typing import List

from memory.interfaces.embedding import EmbeddingProviderInterface


class LocalEmbeddings(EmbeddingProviderInterface):
    """
    Hash-projection embedding provider.

    Algorithm:
        1. Lowercase + split the text into word tokens.
        2. For each token, SHA-256 hash → integer → modulo dimension.
        3. Increment the bucket at that position.
        4. L2-normalise the resulting sparse count vector.

    Semantically similar texts share vocabulary and therefore produce
    similar vectors (cosine similarity), enabling basic recall without
    any ML runtime.
    """

    def __init__(self, dim: int = 1536) -> None:
        self._dimension = dim

    # ------------------------------------------------------------------
    # EmbeddingProviderInterface
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def provider_name(self) -> str:
        return "local"

    def health_check(self) -> bool:
        # Always available — no network or file-system requirements.
        return True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._project(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._project(text)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _project(self, text: str) -> List[float]:
        vec: List[float] = [0.0] * self._dimension
        if not text:
            return vec

        for word in text.lower().split():
            digest = hashlib.sha256(word.encode("utf-8")).hexdigest()
            pos = int(digest, 16) % self._dimension
            vec[pos] += 1.0

        # L2 normalisation
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0.0:
            vec = [v / norm for v in vec]

        return vec
