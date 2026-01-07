from django.apps import AppConfig


class KafkaConsumerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kafka_consumer'
    verbose_name = 'Kafka Consumer'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        pass
