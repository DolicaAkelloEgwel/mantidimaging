from __future__ import (absolute_import, division, print_function)
import helper as h
from core.tools import importer


def cli_register(parser):
    parser.add_argument(
        "-log",
        "--pre-minus-log",
        required=False,
        action='store_true',
        default=False,
        help="Calculate the -log of the sample data.")

    return parser


def gui_register(par):
    raise NotImplementedError("GUI doesn't exist yet")


def execute(data, minus_log=True):
    """
    :param data: Sample data which is to be processed. Expected in radiograms
    :param minus_log: Default True
                      Specify whether to calculate minus log or just return.
    """
    if minus_log:
        # import early to check if tomopy is available
        tomopy = importer.do_importing('tomopy')
        h.pstart("Calculating -log on the sample data.")
        # this check prevents division by 0 errors from the minus_log
        data[data == 0] = 1e-6
        # the operation is done in place
        tomopy.prep.normalize.minus_log(data, out=data)
        h.pstop("Finished calculating -log on the sample data.")

    return data
