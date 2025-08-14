# ui/widgets/presentation_view.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal
import pandas as pd


class PresentationView(QWidget):
    # 信号：通知外部（MainWindow）进度已更新
    progress_updated = pyqtSignal(int)
    playback_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel("请先上传PPT和CSV文件以开始演示")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

        # 数据
        self.raw_slides = []
        self.mouse_data = None

        # 播放状态
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._update_frame)

        self.is_playing = False
        self.current_data_index = 0
        self.current_slide_index_in_data = -1

        # 播放设置
        self.playback_mode = 'speed'  # 'speed' or 'interval'
        self.playback_speed = 1.0
        self.fixed_interval = 3.0  # in seconds

        # 绘图设置
        self.show_trajectory = True
        self.show_markers = {'MOVE': False, 'HOVER': True, 'CLICK': True}
        self.marker_colors = {
            'MOVE': QColor(0, 0, 0, 100),  # 黑色
            'HOVER': QColor(255, 165, 0, 200),  # 橙色
            'CLICK': QColor(0, 100, 255, 255)  # 蓝色
        }

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor("#252526"))
        self.setPalette(p)
        self.playback_finished.connect(self._on_playback_finished)

    def set_slides(self, slide_paths):
        self.raw_slides = [QPixmap(path) for path in slide_paths]
        self.reset_playback()

    def set_mouse_data(self, df):
        self.mouse_data = df
        # 预处理时间戳，只需一次
        if self.mouse_data is not None and not self.mouse_data.empty:
            self.mouse_data['Timestamp'] = pd.to_datetime(self.mouse_data['Timestamp'])
        self.reset_playback()

    def reset_playback(self):
        self.is_playing = False
        self.playback_timer.stop()
        self.current_data_index = 0
        self.update()  # 重绘到初始状态
        if self.mouse_data is not None:
            self.progress_updated.emit(0)

    def _update_frame(self):
        if not self.is_playing or self.mouse_data is None or self.current_data_index >= len(self.mouse_data) - 1:
            self.playback_finished.emit()
            return

        self.current_data_index += 1

        # 触发重绘
        self.update()

        # 更新外部进度条
        self.progress_updated.emit(self.current_data_index)

        # 设置下一次定时器的间隔
        if self.playback_mode == 'speed':
            current_time = self.mouse_data.at[self.current_data_index - 1, 'Timestamp']
            next_time = self.mouse_data.at[self.current_data_index, 'Timestamp']
            delta_seconds = (next_time - current_time).total_seconds()

            # 避免除零和过快/过慢的播放
            delay = max(0.01, delta_seconds) / self.playback_speed
            self.playback_timer.start(int(delay * 1000))
        else:  # interval mode
            self.playback_timer.start(int(self.fixed_interval * 1000))

    def _on_playback_finished(self):
        self.is_playing = False
        self.playback_timer.stop()
        # 可以发出一个信号通知UI更新播放按钮的状态
        # 在MainWindow中连接这个信号

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.mouse_data is None or self.raw_slides is None or self.mouse_data.empty or not self.raw_slides:
            return

        # 获取当前数据点对应的幻灯片索引
        try:
            current_row = self.mouse_data.iloc[self.current_data_index]
            slide_to_show_idx = int(current_row['SlideIndex']) - 1
        except (IndexError, KeyError):
            return

        if not (0 <= slide_to_show_idx < len(self.raw_slides)):
            return

        self.current_slide_index_in_data = slide_to_show_idx
        base_pixmap = self.raw_slides[self.current_slide_index_in_data]
        scaled_pixmap = base_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        final_pixmap = QPixmap(scaled_pixmap.size())
        final_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(final_pixmap)
        painter.drawPixmap(0, 0, scaled_pixmap)

        # ---- 动态绘制轨迹和标记 ----
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 找到当前幻灯片数据的起止点
        slide_data_indices = self.mouse_data.index[
            self.mouse_data['SlideIndex'] == self.current_slide_index_in_data + 1]
        if slide_data_indices.empty:
            painter.end()
            self.image_label.setPixmap(final_pixmap)
            return

        start_index = slide_data_indices[0]
        # 只绘制到当前数据点
        df_to_draw = self.mouse_data.loc[start_index: self.current_data_index]

        original_size = base_pixmap.size()
        displayed_size = scaled_pixmap.size()

        if original_size.width() > 0 and original_size.height() > 0:
            scale_x = displayed_size.width() / original_size.width()
            scale_y = displayed_size.height() / original_size.height()

            # 绘制轨迹线
            if self.show_trajectory and len(df_to_draw) > 1:
                pen = QPen(QColor(255, 0, 0, 180), 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                points = QPolygonF()
                for _, row in df_to_draw.iterrows():
                    points.append(QPointF(row['X'] * scale_x, row['Y'] * scale_y))
                painter.drawPolyline(points)

            # 绘制标记点
            painter.setPen(Qt.PenStyle.NoPen)
            for _, row in df_to_draw.iterrows():
                action_type = row.get('ActionType', 'UNKNOWN')
                if self.show_markers.get(action_type, False):
                    painter.setBrush(QBrush(self.marker_colors.get(action_type, QColor('white'))))
                    painter.drawEllipse(QPointF(row['X'] * scale_x, row['Y'] * scale_y), 5, 5)

        painter.end()
        self.image_label.setPixmap(final_pixmap)

    # --- Public slots for controlling playback ---
    def toggle_playback(self, play):
        if self.mouse_data is None: return
        self.is_playing = play
        if play:
            self._update_frame()  # 立即开始第一帧
        else:
            self.playback_timer.stop()

    def set_playback_mode(self, mode):
        self.playback_mode = mode

    def set_speed(self, speed):
        self.playback_speed = max(0.1, speed)  # 避免速度为0

    def set_interval(self, interval):
        self.fixed_interval = interval

    def set_draw_settings(self, settings):
        self.show_trajectory = settings['show_trajectory']
        self.show_markers = settings['show_markers']
        self.update()  # 立即重绘以反映设置变化

    def scrub_to_position(self, data_index):
        if self.mouse_data is None: return
        self.is_playing = False  # 拖动时暂停播放
        self.playback_timer.stop()
        self.current_data_index = data_index
        self.update()  # 重绘到新位置
        self.progress_updated.emit(self.current_data_index)

    def jump_to_slide(self, slide_number):
        if self.mouse_data is None: return

        matches = self.mouse_data.index[self.mouse_data['SlideIndex'] == slide_number]
        if not matches.empty:
            target_index = matches[0]
            self.scrub_to_position(target_index)