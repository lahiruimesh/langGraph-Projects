from typing import TypedDict


class BMIState(TypedDict):
    weight: float
    height: float
    bmi: float
    category: str
    is_valid: bool