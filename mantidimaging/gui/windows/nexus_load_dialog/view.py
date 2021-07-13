# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, \
    QHeaderView, QCheckBox, QDialogButtonBox, QComboBox, QDoubleSpinBox

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"

FOUND_TEXT = {True: "✓", False: "✕"}

FOUND_COLUMN = 1
PATH_COLUMN = 2
SHAPE_COLUMN = 3
CHECKBOX_COLUMN = 4
TEXT_COLUMNS = [FOUND_COLUMN, PATH_COLUMN, SHAPE_COLUMN]


class NexusLoadDialog(QDialog):
    tree: QTreeWidget
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit
    buttonBox: QDialogButtonBox
    pixelDepthComboBox: QComboBox
    pixelSizeSpinBox: QDoubleSpinBox

    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)
        self.tree.expandItem(self.tree.topLevelItem(1))
        self.checkboxes = dict()

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.accepted.connect(self.parent_view.execute_nexus_load)

    def choose_nexus_file(self):
        """
        Select a NeXus file and attempt to load it. If a file is chosen, clear the information/widgets from the
        QTreeWidget and enable the OK button.
        """
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.checkboxes.clear()
            self.clear_widgets()
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            self.filePathLineEdit.setText(selected_file)
            self.presenter.notify(Notification.NEXUS_FILE_SELECTED)

    def clear_widgets(self):
        """
        Remove text and checkbox widgets from the QTreeWidget when a new file has been selected.
        """
        for position in range(2):
            section: QTreeWidgetItem = self.tree.topLevelItem(position)
            for column in TEXT_COLUMNS:
                section.setText(column, "")

        data_section: QTreeWidgetItem = self.tree.topLevelItem(1)
        for position in range(5):
            child = data_section.child(position)
            for column in TEXT_COLUMNS:
                child.setText(column, "")
            self.tree.removeItemWidget(child, CHECKBOX_COLUMN)

    def set_data_found(self, position: int, found: bool, path: str, shape: Tuple[int, ...]):
        """
        Indicate on the QTreeWidget if the image key and data fields have been found or not.
        :param position: The row position for the data.
        :param found: Whether or not the data has been found.
        :param path: The data path in the NeXus file.
        :param shape: The shape of the data/image key array.
        """
        data_section: QTreeWidgetItem = self.tree.topLevelItem(position)
        self.set_found_status(data_section, found)

        # Nothing else to do if the data wasn't found
        if not found:
            return

        # Add the path and array shape information to the QTreeWidget
        data_section.setText(PATH_COLUMN, path)
        data_section.setText(SHAPE_COLUMN, str(shape))

    def set_images_found(self, position: int, found: bool, shape: Tuple[int, int, int]):
        """
        Indicate on the QTreeWidget if the projections and dark/flat before/after images were found in the data array.
        :param position: The row position for the image type.
        :param found: Whether or not the images were found.
        :param shape: The shape of the images array.
        """
        section: QTreeWidgetItem = self.tree.topLevelItem(1)
        child = section.child(position)
        self.set_found_status(child, found)

        # Nothing else to do if the images weren't found
        if not found:
            return

        # Set shape information and add a "Use?" checkbox
        child.setText(SHAPE_COLUMN, str(shape))
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        if not position:
            checkbox.setEnabled(False)
        self.tree.setItemWidget(child, CHECKBOX_COLUMN, checkbox)
        self.checkboxes[child.text(0)] = checkbox

    def show_exception(self, msg: str, traceback):
        """
        Show an error about an exception.
        :param msg: The error message.
        :param traceback: The traceback.
        """
        self.parent_view.presenter.show_error(msg, traceback)

    def show_missing_data_error(self, msg: str):
        """
        Show an error about missing required data.
        :param msg: The error message.
        """
        self.parent_view.show_error_dialog(msg)

    def disable_ok_button(self):
        """
        Disable the OK button when the NeXus file isn't usable.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    @staticmethod
    def set_found_status(tree_widget_item: QTreeWidgetItem, found: bool):
        """
        Adds a tick or cross to the found column in the QTreeWidget to indicate if certain data could be found in the
        NeXus file.
        :param tree_widget_item: The QTreeWidgetItem that contains a found column.
        :param found: Whether or not the data was found.
        """
        tree_widget_item.setText(FOUND_COLUMN, FOUND_TEXT[found])
        tree_widget_item.setTextAlignment(FOUND_COLUMN, Qt.AlignHCenter)