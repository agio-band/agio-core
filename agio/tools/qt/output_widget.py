from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QSizePolicy,
    QSpacerItem,
)
from PySide6.QtGui import QFont, QTextOption, QCursor, QAction, QFontMetrics
from PySide6.QtCore import Qt

import html

MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30


class OutputWidget(QWidget):
    STYLE_SUCCESS = "color: #4CAF50;"
    STYLE_WARNING = "color: #FFC107; background-color: #3A3A00;"
    STYLE_DEBUG = "color: #9E9E9E;"
    STYLE_ERROR = "color: #F44336; background-color: #4A0000; font-weight: bold;"
    STYLE_INFO = "color: #E0E0E0;"
    STYLE_DEFAULT = "color: #E0E0E0;"

    _LEVEL_STYLES = {
        "success": STYLE_SUCCESS,
        "warning": STYLE_WARNING,
        "debug": STYLE_DEBUG,
        "error": STYLE_ERROR,
        "info": STYLE_INFO,
        "default": STYLE_DEFAULT,
    }

    def __init__(self, title=None, show_buttons=True, parent=None):
        super().__init__(parent)

        self._follow_scroll = True

        if title:
            self.setWindowTitle(title)
            self.setWindowFlags(Qt.WindowType.Tool)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        if show_buttons:
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(4, 4, 4, 4)

            self.clear_btn = QPushButton("Clear")
            self.clear_btn.clicked.connect(self.clear)

            self.follow_btn = QPushButton("Follow")
            self.follow_btn.setCheckable(True)
            self.follow_btn.setChecked(self._follow_scroll)
            self.follow_btn.clicked.connect(self._toggle_follow_scroll)

            btn_layout.addWidget(self.clear_btn)
            btn_layout.addWidget(self.follow_btn)
            btn_layout.addItem(QSpacerItem(1000, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

            main_layout.addLayout(btn_layout)

        # Text output widget
        self.output = QTextBrowser()
        self.output.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        font = QFont("Courier New", 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.output.setFont(font)

        # Setup tab stops
        font_metrics = QFontMetrics(font)
        self.output.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))

        self.output.setMouseTracking(True)
        self.output.setReadOnly(True)

        self.output.setOpenExternalLinks(False)
        self.output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.output.customContextMenuRequested.connect(self._open_context_menu)

        # Override wheelEvent to support font zoom
        self._original_wheel_event = self.output.wheelEvent
        self.output.wheelEvent = self._wheel_event

        main_layout.addWidget(self.output)

    def _toggle_follow_scroll(self):
        self._follow_scroll = self.follow_btn.isChecked()

    def _get_font_size(self):
        return self.output.font().pointSize()

    def _change_font_size(self, increase):
        current_size = self._get_font_size()
        if increase:
            new_size = min(MAX_FONT_SIZE, current_size + 1)
        else:
            new_size = max(MIN_FONT_SIZE, current_size - 1)

        font = self.output.font()
        font.setPointSize(new_size)
        self.output.setFont(font)

        # Update tab stops for new font size
        font_metrics = QFontMetrics(font)
        self.output.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))

    def _wheel_event(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._change_font_size(increase=True)
            else:
                self._change_font_size(increase=False)
            event.accept()
        else:
            self._original_wheel_event(event)

    def _open_context_menu(self, pos):
        menu = self.output.createStandardContextMenu()
        menu.addSeparator()

        clear_action = QAction("Clear Console", self)
        clear_action.triggered.connect(self.clear)
        menu.addAction(clear_action)

        follow_action = QAction("Follow", self, checkable=True, checked=self._follow_scroll)
        follow_action.toggled.connect(self._toggle_follow_scroll)
        menu.addAction(follow_action)

        menu.exec(self.output.mapToGlobal(pos))
        menu.deleteLater()

    def _escape_html(self, text):
        return html.escape(str(text))

    def _format_message(self, message, style):
        escaped = self._escape_html(message)
        # Preserve whitespace and line breaks
        escaped = escaped.replace("\n", "<br>").replace(" ", "&nbsp;")
        return f'<span style="{style}">{escaped}</span>'

    def _append_styled(self, message, style):
        formatted = self._format_message(message, style)
        self.output.append(formatted)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        if self._follow_scroll:
            self.output.horizontalScrollBar().setValue(0)
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    # Public API

    def clear(self):
        self.output.clear()

    def success(self, message):
        self._append_styled(message, self.STYLE_SUCCESS)

    def warning(self, message):
        self._append_styled(message, self.STYLE_WARNING)

    def debug(self, message):
        self._append_styled(message, self.STYLE_DEBUG)

    def error(self, message):
        self._append_styled(message, self.STYLE_ERROR)

    def info(self, message):
        self._append_styled(message, self.STYLE_INFO)

    def print(self, message, color=None):
        if color:
            style = f"color: {color};"
        else:
            style = self.STYLE_DEFAULT
        self._append_styled(message, style)

    def append(self, text):
        self._append_styled(text, self.STYLE_DEFAULT)

    def set_follow_scroll(self, enabled):
        self._follow_scroll = enabled
        if hasattr(self, "follow_btn"):
            self.follow_btn.setChecked(enabled)

    def showEvent(self, event):
        super().showEvent(event)
        if self.windowFlags() & Qt.WindowType.Window:
            self._scroll_to_bottom()



if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = OutputWidget(title="OutputWidget Test", show_buttons=True)
    widget.resize(800, 600)

    # Test different log levels
    widget.info("Application started successfully")
    widget.debug("Debug: Loading configuration from /etc/config.yaml")
    widget.success("Configuration loaded successfully")
    widget.warning("Warning: Disk space is running low (10% remaining)")
    widget.error("Error: Failed to connect to database at 192.168.1.100:5432")

    widget.info("-" * 60)
    widget.info("Testing multi-line output:")
    widget.debug(
        "Line 1: Initializing modules\n"
        "Line 2: Loading plugins\n"
        "Line 3: Starting services"
    )

    widget.info("-" * 60)
    widget.info("Testing HTML special characters (should be escaped):")
    widget.info("HTML tags: <div class='test'>Hello & goodbye</div>")
    widget.info("Comparison: 5 < 10 and 10 > 5")
    widget.info("Ampersand: Tom & Jerry")

    widget.info("-" * 60)
    widget.info("Testing custom colors:")
    widget.print("This is purple text", color="purple")
    widget.print("This is cyan text", color="#00FFFF")
    widget.print("This is orange text", color="orange")
    widget.print("Default color text")

    widget.info("-" * 60)
    widget.info("Testing append method:")
    widget.append("Plain appended text with <b>HTML</b> tags escaped")
    widget.append("<Render Manager>")

    widget.show()
    sys.exit(app.exec())


