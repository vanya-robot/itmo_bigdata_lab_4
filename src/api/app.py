from fastapi import FastAPI, HTTPException, Request, Depends
from src.model import PenguinClassifier
from src.api.schemas import PenguinFeatures
from src.exceptions import ModelLoadError, PredictionError
from src.db.database import db
from src.kafka.producer import send_prediction
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import time
import joblib
import threading

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
    # Запускаем consumer в отдельном процессе
    import multiprocessing
    from src.kafka.consumer import start_consumer
    
    process = multiprocessing.Process(target=start_consumer, daemon=True)
    process.start()
    logger.info("Kafka consumer started in background process")

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
    try:
        logger.info(f"Prediction request: {features}")
        prediction = model.predict(features)
        logger.info(f"Prediction result: {prediction[0]}")
        
        # Сохраняем предсказание в БД
        db_prediction = db.save_prediction(db_session, features, prediction[0])
        
        # Отправляем предсказание в Kafka
        prediction_data = {
            **features.dict(),
            "predicted_species": prediction[0],
            "timestamp": db_prediction.created_at.isoformat()
        }
        send_prediction(prediction_data)
        
        return {"species": prediction[0]}
    
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}", exc_info=True)
        raise HTTPException(status_code=422, detail=str(e))
    except PredictionError as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected prediction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    return {"status": "OK"}