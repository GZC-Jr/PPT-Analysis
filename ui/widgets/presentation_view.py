# PPT-Analysis/ui/widgets/presentation_view.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QTimer


class PresentationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 我们不再直接在image_label上绘制，而是将它作为显示最终结果的画布
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

        # 数据
        self.raw_slides = []  # 存储从文件加载的原始QPixmap
        self.mouse_data = None
        self.current_slide_index = 0

        # 绘图设置
        self.show_trajectory = True
        self.show_markers = {'MOVE': False, 'HOVER': True, 'CLICK': True}
        self.marker_colors = {
            'MOVE': QColor(0, 0, 0, 100),  # 黑色，半透明
            'HOVER': QColor(255, 165, 0, 200),  # 橙色，更醒目
            'CLICK': QColor(0, 100, 255, 255)  # 蓝色，不透明
        }

        # 设置深色背景
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#252526"))
        self.setPalette(p)

    def set_slides(self, slide_paths):
        self.raw_slides = [QPixmap(path) for path in slide_paths]
        if self.raw_slides:
            self.display_slide(0)
        else:
            self.image_label.setText("未加载PPT或无法提取幻灯片")

    def set_mouse_data(self, df):
        self.mouse_data = df
        # 数据更新后，需要重绘当前幻灯片以显示轨迹
        if self.raw_slides:
            self.display_slide(self.current_slide_index)

    def display_slide(self, index):
        if not (0 <= index < len(self.raw_slides)):
            return

        self.current_slide_index = index
        self.update()  # 触发重绘，所有绘图逻辑都在paintEvent中

    def resizeEvent(self, event):
        """窗口大小改变时，只需触发重绘即可"""
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, event):
        """
        核心绘图逻辑：安全、健壮的工作流。
        """
        super().paintEvent(event)

        # 1. 检查是否有内容可绘制
        if not self.raw_slides:
            return

        # 2. 获取当前原始幻灯片
        base_pixmap = self.raw_slides[self.current_slide_index]

        # 3. 缩放基础幻灯片以适应窗口，这是我们的背景
        scaled_pixmap = base_pixmap.scaled(self.size(),
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        # 4. 创建一个新的、空白的、最终要显示的Pixmap
        #    这个新的Pixmap尺寸和缩放后的背景一样大
        final_pixmap = QPixmap(scaled_pixmap.size())
        final_pixmap.fill(Qt.GlobalColor.transparent)  # 用透明背景填充

        # 5. 创建QPainter，目标是这个全新的final_pixmap
        painter = QPainter(final_pixmap)

        # 6. 首先将缩放后的幻灯片背景绘制上去
        painter.drawPixmap(0, 0, scaled_pixmap)

        # 7. 如果有鼠标数据，则在其上绘制轨迹和标记点
        if self.mouse_data is not None:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 筛选出当前幻灯片的数据
            try:
                # 使用 .loc 确保类型正确，并避免SettingWithCopyWarning
                slide_df = self.mouse_data.loc[self.mouse_data['SlideIndex'] == self.current_slide_index + 1]
            except Exception as e:
                print(f"筛选DataFrame时出错: {e}")
                slide_df = None

            if slide_df is not None and not slide_df.empty:
                # 计算坐标转换比例
                original_size = base_pixmap.size()
                displayed_size = scaled_pixmap.size()

                if original_size.width() > 0 and original_size.height() > 0:
                    scale_x = displayed_size.width() / original_size.width()
                    scale_y = displayed_size.height() / original_size.height()

                    # 绘制轨迹线
                    if self.show_trajectory:
                        pen = QPen(QColor(255, 0, 0, 180), 2, Qt.PenStyle.SolidLine)  # 红色半透明
                        painter.setPen(pen)

                        points = QPolygonF()
                        for _, row in slide_df.iterrows():
                            x = row['X'] * scale_x
                            y = row['Y'] * scale_y
                            points.append(QPointF(x, y))

                        painter.drawPolyline(points)

                    # 绘制标记点
                    painter.setPen(Qt.PenStyle.NoPen)  # 标记点我们只填充颜色
                    for _, row in slide_df.iterrows():
                        action_type = row.get('ActionType', 'UNKNOWN')
                        if self.show_markers.get(action_type, False):
                            color = self.marker_colors.get(action_type, QColor('white'))
                            painter.setBrush(QBrush(color))

                            x = row['X'] * scale_x
                            y = row['Y'] * scale_y
                            painter.drawEllipse(QPointF(x, y), 5, 5)  # 稍微大一点

        # 8. 结束绘制
        painter.end()

        # 9. 将这个绘制完成的final_pixmap设置给QLabel
        self.image_label.setPixmap(final_pixmap)