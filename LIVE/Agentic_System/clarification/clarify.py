import pathway as pw
from base import BaseAgent
from prompts import ClarificationAgentPrompt

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from utils import *

from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel
from typing import Literal

class ClarificationSchema(BaseModel):
    message : str
    route : Literal["chat", "orchestrator"]

json_format = {
    "type" : "json_schema",
    "json_schema" : {
        "name": "clarification_output",
        "schema": ClarificationSchema.model_json_schema()
        }
}

MODEL = "gpt-5-nano"
class InputSchema(pw.Schema):
    messages : list[dict]

debeziumTopic = "postgres.public.clarifier_chats"

chatTopic = "chat"
trackTopic = "track"
RouteTopics = {
            "chat": "chatResponse",
            "orchestrator": "orch"
        }

import os

kafkaServer = os.environ["KAFKA_SERVER"]

orchConsumerRdKafkaSettings = {
            "bootstrap.servers": kafkaServer,
            "group.id": "clar_consumer_group",
            "session.timeout.ms": "6000",
            "auto.offset.reset": "latest"
}

debeziumConsumerSettings = {
            "bootstrap.servers": kafkaServer,
            "group.id": "clar_consumer_group",
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

class ClarificationAgent(BaseAgent):
    def __init__(
                self,
                model : str,
                prompt : str,
                **kwargs
            ):
        super().__init__(prompt, model, **kwargs)
        self.prompt = prompt

    @pw.table_transformer
    def execute(self, t: pw.Table) -> pw.Table:
        t = t.with_columns(messages = _add_prompt(pw.this.messages, self.prompt))
        t = t.with_columns(messages = self.client(pw.this.messages)).await_futures()
        t = t.with_columns(route = _get_route_call(pw.this.messages))
        return t

chatStream = pw.io.kafka.read(
        rdkafka_settings=orchConsumerRdKafkaSettings,
        topic=chatTopic,
        schema=chatInputSchema,
        format="json",
        )   
trackStream = chatStream.select(pw.this.user_id,pw.this.conversation_id,messages = pw.this.messages,agent = "Clarification", status="Processing")

pw.io.kafka.write(
            trackStream,
            orchProducerRdKafkaSettings,
            topic_name=trackTopic
        )
clar = ClarificationAgent(MODEL, ClarificationAgentPrompt, response_format = json_format)
chatStream = chatStream.with_columns(timestamp = 0,route = "Chat", status = "None")

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


mainStream = chatStream.asof_now_join_left(
    mainStream, 
    pw.left.conversation_id == pw.right.conversation_id
).select(
    pw.left.user_id,
    pw.left.conversation_id,
    messages = pw.if_else(pw.right.messages.is_none(), pw.left.messages,
                          pw.if_else(pw.this.route == "Chat",
                        _add_chat(pw.left.messages,pw.right.messages),
                        _add_context(pw.left.messages,pw.right.messages))), 
    timestamp = pw.coalesce(pw.right.timestamp, pw.left.timestamp)
)

mainStream = clar.execute(mainStream).await_futures()

savingStream = mainStream.select(pw.this.user_id, pw.this.conversation_id, messages = pw.apply_with_type(pw.Json,pw.Json,pw.this.messages),timestamp = pw.this.timestamp)

pw.io.postgres.write(savingStream, postgresSettings, "clarifier_chats", output_table_type="snapshot", primary_key=[mainStream.conversation_id])

pw.io.jsonlines.write(mainStream,"./debugStream.jsonl")

for routeName,routeTopic in RouteTopics.items():
    routeTable = mainStream.filter(pw.this.route == routeName).select(
                user_id = pw.this.user_id,
                conversation_id = pw.this.conversation_id,
                messages = _remove_clar_context(pw.this.messages)
            )
    pw.io.kafka.write(
        routeTable,
        rdkafka_settings=orchProducerRdKafkaSettings,
        topic_name=routeTopic
    )

pw.run()
