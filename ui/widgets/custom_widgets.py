from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtProperty

class Switch(QCheckBox):
    """一个自定义的开关控件，样式更美观"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景颜色
        if self.isChecked():
            bg_color = QColor("#3D7AF5")  # 选中时的蓝色
            handle_color = QColor("#FFFFFF")
            handle_pos = self.width() - self.height() + 2
        else:
            bg_color = QColor("#777777")  # 未选中时的灰色
            handle_color = QColor("#DDDDDD")
            handle_pos = 2

        # 绘制背景
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        # 绘制滑块
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(QRectF(handle_pos, 2, self.height() - 4, self.height() - 4))

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)