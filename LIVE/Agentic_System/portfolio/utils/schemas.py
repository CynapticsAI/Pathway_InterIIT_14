import pathway as pw

class chatInputSchema(pw.Schema):
    user_id: str
    conversation_id: str
    messages: list[dict]

class postgresStoreSchema(pw.Schema):
    user_id: str
    conversation_id: str
    messages: list[pw.Json]
    timestamp: int

class agentReqSchema(pw.Schema):
    user_id: str
    conversation_id: str
    agent: str
    timestamp: int
    messages: list[dict]

class agentResSchema(pw.Schema):
    user_id: str
    conversation_id: str
    agent: str
    status: str
    timestamp: int
    messages: list[dict]

