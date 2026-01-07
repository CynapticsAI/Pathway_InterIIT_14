import json
from kafka import KafkaProducer
import logging
import sys

kafkaBroker = 'localhost:29092'
kafkaTopic = 'chat' 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def createKafkaProducer():
        """
        Creates and connects the Kafka Producer.
        The serializer is changed to json.dumps to handle dictionary payloads.
        """
        producer = KafkaProducer(
            bootstrap_servers=[kafkaBroker],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all' 
        )
        logger.info(f"Kafka Producer successfully connected to: {kafkaBroker}")
        return producer
    

def sendMessageToKafka(producer, content: str):
    """
    Wraps the raw string content into the InputSchema format and sends to Kafka.
    """
    
    message_payload = {
        "user_id": "1",
        "conversation_id": "50",
        "messages": [
            {"role": "user", "content": content}
        ],
        "timestamp": 0,
        "agent": "None"
    }
    
    try:
        future = producer.send(
            topic=kafkaTopic, 
            value=message_payload, 
            key='userMessage'.encode('utf-8')
        )
        recordMetadata = future.get(timeout=10) 
        
        logger.info(f"Message sent successfully to topic: **{recordMetadata.topic}**, partition: **{recordMetadata.partition}**, offset: **{recordMetadata.offset}**")
        logger.info(f"Content sent: **'{json.dumps(message_payload)}'**")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}")
        return False


def main():
    producer = createKafkaProducer()

    logger.info("\n--- Kafka Input Sender ---\n")
    logger.info(f"**Topic:** {kafkaTopic}")
    logger.info("Enter 'exit' or 'quit' to stop the script.")
    
    while True:
        try:
            userInput = input("Enter content to send to Kafka: ")
            
            if userInput.lower() in ['exit', 'quit']:
                logger.info("Exiting producer script.")
                break

            if userInput.strip():
                sendMessageToKafka(producer, userInput)
            else:
                logger.warning("Input was empty. Please try again.")

        except KeyboardInterrupt:
            logger.info("\nExiting producer script.")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred during input: {e}")
            break

    logger.info("Flushing and closing producer.")
    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()
