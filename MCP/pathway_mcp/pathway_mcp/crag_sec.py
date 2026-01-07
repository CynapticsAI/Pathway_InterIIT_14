import pathway as pw
from base import BaseAgent
from prompts import CorrectiveRagPrompt2
from utils import _add_prompt

with open('app.yaml', 'r') as f:
    cfg = pw.load_yaml(f)
MODEL = "gpt-4.1-nano"
MCP_URL = cfg['mcp_url']
MCP_CONFIG = [{
    "mcp_url" : MCP_URL,
    "mcp_token" : "aba",
}]
tools_filter = [
        'live_rag_sec',
        'list_documents_sec'
        'search_web_whitelist',
    ]

class InputSchema(pw.Schema):
    messages : list[dict]

class CorrectiveRag(BaseAgent):
    def __init__(
                self,
                model : str,
                prompt : str,
                mcp_config: list,
                **kwargs
            ):
        super().__init__(prompt, model, mcp_config, **kwargs)
        self.prompt = prompt

    @pw.table_transformer
    def execute(self, t: pw.Table) -> pw.Table:
        t = t.with_columns(messages = _add_prompt(pw.this.messages, self.prompt))
        t = t.with_columns(messages = self.client(pw.this.messages)).await_futures()
        return t
    
rag_sec = CorrectiveRag(MODEL, CorrectiveRagPrompt2, MCP_CONFIG, tools_filter= tools_filter, service_tier = 'priority')






