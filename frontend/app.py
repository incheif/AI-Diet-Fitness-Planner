import streamlit as st
import requests
import json
import pandas as pd

# Backend URL
BACKEND_URL = "http://127.0.0.1:8000/generate_plan"

st.title("🥗 NutriFitAI - Personalized Diet & Workout Planner")
st.write("Enter your details to generate a tailored weekly diet and workout plan powered by AI.")

with st.form("user_input_form"):
    st.subheader("👤 User Information")
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Your Name (optional)")
        age = st.number_input("Age", min_value=10, max_value=100, step=1, value=30)
        sex = st.selectbox("Sex", ["Male", "Female"], help="Select biological sex for BMR calculation")
        height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.1, value=170.0)
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, step=0.1, value=70.0)

    with col2:
        activity_level = st.selectbox(
            "Activity Level",
            ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
            help="Sedentary: little to no exercise; Light: light exercise 1-3 days/week; Moderate: moderate exercise 3-5 days/week; Active: hard exercise 6-7 days/week; Very Active: very hard exercise or physical job"
        )
        fitness_goal = st.selectbox(
            "Fitness Goal",
            ["Lose", "Maintain", "Gain"],
            help="Lose: weight loss; Maintain: maintain current weight; Gain: muscle gain"
        )
        workout_days_per_week = st.slider(
            "Workout Days per Week", min_value=0, max_value=7, value=3,
            help="Number of days you plan to work out each week"
        )

    st.subheader("🍽️ Dietary Preferences")
    dietary_preferences = st.multiselect(
        "Dietary Preferences",
        ["Vegetarian", "Vegan", "Non-Vegetarian", "Keto", "Paleo", "Balanced"],
        help="Select all that apply"
    )
    restrictions = st.multiselect(
        "Dietary Restrictions",
        ["Nuts", "Dairy", "Gluten", "Soy", "Shellfish", "Egg"],
        help="Select any allergies or foods to avoid"
    )

    st.subheader("🏋️ Workout Preferences")
    equipment = st.multiselect(
        "Available Equipment",
        ["Dumbbells", "Resistance Bands", "Barbell", "Treadmill", "Yoga Mat", "None"],
        help="Select all available equipment"
    )
    notes = st.text_area(
        "Additional Notes",
        placeholder="Mention any injuries, lifestyle factors, or specific preferences (e.g., prefer home workouts, avoid running)"
    )

    submitted = st.form_submit_button("Generate Plan")

if submitted:
    # Match the backend model
    user_data = {
        "name": name if name else None,
        "age": age,
        "sex": sex.lower(),
        "height_cm": float(height),
        "weight_kg": float(weight),
        "activity_level": activity_level.lower(),
        "fitness_goal": fitness_goal.lower(),
        "dietary_preferences": [pref.lower() for pref in dietary_preferences],
        "restrictions": [res.lower() for res in restrictions],
        "workout_days_per_week": workout_days_per_week,
        "equipment": [eq.lower() for eq in equipment],
        "notes": notes
    }

    # Send to FastAPI without API key header (handled by backend .env)
    try:
        with st.spinner("Generating your personalized plan..."):
            response = requests.post(BACKEND_URL, json=user_data, timeout=30)

        if response.status_code == 200:
            plan = response.json()
            st.success("✅ Your Personalized Weekly Plan is Ready!")

            # Summary
            st.subheader("📊 Your Nutrition & Fitness Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Basal Metabolic Rate (BMR)", f"{plan['bmr']} kcal/day")
                st.metric("Total Daily Energy Expenditure (TDEE)", f"{plan['tdee']} kcal/day")
            with col2:
                st.metric("Daily Calorie Target", f"{plan['calorie_target']} kcal/day")

            st.subheader("🍽️ Macronutrient Breakdown")
            st.json(plan["macros"])

            # Diet Plan Table
            st.subheader("📅 Weekly Diet Plan")
            diet_data = {
                "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "Meals": [plan["plan"]["diet_plan"].get(day, "No plan for this day") for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
            }
            diet_df = pd.DataFrame(diet_data)
            st.table(diet_df)

            # Workout Plan Table
            st.subheader("💪 Weekly Workout Plan")
            workout_data = {
                "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "Workout": [plan["plan"]["workout_plan"].get(day, "Rest or no plan") for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
            }
            workout_df = pd.DataFrame(workout_data)
            st.table(workout_df)

            # Tips
            if "tips" in plan["plan"]:
                st.subheader("✨ Tips for Success")
                for tip in plan["plan"]["tips"]:
                    st.write(f"- {tip}")

        else:
            st.error(f"⚠️ Error from backend: {response.text}")
    except requests.exceptions.Timeout:
        st.error("⚠️ Request timed out. Please try again or check the backend server.")
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Could not connect to the backend server. Ensure it’s running at http://127.0.0.1:8000.")
    except Exception as e:
        st.error(f"⚠️ An error occurred: {str(e)}")