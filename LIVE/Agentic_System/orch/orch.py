import pathway as pw
from pydantic import BaseModel
from typing import Literal

from prompts import OrchPrompt
from base import BaseAgent

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from utils import *

from dotenv import load_dotenv
load_dotenv()

import logging

#Kafka details
chatTopic = "orch"
resposneTopic = "response" 
finalResponseTopic = "chatResponse"
trackTopic = "track"
debeziumTopic = "postgres.public.orch_chats"

kafkaServer = os.environ["KAFKA_SERVER"]

AgentTopics = {
            "Market Analyser Agent": "marketAnalyzer",
            "Macro Economic Agent": "macro",
            "Portfolio Agent": "portfolioAgent",
            "Strategy Agent": "strategyAgent"
        }
orchConsumerRdKafkaSettings = {
            "bootstrap.servers": kafkaServer,
            "group.id": "orch_consumer_group",
            "session.timeout.ms": "6000",
            "auto.offset.reset": "latest"
}

debeziumConsumerSettings = {
            "bootstrap.servers": kafkaServer,
            "group.id": "orch_consumer_group",
            "session.timeout.ms": "6000",
            "auto.offset.reset": "earliest"
        }

orchProducerRdKafkaSettings = {
            "bootstrap.servers": kafkaServer,
        }

postgresSettings = {
    "host": "postgres",
    "port": "5432",
    "dbname": "test_db",
    "user": "user",
    "password": "password",
}

#Orch
class Orchestrator(BaseAgent):
    def __init__(
            self,
            prompt : str,
            model = 'gpt-5-nano',
            mcp_url = None,
            **kwargs
    ):
        super().__init__(prompt, model, mcp_url, **kwargs)

    @pw.table_transformer
    def execute(self, t: pw.Table) -> pw.Table:
        t = t.with_columns(messages = _add_prompt(pw.this.messages, self.prompt))
        t = t.with_columns(messages = self.client(pw.this.messages)).await_futures()
        t = t.with_columns(agent = _get_agent_call(pw.this.messages))
        t = t.with_columns(satisfied = _update_satisfied(pw.this.messages))
        return t


class OrcOut(BaseModel):
        query : str
        agent : Literal['Market Analyser Agent', 'Macro Economic Agent','Portfolio Agent','Strategy Agent', 'None']
        satisfied : Literal['satisfied', 'clarification needed']

response_format = {
        "type" : "json_schema",
        "json_schema" : {
            "name" : "orchestrator_output",
            "schema" : OrcOut.model_json_schema()
        }
    }

orch = Orchestrator(
    prompt = OrchPrompt,
    model = 'gpt-5-mini',
    response_format = response_format
)


chatStream = pw.io.kafka.read(
        rdkafka_settings=orchConsumerRdKafkaSettings,
        topic=chatTopic,
        schema=chatInputSchema,
        format="json",
        )

chatStream = chatStream.with_columns(timestamp = 0,agent = "Chat", status = "None")

agentResStream = pw.io.kafka.read(
        rdkafka_settings=orchConsumerRdKafkaSettings,
        topic=resposneTopic,
        schema=agentResSchema,
        format="json",
        )

pw.universes.promise_are_pairwise_disjoint(chatStream,agentResStream)

inputStream = chatStream.concat(agentResStream)

trackStream = inputStream.select(pw.this.user_id,pw.this.conversation_id,messages = pw.this.messages,agent = "Orchestrator", status="Processing")

pw.io.kafka.write(
            trackStream,
            orchConsumerRdKafkaSettings,
            topic_name=trackTopic
        )

pw.io.jsonlines.write(inputStream,"./inputStream.jsonl")

mainStream = pw.io.debezium.read(
    debeziumConsumerSettings,
    topic_name=debeziumTopic,
    schema=postgresStoreSchema
)

mainStream = mainStream.groupby(pw.this.conversation_id).reduce(
    pw.this.conversation_id,
    user_id = pw.reducers.latest(pw.this.user_id),
    messages = pw.reducers.latest(pw.this.messages),
    timestamp = pw.reducers.latest(pw.this.timestamp)
).with_columns(messages = pw.apply_with_type(convert_string_to_list_of_dicts,list[pw.Json],pw.this.messages))

mainStream = inputStream.asof_now_join_left(
    mainStream, 
    pw.left.conversation_id == pw.right.conversation_id
).select(
    pw.left.user_id,
    pw.left.conversation_id,
    messages = pw.if_else(pw.right.messages.is_none(), pw.left.messages,
                          pw.if_else(pw.this.agent == "Chat",
                        _add_chat(pw.left.messages,pw.right.messages),
                        _add_context(pw.left.messages,pw.right.messages))), 
    timestamp = pw.coalesce(pw.right.timestamp, pw.left.timestamp)
)

mainStream = orch.execute(mainStream).await_futures()

pw.io.jsonlines.write(mainStream,"./debugStream.jsonl")
savingStream = mainStream.select(pw.this.user_id, pw.this.conversation_id, messages = pw.apply_with_type(pw.Json,pw.Json,pw.this.messages),timestamp = pw.this.timestamp)
pw.io.postgres.write(savingStream, postgresSettings, "orch_chats", output_table_type="snapshot", primary_key=[mainStream.conversation_id])

## Clarification
resClarification = mainStream.filter(pw.this.satisfied == "clarification needed")
for agentName, agentTopic in AgentTopics.items():
    agentTable = resClarification.filter(pw.this.agent == agentName).select(
                user_id = pw.this.user_id,
                conversation_id = pw.this.conversation_id,
                agent = pw.this.agent,
                timestamp = pw.this.timestamp,
                messages = _remove_context(pw.this.messages)
            )
    pw.io.kafka.write(
        agentTable,
        rdkafka_settings=orchProducerRdKafkaSettings,
        topic_name=agentTopic
    )



## Satisfied
satisfiedStream = mainStream.filter(pw.this.satisfied == "satisfied")

satisfiedStream = satisfiedStream.with_columns(messages = _get_final_output(pw.this.messages))

pw.io.kafka.write(
        satisfiedStream,
        rdkafka_settings=orchProducerRdKafkaSettings,
        topic_name=finalResponseTopic
        )

        
pw.io.jsonlines.write(satisfiedStream, "./finalResponse.jsonl")

pw.run()
