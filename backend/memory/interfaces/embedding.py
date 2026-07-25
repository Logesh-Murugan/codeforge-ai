"""
EmbeddingProviderInterface — contract all embedding backends must satisfy.

Decouples the rest of the memory subsystem from any specific provider
(Ollama, HuggingFace, LocalHash, …).  No vendor SDK is imported here.
"""
import abc
from typing import List


class EmbeddingProviderInterface(abc.ABC):
    """Abstract base class for any embedding generation backend."""

    # ------------------------------------------------------------------
    # Core embedding methods
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of documents.

        Args:
            texts: Non-empty list of text strings.

        Returns:
            List of float vectors, one per input document, all of
            identical length equal to ``self.dimension``.
        """

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single search query.

        Implementations MAY apply a different instruction prefix than
        ``embed_documents`` (e.g. "query: " for nomic-embed-text).

        Args:
            text: Query string.

        Returns:
            Float vector of length ``self.dimension``.
        """

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """
        Vector dimensionality produced by this provider.

        All vectors returned by ``embed_documents`` and ``embed_query``
        must have exactly this length.
        """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """
        Human-readable provider identifier, e.g. "ollama", "huggingface",
        "local".  Used for logging and provider-switching decisions.
        """

    # ------------------------------------------------------------------
    # Optional lifecycle helpers
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """
        Liveness probe.  Providers that require a live network service
        (Ollama, HuggingFace Inference API) must override this and
        verify that the service is reachable.

        Returns:
            True if the provider is healthy and ready; False otherwise.
        """
        return True
