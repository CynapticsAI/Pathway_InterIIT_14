import os
from abc import ABC
import abc
import pathway as pw
from pathway.xpacks.llm import llms


class BaseAgent(ABC):
    """
    Abstract base class for LLM-powered agents that process Pathway tables.

    Initializes a LiteLLMChat client using the specified model, retry strategy,
    and API keys, and defines an abstract `execute` method to be implemented
    by subclasses for table transformations.

    Note: API key auto detected according to model type. Supported types are OpenAI and Groq

    Args:
        prompt (str): System prompt or context for the agent.
        model (str): Model identifier (default: 'groq/openai/gpt-oss-120b').
        mcp_url (str | None): Optional MCP endpoint URL.
        retry_strategy: Retry strategy for LLM requests (default: NoRetryStrategy()).
        **kwargs: Additional keyword arguments passed to LiteLLMChat.
    """
    def __init__(
            self,
            prompt : str,
            model = 'groq/openai/gpt-oss-120b',
            mcp_config: list| None = None,
            retry_strategy =  pw.udfs.NoRetryStrategy(),
            **kwargs
    ) -> None:
        
        self.client = llms.LiteLLMChat(
            retry_strategy= retry_strategy,
            model = model,
            api_key = os.environ['GROQ_API_KEY'] if 'groq' in model else os.environ['OPENAI_API_KEY'],
            mcp_config = mcp_config,
            **kwargs
        )

        self.prompt = prompt
    

    @abc.abstractmethod
    def execute(self, t : pw.Table) -> pw.Table:
        pass

    
