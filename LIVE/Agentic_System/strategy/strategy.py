import pathway as pw
from dotenv import load_dotenv
load_dotenv()

from base import BaseAgent
from prompts import StrategyAgentPrompt

from utils import * 
import os

class PortfolioAgent(BaseAgent):
    def __init__(
            self,
            model : str =  'groq/openai/gpt-oss-120b',
            prompt : str = "",
            mcp_url : str | None = None,
            **kwargs
    ):
        super().__init__(
            prompt = prompt,
            model = model,
            mcp_url= mcp_url,
            **kwargs
        )

    def execute(self, t: pw.Table) -> pw.Table:
        t = t.with_columns(messages = _add_prompt(pw.this.messages, self.prompt))
        t = t.with_columns(messages = _add_user_id(pw.this.messages, pw.this.user_id))
        t = t.with_columns(messages = self.client(pw.this.messages)).await_futures()
        return t
agentTopic = "strategyAgent"
resTopic = "response"

trackingTopic = "track"

kafkaServer = os.environ["KAFKA_SERVER"]

agentConsumerSettings = {
        "bootstrap.servers": kafkaServer,
            "group.id": "agent_consumer_group",
            "session.timeout.ms": "6000",
            "auto.offset.reset": "latest"
        }

agentProducerSettings = {
            "bootstrap.servers": kafkaServer,
        }



t = pw.io.kafka.read(
            agentConsumerSettings,
            topic=agentTopic,
            schema=agentReqSchema,
            format="json"
        )

tools_filter = [
    'optimize_strategy',
    'create_strategy',
]
trackStream = t.select(pw.this.user_id,pw.this.conversation_id,messages = pw.this.messages,agent = pw.this.agent, status="Processing")

pw.io.kafka.write(
            trackStream,
            agentProducerSettings,
            topic_name=trackingTopic
        )

mcp_config = [{
    "mcp_url" : os.environ["mcp_url_1"],
    "mcp_token" : "aba"
},
{
    "mcp_url" : os.environ["mcp_url_2"],
    "mcp_token" : "aba"
}]

market = PortfolioAgent(model = 'gpt-4.1-nano', prompt =StrategyAgentPrompt, mcp_config=mcp_config, tools_filter = tools_filter, service_tier = 'priority')
t = market.execute(t).await_futures()
pw.io.kafka.write(
            t,
            rdkafka_settings=agentProducerSettings,
            topic_name=resTopic
        )
pw.io.jsonlines.write(t,"./strat.jsonl")

pw.run()
