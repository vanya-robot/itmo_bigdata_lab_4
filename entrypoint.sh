#!/bin/bash

# Запускаем Kafka Consumer в фоновом режиме
# python src/kafka/consumer.py &

# Запускаем FastAPI приложение
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000