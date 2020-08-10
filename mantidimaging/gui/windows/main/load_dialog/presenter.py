import traceback
from enum import auto, Enum
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from mantidimaging.core.io.loader import read_in_shape
from mantidimaging.core.io.utility import get_file_extension, get_prefix, get_file_names
from mantidimaging.core.utility import size_calculator

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.load_dialog.view import MWLoadDialog
logger = getLogger(__name__)


class Notification(Enum):
    UPDATE = auto()
    UPDATE_EXPECTED_MEM_USAGE = auto()


class LoadPresenter:
    view: 'MWLoadDialog'

    def __init__(self, view: 'MWLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.last_shape = (0, 0, 0)
        self.dtype = '32'
        # Populate the size calculator result with initial values (zeros)
        self._update_expected_mem_usage()

    def notify(self, n: Notification):
        if n == Notification.UPDATE:
            self.do_update_dialogue()
        elif n == Notification.UPDATE_EXPECTED_MEM_USAGE:
            self.do_update_expected_memory_usage()

    def do_update_dialogue(self):
        """
        Updates the memory usage and the indices in the dialog.
        """
        select_file_successful = self.view.select_file(self.view.sample, "Sample")
        if not select_file_successful:
            return False

        self.view.sample.widget.setExpanded(True)
        
        sample_filename = self.view.sample.file()
        self.image_format = get_file_extension(sample_filename)

        filename = self.view.sample.path_text()
        dirname = self.view.sample.directory()
        try:
            self.last_shape, sinograms = read_in_shape(dirname, in_prefix=get_prefix(filename),
                                                       in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error("Failed to read file %s (%s)", sample_filename, e)
            self.view.show_error("Failed to read this file. See log for details.",
                                 traceback.format_exc())
            self.last_shape = (0, 0, 0)
            sinograms = False

        sample_dirname = Path(dirname)


        self.view.flat.path = self._find_images(sample_dirname, "Flat")
        self.view.dark.path = self._find_images(sample_dirname, "Dark")
        self.view.proj_180deg.path = self._find_180deg_proj(sample_dirname)
        self.view.sample_log.path = self._find_log(sample_dirname, self.view.sample.directory())
        self.view.flat_log.path = self._find_log(sample_dirname, self.view.flat.directory())

        self.view.images_are_sinograms.setChecked(sinograms)

        self.view.update_indices(self.view.sample, self.last_shape[0])
        self._update_expected_mem_usage()

    def _update_expected_mem_usage(self):
        start = self.view.index_start.value()
        end = self.view.index_end.value()
        increment = self.view.index_step.value()

        num_images = size_calculator.number_of_images_from_indices(start, end, increment)

        single_mem = size_calculator.to_MB(size_calculator.single_size(self.last_shape, axis=0), dtype='32')

        exp_mem = round(single_mem * num_images, 2)
        self.view.update_expected_mem_usage(num_images, self.last_shape, exp_mem)

    def _find_images(self, sample_dirname: Path, type: str) -> str:
        try:
            path_filenames = get_file_names(sample_dirname.absolute(), self.image_format, prefix=f"*{type}")
            return path_filenames[0]
        except RuntimeError:
            logger.info(f"Could not find {type} files in {sample_dirname.absolute()}")

        expected_folder_path = sample_dirname / ".." / f"{type}_After"
        try:
            path_filenames = get_file_names(expected_folder_path.absolute(), self.image_format)
            return path_filenames[0]
        except RuntimeError:
            logger.info(f"Could not find {type} files in {expected_folder_path.absolute()}")
            expected_folder_path = sample_dirname / ".." / f"{type}_Before"
            try:
                path_filenames = get_file_names(expected_folder_path.absolute(), self.image_format)
                return path_filenames[0]
            except RuntimeError:
                logger.info(f"Could not find {type} files in {expected_folder_path.absolute()}")

        return ""

    def do_update_expected_memory_usage(self):
        self._update_expected_mem_usage()

    def _find_180deg_proj(self, sample_dirname: Path):
        expected_path = sample_dirname / '..' / '180deg'
        try:
            return get_file_names(expected_path.absolute(), self.image_format)[0]
        except RuntimeError:
            logger.info(f"Could not find 180 degree projection in {expected_path}")
        return ""

    def _find_log(self, dirname: Path, log_name: str):
        expected_path = dirname / '..'
        try:
            return get_file_names(expected_path.absolute(), "txt", prefix=log_name)[0]
        except RuntimeError:
            logger.info(f"Could not find a log file for {log_name} in {dirname}")
        return ""