import os
import tempfile
import unittest

import numpy as np

import mantidimaging.tests.test_helper as th

from mantidimaging.gui.main_window.load_dialog import MWLoadDialog
from mantidimaging.gui.main_window.mw_presenter import (
        MainWindowPresenter, Notification)
from mantidimaging.gui.main_window.mw_view import MainWindowView

mock = th.import_mock()


class MainWindowPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.config = None
        self.view = mock.create_autospec(MainWindowView)
        self.view.load_dialogue = mock.create_autospec(MWLoadDialog)
        self.presenter = MainWindowPresenter(self.view, self.config)

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")

    def test_attempt_to_load_bad_datafile_shows_error(self):
        with tempfile.NamedTemporaryFile() as f:
            dirname = os.path.dirname(f.name)

            # Bad data file
            bad_filename = os.path.join(dirname, 'test_bad_nexus.nxs')
            with open(bad_filename, 'w') as tf:
                tf.write('000')

            # Set load parameters
            self.view.load_dialogue.sample_file = lambda: 'test_bad_nexus'
            self.view.load_dialogue.sample_path = lambda: dirname
            self.view.load_dialogue.image_format = 'nxs'
            self.view.load_dialogue.parallel_load = lambda: False
            self.view.load_dialogue.indices = lambda: (-1, 0, 0)
            self.view.load_dialogue.window_title = lambda: 'test_bad_nexus'

            # Ask for load
            self.presenter.notify(Notification.LOAD)

            # Expect error message
            self.view.show_error_dialog.assert_called_once_with(
                    "Failed to read data file. See log for details.")


if __name__ == '__main__':
    unittest.main()