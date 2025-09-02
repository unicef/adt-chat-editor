"""LLM client singleton accessor."""

from src.llm.llm_factory import LLMClientFactory
from src.settings import custom_logger
from src.structs.llm_clients import LLMClient

logger = custom_logger("LLM Client")


class LLMClientSingleton:
    """Provide a cached singleton LLM client instance."""

    _instance = None

    @classmethod
    def get_client(cls):
        """Return the cached client or create it once."""
        if cls._instance is None:
            cls._instance = LLMClientFactory(LLMClient.OPENAI).get_client()
        return cls._instance


try:
    llm_client = LLMClientSingleton.get_client()
    logger.info(f"LLM client initialized: {llm_client}")
except Exception as e:  # pragma: no cover - environment dependent
    logger.warning(f"LLM client unavailable during import: {e}")
    llm_client = None
