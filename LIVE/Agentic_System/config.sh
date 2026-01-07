docker compose exec debezium bash connector.sh

topics="chatResponse orch response track marketAnalyzer macro postgres.public.orch_chats postgres.public.clarifier_chats"

for topic in $topics; do
  docker compose exec kafka kafka-topics --create --topic "$topic" --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 --if-not-exists
done
