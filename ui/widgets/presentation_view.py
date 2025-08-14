# ui/widgets/presentation_view.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal
import pandas as pd
import numpy as np


class PresentationView(QWidget):
    progress_updated = pyqtSignal(int)
    playback_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel("请先上传PPT和CSV文件以开始演示")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

        # --- 重新组织状态和设置 ---
        self.raw_slides = []
        self.mouse_data = None
        self.is_playing = False
        self.current_data_index = 0
        self.playback_timer = QTimer(self);
        self.playback_timer.timeout.connect(self._update_frame)

        # 播放参数
        self.playback_mode = 'speed'
        self.playback_speed = 1.0
        self.fixed_interval = 3.0

        # 可见性设置
        self.visibility = {
            'show_trajectory': True,
            'show_tail': False,
            'show_markers': {'MOVE': False, 'HOVER': True, 'CLICK': True}
        }
        # 详细属性设置
        self.trajectory_props = {
            'color': QColor("red"), 'thickness': 2, 'style': Qt.PenStyle.SolidLine
        }
        self.tail_props = {'length': 50}  # 尾迹长度（数据点数量）
        self.marker_props = {
            'MOVE': {'color': QColor(0, 0, 0, 150), 'radius': 4},
            'HOVER': {'color': QColor(255, 165, 0, 200), 'radius': 5},
            'CLICK': {'color': QColor(0, 100, 255, 255), 'radius': 5}
        }

        self.setAutoFillBackground(True)
        p = self.palette();
        p.setColor(self.backgroundRole(), QColor("#252526"));
        self.setPalette(p)
        self.playback_finished.connect(self._on_playback_finished)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.mouse_data is None or self.raw_slides is None or self.mouse_data.empty or not self.raw_slides: return

        try:
            current_row = self.mouse_data.iloc[self.current_data_index]
            slide_to_show_idx = int(current_row['SlideIndex']) - 1
        except (IndexError, KeyError):
            return

        if not (0 <= slide_to_show_idx < len(self.raw_slides)): return

        base_pixmap = self.raw_slides[slide_to_show_idx]
        scaled_pixmap = base_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
        final_pixmap = QPixmap(scaled_pixmap.size());
        final_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(final_pixmap)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        slide_data_indices = self.mouse_data.index[self.mouse_data['SlideIndex'] == slide_to_show_idx + 1]
        if slide_data_indices.empty:
            painter.end();
            self.image_label.setPixmap(final_pixmap);
            return

        start_index = slide_data_indices[0]
        df_to_draw = self.mouse_data.loc[start_index: self.current_data_index]

        original_size = base_pixmap.size()
        displayed_size = scaled_pixmap.size()

        if original_size.width() > 0 and original_size.height() > 0:
            scale_x = displayed_size.width() / original_size.width()
            scale_y = displayed_size.height() / original_size.height()

            # --- 核心绘图逻辑重写 ---
            if self.visibility['show_trajectory'] and len(df_to_draw) > 1:
                if self.visibility['show_tail']:
                    # 绘制尾迹
                    tail_len = self.tail_props['length']
                    points_to_draw = df_to_draw.tail(tail_len)

                    for i in range(1, len(points_to_draw)):
                        p1 = points_to_draw.iloc[i - 1]
                        p2 = points_to_draw.iloc[i]

                        # 计算淡出效果的透明度
                        alpha = int(255 * (i / len(points_to_draw)))
                        color = self.trajectory_props['color']
                        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha),
                                   self.trajectory_props['thickness'],
                                   self.trajectory_props['style'])
                        painter.setPen(pen)
                        painter.drawLine(QPointF(p1['X'] * scale_x, p1['Y'] * scale_y),
                                         QPointF(p2['X'] * scale_x, p2['Y'] * scale_y))
                else:
                    # 绘制完整轨迹线
                    pen = QPen(self.trajectory_props['color'], self.trajectory_props['thickness'],
                               self.trajectory_props['style'])
                    painter.setPen(pen)
                    points = QPolygonF(
                        [QPointF(row['X'] * scale_x, row['Y'] * scale_y) for _, row in df_to_draw.iterrows()])
                    painter.drawPolyline(points)

            # 绘制标记点
            painter.setPen(Qt.PenStyle.NoPen)
            for _, row in df_to_draw.iterrows():
                action_type = row.get('ActionType', 'UNKNOWN')
                if self.visibility['show_markers'].get(action_type, False):
                    props = self.marker_props.get(action_type, {'color': QColor('white'), 'radius': 5})
                    painter.setBrush(QBrush(props['color']))
                    painter.drawEllipse(QPointF(row['X'] * scale_x, row['Y'] * scale_y), props['radius'],
                                        props['radius'])

        painter.end()
        self.image_label.setPixmap(final_pixmap)

    # --- 新的公共槽，用于接收来自Controls的设置 ---
    def update_visibility(self, settings):
        self.visibility = settings
        self.update()

    def update_trajectory_props(self, props):
        self.trajectory_props.update(props)
        self.update()

    def update_marker_props(self, marker_type, props):
        if marker_type in self.marker_props:
            self.marker_props[marker_type].update(props)
            self.update()

    # --- 其他方法保持不变 ---
    def set_slides(self, slide_paths):
        self.raw_slides = [QPixmap(path) for path in slide_paths]; self.reset_playback()

    def set_mouse_data(self, df):
        if df is not None and not df.empty:
            self.mouse_data = df.copy(); self.mouse_data['Timestamp'] = pd.to_datetime(self.mouse_data['Timestamp'])
        else:
            self.mouse_data = None
        self.reset_playback()

    def reset_playback(self):
        self.is_playing = False; self.playback_timer.stop(); self.current_data_index = 0; self.update(); self.progress_updated.emit(
            0)

    def _update_frame(self):
        if not self.is_playing or self.mouse_data is None or self.current_data_index >= len(
            self.mouse_data) - 1: self.playback_finished.emit(); return
        self.current_data_index += 1;
        self.update();
        self.progress_updated.emit(self.current_data_index)
        if self.playback_mode == 'speed':
            delta = (self.mouse_data.at[self.current_data_index, 'Timestamp'] - self.mouse_data.at[
                self.current_data_index - 1, 'Timestamp']).total_seconds()
            delay = max(0.01, delta) / self.playback_speed;
            self.playback_timer.start(int(delay * 1000))
        else:
            self.playback_timer.start(int(self.fixed_interval * 1000))

    def _on_playback_finished(self):
        self.is_playing = False; self.playback_timer.stop()

    def toggle_playback(self, play):
        if self.mouse_data is not None and not self.mouse_data.empty: self.is_playing = play; self._update_frame() if play else self.playback_timer.stop()

    def set_playback_mode(self, mode):
        self.playback_mode = mode

    def set_speed(self, speed):
        self.playback_speed = max(0.1, speed)

    def set_interval(self, interval):
        self.fixed_interval = interval

    def scrub_to_position(self, data_index):
        if self.mouse_data is None: return
        self.is_playing = False;
        self.playback_timer.stop();
        self.current_data_index = data_index;
        self.update();
        self.progress_updated.emit(self.current_data_index)

    def jump_to_slide(self, slide_number):
        if self.mouse_data is None: return
        matches = self.mouse_data.index[self.mouse_data['SlideIndex'] == slide_number]
        if not matches.empty: self.scrub_to_position(matches[0])