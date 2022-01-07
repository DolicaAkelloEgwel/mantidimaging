# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from logging import getLogger
from typing import Dict, Optional, List, Union

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset, StackDataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: Optional[Images], images_id: uuid.UUID) -> bool:
    return isinstance(dataset_attribute, Images) and dataset_attribute.id == images_id


class MainWindowModel(object):
    def __init__(self):
        super().__init__()
        self.datasets: Dict[uuid.UUID, Union[StackDataset, Dataset]] = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID):
        for dataset in self.datasets.values():
            for image in dataset.all:
                if images_uuid == image.id:
                    return image
        return None

    def do_load_dataset(self, parameters: LoadingParameters, progress) -> Dataset:
        sample = loader.load_p(parameters.sample, parameters.dtype, progress)
        ds = Dataset(sample)

        sample._is_sinograms = parameters.sinograms
        sample.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            ds.sample.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            ds.flat_before = flat_before
            if parameters.flat_before.log_file:
                flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            ds.flat_after = flat_after
            if parameters.flat_after.log_file:
                flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
            ds.dark_before = dark_before
        if parameters.dark_after:
            dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)
            ds.dark_after = dark_after

        if parameters.proj_180deg:
            sample.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress)

        self.datasets[ds.id] = ds
        return ds

    def load_images(self, file_path: str, progress) -> Images:
        images = loader.load_stack(file_path, progress)
        sd = StackDataset([images])
        self.datasets[sd.id] = sd
        return images

    def do_images_saving(self, images_id, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        filenames = saver.save(images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        images.filenames = filenames
        return True

    def set_image_data_by_uuid(self, images_id: uuid.UUID, new_data: np.ndarray):
        """
        Updates the data of an existing dataset/images object.
        :param images_id: The id of the image to update.
        :param new_data: The new image data.
        """
        for dataset in self.datasets.values():
            if images_id in dataset:
                dataset.replace(images_id, new_data)
                return
        self.raise_error_when_images_not_found(images_id)

    def add_180_deg_to_dataset(self, dataset_id: uuid.UUID, _180_deg_file: str) -> Images:
        """
        Loads to 180 projection and adds this to a given Images ID.
        :param dataset_id: The ID of the Dataset.
        :param _180_deg_file: The location of the 180 projection.
        :return: The loaded 180 Image object.
        """
        if dataset_id in self.datasets:
            dataset = self.datasets[dataset_id]
        else:
            raise RuntimeError(f"Failed to get Dataset with ID {dataset_id}")
        _180_deg = loader.load(file_names=[_180_deg_file]).sample
        dataset.proj180deg = _180_deg
        return _180_deg

    def add_projection_angles_to_sample(self, images_id: uuid.UUID, proj_angles: ProjectionAngles):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        images.set_projection_angles(proj_angles)

    def raise_error_when_images_not_found(self, images_id: uuid.UUID):
        raise RuntimeError(f"Failed to get Images with ID {images_id}")

    def add_log_to_sample(self, images_id: uuid.UUID, log_file: str):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            raise RuntimeError
        log = loader.load_log(log_file)
        log.raise_if_angle_missing(images.filenames)
        images.log_file = log

    def _remove_dataset(self, dataset_id: uuid.UUID):
        """
        Removes a dataset and the image stacks it contains from the model.
        :param dataset_id: The dataset ID.
        """
        del self.datasets[dataset_id]

    def remove_container(self, container_id: uuid.UUID) -> Optional[List[uuid.UUID]]:
        """
        Removes a container from the model.
        :param container_id: The ID of the dataset or image stack.
        :return: A list of the IDs of all the image stacks that were deleted from the model if a match was found, None
            otherwise.
        """
        if container_id in self.datasets:
            stacks_in_dataset = self.datasets[container_id].all_image_ids
            self._remove_dataset(container_id)
            return stacks_in_dataset
        else:
            for dataset in self.datasets.values():
                if container_id in dataset:
                    dataset.delete_stack(container_id)
                    return [container_id]
        self.raise_error_when_images_not_found(container_id)
        return None

    def add_dataset_to_model(self, dataset: Union[Dataset, StackDataset]):
        self.datasets[dataset.id] = dataset

    @property
    def image_ids(self) -> List[uuid.UUID]:
        images = []
        for dataset in self.datasets.values():
            images += dataset.all
        return [image.id for image in images if image is not None]

    def add_recon_to_dataset(self, recon_data: Images, stack_id: uuid.UUID):
        for dataset in self.datasets.values():
            if stack_id in dataset:
                dataset.recons.append(recon_data)
                return
        self.raise_error_when_images_not_found(stack_id)
