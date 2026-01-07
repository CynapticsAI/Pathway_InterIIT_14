CREATE TABLE IF NOT EXISTS clarifier_chats (
    user_id varchar(256) NOT NULL,
		conversation_id varchar(256) PRIMARY KEY,
		messages JSONB NOT NULL,
		timestamp integer NOT NULL
);
CREATE TABLE IF NOT EXISTS orch_chats (
    user_id varchar(256) NOT NULL,
		conversation_id varchar(256) PRIMARY KEY,
		messages JSONB NOT NULL,
		timestamp integer NOT NULL
);

CREATE TABLE IF NOT EXISTS test_chat (
    user_id varchar(256) NOT NULL,
		conversation_id varchar(256) PRIMARY KEY,
		messages JSON NOT NULL,
		timestamp integer NOT NULL
);
