from state import BMIState


def input_node(state: BMIState):
    weight = float(input("Enter weight (kg): "))
    height = float(input("Enter height (m): "))

    return {
        "weight": weight,
        "height": height
    }


def calculate_bmi_node(state: BMIState):
    bmi = state["weight"] / (state["height"] ** 2)

    return {
        "bmi": round(bmi, 2)
    }


def result_node(state: BMIState):
    bmi = state["bmi"]

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal Weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    print("\n===== BMI RESULT =====")
    print(f"BMI: {bmi}")
    print(f"Category: {category}")

    return {
        "category": category
    }