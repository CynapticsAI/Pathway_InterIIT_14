import pathway as pw
from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp
from crag_sec import rag_sec
from crag_tax import rag_tax
from utils import _add_message_format, _remove_message_format

class InputSchema(pw.Schema):
    query : str

class RagSecTool(McpServable):
    def call_rag_sec(self, t: pw.Table) -> pw.Table:
        """
        MCP Tool: Executes a live Retrieval-Augmented Generation pipeline for SEC filing queries.

        Args:
            query (str): The user query string requesting structured information extracted from SEC filings.
        
        Returns:
            answer (str): answer to the query via RAG of SEC Fillings
        """

        t = t.with_columns(messages = _add_message_format(pw.this.query))
        t = rag_sec.execute(t)
        pw.io.fs.write(t, 'debug_sec.json', 'json')
        t = t.with_columns(result = _remove_message_format(pw.this.messages))
        return t
    
    def register_mcp(self, server: McpServer):
        server.tool(
            "rag_tool_sec",
            request_handler=self.call_rag_sec,
            schema=InputSchema,
        )


class RagTaxTool(McpServable):
    def call_rag_tax(self, t : pw.Table) -> pw.Table:
        """
        MCP Tool: Executes a live Retrieval-Augmented Generation pipeline for Tax filing queries.

        Args:
            query (str): The user query string requesting structured information extracted from TAX filings.
        
        Returns:
            answer (str): answer to the query via RAG of Tax and Tarriff Fillings
        """

        t = t.with_columns(messages = _add_message_format(pw.this.query))
        t = rag_tax.execute(t)
        pw.io.fs.write(t, 'debug_tax.json', 'json')
        t = t.with_columns(result = _remove_message_format(pw.this.messages)) 
        return t
    
    def register_mcp(self, server: McpServer):
        server.tool(
            "rag_tool_tax",
            request_handler=self.call_rag_tax,
            schema=InputSchema,
        )

rag_sec_function= RagSecTool()
rag_tax_function= RagTaxTool()

pathway_mcp_server = PathwayMcp(
    name="Streamable MCP Server",
    transport="streamable-http",
    host="0.0.0.0",
    port=8123,
    serve=[rag_sec_function, rag_tax_function],
)

pw.run(terminate_on_error= False)
