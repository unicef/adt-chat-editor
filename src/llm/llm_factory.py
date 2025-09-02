"""Factory that creates LLM client instances based on environment variables."""

import os

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from src.settings import custom_logger
from src.structs.llm_clients import LLMClient

LLM_CLIENTS_REQ_CONFIG = {
    LLMClient.GROQ: {
        "GROQ_MODEL",
        "GROQ_API_KEY",
    },
    LLMClient.OPENAI: {
        "OPENAI_MODEL",
        "OPENAI_API_KEY",
    },
}


class LLMClientFactory:
    """Create configured LLM client instances."""

    def __init__(self, client: LLMClient):
        """Initialize factory with desired client backend."""
        self.logger = custom_logger(__name__)
        self.client = client
        self.config = self._get_config()

    def _get_config(self):
        required_vars = LLM_CLIENTS_REQ_CONFIG[self.client]
        missing_vars = [var for var in required_vars if os.getenv(var) is None]

        if missing_vars:
            self.logger.error(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        if self.client == LLMClient.GROQ:
            config_dict = {
                "model_name": os.getenv("GROQ_MODEL"),
                "api_key": os.getenv("GROQ_API_KEY"),
            }
        elif self.client == LLMClient.OPENAI:
            config_dict = {
                "model_name": os.getenv("OPENAI_MODEL"),
                "api_key": os.getenv("OPENAI_API_KEY"),
            }
        else:
            raise ValueError(f"Executor not defined: {self.client}")

        return config_dict

    def get_client(self) -> ChatGroq | ChatOpenAI:
        """Get the LLM client."""
        if self.client == LLMClient.GROQ:
            return ChatGroq(**self.config)
        elif self.client == LLMClient.OPENAI:
            return ChatOpenAI(**self.config)
        else:
            raise ValueError(f"Invalid client: {self.client}")
