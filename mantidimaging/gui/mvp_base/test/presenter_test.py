import unittest

from testfixtures import LogCapture

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.mvp_base import (
        BaseDialogView, BaseMainWindowView, BasePresenter)

mock = import_mock()


class MainWindowPresenterTest(unittest.TestCase):

    def test_default_notify_method_raises_exception(self):
        view = mock.create_autospec(BaseMainWindowView)
        presenter = BasePresenter(view)

        with self.assertRaises(NotImplementedError):
            presenter.notify(0)

    def test_show_error_message_forwarded_to_main_window_view(self):
        view = mock.create_autospec(BaseMainWindowView)
        presenter = BasePresenter(view)

        presenter.show_error("test message")
        view.show_error_dialog.assert_called_once_with("test message")

    def test_show_error_message_forwarded_to_dialog_view(self):
        view = mock.create_autospec(BaseDialogView)
        presenter = BasePresenter(view)

        presenter.show_error("test message")
        view.show_error_dialog.assert_called_once_with("test message")

    def test_bad_view_causes_errors_to_be_logged(self):
        class V(object):
            pass

        view = V()
        presenter = BasePresenter(view)

        with LogCapture() as l:
            presenter.show_error("test message")

        l.check(
            ('mantidimaging.gui.mvp_base.presenter', 'ERROR',
             'Presenter error: test message')
        )


if __name__ == '__main__':
    unittest.main()