import os

CATEGORY_ORDER = ["Extremely_Low", "Low", "Moderate", "High", "Extremely_High"]

_spanish_map = {
    "Extremely_Low": "Muy Bajo",
    "Low": "Bajo",
    "Moderate": "Moderado",
    "High": "Alto",
    "Extremely_High": "Muy Alto",
}

def parse_ranges(path: str):
    """Parses the ranges.md file to extract thresholds for each variable."""
    ranges = {}
    current_var = None
    
    if not os.path.exists(path):
        return ranges

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_var = line.replace("## ", "").strip()
                ranges[current_var] = {}
            elif current_var and ":" in line:
                parts = line.split(":")
                category = parts[0].strip()
                try:
                    # Extract number, ignoring comments like (>= High)
                    val_str = parts[1].split("(")[0].strip()
                    value = float(val_str)
                    ranges[current_var][category] = value
                except ValueError:
                    continue
    return ranges

def category_index(cat: str) -> int:
    try:
        return CATEGORY_ORDER.index(cat)
    except ValueError:
        return CATEGORY_ORDER.index("Moderate")

def category_spanish(cat: str) -> str:
    return _spanish_map.get(cat, cat)

def determine_category(value, thresholds):
    """Given a numeric value and thresholds dict produce a category."""
    if not thresholds:
        return "Moderate"
    
    # Thresholds in file are upper bounds for that category (approx)
    # Extremely_Low <= P10
    # Low <= P25
    # Moderate <= P50
    # High <= P75
    # Extremely_High > P75
    
    # We check in order
    if value <= thresholds.get("Extremely_Low", -float('inf')):
        return "Extremely_Low"
    if value <= thresholds.get("Low", -float('inf')):
        return "Low"
    if value <= thresholds.get("Moderate", -float('inf')):
        return "Moderate"
    if value <= thresholds.get("High", -float('inf')):
        return "High"
    
    return "Extremely_High"

def distance_score(actual_cat: str, target_cat: str, weight: float) -> float:
    """Simple distance scoring: full weight if exact match, else subtract ordinal distance.
    Minimum score 0.
    """
    diff = abs(category_index(actual_cat) - category_index(target_cat))
    # If weight is small (e.g. < 1), we assume it's a 0-1 scale and we shouldn't subtract integers.
    # But standard logic implies 1-5 scale.
    # Let's adapt: if weight <= 1, we treat it as percentage multiplier of a base score?
    # No, let's stick to the logic: Score = Weight - (Penalty * Diff)
    # If Weight is 5, Diff 1 -> 4.
    # If Weight is 0.7, Diff 1 -> 0.
    return max(0.0, weight - diff)
