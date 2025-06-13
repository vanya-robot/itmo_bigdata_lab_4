from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from src.config import settings
from src.api.schemas import PenguinFeatures
import logging

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """Инициализация подключения и создание таблиц"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        self._create_tables()
        
    def _create_tables(self):
        """Определение моделей и создание таблиц"""
        class Prediction(self.Base):
            __tablename__ = "predictions"
            
            id = Column(Integer, primary_key=True, index=True)
            island = Column(String)
            culmen_length_mm = Column(Float)
            culmen_depth_mm = Column(Float)
            flipper_length_mm = Column(Float)
            body_mass_g = Column(Float)
            sex = Column(String)
            predicted_species = Column(String)
            created_at = Column(DateTime(timezone=True), server_default=func.now())
        
        self.Prediction = Prediction
        self.Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables initialized")
    
    def get_db(self) -> Generator[Session, None, None]:
        """Генератор сессий для FastAPI Depends"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def save_prediction(self, db: Session, features: PenguinFeatures, prediction: str):
        """Сохранение предсказания в БД"""
        db_prediction = self.Prediction(
            island=features.island,
            culmen_length_mm=features.culmen_length_mm,
            culmen_depth_mm=features.culmen_depth_mm,
            flipper_length_mm=features.flipper_length_mm,
            body_mass_g=features.body_mass_g,
            sex=features.sex,
            predicted_species=prediction
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        return db_prediction

db = Database()