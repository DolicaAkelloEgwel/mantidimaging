# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import traceback
from enum import Enum, auto
from typing import TYPE_CHECKING

from mantidimaging.gui.dialogs.async_task import start_async_task_view, TaskWorkerThread

if TYPE_CHECKING:
    from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog


class Notification(Enum):
    IMAGE_FILE_SELECTED = auto()


class AddImagesToDatasetPresenter:
    view: 'AddImagesToDatasetDialog'

    def __init__(self, view: 'AddImagesToDatasetDialog'):
        self.view = view
        self.images = None

    def notify(self, n: Notification):
        try:
            if n == Notification.IMAGE_FILE_SELECTED:
                self.load_images()
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())

    def load_images(self):
        start_async_task_view(self.view, self.view.parent_view.presenter.model.load_image_stack,
                              self._on_images_load_done, {'file_path': self.view.path})

    def _on_images_load_done(self, task: 'TaskWorkerThread'):
        if task.was_successful():
            self.images = task.result
            self.view.parent_view.execute_add_to_dataset()
        else:
            pass
