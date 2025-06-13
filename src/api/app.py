from fastapi import FastAPI, HTTPException, Request, Depends
from src.model import PenguinClassifier
from src.api.schemas import PenguinFeatures
from src.exceptions import ModelLoadError, PredictionError
from src.db.database import db
from src.kafka.producer import kafka_producer
from src.kafka.consumer import kafka_consumer
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import time
import joblib
import threading
import traceback

LOG_DIR = Path("logs/")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("api logger")

app = FastAPI(title="Penguin Species Classifier API")

@app.on_event("startup")
def startup_event():
    import threading
    def run_consumer():
        kafka_consumer.start_consuming()
    
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Kafka consumer started in background")

# Логирование запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"Request: {request.method} {request.url} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.2f}ms"
    )
    return response

try:
    model = PenguinClassifier.load('./experiments/penguin_model.pkl')
    logger.info("Model loaded successfully")
except (FileNotFoundError, joblib.UnpicklingError) as e:
    logger.critical(f"Failed to load model: {str(e)}")
    raise ModelLoadError(f"Cannot load model: {str(e)}")
except Exception as e:
    logger.critical(f"Unexpected error loading model: {str(e)}")
    raise RuntimeError("Cannot start API due to unexpected error")

@app.post("/predict")
async def predict(
    features: PenguinFeatures,
    db_session: Session = Depends(db.get_db)
    ):

    context = {
        "endpoint": "/predict",
        "features": features.dict()
    }

    try:
        logger.info(f"Prediction request: {features}")
        prediction = model.predict(features)
        logger.info(f"Prediction result: {prediction[0]}")
        
        # Сохраняем предсказание в БД
        db_prediction = db.save_prediction(db_session, features, prediction[0])
        
        # Отправляем предсказание в Kafka

        kafka_producer.send_prediction(features.dict(), prediction[0])
        
        return {"species": prediction[0]}
    
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}", exc_info=True)
        kafka_producer.send_validation_error(str(e), features.dict())
        raise HTTPException(status_code=422, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        kafka_producer.send_processing_error(str(e), context)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.critical(f"Unexpected error: {traceback.format_exc()}")
        kafka_producer.send_processing_error(str(e), context)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    return {"status": "OK"}