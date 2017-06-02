from __future__ import absolute_import, division, print_function
from isis_imaging import helper as h


def timed_import(config):
    """
    Wraps the importing function in a timer.
    This function should not be used from the filters as it will add a lot of clutter to the stdout.

    :param config: A ReconstructionConfig with all the necessary parameters to run a reconstruction.

    :return: the imported tool
    """

    h.pstart("Importing tool " + config.func.tool)
    tool = do_importing(config.func.tool, config.func.algorithm)
    h.pstop("Tool loaded.")
    return tool


def do_importing(tool, alg='fbp'):
    """
    The main importing function. Does the decision on which tool to import based on the input.

    :param tool: The name of the tool to be imported
    :param alg: The algorithm that will be used. This is only done the enusre that it is actually supported.
        If no algorithm is provided, the default is 'fbp', because it's supported by all tools.
    :return: the tool reference
    """
    if not isinstance(tool, str):
        raise ValueError(
            "The name of a reconstruction tool is required as a string. Got: {0}".
            format(tool))
    if 'tomopy' == tool:
        from isis_imaging.core.tools.tomopy_tool import TomoPyTool
        TomoPyTool.check_algorithm_compatibility(alg)
        imported_tool = TomoPyTool()

    elif 'astra' == tool:
        from isis_imaging.core.tools.astra_tool import AstraTool
        AstraTool.check_algorithm_compatibility(alg)
        imported_tool = AstraTool()
    else:
        raise ValueError("Tried to import unknown tool: {0}".format(tool))

    return imported_tool
