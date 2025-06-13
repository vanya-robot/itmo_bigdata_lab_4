from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class KafkaPredictionData(BaseModel):
    island: str
    culmen_length_mm: float
    culmen_depth_mm: float
    flipper_length_mm: float
    body_mass_g: float
    sex: str
    predicted_species: str
    timestamp: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }