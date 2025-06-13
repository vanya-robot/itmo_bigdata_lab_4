import pytest
from unittest.mock import patch, MagicMock
from src.kafka.producer import KafkaProducerWrapper, send_prediction
from src.kafka.consumer import KafkaConsumerWrapper
from src.config import settings

@pytest.fixture
def mock_producer():
    with patch('confluent_kafka.Producer') as mock:
        yield mock

@pytest.fixture
def mock_consumer():
    with patch('confluent_kafka.Consumer') as mock:
        yield mock

def test_kafka_producer_send(mock_producer):
    # Setup
    mock_prod_instance = MagicMock()
    mock_producer.return_value = mock_prod_instance
    
    # Test
    wrapper = KafkaProducerWrapper()
    test_data = {"test": "data"}
    wrapper.send_prediction(test_data)
    
    # Assert
    mock_prod_instance.produce.assert_called_once()
    mock_prod_instance.poll.assert_called_once_with(0)

def test_kafka_consumer(mock_consumer):
    # Setup
    mock_cons_instance = MagicMock()
    mock_consumer.return_value = mock_cons_instance
    
    # Test
    wrapper = KafkaConsumerWrapper()
    
    # Assert
    mock_cons_instance.subscribe.assert_called_once_with([settings.kafka_topic])