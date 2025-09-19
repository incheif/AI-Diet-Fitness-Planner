# main.py
from fastapi import FastAPI, HTTPException
from datetime import datetime
from backend.models import UserInput
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from backend.utils import (
    compute_bmr, activity_multiplier, adjust_for_goal, compute_macros,
    generate_diet_plan, generate_workout_plan, combine_plans
)

app = FastAPI(title="AI Diet & Workout Planner")

@app.post("/generate_plan")
async def generate_plan(user: UserInput):
    # Validate input
    if user.age <= 0 or user.height_cm <= 0 or user.weight_kg <= 0 or user.workout_days_per_week < 0:
        raise HTTPException(status_code=400, detail="Invalid numeric values")
    if user.sex.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Sex must be 'male' or 'female'")
    if user.activity_level.lower() not in ["sedentary", "light", "moderate", "active", "very_active"]:
        raise HTTPException(status_code=400, detail="Invalid activity level")
    if user.fitness_goal.lower() not in ["lose", "maintain", "gain"]:
        raise HTTPException(status_code=400, detail="Invalid fitness goal")

    user_data = user.dict()  # Convert to dict for easier passing
    user_data["calorie_target"] = None  # Will be set later

    try:
        # Step 1: BMR
        bmr = compute_bmr(user.sex, user.weight_kg, user.height_cm, user.age)

        # Step 2: TDEE
        tdee = bmr * activity_multiplier(user.activity_level)

        # Step 3: Adjust calories for goal
        calorie_target = adjust_for_goal(tdee, user.fitness_goal)
        user_data["calorie_target"] = round(calorie_target)

        # Step 4: Compute macros
        macros = compute_macros(user.weight_kg, calorie_target, user.fitness_goal)

        # Step 5: Generate AI plans with three LLM calls
        logger.info("Generating diet plan...")
        diet_plan = generate_diet_plan(user_data, macros)
        logger.info("Generating workout plan...")
        workout_plan = generate_workout_plan(user_data)
        logger.info("Combining plans...")
        combined_plan = combine_plans(diet_plan, workout_plan, user_data)

        return {
            "created_at": datetime.utcnow().isoformat(),
            "bmr": round(bmr),
            "tdee": round(tdee),
            "calorie_target": round(calorie_target),
            "macros": macros,
            "plan": combined_plan
        }
    except ValueError as e:
        logger.error(f"Error generating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")