import json
import logging
from datetime import datetime
from confluent_kafka import Producer
from typing import Dict, Any
from pydantic import BaseModel
import traceback
from src.config import settings

logger = logging.getLogger("kafka-producer")

class KafkaMessage(BaseModel):
    timestamp: str
    payload: Dict[str, Any]

class PredictionMessage(KafkaMessage):
    predicted_species: str

class ErrorMessage(KafkaMessage):
    error_type: str
    error_message: str
    stack_trace: str

class KafkaProducer:
    def __init__(self):
        self._producer = Producer({
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'message.timeout.ms': 3000
        })
        self.prediction_topic = "predictions"
        self.error_topic = "prediction_errors"

    def _delivery_report(self, err, msg):
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()}")

    def _send(self, topic: str, message: BaseModel):
        try:
            self._producer.produce(
                topic=topic,
                value=message.json().encode('utf-8'),
                callback=self._delivery_report
            )
            self._producer.poll(0)
        except Exception as e:
            logger.critical(f"Kafka producer failure: {e}")
            raise

    def send_prediction(self, features: Dict[str, Any], prediction: str):
        """Отправка успешного предсказания"""
        message = PredictionMessage(
            timestamp=datetime.now().isoformat(),
            predicted_species=prediction,
            payload=features
        )
        self._send(self.prediction_topic, message)
        logger.info(f"Prediction sent to Kafka: {prediction}")

    def send_validation_error(self, error: str, features: Dict[str, Any]):
        """Ошибка валидации входных данных"""
        message = ErrorMessage(
            timestamp=datetime.now().isoformat(),
            error_type="ValidationError",
            error_message=error,
            payload=features,
            stack_trace=traceback.format_exc()
        )
        self._send(self.error_topic, message)
        logger.warning(f"Validation error sent to Kafka: {error}")

    def send_processing_error(self, error: str, context: Dict[str, Any]):
        """Ошибка обработки запроса"""
        message = ErrorMessage(
            timestamp=datetime.now().isoformat(),
            error_type="ProcessingError",
            error_message=error,
            payload=context,
            stack_trace=traceback.format_exc()
        )
        self._send(self.error_topic, message)
        logger.error(f"Processing error sent to Kafka: {error}")

kafka_producer = KafkaProducer()