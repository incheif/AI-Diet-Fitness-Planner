from fastapi import FastAPI, HTTPException
from datetime import datetime
from backend.models import UserInput

from backend.utils import compute_bmr, activity_multiplier, adjust_for_goal, compute_macros, generate_dummy_weekly_plan

app = FastAPI(title="AI Diet & Workout Planner")

@app.post("/generate_plan")
async def generate_plan(user: UserInput):
    # Validate input
    if user.age <= 0 or user.height_cm <= 0 or user.weight_kg <= 0:
        raise HTTPException(status_code=400, detail="Invalid numeric values")

    # Step 1: BMR
    bmr = compute_bmr(user.sex, user.weight_kg, user.height_cm, user.age)

    # Step 2: TDEE
    tdee = bmr * activity_multiplier(user.activity_level)

    # Step 3: Adjust calories for goal
    calorie_target = adjust_for_goal(tdee, user.fitness_goal)

    # Step 4: Compute macros
    macros = compute_macros(user.weight_kg, calorie_target, user.fitness_goal)

    # Step 5: Generate dummy plan
    plan = generate_dummy_weekly_plan()

    return {
        "created_at": datetime.utcnow().isoformat(),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calorie_target": round(calorie_target),
        "macros": macros,
        "plan": plan
    }
