# Pathway MCP Server

A powerful **Model Context Protocol (MCP)** server built with [Pathway](https://pathway.com/) that provides specialized Retrieval-Augmented Generation (RAG) capabilities for SEC filings and Tax/Tariff policy documents. This server enables AI assistants to query and extract precise information from financial and regulatory documents through a corrective RAG pipeline.

## 🌟 Features

- **Dual RAG Pipelines**: Separate specialized agents for SEC filings and Tax/Tariff documents
- **MCP Protocol Support**: Fully compatible with MCP-enabled AI assistants and tools
- **Corrective RAG**: Advanced retrieval strategy with multi-attempt refinement and web search fallback
- **Streaming HTTP Transport**: Real-time data processing with Pathway's streaming capabilities
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **LLM Evaluation**: Built-in judge system for response quality assessment

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Evaluation](#evaluation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Pathway MCP Server                        │
│                    (Port 8123)                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  RagSecTool      │         │  RagTaxTool      │         │
│  │  (SEC Filings)   │         │  (Tax/Tariffs)   │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                    │
│           ▼                            ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ CorrectiveRag    │         │ CorrectiveRag    │         │
│  │ (crag_sec.py)    │         │ (crag_tax.py)    │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                    │
│           └────────────┬───────────────┘                    │
│                        ▼                                     │
│              ┌──────────────────┐                           │
│              │   BaseAgent      │                           │
│              │  (LiteLLMChat)   │                           │
│              └──────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  External MCP    │
              │  RAG Service     │
              └──────────────────┘
```

### Key Components

1. **PathwayMcp Server** (`app.py`): Main MCP server handling HTTP requests
2. **RAG Tools**: Two specialized tools for different document types
   - `RagSecTool`: SEC filing queries
   - `RagTaxTool`: Tax and tariff policy queries
3. **CorrectiveRag Agents** (`crag_sec.py`, `crag_tax.py`): Implement corrective RAG logic
4. **BaseAgent** (`base.py`): Abstract base class for LLM-powered agents
5. **Utilities** (`utils.py`): Message formatting and transformation helpers
6. **Prompts** (`prompts.py`): Specialized system prompts for each domain

## 🔧 Prerequisites

- **Python**: 3.8 or higher
- **Docker** (optional): For containerized deployment
- **API Keys**:
  - `GROQ_API_KEY`: For Groq LLM access
  - `OPENAI_API_KEY`: For OpenAI models (optional)
  - `PATHWAY_LICENSE_KEY`: For Pathway framework

## 📦 Installation

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pathway_mcp
   ```

2. **Set up environment variables**:
   ```bash
   export GROQ_API_KEY="your-groq-api-key"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional
   export PATHWAY_LICENSE_KEY="your-pathway-license-key"
   ```

3. **Install dependencies**:
   ```bash
   pip install pathway
   pip install groq  # For evaluation
   ```

4. **Configure MCP endpoint**:
   Edit `app.yaml` to set your MCP service URL:
   ```yaml
   mcp_url: "http://your-mcp-service-url:port/mcp"
   ```

### Docker Installation

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   Or manually:
   ```bash
   docker build -t pathway_mcp .
   docker run -p 8123:8123 \
     -e GROQ_API_KEY=$GROQ_API_KEY \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     -e PATHWAY_LICENSE_KEY=$PATHWAY_LICENSE_KEY \
     pathway_mcp
   ```

## ⚙️ Configuration

### Model Configuration

Both RAG agents use the `gpt-4.1-nano` model by default. You can modify this in:
- `crag_sec.py`: Line 8
- `crag_tax.py`: Line 9

### Tool Filters

Each agent has specific tool filters configured:

**SEC Agent** (`crag_sec.py`):
```python
tools_filter = [
    'live_rag_sec',
    'list_documents_sec',
    'search_web_whitelist',
]
```

**Tax Agent** (`crag_tax.py`):
```python
tools_filter = [
    'list_documents_tax',
    'live_rag_tax',
    'search_web_whitelist',
]
```

## 🚀 Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:8123` and expose two MCP tools:
- `rag_tool_sec`: For SEC filing queries
- `rag_tool_tax`: For Tax/Tariff queries

### Making Queries

The server accepts queries through the MCP protocol. Each tool expects an input with the following schema:

```python
{
    "query": "Your question here"
}
```

### Example Queries

#### SEC Filings
```
"What was Apple's total net sales for fiscal year 2023?"
"For Microsoft's latest 10-K, give me the revenue, number of employees, and supply chain risks."
"What supply chain risk factors did Tesla mention in its latest 10-K?"
```

#### Tax/Tariff Documents
```
"What is the tariff rate on imported steel under Section 232?"
"Summarize the Trump Administration tariff actions and their economic impact"
"According to the CEA report, how many jobs would be saved if TCJA provisions are extended?"
```

### Response Format

Responses are returned as verbatim excerpts from the source documents. The agents follow strict rules:
- **No paraphrasing**: Text is extracted exactly as it appears
- **No summarization**: Original wording is preserved
- **No commentary**: Only the requested information is returned

## 📚 API Reference

### RagSecTool

**Tool Name**: `rag_tool_sec`

**Description**: Executes a live Retrieval-Augmented Generation pipeline for SEC filing queries.

**Input Schema**:
```python
{
    "query": str  # User query requesting information from SEC filings
}
```

**Output**:
```python
{
    "result": str  # Verbatim answer extracted from SEC filings
}
```

**Features**:
- Multi-attempt retrieval (up to 3 attempts)
- Retriever-aware query refinement
- Web search fallback
- State tracking for multi-part queries

### RagTaxTool

**Tool Name**: `rag_tool_tax`

**Description**: Executes a live Retrieval-Augmented Generation pipeline for Tax and Tariff filing queries.

**Input Schema**:
```python
{
    "query": str  # User query requesting information from tax/tariff documents
}
```

**Output**:
```python
{
    "result": str  # Verbatim answer extracted from tax/tariff filings
}
```

**Features**:
- Sequential retrieval with 3-turn budget
- Parallel query execution for independent sub-questions
- Query decomposition for complex requests
- Web search escalation

## 📁 Project Structure

```
pathway_mcp/
├── app.py                 # Main MCP server application
├── base.py                # BaseAgent abstract class
├── crag_sec.py            # SEC filings RAG agent
├── crag_tax.py            # Tax/Tariff RAG agent
├── utils.py               # Message formatting utilities
├── prompts.py             # System prompts for agents
├── llm_judge.py           # Evaluation system
├── dataset.json           # Evaluation dataset
├── app.yaml               # MCP endpoint configuration
├── Dockerfile             # Docker container definition
├── compose.yaml           # Docker Compose configuration
└── README.md              # This file
```

### File Descriptions

#### Core Application Files

- **`app.py`**: Main entry point that creates and runs the Pathway MCP server with both RAG tools
- **`base.py`**: Abstract base class providing LiteLLM integration and common agent functionality
- **`crag_sec.py`**: Corrective RAG implementation for SEC filings with specialized prompts
- **`crag_tax.py`**: Corrective RAG implementation for tax/tariff documents with specialized prompts

#### Utility Files

- **`utils.py`**: Helper functions for message transformation:
  - `_add_message_format()`: Converts query strings to message format
  - `_remove_message_format()`: Extracts content from message format
  - `_add_prompt()`: Injects system prompts into message chains
  - `_flip_roles()`: Transforms tool call sequences for LLM consumption

- **`prompts.py`**: Contains two comprehensive system prompts:
  - `CorrectiveRagPrompt2`: For SEC filing analysis (838 lines)
  - `CorrectiveRagTaxPrompt`: For tariff/tax analysis

#### Evaluation Files

- **`llm_judge.py`**: Automated evaluation system using Groq LLM to assess:
  - Helpfulness (0-10 scale)
  - Accuracy (0 or 10)
  - Detailed analysis of responses

- **`dataset.json`**: Test dataset with queries, answers, and ground truth

#### Configuration Files

- **`app.yaml`**: MCP service endpoint configuration
- **`Dockerfile`**: Container image based on `pgoldt/road:latest`
- **`compose.yaml`**: Docker Compose setup with environment variables

## 🛠️ Development

### BaseAgent Class

The `BaseAgent` class provides a foundation for creating LLM-powered agents:

```python
class BaseAgent(ABC):
    def __init__(
        self,
        prompt: str,
        model='groq/openai/gpt-oss-120b',
        mcp_config: list | None = None,
        retry_strategy=pw.udfs.NoRetryStrategy(),
        **kwargs
    ):
        # Initializes LiteLLMChat client
        
    @abc.abstractmethod
    def execute(self, t: pw.Table) -> pw.Table:
        # Must be implemented by subclasses
        pass
```

### Creating Custom Agents

To create a new RAG agent:

1. **Inherit from BaseAgent**:
   ```python
   from base import BaseAgent
   
   class MyCustomRag(BaseAgent):
       def __init__(self, model, prompt, mcp_config, **kwargs):
           super().__init__(prompt, model, mcp_config, **kwargs)
   ```

2. **Implement the execute method**:
   ```python
   @pw.table_transformer
   def execute(self, t: pw.Table) -> pw.Table:
       t = t.with_columns(messages=_add_prompt(pw.this.messages, self.prompt))
       t = t.with_columns(messages=self.client(pw.this.messages)).await_futures()
       return t
   ```

3. **Register with MCP server**:
   ```python
   class MyCustomTool(McpServable):
       def call_my_rag(self, t: pw.Table) -> pw.Table:
           # Implementation
           
       def register_mcp(self, server: McpServer):
           server.tool("my_tool_name", request_handler=self.call_my_rag, schema=InputSchema)
   ```

### Debugging

Debug output is written to JSON files:
- `debug_sec.json`: SEC agent debug output
- `debug_tax.json`: Tax agent debug output

These files contain the full message history for each query.

## 📊 Evaluation

### Running the Judge

The project includes an automated evaluation system:

```bash
python llm_judge.py
```

### Evaluation Metrics

The judge evaluates responses on two dimensions:

1. **Helpfulness** (0-10):
   - 8-10: Fully answers the question clearly
   - 5-7: Partially useful or somewhat relevant
   - 3-4: Slightly relevant but not useful
   - 1-2: Mostly unhelpful
   - -1: Asks for clarification instead of answering

2. **Accuracy** (0 or 10):
   - 10: Meaningfully aligns with ground truth
   - 0: Entirely incorrect or irrelevant
   - -1: Asks for clarification instead of answering

### Dataset Format

The `dataset.json` file should contain entries like:

```json
[
  {
    "query": "User question here",
    "answer": "Agent's response",
    "ground_truth": "Expected correct answer"
  }
]
```

## 🔍 Troubleshooting

### Common Issues

#### Server Won't Start

**Problem**: Server fails to start or crashes immediately

**Solutions**:
- Verify all environment variables are set correctly
- Check that the MCP endpoint in `app.yaml` is accessible
- Ensure Pathway license is valid
- Review logs for specific error messages

#### No Results Returned

**Problem**: Queries return empty or "could not be located" responses

**Solutions**:
- Verify the MCP service URL in `app.yaml` is correct and accessible
- Check that the external MCP RAG service is running
- Ensure the query is well-formed and specific
- Review the debug JSON files for retrieval details

#### API Key Errors

**Problem**: Authentication failures with LLM providers

**Solutions**:
- Verify `GROQ_API_KEY` is set correctly
- If using OpenAI models, ensure `OPENAI_API_KEY` is set
- Check API key permissions and quotas
- Verify the model name matches your API provider

#### Docker Issues

**Problem**: Container fails to build or run

**Solutions**:
- Ensure Docker is installed and running
- Check that all environment variables are passed to the container
- Verify port 8123 is not already in use
- Review Docker logs: `docker logs pathway_mcp`

### Debug Mode

To enable verbose logging, modify the server startup:

```python
pw.run(terminate_on_error=True)  # Change to True for debugging
```

### Performance Optimization

For better performance:
- Adjust `k` values in RAG queries (lower for faster, higher for more comprehensive)
- Use `service_tier='priority'` for faster LLM responses (already configured)
- Consider caching frequently requested information
- Monitor and optimize MCP endpoint response times

## 🔐 Security Considerations

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use secure methods to inject credentials
- **Network**: Consider using HTTPS for production deployments
- **Access Control**: Implement authentication if exposing publicly
- **Rate Limiting**: Monitor and limit API usage to prevent abuse

## 🚦 Production Deployment

### Recommendations

1. **Use HTTPS**: Configure reverse proxy (nginx, Caddy) with SSL/TLS
2. **Environment Management**: Use secrets management (AWS Secrets Manager, HashiCorp Vault)
3. **Monitoring**: Implement logging and monitoring (Prometheus, Grafana)
4. **Scaling**: Consider horizontal scaling with load balancers
5. **Health Checks**: Add health check endpoints for orchestration

### Example Production Setup

```yaml
# docker-compose.prod.yaml
services:
  pathway_mcp:
    image: pgoldt/pathway_mcp:latest
    restart: always
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - PATHWAY_LICENSE_KEY=${PATHWAY_LICENSE_KEY}
    ports:
      - "127.0.0.1:8123:8123"  # Bind to localhost only
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📖 Additional Resources

- [Pathway Documentation](https://pathway.com/developers/documentation/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Groq API Documentation](https://console.groq.com/docs)

---

**Built with [Pathway](https://pathway.com/)** - Real-time data processing framework
