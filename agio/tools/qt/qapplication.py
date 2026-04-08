import logging

from PySide6.QtCore import Signal, QTimer, QEvent, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget, QMenu

from agio.tools.qt.error_dialog import ErrorDialog

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
