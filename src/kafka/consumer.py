import json
import logging
from confluent_kafka import Consumer, KafkaError
from typing import Dict, Any
from src.config import settings

logger = logging.getLogger("kafka-consumer")

class KafkaConsumer:
    def __init__(self):
        self._consumer = Consumer({
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'group.id': 'penguin-consumers',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        self.prediction_topic = "predictions"
        self.error_topic = "prediction_errors"

    def start_consuming(self):
        """Основной цикл обработки сообщений"""
        self._consumer.subscribe([self.prediction_topic, self.error_topic])
        
        try:
            while True:
                msg = self._consumer.poll(1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    self._handle_kafka_error(msg.error())
                    continue
                    
                self._process_message(msg)
                self._consumer.commit(msg)
        finally:
            self._consumer.close()

    def _handle_kafka_error(self, error):
        if error.code() == KafkaError._PARTITION_EOF:
            logger.debug("Reached end of partition")
        else:
            logger.error(f"Consumer error: {error}")

    def _process_message(self, msg):
        try:
            data = json.loads(msg.value().decode('utf-8'))
            
            if msg.topic() == self.error_topic:
                self._process_error(data)
            else:
                self._process_prediction(data)
                
        except Exception as e:
            logger.error(f"Message processing failed: {e}")

    def _process_prediction(self, prediction: Dict[str, Any]):
        """Обработка успешных предсказаний"""
        logger.info(f"New prediction: {prediction}")

    def _process_error(self, error: Dict[str, Any]):
        """Обработка ошибок"""
        logger.error(
            f"Error received [{error['error_type']}]: {error['error_message']}\n"
            f"Context: {error['payload']}\n"
            f"Stack trace: {error['stack_trace']}"
        )

kafka_consumer = KafkaConsumer()