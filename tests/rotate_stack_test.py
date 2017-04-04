from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

import helper as h
from core.filters import rotate_stack
from tests import test_helper as th


class RotateStackTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RotateStackTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        # only works on square images
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))

        # empty params
        result = rotate_stack.execute(images, None)[0]
        npt.assert_equal(result, control)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        th.switch_mp_off()
        self.do_execute()
        th.switch_mp_on()

    def do_execute(self):
        # only works on square images
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))

        rotation = 1  # once clockwise
        images[:, 0, 0] = 42  # set all images at 0,0 to 42
        result = rotate_stack.execute(images, rotation)[0]
        w = result.shape[2]
        npt.assert_equal(result[:, 0, w - 1], 42.0)

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
        # only works on square images
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))
        rotation = 1  # once clockwise
        images[:, 0, 0] = 42  # set all images at 0,0 to 42
        cached_memory = h.get_memory_usage_linux(kb=True)[0]
        result = rotate_stack.execute(images, rotation)[0]
        w = result.shape[2]
        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        npt.assert_equal(result[:, 0, w - 1], 42.0)


if __name__ == '__main__':
    unittest.main()
