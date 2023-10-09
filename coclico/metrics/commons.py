from typing import Tuple, List
from coclico.config import composed_class_separator


def split_composed_class(class_key: str) -> List[str]:
    """Split composed class key (separated by COMPOSED_CLASS_SEPARATOR) into its elementary classes.
    Example "3_4_5" becomes ["3", "4", "5"]
    Args:
        class_key (str): origin key

    Returns:
        List[str]: splitted keys
    """
    return class_key.split(composed_class_separator)


def bounded_affine_function(coordinates_min: Tuple, coordinates_max: Tuple, x_query: float) -> float:
    """Compute clamped affine function
               max ________ or ______min
              /                         \\
             /                           \\
    _____min/                             \\max________

    Args:
        coordinates_min (Tuple): (x, y) tuple for the first point with the lowest x value
        coordinates_max (Tuple): (x, y) tuple for the first point with the highest x value
        x_query (float): query value

    Returns:
        float: _description_
    """

    x_min, y_min = coordinates_min
    x_max, y_max = coordinates_max

    if x_query < x_min:
        y_query = y_min

    elif x_query > x_max:
        y_query = y_max

    else:
        # affine function y = a*x + b
        a = (y_max - y_min) / (x_max - x_min)
        b = y_min - a * x_min

        y_query = a * x_query + b

    return y_query
