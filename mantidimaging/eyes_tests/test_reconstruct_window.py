# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class ReconstructionWindowTest(BaseEyesTest):
    def setUp(self):
        super(ReconstructionWindowTest, self).setUp()

    def tearDown(self):
        self.imaging.recon.close()
        super().tearDown()

    def test_reconstruction_window_opens(self):
        self.imaging.show_recon_window()

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_opens_with_data(self):
        self._load_data_set()

        self.imaging.show_recon_window()

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_cor_and_tilt_tab(self):
        self.imaging.show_recon_window()

        self.imaging.recon.tabWidget.setCurrentWidget(self.imaging.recon.resultsTab)

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_reconstruct_tab(self):
        self.imaging.show_recon_window()

        self.imaging.recon.tabWidget.setCurrentWidget(self.imaging.recon.reconTab)

        self.check_target(widget=self.imaging.recon)

    def test_negative_nan_overlay(self):
        data = np.random.rand(5, 200, 200)
        images = Images(data)
        self.imaging.presenter.create_new_stack(Images(data), "bad_data")
        images.data[0:, 190:] = 0
        images.data[0:, 195:] = np.nan

        self.imaging.show_recon_window()
        self.check_target(widget=self.imaging.recon)
