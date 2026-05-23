import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger("AIJobAgent.Parser")

def extract_json(text: str) -> Dict[str, Any]:
    """
    Safely parses JSON from LLM outputs, stripping Markdown code blocks 
    and isolating JSON braces from surrounding conversation.
    
    Args:
        text (str): Raw string output from LLM.
        
    Returns:
        Dict: Parsed JSON object.
    """
    cleaned_text = text.strip()
    
    # 1. Strip standard markdown wrappers if present
    if cleaned_text.startswith("```"):
        # Match ```json <content> ``` or ``` <content> ```
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(1).strip()

    # 2. Direct parsing attempt
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    # 3. Scanning fallbacks: slice between first '{' and last '}'
    try:
        start_idx = cleaned_text.find("{")
        end_idx = cleaned_text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_slice = cleaned_text[start_idx:end_idx + 1]
            return json.loads(json_slice)
    except Exception as e:
        logger.debug(f"Slice parsing fallback failed: {e}")
        
    raise ValueError("Failed to extract structurally valid JSON from LLM response.")


def validate_structure(data: dict) -> bool:
    """
    Enforces operational schema rules on the generated agent execution plan.
    """
    if not isinstance(data, dict):
        raise ValueError("Root element of plan must be a JSON object.")

    if "goal" not in data or not data["goal"]:
        raise ValueError("Schema violation: Missing or empty 'goal' field.")

    if "steps" not in data:
        raise ValueError("Schema violation: Missing 'steps' list.")

    if not isinstance(data["steps"], list):
        raise ValueError("Schema violation: 'steps' must be a JSON array.")

    for idx, step in enumerate(data["steps"]):
        if not isinstance(step, dict):
            raise ValueError(f"Schema violation: Step at index {idx} is not an object.")
        if "action" not in step or not step["action"]:
            raise ValueError(f"Schema violation: Step {idx} is missing 'action' name.")
        if "input" not in step:
            raise ValueError(f"Schema violation: Step {idx} is missing 'input' field.")
            
    return True
