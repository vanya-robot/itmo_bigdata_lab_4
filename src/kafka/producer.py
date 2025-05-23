from confluent_kafka import Producer
import json
import os
from src.config import settings

conf = {
    'bootstrap.servers': settings.get_kafka_brokers(),
    'security.protocol': settings.get_kafka_security_protocol(),
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': settings.get_kafka_username(),
    'sasl.password': settings.get_kafka_password()
}

producer = Producer(conf)
topic = os.getenv('KAFKA_TOPIC')

def delivery_report(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()}')

def send_prediction(prediction_data):
    try:
        producer.produce(
            topic=topic,
            value=json.dumps(prediction_data).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()
    except Exception as e:
        print(f"Failed to send message: {e}")