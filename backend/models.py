from typing import List, Optional
from pydantic import BaseModel

class UserInput(BaseModel):
    name: Optional[str] = None
    age: int
    sex: str  # 'male' or 'female'
    height_cm: float
    weight_kg: float
    activity_level: str  # sedentary, light, moderate, active, very_active
    fitness_goal: str  # lose, maintain, gain
    dietary_preferences: Optional[List[str]] = []
    restrictions: Optional[List[str]] = []
    workout_days_per_week: int
    equipment: Optional[List[str]] = []
    notes: Optional[str] = ""
