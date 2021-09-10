# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import enum
import traceback
from enum import auto, Enum
from logging import getLogger
from typing import TYPE_CHECKING, Optional, Union, Tuple

import h5py
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.data_containers import ProjectionAngles

if TYPE_CHECKING:
    from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class Notification(Enum):
    NEXUS_FILE_SELECTED = auto()


class ImageKeys(enum.Enum):
    Projections = 0
    FlatField = 1
    DarkField = 2


IMAGE_TITLE_MAP = {ImageKeys.Projections: "Projections", ImageKeys.FlatField: "Flat", ImageKeys.DarkField: "Dark"}
BEFORE_TITLE_MAP = {True: "Before", False: "After"}

TOMO_ENTRY = "tomo_entry"
DATA_PATH = "instrument/detector/data"
IMAGE_KEY_PATH = "instrument/detector/image_key"
ROTATION_ANGLE_PATH = "sample/rotation_angle"

THRESHOLD_180 = 0.5


def _missing_data_message(data_name: str) -> str:
    """
    Creates a message for logging when certain data is missing in the NeXus file.
    :param data_name: The name of the missing data.
    :return: A string telling the user that the data is missing.
    """
    return f"The NeXus file does not contain the required {data_name} data."


class NexusLoadPresenter:
    view: 'NexusLoadDialog'

    def __init__(self, view: 'NexusLoadDialog'):
        self.view = view
        self.nexus_file = None
        self.tomo_entry = None
        self.data = None
        self.tomo_path = ""
        self.image_key_dataset = None
        self.title = ""

        self.sample_array = None
        self.dark_before_array = None
        self.flat_before_array = None
        self.flat_after_array = None
        self.dark_after_array = None

    def notify(self, n: Notification):
        try:
            if n == Notification.NEXUS_FILE_SELECTED:
                self.scan_nexus_file()
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())

    def scan_nexus_file(self):
        """
        Try to open the NeXus file and display its contents on the view.
        """
        file_path = self.view.filePathLineEdit.text()
        with h5py.File(file_path, "r") as self.nexus_file:
            self.tomo_entry = self._look_for_nxtomo_entry()
            if self.tomo_entry is None:
                return

            self.data = self._look_for_tomo_data_and_update_view(DATA_PATH, 2)
            if self.data is None:
                return

            self.image_key_dataset = self._look_for_tomo_data_and_update_view(IMAGE_KEY_PATH, 0)
            if self.image_key_dataset is None:
                return

            rotation_angles = self._look_for_tomo_data_and_update_view(ROTATION_ANGLE_PATH, 1)
            if rotation_angles is None:
                pass
            else:
                self.projection_angles = rotation_angles[np.where(
                    self.image_key_dataset[...] == ImageKeys.Projections.value)]

            self._get_data_from_image_key()
            self.title = self._find_data_title()

    def _missing_data_error(self, field: str):
        """
        Create a missing data message and display it on the view.
        :param field: The name of the field that couldn't be found in the NeXus file.
        """
        error_msg = _missing_data_message(field)
        logger.error(error_msg)
        self.view.show_missing_data_error(error_msg)

    def _look_for_tomo_data_and_update_view(self, field: str,
                                            position: int) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Looks for the data in the NeXus file and adds information about it to the view if it's found.
        :param field: The name of the NeXus field.
        :param position: The position of the field information row in the view's QTreeWidget.
        :return: The h5py Group/Dataset if it could be found, None otherwise.
        """
        dataset = self._look_for_tomo_data(field)
        if dataset is None:
            self._missing_data_error(field)
            self.view.set_data_found(position, False, "", ())
            self.view.disable_ok_button()
        else:
            self.view.set_data_found(position, True, self.tomo_path + "/" + field, dataset.shape)
        return dataset

    def _look_for_nxtomo_entry(self) -> Optional[h5py.Group]:
        """
        Look for a tomo_entry field in the NeXus file. Generate an error and disable the view OK button if it can't be
        found.
        :return: The first tomo_entry group if one could be found, None otherwise.
        """
        assert self.nexus_file is not None
        for key in self.nexus_file.keys():
            if TOMO_ENTRY in self.nexus_file[key].keys():
                self.tomo_path = f"{key}/{TOMO_ENTRY}"
                return self.nexus_file[key][TOMO_ENTRY]

        self._missing_data_error(TOMO_ENTRY)
        self.view.disable_ok_button()
        return None

    def _look_for_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the tomo entry field.
        :param entry_path: The path in which the data is found.
        :return: The Nexus Group/Dataset if it exists, None otherwise.
        """
        assert self.tomo_entry is not None
        try:
            return self.tomo_entry[entry_path]
        except KeyError:
            return None

    def _get_data_from_image_key(self):
        """
        Looks for the projection and dark/flat before/after images and update the information on the view.
        """
        self.sample_array = self._get_images(ImageKeys.Projections)
        self.view.set_images_found(0, self.sample_array.size != 0, self.sample_array.shape)
        if self.sample_array.size == 0:
            self._missing_data_error("projection images")
            self.view.disable_ok_button()
            return
        self.view.set_projections_increment(self.sample_array.shape[0])

        self.flat_before_array = self._get_images(ImageKeys.FlatField, True)
        self.view.set_images_found(1, self.flat_before_array.size != 0, self.flat_before_array.shape)

        self.flat_after_array = self._get_images(ImageKeys.FlatField, False)
        self.view.set_images_found(2, self.flat_after_array.size != 0, self.flat_after_array.shape)

        self.dark_before_array = self._get_images(ImageKeys.DarkField, True)
        self.view.set_images_found(3, self.dark_before_array.size != 0, self.dark_before_array.shape)

        self.dark_after_array = self._get_images(ImageKeys.DarkField, False)
        self.view.set_images_found(4, self.dark_after_array.size != 0, self.dark_after_array.shape)

    def _get_images(self, image_key_number: ImageKeys, before: Optional[bool] = None) -> np.ndarray:
        """
        Retrieve images from the data based on an image key number.
        :param image_key_number: The image key number.
        :param before: True if the function should return before images, False if the function should return after
                       images. Ignored when getting projection images.
        :return: The set of images that correspond with a given image key.
        """
        assert self.image_key_dataset is not None
        assert self.data is not None
        if image_key_number is ImageKeys.Projections:
            indices = self.image_key_dataset[...] == image_key_number.value
        else:
            if before:
                indices = self.image_key_dataset[:self.image_key_dataset.size // 2] == image_key_number.value
            else:
                indices = self.image_key_dataset[:] == image_key_number.value
                indices[:self.image_key_dataset.size // 2] = False
        # Shouldn't have to use numpy.where but h5py doesn't allow indexing with bool arrays currently
        return self.data[np.where(indices)]

    def _find_data_title(self) -> str:
        """
        Find the title field in the tomo_entry.
        :return: The title if it was found, "NeXus Data" otherwise.
        """
        assert self.tomo_entry is not None
        try:
            return self.tomo_entry["title"][0].decode("UTF-8")
        except (KeyError, ValueError):
            logger.info("A valid title couldn't be found. Using 'NeXus Data' instead.")
            return "NeXus Data"

    def get_dataset(self) -> Tuple[Dataset, str]:
        """
        Create a Dataset and title using the arrays that have been retrieved from the NeXus file.
        :return: A tuple containing the Dataset and the data title string.
        """
        sample_images = self._create_sample_images()
        return Dataset(sample=sample_images,
                       flat_before=self._create_images_if_required(self.flat_before_array, "Flat Before"),
                       flat_after=self._create_images_if_required(self.flat_after_array, "Flat After"),
                       dark_before=self._create_images_if_required(self.dark_before_array, "Dark Before"),
                       dark_after=self._create_images_if_required(self.dark_after_array, "Dark After")), self.title

    def _create_sample_images(self):

        assert self.sample_array is not None

        # Find 180deg projection
        proj180deg = None
        diff = np.abs(self.projection_angles - 180)
        if np.amin(diff) <= THRESHOLD_180:
            proj180deg = Images(self.sample_array[diff.argmin()])

        # Create sample array and Images object
        self.sample_array = self.sample_array[self.view.start_widget.value():self.view.stop_widget.value():self.view.
                                              step_widget.value()]
        sample_images = self._create_images(self.sample_array, "Projections")

        # Set attributes
        sample_images.pixel_size = int(self.view.pixelSizeSpinBox.value())
        sample_images.set_projection_angles(
            ProjectionAngles(self.projection_angles[self.view.start_widget.value():self.view.stop_widget.value():self.
                                                    view.step_widget.value()]))
        if proj180deg is not None:
            sample_images.proj180deg = proj180deg
        return sample_images

    def _create_images(self, data_array: np.ndarray, name: str) -> Images:
        """
        Use a data array to create an Images object.
        :param data_array: The images array obtained from the NeXus file.
        :param name: The name of the image dataset.
        :return: An Images object.
        """
        data = pu.create_array(data_array.shape, self.view.pixelDepthComboBox.currentText())
        data[:] = data_array
        return Images(data, [f"{name} {self.title}"])

    def _create_images_if_required(self, data_array: np.ndarray, name: str) -> Optional[Images]:
        """
        Create the Images objects if the corresponding data was found in the NeXus file, and the user checked the
        "Use?" checkbox.
        :param data_array: The images data array.
        :param name: The name of the images.
        :return: An Images object or None.
        """
        if data_array.size == 0 or not self.view.checkboxes[name].isChecked():
            return None
        return self._create_images(data_array, name)
