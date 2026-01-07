curl -H 'Content-Type: application/json' localhost:8083/connectors --data '
{
  "name": "chats-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "plugin.name": "pgoutput",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "user",
    "database.password": "password",
    "database.dbname" : "test_db",
    "topic.prefix": "postgres", 
    "table.include.list": "public.clarifier_chats,orch_chats,public.test_chat"
  }
}'
