def compute_bmr(sex: str, weight: float, height: float, age: int) -> float:
    """Mifflin–St Jeor formula"""
    if sex.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return bmr

def activity_multiplier(level: str) -> float:
    """TDEE multipliers based on activity level"""
    mapping = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return mapping.get(level.lower(), 1.2)

def adjust_for_goal(tdee: float, goal: str) -> float:
    """Adjust calories based on fitness goal"""
    goal = goal.lower()
    if goal == "lose":
        return tdee - 500
    elif goal == "gain":
        return tdee + 300
    return tdee  # maintain

def compute_macros(weight: float, calories: float, goal: str) -> dict:
    """Compute protein, fat, carbs"""
    if goal.lower() == "lose":
        protein_g = weight * 1.8
        fat_g = (calories * 0.25) / 9
    else:  # maintain/gain
        protein_g = weight * 1.5
        fat_g = (calories * 0.3) / 9
    carbs_g = (calories - (protein_g*4 + fat_g*9)) / 4
    return {
        "protein_g": round(protein_g),
        "fat_g": round(fat_g),
        "carbs_g": round(carbs_g)
    }

def generate_dummy_weekly_plan() -> dict:
    """Return a dummy weekly plan"""
    days = []
    for i in range(7):
        days.append({
            "day": f"Day {i+1}",
            "meals": [
                {"name": "Breakfast", "calories": 400},
                {"name": "Lunch", "calories": 600},
                {"name": "Dinner", "calories": 500},
                {"name": "Snack", "calories": 200},
            ],
            "workout": {"type": "Full Body", "duration_min": 45, "exercises": ["Squats", "Push-ups", "Plank"]},
        })
    return {
        "summary": "Dummy 7-day plan",
        "days": days,
        "grocery_list": ["eggs", "chicken", "rice", "vegetables", "fruits"]
    }
