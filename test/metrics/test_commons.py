import coclico.metrics.commons
import pytest


affine_func_data = [
    ((1, 3), (2, 1), [(0, 3), (1, 3), (1.5, 2), (1.75, 1.5), (2, 1), (3, 1)]),
    ((1, 0), (5, 2), [(-1, 0), (1, 0), (2, 0.5), (4, 1.5), (5, 2), (12, 2)]),
]


@pytest.mark.parametrize("coord_min,coord_max,queries", affine_func_data)
def test_bounded_affine_function(coord_min, coord_max, queries):
    for x_query, y_query in queries:
        assert coclico.metrics.commons.bounded_affine_function(coord_min, coord_max, x_query) == y_query
