from __future__ import (absolute_import, division, print_function)
from mantidimaging import helper as h
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.parallel import shared_mem as psm
import scipy.ndimage as scipy_ndimage


def _cli_register(parser):
    default_size = None
    default_order = 0
    parser.add_argument(
        "--gaussian-size",
        required=False,
        type=float,
        default=default_size,
        help="Apply gaussian filter (2d) on reconstructed volume with the "
        "given window size.")

    parser.add_argument(
        "--gaussian-mode",
        type=str,
        required=False,
        default=modes()[0],
        choices=modes(),
        help="Default: %(default)s\nMode of gaussian filter which determines "
        "how the array borders are handled.(pre processing).")

    parser.add_argument(
        "--gaussian-order",
        required=False,
        type=int,
        default=default_order,
        help="Default: %(default)d\nThe order of the filter along each axis "
        "is given as a sequence of integers, \n"
        "or as a single number. An order of 0 corresponds to "
        "convolution with a Gaussian kernel.\n"
        "An order of 1, 2, or 3 corresponds to convolution "
        "with the first, second or third derivatives of a Gaussian.\n"
        "Higher order derivatives are not implemented.")

    return parser


def modes():
    return ['reflect', 'constant', 'nearest', 'mirror', 'wrap']


def execute(data, size, mode, order, cores=None, chunksize=None):
    """
    Execute the Gaussian filter.

    :param data: Input data as a 3D numpy.ndarray

    :param size: Size of the kernel

    :param mode: The mode with which to handle the endges.
                 One of [reflect, constant, nearest, mirror, wrap].

    :param order: The order of the filter along each axis is given as a
                  sequence of integers, or as a single number.
                  An order of 0 corresponds to convolution with a Gaussian kernel.
                  An order of 1, 2, or 3 corresponds to convolution
                  with the first, second or third derivatives of a Gaussian.
                  Higher order derivatives are not implemented

    :param cores: The number of cores that will be used to process the data.

    :param chunksize: The number of chunks that each worker will receive.

    :return: The processed 3D numpy.ndarray

    Example command line:

    mantidimaging -i /some/data --gaussian-size 3

    mantidimaging -i /some/data --gaussian-size 3
                   --gaussian-mode 'nearest'

    mantidimaging -i /some/data --gaussian-size 3
                   --gaussian-mode 'nearest' --gaussian-order 1

    [Full ref](https://docs.scipy.org/doc/scipy-0.16.1/reference/generated/scipy.ndimage.filters.gaussian_filter.html)
    """
    h.check_data_stack(data)

    if size and size > 1:
        if pu.multiprocessing_available():
            data = _execute_par(data, size, mode, order, cores, chunksize)
        else:
            data = _execute_seq(data, size, mode, order)

    h.check_data_stack(data)
    return data


def _execute_seq(data, size, mode, order):
    # Sequential CPU version of the Gaussian filter
    h.pstart("Starting  gaussian filter, with pixel data type: {0}, "
             "filter size/width: {1}.".format(data.dtype, size))

    h.prog_init(data.shape[0], "Gaussian")
    for idx in range(0, data.shape[0]):
        data[idx] = scipy_ndimage.gaussian_filter(
            data[idx], size, mode=mode, order=order)
        h.prog_update()

    h.prog_close()

    h.pstop("Finished  gaussian filter, with pixel data type: {0}, "
            "filter size/width: {1}.".format(data.dtype, size))

    return data


def _execute_par(data, size, mode, order, cores=None, chunksize=None):
    # Parallel CPU version of the Gaussian filter
    # create the partial function to forward the parameters
    f = psm.create_partial(
        scipy_ndimage.gaussian_filter,
        fwd_func=psm.return_fwd_func,
        sigma=size,
        mode=mode,
        order=order)

    h.pstart("Starting PARALLEL gaussian filter, with pixel data type: {0}, "
             "filter size/width: {1}.".format(data.dtype, size))
    data = psm.execute(data, f, cores, chunksize, "Gaussian")

    h.pstop("Finished  gaussian filter, with pixel data type: {0}, "
            "filter size/width: {1}.".format(data.dtype, size))

    return data