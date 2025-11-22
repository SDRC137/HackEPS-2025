CATEGORY_ORDER = ["Extremely_Low", "Low", "Moderate", "High", "Extremely_High"]

_spanish_map = {
    "Extremely_Low": "Muy Bajo",
    "Low": "Bajo",
    "Moderate": "Moderado",
    "High": "Alto",
    "Extremely_High": "Muy Alto",
}

def parse_ranges(path: str):
    """Stub parser: returns empty thresholds dict.
    Expected real implementation to parse markdown with ranges per variable.
    """
    return {}

def category_index(cat: str) -> int:
    try:
        return CATEGORY_ORDER.index(cat)
    except ValueError:
        return CATEGORY_ORDER.index("Moderate")

def category_spanish(cat: str) -> str:
    return _spanish_map.get(cat, cat)

def determine_category(value, thresholds):
    """Given a numeric value and thresholds dict produce a category.
    Stub: returns Moderate always; extend with real threshold logic.
    """
    return "Moderate"

def distance_score(actual_cat: str, target_cat: str, weight: float) -> float:
    """Simple distance scoring: full weight if exact match, else subtract ordinal distance.
    Minimum score 0.
    """
    diff = abs(category_index(actual_cat) - category_index(target_cat))
    return max(0.0, weight - diff)
