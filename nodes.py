from state import BMIState


def input_node(state: BMIState):
    weight = float(input("Enter weight (kg): "))
    height = float(input("Enter height (m): "))

    return {
        "weight": weight,
        "height": height
    }

def validate_bmi_node(state):
    height = state["height"]

    if height <= 0:
        print("\nInvalid height!")
        return {
            "is_valid": False
        }

    return {
        "is_valid": True
    }

def validation_router(state):
    if state["is_valid"]:
        return "valid"

    return "invalid"

def calculate_bmi_node(state: BMIState):
    bmi = state["weight"] / (state["height"] ** 2)

    return {
        "bmi": round(bmi, 2)
    }

def result_node(state: BMIState):
    print(f"\nBMI: {state['bmi']}")
    return {}


def underweight_node(state: BMIState):
    print("\nAdvice:")
    print("Increase calorie intake and strength training.")

    return {}


def normal_node(state: BMIState):
    print("\nAdvice:")
    print("Maintain your healthy lifestyle.")

    return {}


def overweight_node(state: BMIState):
    print("\nAdvice:")
    print("Focus on exercise and balanced nutrition.")

    return {}

def bmi_router(state: BMIState):
    bmi = state["bmi"]
    print(f"\nYour BMI is: {bmi}")

    if bmi < 18.5:
        return "underweight"

    elif bmi < 25:
        return "normal"

    else:
        return "overweight"

