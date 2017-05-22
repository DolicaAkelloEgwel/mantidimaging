from __future__ import absolute_import, division, print_function

import numpy as np
from matplotlib.backends.backend_qt4agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.colorbar import ColorbarBase
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector, Slider
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt

from core.algorithms import gui_compile_ui
from gui.stack_visualiser.sv_presenter import ImgpyStackViewerPresenter
from gui.stack_visualiser.zoom_rectangle import FigureCanvasColouredRectangle


class ImgpyStackVisualiserView(QtGui.QMainWindow):
    def __init__(self,
                 parent,
                 dock_parent,
                 data,
                 axis=0,
                 cmap='Greys_r',
                 block=False,
                 **kwargs):

        # enfornce not showing a single image
        assert data.ndim == 3, "Data does NOT have 3 dimensions! Dimensions found: {0}".format(
            data.ndim)

        super(ImgpyStackVisualiserView, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/stack.ui', self)

        # black magic to swap out the closeEvent, but still keep the old one
        self.dock_parent = dock_parent
        self.dock_parent.oldCloseEvent = self.dock_parent.closeEvent
        self.dock_parent.closeEvent = self.closeEvent

        # View doesn't take any ownership of the data!
        self.presenter = ImgpyStackViewerPresenter(self, data, axis)

        self.axis = axis
        self.cmap = cmap
        self.block = block

        self.mplfig = Figure()
        self.image_axis = self.mplfig.add_subplot(111)

        self.canvas = FigureCanvasColouredRectangle(self.mplfig)
        self.canvas.rectanglecolor = Qt.yellow
        self.canvas.setParent(self)
        self.previous_region = None

        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)

        self.slider_axis = self.mplfig.add_axes(
            [0.25, 0.01, 0.5, 0.03], axisbg='lightgoldenrodyellow')

        # initialise the slider
        self.slider = self.initialiseSlider(self.slider_axis,
                                            data.shape[self.axis] - 1)
        self.image = self.image_axis.imshow(
            self.presenter.get_image(0), cmap=cmap, **kwargs)
        self.rectangle = self.createRectangleSelector(self.image_axis, 1)

        self.mplvl.addWidget(self.toolbar)
        self.mplvl.addWidget(self.canvas)

        # self.change_value_rangle(0, 16000)

        # store the selected region

        # not particularly interested in that for now
        # self.fig.canvas.mpl_connect('key_press_event', self.toggle_selector)

        # define slider
        # add the axis for the slider
        # self.slider_axis = self.axes[1]

    def apply_to_data(self, func, *args, **kwargs):
        self.presenter.apply_to_data(func, *args, **kwargs)

    def closeEvent(self, event):
        # setting floating to false tricks qt, because in the next call
        # self.window() will refer to the main window!
        # However if we do self.window() while setFloating is True
        # the window() returns the QDockWidget, not the MainWindow that we want
        self.parent().setFloating(False)
        self.window().remove_stack(self)  # refers to MainWindow
        self.deleteLater()
        self.parent().deleteLater()

    def createRectangleSelector(self, axis, button=1):
        # drawtype is 'box' or 'line' or 'none'
        return RectangleSelector(
            axis,
            self.line_select_callback,
            drawtype='box',
            useblit=False,
            button=[1, 3],  # don't use middle button
            spancoords='pixels',
            interactive=True)

    def line_select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x0, y0 = eclick.xdata, eclick.ydata
        x1, y1 = erelease.xdata, erelease.ydata
        # different order here, than in how we handle it
        # this is because the unpacking for draw_rect is different
        # this is because the unpacking for draw_rect is different
        self.previous_region = (x0, x1, y0, y1)
        region = "%i %i %i %i" % (x0, y0, x1, y1)
        print(region)

    def update_current_image(self, val=None):
        """
        If the name of this is changed to just update,
        it causes an internal error with the matplotlib backend implementation!

        :param val: Not used, but cannot be removed because slider.on_changed passes in a param
                    ^ I guess we can actually use the val instead?
        """
        ind = int(self.slider.val)

        self.image.set_data(self.presenter.get_image(ind))

    def change_value_rangle(self, low, high):
        self.image.set_clim((low, high))

    def toggle_selector(self, event):
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and self.rectangle.active:
            print(' RectangleSelector deactivated.')
            self.rectangle.set_active(False)
        if event.key in ['A', 'a'] and not self.rectangle.active:
            print(' RectangleSelector activated.')
            self.rectangle.set_active(True)

    def initialiseSlider(self, slider_axis, length):
        # axcolor = 'lightgoldenrodyellow'

        slider = Slider(
            slider_axis, 'Slices', 0, length, valinit=0, valfmt='%i')

        # Change to on_changed(lambda x: self.presenter.notify(Notification.IMAGE_CHANGED))?
        slider.on_changed(self.update_current_image)
        return slider


# def show_3d(data, axis=0, cmap='Greys_r', block=False, **kwargs):
#     s = ImgpyStackVisualiserView(data, axis, cmap, block)