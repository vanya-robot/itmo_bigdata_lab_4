from confluent_kafka import Consumer
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

consumer = Consumer(conf)
topic = os.getenv('KAFKA_TOPIC')
consumer.subscribe([topic])

def consume_predictions():
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            prediction = json.loads(msg.value().decode('utf-8'))
            print(f"Received prediction: {prediction}")
            # Здесь можно добавить логику обработки сообщения
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == '__main__':
    consume_predictions()