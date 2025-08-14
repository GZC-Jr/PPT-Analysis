from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QStackedWidget
from PyQt6.QtGui import QFont, QColor
import datetime


class LogConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        # 日志视图
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Courier New", 10))

        # 终端视图 (目前是占位符)
        self.console_view = QTextEdit()
        self.console_view.setPlaceholderText(">>> Python 终端（功能待实现）")
        self.console_view.setFont(QFont("Courier New", 10))

        self.stack.addWidget(self.log_view)
        self.stack.addWidget(self.console_view)

    def add_log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_line = f"[{timestamp}] {message}"

        if "错误" in message or "失败" in message:
            self.log_view.setTextColor(QColor("red"))
        elif "警告" in message:
            self.log_view.setTextColor(QColor("yellow"))
        else:
            self.log_view.setTextColor(QColor("white"))

        self.log_view.append(log_line)

    def switch_to_log(self):
        self.stack.setCurrentWidget(self.log_view)

    def switch_to_console(self):
        self.stack.setCurrentWidget(self.console_view)