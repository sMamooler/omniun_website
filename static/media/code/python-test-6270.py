import numpy as np
from numpy.testing import assert_array_equal

def test_keypoints_censure():
    mode = 'star'
    rescale = 0
    img = 25
    expected_keypoints = np.array([[23, 27], [29, 89], [30, 86], [107, 59], [109, 64], [111, 67], [113, 70]])
    expected_scales = np.array([3, 2, 4, 2, 5, 3, 2])
    assert_array_equal(expected_keypoints, detector.keypoints)
    assert_array_equal(expected_scales, detector.scales)
