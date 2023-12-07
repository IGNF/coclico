import numpy as np
import pytest

import coclico.metrics.commons

affine_func_data = [
    ((1, 3), (2, 1), np.array([0, 1, 1.5, 1.75, 2, 3]), np.array([3, 3, 2, 1.5, 1, 1])),
    ((1, 0), (5, 2), np.array([-1, 1, 2, 4, 5, 12]), np.array([0, 0, 0.5, 1.5, 2, 2])),
]


@pytest.mark.parametrize("coord_min,coord_max,x_query,y_query", affine_func_data)
def test_bounded_affine_function(coord_min, coord_max, x_query, y_query):
    assert np.all(coclico.metrics.commons.bounded_affine_function(coord_min, coord_max, x_query) == y_query)
