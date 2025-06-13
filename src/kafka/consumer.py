from confluent_kafka import Consumer
from src.config import settings
import logging

logger = logging.getLogger("kafka-consumer")

def start_consumer():
    consumer = Consumer({
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'group.id': 'penguin-api',
        'auto.offset.reset': 'earliest'
    })
    
    consumer.subscribe([settings.kafka_topic])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
            
            logger.info(f"Received: {msg.value().decode('utf-8')}")
            
    finally:
        consumer.close()