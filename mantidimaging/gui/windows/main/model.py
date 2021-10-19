# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import uuid
from logging import getLogger
from typing import Dict, List, Optional

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: Optional[uuid.UUID], images_id: uuid.UUID):
    return isinstance(dataset_attribute, uuid.UUID) and dataset_attribute == images_id


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.datasets: List[Dataset] = []
        self.images: Dict[uuid.UUID, Images] = {}
        self._stack_names = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID):
        if images_uuid in self.images:
            return self.images[images_uuid]
        return None

    def do_load_dataset(self, parameters: LoadingParameters, progress):
        sample_images = loader.load_p(parameters.sample, parameters.dtype, progress)
        self.images[sample_images.id] = sample_images
        ds = Dataset(sample_images.id)

        sample_images._is_sinograms = parameters.sinograms
        sample_images.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            sample_images.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            self.images[flat_before.id] = flat_before
            ds.flat_before = flat_before.id
            if parameters.flat_before.log_file:
                flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            self.images[flat_after.id] = flat_after
            if parameters.flat_after.log_file:
                flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
            self.images[dark_before.id] = dark_before
            ds.dark_before = dark_before.id
        if parameters.dark_after:
            dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)
            self.images[dark_after.id] = dark_after
            ds.dark_after = dark_after.id

        if parameters.proj_180deg:
            sample_images.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress) # todo: add to dataset?

        self.datasets.append(ds)
        return ds

    def load_images(self, file_path: str, progress) -> Images:
        images = loader.load_stack(file_path, progress)
        self.images[images.id] = images.id
        return images

    def do_images_saving(self, stack_uuid, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        images = self.get_images_by_uuid(stack_uuid)
        filenames = saver.save(images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        images.filenames = filenames
        return True

    def create_name(self, filename):
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        current_names = self._stack_names
        num = 1
        while name in current_names:
            num += 1
            name = f"{filename}_{num}"

        return name

    def set_images_by_uuid(self, images_id: uuid.UUID, new_images: Images):
        """
        Updates the images of an existing dataset/images object.
        :param images_id: The id of the image to update.
        :param new_images: The new images data.
        """
        if images_id in self.images:
            self.images[images_id] = new_images
        # todo: raise error for else case

    def add_180_deg_to_dataset(self, stack_id, _180_deg_file):
        images = self.get_images_by_uuid(stack_id)
        if stack_id is None:
            raise RuntimeError(f"Failed to get stack with name {stack_id}") # todo: change message

        _180_deg = loader.load(file_names=[_180_deg_file]).sample
        images.proj180deg = _180_deg
        return _180_deg

    def add_projection_angles_to_sample(self, images_id: uuid.UUID, proj_angles: ProjectionAngles):
        images = self.get_images_by_uuid(images_id)
        if images_id is None:
            raise RuntimeError(f"Failed to get stack with name {images_id}") # todo: change message
        images.set_projection_angles(proj_angles)

    def load_log(self, log_file: str):
        return loader.load_log(log_file)

    def add_log_to_sample(self, images_id: uuid.UUID, log_file: str):
        images = self.get_images_by_uuid(images_id)
        log = self.load_log(log_file)
        log.raise_if_angle_missing(images.filenames)
        images.log_file = log
        # todo - send update here or do it from presenter?

    def delete_images(self, images_id: uuid.UUID):
        if images_id in self.images:
            del self.images[images_id]
            for dataset in self.datasets:
                if _matching_dataset_attribute(dataset.sample, images_id):
                    dataset.sample = None
                if _matching_dataset_attribute(dataset.flat_before, images_id):
                    dataset.flat_before = None
                if _matching_dataset_attribute(dataset.flat_after, images_id):
                    dataset.flat_after = None
                if _matching_dataset_attribute(dataset.dark_before, images_id):
                    dataset.dark_before = None
                if _matching_dataset_attribute(dataset.flat_before, images_id):
                    dataset.dark_before = None
        # TODO - delete dataset implementation here
        # TODO - rename method
