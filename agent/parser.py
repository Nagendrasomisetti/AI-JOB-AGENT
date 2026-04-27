import json

def extract_json(text: str):
    """
    Extract JSON from LLM response safely
    """

    try:
        # Try direct parse
        return json.loads(text)
    except:
        pass

    # Try to extract JSON block
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except:
        raise ValueError("Invalid JSON format from LLM")


def validate_structure(data: dict):
    if "goal" not in data:
        raise ValueError("Missing goal")

    if "steps" not in data:
        raise ValueError("Missing steps")

    if not isinstance(data["steps"], list):
        raise ValueError("Steps must be a list")

    for step in data["steps"]:
        if "action" not in step or "input" not in step:
            raise ValueError("Invalid step format")

    return True

