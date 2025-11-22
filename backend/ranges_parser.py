import os
from typing import Dict, List

CATEGORY_ORDER = [
    "Extremely_Low",
    "Low",
    "Moderate",
    "High",
    "Extremely_High",
]

def parse_ranges(md_path: str) -> Dict[str, Dict[str, float]]:
    """Parse ranges.md extracting thresholds.

    Expected pattern:
    ## variable_name\n
    Category: value\n repeated.
    Stops at blank line or next ##.
    Returns {variable: {category: threshold_float}}.
    """
    if not os.path.isfile(md_path):
        return {}
    ranges: Dict[str, Dict[str, float]] = {}
    current_var = None
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("## "):
                current_var = line[3:].strip()
                ranges[current_var] = {}
                continue
            if current_var and ":" in line:
                try:
                    cat, val = line.split(":", 1)
                    cat = cat.strip()
                    val = val.strip().split()[0]  # remove trailing tokens
                    ranges[current_var][cat] = float(val)
                except Exception:
                    continue
    return ranges

def determine_category(value: float, thresholds: Dict[str, float]) -> str:
    """Given a numeric value and thresholds mapping category->limit, return category."""
    # Ensure iteration in defined order
    for cat in CATEGORY_ORDER[:-1]:  # last handled by else
        limit = thresholds.get(cat)
        if limit is not None and value <= limit:
            return cat
    return CATEGORY_ORDER[-1]

def category_index(category: str) -> int:
    try:
        return CATEGORY_ORDER.index(category)
    except ValueError:
        return 2  # default Moderate

def distance_score(actual_cat: str, target_cat: str, weight: float) -> float:
    """Weight * (1 - ordinal_distance/max_distance)."""
    max_dist = len(CATEGORY_ORDER) - 1  # 4
    d = abs(category_index(actual_cat) - category_index(target_cat))
    return weight * (1 - d / max_dist)

SPANISH_CATEGORY = {
    "Extremely_Low": "Extremadamente Bajo",
    "Low": "Bajo",
    "Moderate": "Moderado",
    "High": "Alto",
    "Extremely_High": "Extremadamente Alto",
}

def category_spanish(cat: str) -> str:
    return SPANISH_CATEGORY.get(cat, cat)
