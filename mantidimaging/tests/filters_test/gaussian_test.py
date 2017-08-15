from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from mantidimaging import helper as h
from mantidimaging.tests import test_helper as th
from mantidimaging.core.filters import gaussian


class GaussianTest(unittest.TestCase):
    """
    Surprisingly sequential Gaussian seems to outperform parallel Gaussian on very small data.
    This does not scale and parallel execution is always faster on any reasonably sized data (e.g. 143,512,512)
    """

    def __init__(self, *args, **kwargs):
        super(GaussianTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = None
        mode = None
        order = None
        result = gaussian.execute(images, size, mode, order)
        npt.assert_equal(result, control)

    def test_executed_parallel(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1
        result = gaussian.execute(images, size, mode, order)
        th.assert_not_equals(result, control)

    def test_executed_no_helper_parallel(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1
        result = gaussian.execute(images, size, mode, order)
        th.assert_not_equals(result, control)

    def test_executed_no_helper_seq(self):
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1

        th.switch_mp_off()
        result = gaussian.execute(images, size, mode, order)
        th.switch_mp_on()

        th.assert_not_equals(result, control)

    def test_memory_change_acceptable(self):
        """
        Expected behaviour for the filter is to be done in place
        without using more memory.
        In reality the memory is increased by about 40MB (4 April 2017),
        but this could change in the future.
        The reason why a 10% window is given on the expected size is
        to account for any library imports that may happen.
        This will still capture if the data is doubled, which is the main goal.
        """
        images, control = th.gen_img_shared_array_and_copy()

        size = 3
        mode = 'reflect'
        order = 1
        cached_memory = h.get_memory_usage_linux(kb=True)[0]
        result = gaussian.execute(images, size, mode, order)
        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        th.assert_not_equals(result, control)


if __name__ == '__main__':
    unittest.main()