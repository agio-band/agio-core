import inspect
import logging
import sys
from contextlib import contextmanager

from PySide6.QtCore import *
from PySide6.QtCore import QTimer
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from agio.tools.qt.qapplication import QApp

logger = logging.getLogger(__name__)


def get_main_parent():
    qapp = QApplication.instance()
    if qapp is None:
        raise RuntimeError('QApplication not created')
    return QApplication.topLevelWidgets()[0]


def center_on_screen(widget, app = None):
    app = app or QApplication.instance()
    cursor_pos: QPoint = QCursor.pos()
    current_screen: QScreen = app.screenAt(cursor_pos)
    if current_screen is None:
        current_screen = app.primaryScreen()
        if current_screen is None:
            print("Screens not found")
            return
    screen_geometry = current_screen.availableGeometry()
    widget_geometry = widget.frameGeometry()
    widget_geometry.moveCenter(screen_geometry.center())
    widget.move(widget_geometry.topLeft())


def show_message_dialog(message: str, title: str = None, level: str = None, on_top: bool = True, exception=None, parent=None):
    data = {
        'message': message,
        'title': title,
        'level': level,
        'on_top': on_top,
        'exception': exception,
        'parent': parent
    }
    try:
        app = QApp.instance() or QApp()
        app.show_message_dialog_signal.emit(data)
    except Exception as e:
        logger.exception(f'Message dialog failed: {data}')


def open_widget(widget, on_center: bool = True, qapp: QApplication = None, *args, **kwargs):
    """
    Use this function to open a any PySide6 dialogs.
    - apply style
    - fix core events
    - apply app name
    - apply app icon
    """
    qapp = qapp or QApp.instance() or QApp()
    qapp.setQuitOnLastWindowClosed(True)
    qapp.setApplicationName(kwargs.pop('app_name', 'agio'))

    # break qt event loop every N time to catch python core events
    timer = QTimer()
    timer.start(100)    # TODO make unique for all widgets
    timer.timeout.connect(lambda: None)

    try:
        if inspect.isclass(widget):
            w = widget(*args, **kwargs)
        else:
            w = widget
        if on_center:
            center_on_screen(w, qapp)
        w.show()
        sys.exit(qapp.exec())
    except Exception:
        logging.exception(f"Application startup error")


@contextmanager
def main_app(app_name: str = 'agio', dialog_mode: bool = True):
    """
    Open main app
    dialog_mode: close app on dialog closed
    """
    from agio.core.events import on_exit

    if QApplication.instance():
        QMessageBox.critical(None, "Error", f"Main Qt App already started")
        return
    qapp = QApp(app_name, exit_on_widget_close=dialog_mode)
    on_exit(lambda *args: qapp.quit())
    try:
        yield qapp
        qapp.exec()
    except Exception as e:
        logging.exception("Application startup error")
        QMessageBox.critical(None, "Error", f"{type(e).__name__}: {e}")