from confluent_kafka import Producer
from src.config import settings
import json
import logging

logger = logging.getLogger("kafka-producer")

producer = Producer({
    'bootstrap.servers': settings.kafka_bootstrap_servers
})

def send_prediction(prediction_data: dict):
    try:
        producer.produce(
            topic=settings.kafka_topic,
            value=json.dumps(prediction_data).encode('utf-8'),
            callback=lambda err, msg: (
                logger.error(f'Delivery failed: {err}') if err else
                logger.info(f'Delivered to {msg.topic()}')
        ))
        producer.poll(0)
    except Exception as e:
        logger.error(f"Send error: {e}", exc_info=True)
        raise