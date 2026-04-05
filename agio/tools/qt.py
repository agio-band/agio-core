import inspect
import logging
import sys
import traceback
from contextlib import contextmanager

from PySide6.QtCore import *
from PySide6.QtCore import QTimer, QEvent
from PySide6.QtGui import *
from PySide6.QtWidgets import *


logger = logging.getLogger(__name__)


class QApp(QApplication):
    levels = {
        'info': QMessageBox.Icon.Information,
        'warning': QMessageBox.Icon.Warning,
        'error': QMessageBox.Icon.Critical
    }
    show_message_dialog_signal = Signal(dict)

    def __init__(self, app_name='agio', exit_on_widget_close: bool = True, argv=None):
        from agio.core.workspaces import resources

        super().__init__(argv or [])
        self.show_message_dialog_signal.connect(self.show_message_dialog)
        self.setQuitOnLastWindowClosed(exit_on_widget_close)
        self.setApplicationName(app_name)
        self.installEventFilter(self)
        self.app_icon = QIcon(resources.get_res('core/agio-icon.png'))

        # break qt event loop every N time to catch python core events
        self._event_timer = QTimer()
        self._event_timer.start(100)
        self._event_timer.timeout.connect(lambda: None)

    def eventFilter(self, object, event):
        if event.type() == QEvent.ChildPolished:
            if isinstance(object, QWidget) and not isinstance(object, QMenu) and not object.parent():
                try:
                    self.update_widget(object)
                except Exception as e:
                    logger.error(str(e))
        return False

    def update_widget(self, widget):
        widget.setWindowIcon(self.app_icon)

    def show_message_dialog(self, data: dict):
        message = data.get('message', 'No message')
        title = data.get('title') or 'agio'
        level= data.get('level') or 'info'

        msg = ErrorDialog(
            title=title,
            message=message,
            details=data.get('details'),
            parent=data.get('parent'),
            icon=self.levels.get(level)
        )
        if data.get('on_top'):
            msg.setWindowFlags(Qt.WindowStaysOnTopHint)

        msg.exec_()


class ErrorDialog(QMessageBox):
    def __init__(self, title, message, details, icon=None, parent=None, on_top=False):
        super().__init__(parent)
        self.setIcon(icon or QMessageBox.Icon.Critical)
        self.setWindowTitle(title)
        self.setText(message)
        if details:
            self.setDetailedText(details)
        if on_top:
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.setMinimumWidth(350)

    @staticmethod
    def detailed_error(title, message, exception=None, parent=None, on_top=False):
        full_traceback = None
        error_msg = f"{message}"
        if exception is not None:
            if isinstance(exception, Exception):
                tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
                full_traceback = "".join(tb_lines)
            else:
                full_traceback = str(exception)
            error_msg = f"{error_msg}\n\n{str(exception)}"
        dialog = ErrorDialog(
            title=title,
            message=error_msg,
            details=full_traceback,
            parent=parent,
            on_top=on_top,
        )
        dialog.exec()


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