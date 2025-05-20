from src.llm.llm_factory import LLMClientFactory
from src.structs.llm_clients import LLMClient


class LLMClientSingleton:
    _instance = None

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            cls._instance = LLMClientFactory(LLMClient.OPENAI).get_client()
        return cls._instance


llm_client = LLMClientSingleton.get_client()
