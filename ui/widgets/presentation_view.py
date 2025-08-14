from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QTimer


class PresentationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

        # 数据
        self.slides = []
        self.mouse_data = None
        self.current_slide_index = 0

        # 绘图数据
        self.trajectory_points = []
        self.marker_points = []  # list of (QPointF, QColor)

        # 绘图设置
        self.show_trajectory = True
        self.show_markers = {'MOVE': False, 'HOVER': True, 'CLICK': True}
        self.marker_colors = {
            'MOVE': QColor('black'),
            'HOVER': QColor('red'),
            'CLICK': QColor('blue')
        }

        self.set_background_color(QColor("#252526"))

    def set_background_color(self, color):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    def set_slides(self, slide_paths):
        self.slides = [QPixmap(path) for path in slide_paths]
        if self.slides:
            self.display_slide(0)
        else:
            self.image_label.setText("未加载PPT或无法提取幻灯片")

    def set_mouse_data(self, df):
        self.mouse_data = df

    def display_slide(self, index):
        if 0 <= index < len(self.slides):
            self.current_slide_index = index

            # 缩放图片以适应窗口大小，同时保持纵横比
            pixmap = self.slides[index]
            scaled_pixmap = pixmap.scaled(self.image_label.size(),
                                          Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            # TODO: 更新轨迹和标记点
            self.update()  # 触发重绘

    def resizeEvent(self, event):
        """窗口大小改变时，重新缩放并显示当前幻灯片"""
        super().resizeEvent(event)
        if self.slides:
            self.display_slide(self.current_slide_index)

    def paintEvent(self, event):
        """
        在 image_label 上绘制轨迹和标记点。这是核心绘图逻辑。
        """
        super().paintEvent(event)

        if not self.image_label.pixmap() or self.mouse_data is None:
            return

        painter = QPainter(self.image_label.pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # TODO: 这里需要实现完整的播放逻辑，根据当前播放时间点来绘制
        # 以下是绘制所有点的示例

        slide_df = self.mouse_data[self.mouse_data['SlideIndex'] == self.current_slide_index + 1]

        # 获取原始幻灯片和显示pixmap的尺寸比例
        original_size = self.slides[self.current_slide_index].size()
        displayed_size = self.image_label.pixmap().size()

        # 处理可能的除零错误
        if original_size.width() == 0 or original_size.height() == 0:
            return

        scale_x = displayed_size.width() / original_size.width()
        scale_y = displayed_size.height() / original_size.height()

        # 计算偏移量以使图像居中
        offset_x = (self.image_label.width() - displayed_size.width()) / 2
        offset_y = (self.image_label.height() - displayed_size.height()) / 2

        # 1. 绘制轨迹线
        if self.show_trajectory and not slide_df.empty:
            pen = QPen(QColor("red"), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)

            points = QPolygonF()
            for _, row in slide_df.iterrows():
                # 转换坐标
                x = row['X'] * scale_x
                y = row['Y'] * scale_y
                points.append(QPointF(x, y))

            painter.drawPolyline(points)

        # 2. 绘制标记点
        for _, row in slide_df.iterrows():
            action_type = row['ActionType']
            if self.show_markers.get(action_type, False):
                color = self.marker_colors.get(action_type, QColor('white'))
                painter.setPen(QPen(color, 1))
                painter.setBrush(QBrush(color))

                x = row['X'] * scale_x
                y = row['Y'] * scale_y
                painter.drawEllipse(QPointF(x, y), 4, 4)  # 绘制半径为4的圆点

        painter.end()