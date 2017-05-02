from __future__ import (absolute_import, division, print_function)
from core.tools.abstract_tool import AbstractTool
import helper as h


class AstraTool(AbstractTool):
    """
    Uses TomoPy's integration of Astra
    """

    @staticmethod
    def tool_supported_methods():
        return [
            'FP', 'FP_CUDA', 'BP', 'BP_CUDA', 'FBP', 'FBP_CUDA', 'SIRT',
            'SIRT_CUDA', 'SART', 'SART_CUDA', 'CGLS', 'CGLS_CUDA'
        ]

    @staticmethod
    def check_algorithm_compatibility(algorithm):
        # get full caps, because all the names in ASTRA are in FULL CAPS
        ALGORITHM = algorithm.upper()

        if ALGORITHM not in AstraTool.tool_supported_methods():
            raise ValueError(
                "The selected algorithm {0} is not supported by Astra.".format(
                    ALGORITHM))

    def __init__(self):
        AbstractTool.__init__(self)

        # we import tomopy so that we can use Astra through TomoPy's
        # implementation
        self._tomopy = self.import_self()

    def import_self(self):
        # use Astra through TomoPy
        from core.tools.tomopy_tool import TomoPyTool
        t = TomoPyTool()
        return t.import_self()

    @staticmethod
    def _import_astra():
        try:
            import astra
        except ImportError as exc:
            raise ImportError(
                "Cannot find and import the astra toolbox package: {0}".format(
                    exc))

        min_astra_version = 1.8
        astra_version = astra.__version__
        if isinstance(astra_version,
                      float) and astra_version >= min_astra_version:
            print("Imported astra successfully. Version: {0}".format(
                astra_version))
        else:
            raise RuntimeError(
                "Could not find the required version of astra. Found version: {0}".
                format(astra_version))

        print("Astra using CUDA: {0}".format(astra.astra.use_cuda()))
        return astra

    def run_reconstruct(self, data, config, proj_angles=None, **kwargs):
        """
        Run a reconstruction with TomoPy's ASTRA integration, using the CPU and GPU algorithms they provide.
        TODO This reconstruction function does NOT fully support the full range of options that are available for
         each algorithm in Astra.

        Information about how to use Astra through TomoPy is available at:
        http://tomopy.readthedocs.io/en/latest/ipynb/astra.html

        More information about the ASTRA Reconstruction parameters is available at:
        http://www.astra-toolbox.com/docs/proj2d.html
        http://www.astra-toolbox.com/docs/algs/index.html

        :param sample: The sample image data as a 3D numpy.ndarray
        :param config: A ReconstructionConfig with all the necessary parameters to run a reconstruction.
        :param proj_angles: The projection angle for each slice
        :param kwargs: Any keyword arguments will be forwarded to the TomoPy reconstruction function
        :return: The reconstructed volume
        """

        import tomorec.tool_imports as tti
        astra = tti.import_tomo_tool('astra')

        plow = (data.shape[2] - cor * 2)
        phigh = 0

        proj_geom = astra.create_proj_geom('parallel3d', .0, 1.0,
                                           data.shape[1], sinograms.shape[2],
                                           proj_angles)
        sinogram_id = astra.data3d.create('-sino', proj_geom, sinograms)

        vol_geom = astra.create_vol_geom(data.shape[1], sinograms.shape[2],
                                         data.shape[1])
        recon_id = astra.data3d.create('-vol', vol_geom)
        alg_cfg = astra.astra_dict(alg_cfg.algorithm)
        alg_cfg['ReconstructionDataId'] = recon_id
        alg_cfg['ProjectionDataId'] = sinogram_id
        alg_id = astra.algorithm.create(alg_cfg)

        number_of_iters = 100
        astra.algorithm.run(alg_id, number_of_iters)
        recon = astra.data3d.get(recon_id)

        astra.algorithm.delete(alg_id)
        astra.data3d.delete(recon_id)
        astra.data3d.delete(sinogram_id)

        return recon
