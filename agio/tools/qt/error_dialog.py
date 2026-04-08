import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox


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
