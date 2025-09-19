# Improved models.py (unchanged from previous version)
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    name: Optional[str] = None
    age: int = Field(..., gt=0, description="Age must be positive")
    sex: str = Field(..., pattern="^(male|female)$", description="Must be 'male' or 'female'")
    height_cm: float = Field(..., gt=0, description="Height in cm must be positive")
    weight_kg: float = Field(..., gt=0, description="Weight in kg must be positive")
    activity_level: str = Field(..., pattern="^(sedentary|light|moderate|active|very_active)$",
                                description="Activity level options")
    fitness_goal: str = Field(..., pattern="^(lose|maintain|gain)$", description="Fitness goal options")
    dietary_preferences: Optional[List[str]] = Field(default_factory=list)
    restrictions: Optional[List[str]] = Field(default_factory=list)
    workout_days_per_week: int = Field(..., ge=0, le=7, description="0-7 days per week")
    equipment: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = ""

    @validator("sex", "activity_level", "fitness_goal", pre=True)
    def lower_case(cls, v):
        return v.lower()