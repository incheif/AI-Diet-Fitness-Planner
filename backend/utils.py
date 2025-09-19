# utils.py
import requests
from typing import Dict, Any, List
import json
import os
from dotenv import load_dotenv
import logging
import re
from time import sleep
from requests.exceptions import HTTPError

# Configure logging
logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

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

def clean_json_response(response: str) -> str:
    """Strip markdown code blocks and extra text from LLM response."""
    # Remove ```json
    response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response, flags=re.MULTILINE)
    # Remove any leading/trailing whitespace or newlines
    response = response.strip()
    # Log cleaned response for debugging
    logger.debug(f"Cleaned JSON response: {response[:100]}...")  # Truncate for brevity
    return response

def call_llm(prompt: str, model: str = "gemini-1.5-flash", retries: int = 3, max_tokens: int = 2000) -> str:
    """Call Google's Gemini API with retries and higher token limit."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=data, params={"key": GEMINI_API_KEY})
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"Gemini API response: {response_data}")
            if "candidates" not in response_data or not response_data["candidates"]:
                raise ValueError("No candidates in Gemini API response")
            if response_data.get("finishReason") == "MAX_TOKENS" and attempt < retries - 1:
                logger.warning("Response truncated due to token limit, retrying with higher limit...")
                data["generationConfig"]["maxOutputTokens"] = max_tokens + 1000
                continue
            return clean_json_response(response_data["candidates"][0]["content"]["parts"][0]["text"])
        except HTTPError as e:
            if response.status_code == 429 and attempt < retries - 1:
                logger.warning(f"Rate limit hit, retrying in {2 ** attempt} seconds...")
                sleep(2 ** attempt)
                continue
            logger.error(f"Gemini API request failed: {str(e)}")
            raise ValueError(f"LLM API call failed: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {str(e)}")
            raise ValueError(f"LLM API call failed: {str(e)}")

def validate_diet_plan(plan: Dict[str, str], dietary_preferences: List[str], restrictions: List[str]) -> None:
    """Validate diet plan for compliance with preferences and restrictions."""
    non_veg_terms = ["chicken", "beef", "fish", "salmon", "tuna", "turkey", "steak", "meatballs"]
    nut_terms = ["nut", "peanut", "almond", "cashew", "walnut", "hazelnut", "pecan", "pistachio"]
    is_vegetarian = "vegetarian" in [pref.lower() for pref in dietary_preferences]
    no_nuts = "no nuts" in [restr.lower() for restr in restrictions]

    for day, meals in plan.items():
        meals_lower = meals.lower()
        if is_vegetarian and any(term in meals_lower for term in non_veg_terms):
            raise ValueError(f"Non-vegetarian item found in {day} for vegetarian diet: {meals}")
        if no_nuts and any(term in meals_lower for term in nut_terms):
            raise ValueError(f"Nut-containing item found in {day} despite no-nuts restriction: {meals}")

def generate_diet_plan(user_data: Dict[str, Any], macros: Dict[str, int]) -> Dict[str, str]:
    """Use LLM to generate a detailed diet plan with strict adherence to preferences."""
    dietary_prefs = ', '.join(user_data['dietary_preferences']) or "none"
    restrictions = ', '.join(user_data['restrictions']) or "none"
    prompt = f"""
    You are a nutrition expert. Generate a detailed 7-day diet plan for a {user_data['sex']} aged {user_data['age']}, weight {user_data['weight_kg']}kg, height {user_data['height_cm']}cm.
    Activity level: {user_data['activity_level']}, Fitness goal: {user_data['fitness_goal']}.
    Dietary preferences: {dietary_prefs}. Strictly adhere to these preferences (e.g., vegetarian means NO meat, fish, poultry, or animal-derived products like gelatin).
    Restrictions: {restrictions}. Do not include restricted foods (e.g., NO nuts or nut-derived products like peanut butter if 'no nuts' is specified).
    Target calories: {user_data['calorie_target']}, Macros: Protein {macros['protein_g']}g, Fat {macros['fat_g']}g, Carbs {macros['carbs_g']}g.
    Make it realistic, varied, and include meal breakdowns (breakfast, lunch, dinner, snacks) with approximate calorie counts per meal.
    **Important**: Previous responses included non-vegetarian items (e.g., chicken, salmon) and nuts (e.g., peanut butter) despite vegetarian and no-nuts restrictions. This is incorrect. Strictly follow the preferences and restrictions provided.
    Output ONLY a valid JSON object: {{"Monday": "Breakfast: description (calories), Lunch: description (calories), Dinner: description (calories), Snacks: description (calories)", ..., "Sunday": "..."}}.
    Do not include any other text, explanations, or markdown (e.g., ```json). Return the JSON object directly.
    """
    response = call_llm(prompt, max_tokens=2000)
    try:
        parsed = json.loads(response)
        if not isinstance(parsed, dict) or not all(day in parsed for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            raise ValueError("Invalid diet plan structure")
        validate_diet_plan(parsed, user_data['dietary_preferences'], user_data['restrictions'])
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from LLM for diet plan: {response}")
        raise ValueError(f"Invalid JSON response from LLM for diet plan: {str(e)}")

def generate_workout_plan(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Use LLM to generate a detailed workout plan."""
    prompt = f"""
    You are a fitness expert. Generate a detailed 7-day workout plan for a {user_data['sex']} aged {user_data['age']}, weight {user_data['weight_kg']}kg, height {user_data['height_cm']}cm.
    Activity level: {user_data['activity_level']}, Fitness goal: {user_data['fitness_goal']}.
    Workout days per week: {user_data['workout_days_per_week']}.
    Available equipment: {', '.join(user_data['equipment'])}.
    Notes: {user_data['notes']}.
    Include warm-up, main exercises with sets/reps, cool-down. Tailor to goal (e.g., strength for gain, cardio for lose). For low-impact workouts, avoid high-intensity exercises if specified in notes.
    Output ONLY a valid JSON object: {{"Monday": "Warm-up: description, Main: description (sets/reps), Cool-down: description", ..., "Sunday": "..."}}.
    Do not include any other text, explanations, or markdown (e.g., ```json
    """
    response = call_llm(prompt, max_tokens=2000)
    try:
        parsed = json.loads(response)
        if not isinstance(parsed, dict) or not all(day in parsed for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
            raise ValueError("Invalid workout plan structure")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from LLM for workout plan: {response}")
        raise ValueError(f"Invalid JSON response from LLM for workout plan: {str(e)}")

def combine_plans(diet_plan: Dict[str, str], workout_plan: Dict[str, str], user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to combine and refine the diet and workout plans."""
    prompt = f"""
    You are a health and fitness expert. You have a diet plan: {json.dumps(diet_plan)}
    And a workout plan: {json.dumps(workout_plan)}
    For user: {json.dumps(user_data)}
    Combine them into a cohesive weekly plan. Adjust for synergy (e.g., higher protein on workout days, recovery meals post-workout).
    Strictly adhere to dietary preferences ({', '.join(user_data['dietary_preferences'])} or none) and restrictions ({', '.join(user_data['restrictions'])} or none).
    Add tips for tracking progress, hydration, and sleep.
    Output ONLY a valid JSON object with keys 'diet_plan', 'workout_plan', 'tips'.
    'diet_plan' and 'workout_plan' must be dictionaries with days (Monday to Sunday) as keys and strings as values.
    'tips' must be a list of strings.
    Do not include any other text, explanations, or markdown (e.g., ```json). Return the JSON object directly.
    """
    response = call_llm(prompt, max_tokens=3000)  # Higher limit for combined plan
    try:
        parsed = json.loads(response)
        if not isinstance(parsed, dict) or not all(key in parsed for key in ["diet_plan", "workout_plan", "tips"]):
            raise ValueError("Invalid combined plan structure")
        validate_diet_plan(parsed["diet_plan"], user_data['dietary_preferences'], user_data['restrictions'])
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from LLM for combined plan: {response}")
        raise ValueError(f"Invalid JSON response from LLM for combined plan: {str(e)}")