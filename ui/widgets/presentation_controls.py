# ui/widgets/presentation_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QSlider, QLineEdit, QPushButton, QCheckBox,
                             QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from ui.widgets.custom_widgets import Switch


class PresentationControls(QWidget):
    # --- 定义所有对外通信的信号 ---
    # 播放控制
    play_toggled = pyqtSignal(bool)  # True for play, False for pause
    progress_scrubbed = pyqtSignal(int)  # 用户拖动进度条时发出

    # 播放设置
    playback_mode_changed = pyqtSignal(str)  # 'speed' or 'interval'
    speed_changed = pyqtSignal(float)
    interval_changed = pyqtSignal(float)  # in seconds
    jump_to_slide_requested = pyqtSignal(int)

    # 绘图设置
    draw_settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        self.playback_mode_changed.emit('speed')  # 初始模式

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 轨迹线组
        trajectory_group = QGroupBox("轨迹线")
        trajectory_layout = QHBoxLayout()
        self.show_trajectory_switch = Switch()
        self.show_trajectory_switch.setChecked(True)
        trajectory_layout.addWidget(QLabel("显示轨迹线"))
        trajectory_layout.addStretch()
        trajectory_layout.addWidget(self.show_trajectory_switch)
        trajectory_group.setLayout(trajectory_layout)
        main_layout.addWidget(trajectory_group)

        # 标记点组
        markers_group = QGroupBox("标记点")
        markers_layout = QVBoxLayout()
        self.move_switch = Switch()
        self.hover_switch = Switch()
        self.hover_switch.setChecked(True)
        self.click_switch = Switch()
        self.click_switch.setChecked(True)
        markers_layout.addLayout(self._create_switch_layout("移动 (黑色)", self.move_switch))
        markers_layout.addLayout(self._create_switch_layout("停留 (橙色)", self.hover_switch))
        markers_layout.addLayout(self._create_switch_layout("点击 (蓝色)", self.click_switch))
        markers_group.setLayout(markers_layout)
        main_layout.addWidget(markers_group)

        # 播放类型组
        playback_group = QGroupBox("播放类型")
        playback_layout = QVBoxLayout()

        # 使用QButtonGroup确保互斥
        self.mode_button_group = QButtonGroup(self)

        # -- 倍速播放 --
        self.speed_checkbox = QCheckBox("倍速播放")
        self.speed_checkbox.setChecked(True)
        self.mode_button_group.addButton(self.speed_checkbox)

        speed_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 200)  # 0.5x to 20.0x
        self.speed_slider.setValue(10)  # 1.0x
        self.speed_edit = QLineEdit("1.0")
        self.speed_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")))
        self.speed_edit.setFixedWidth(50)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_edit)
        speed_layout.addWidget(QLabel("x"))

        # -- 等距播放 --
        self.interval_checkbox = QCheckBox("等距播放")
        self.mode_button_group.addButton(self.interval_checkbox)

        interval_layout = QHBoxLayout()
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(1, 100)  # 1.0s to 10.0s
        self.interval_slider.setValue(30)  # 3.0s
        self.interval_slider.setEnabled(False)  # 默认禁用
        self.interval_edit = QLineEdit("3.0")
        self.interval_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")))
        self.interval_edit.setFixedWidth(50)
        self.interval_edit.setEnabled(False)  # 默认禁用
        interval_layout.addWidget(self.interval_slider)
        interval_layout.addWidget(self.interval_edit)
        interval_layout.addWidget(QLabel("S"))

        # -- 跳转 --
        jump_layout = QHBoxLayout()
        self.jump_edit = QLineEdit()
        self.jump_edit.setPlaceholderText("页码")
        self.jump_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]{1,4}")))
        self.jump_button = QPushButton("跳转")
        jump_layout.addWidget(QLabel("跳转到:"))
        jump_layout.addWidget(self.jump_edit)
        jump_layout.addWidget(self.jump_button)

        playback_layout.addWidget(self.speed_checkbox)
        playback_layout.addLayout(speed_layout)
        playback_layout.addWidget(self.interval_checkbox)
        playback_layout.addLayout(interval_layout)
        playback_layout.addLayout(jump_layout)
        playback_group.setLayout(playback_layout)
        main_layout.addWidget(playback_group)

        # 播放控制
        play_control_group = QGroupBox("播放控制")
        play_control_layout = QHBoxLayout()
        self.play_button = QPushButton("▶ 播放")
        self.play_button.setCheckable(True)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_label = QLabel("0 / 0")

        play_control_layout.addWidget(self.play_button)
        play_control_layout.addWidget(self.progress_slider)
        play_control_layout.addWidget(self.progress_label)
        play_control_group.setLayout(play_control_layout)
        main_layout.addWidget(play_control_group)

    def _create_switch_layout(self, label_text, switch_widget):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addStretch()
        layout.addWidget(switch_widget)
        return layout

    def _connect_signals(self):
        # 播放控制
        self.play_button.toggled.connect(self._on_play_toggled)
        self.progress_slider.sliderReleased.connect(self._on_progress_scrubbed)  # 拖动释放后才触发

        # 模式切换
        self.speed_checkbox.toggled.connect(self._on_mode_changed)

        # 参数设置
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        self.speed_edit.editingFinished.connect(self._on_speed_edit_changed)
        self.interval_slider.valueChanged.connect(self._on_interval_slider_changed)
        self.interval_edit.editingFinished.connect(self._on_interval_edit_changed)

        # 跳转
        self.jump_button.clicked.connect(self._on_jump_requested)

        # 绘图开关
        self.show_trajectory_switch.toggled.connect(self._emit_draw_settings)
        self.move_switch.toggled.connect(self._emit_draw_settings)
        self.hover_switch.toggled.connect(self._emit_draw_settings)
        self.click_switch.toggled.connect(self._emit_draw_settings)

    # --- SLOTS for internal logic ---
    def _on_play_toggled(self, checked):
        self.play_button.setText("❚❚ 暂停" if checked else "▶ 播放")
        self.play_toggled.emit(checked)

    def _on_progress_scrubbed(self):
        self.progress_scrubbed.emit(self.progress_slider.value())

    def _on_mode_changed(self, is_speed_mode):
        self.speed_slider.setEnabled(is_speed_mode)
        self.speed_edit.setEnabled(is_speed_mode)
        self.interval_slider.setEnabled(not is_speed_mode)
        self.interval_edit.setEnabled(not is_speed_mode)

        mode = 'speed' if is_speed_mode else 'interval'
        self.playback_mode_changed.emit(mode)

    def _on_speed_slider_changed(self, value):
        speed = value / 10.0
        self.speed_edit.setText(f"{speed:.1f}")
        self.speed_changed.emit(speed)

    def _on_speed_edit_changed(self):
        try:
            speed = float(self.speed_edit.text())
            if 0.5 <= speed <= 20.0:
                self.speed_slider.setValue(int(speed * 10))
                self.speed_changed.emit(speed)
            else:
                self._on_speed_slider_changed(self.speed_slider.value())  # 恢复滑块值
        except ValueError:
            self._on_speed_slider_changed(self.speed_slider.value())  # 恢复滑块值

    def _on_interval_slider_changed(self, value):
        interval = value / 10.0
        self.interval_edit.setText(f"{interval:.1f}")
        self.interval_changed.emit(interval)

    def _on_interval_edit_changed(self):
        try:
            interval = float(self.interval_edit.text())
            if 0.1 <= interval <= 10.0:
                self.interval_slider.setValue(int(interval * 10))
                self.interval_changed.emit(interval)
            else:
                self._on_interval_slider_changed(self.interval_slider.value())
        except ValueError:
            self._on_interval_slider_changed(self.interval_slider.value())

    def _on_jump_requested(self):
        if self.jump_edit.text().isdigit():
            self.jump_to_slide_requested.emit(int(self.jump_edit.text()))

    def _emit_draw_settings(self):
        settings = {
            'show_trajectory': self.show_trajectory_switch.isChecked(),
            'show_markers': {
                'MOVE': self.move_switch.isChecked(),
                'HOVER': self.hover_switch.isChecked(),
                'CLICK': self.click_switch.isChecked()
            }
        }
        self.draw_settings_changed.emit(settings)

    # --- Public methods for MainWindow to call ---
    def set_progress_range(self, max_value):
        self.progress_slider.setRange(0, max_value)

    def update_progress(self, value):
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(value)
        self.progress_slider.blockSignals(False)
        self.progress_label.setText(f"{value} / {self.progress_slider.maximum()}")

    def reset_controls(self):
        self.play_button.setChecked(False)
        self.progress_slider.setRange(0, 0)
        self.update_progress(0)