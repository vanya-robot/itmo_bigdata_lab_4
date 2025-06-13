import pytest
from confluent_kafka import Consumer, Producer
import json
import os

@pytest.fixture
def kafka_config():
    return {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest'
    }

def test_kafka_producer_consumer(kafka_config):
    test_topic = "test-topic"
    test_message = {"test": "value"}
    
    # Producer
    producer = Producer({'bootstrap.servers': 'localhost:9092'})
    producer.produce(test_topic, json.dumps(test_message).encode('utf-8'))
    producer.flush()
    
    # Consumer
    consumer = Consumer(kafka_config)
    consumer.subscribe([test_topic])
    
    msg = consumer.poll(10)
    assert msg is not None
    assert json.loads(msg.value().decode('utf-8')) == test_message