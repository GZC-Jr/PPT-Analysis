from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QSlider, QLineEdit, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.widgets.custom_widgets import Switch  # 导入自定义开关


class PresentationControls(QWidget):
    # 定义信号，用于与视图通信
    settings_changed = pyqtSignal(dict)
    play_pause_clicked = pyqtSignal()
    progress_changed = pyqtSignal(int)
    jump_to_slide = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

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
        self.move_switch.setChecked(False)  # 移动点默认关闭，因为太多了
        move_layout = QHBoxLayout()
        move_layout.addWidget(QLabel("移动"))
        move_layout.addStretch()
        move_layout.addWidget(self.move_switch)

        self.hover_switch = Switch()
        self.hover_switch.setChecked(True)
        hover_layout = QHBoxLayout()
        hover_layout.addWidget(QLabel("停留"))
        hover_layout.addStretch()
        hover_layout.addWidget(self.hover_switch)

        self.click_switch = Switch()
        self.click_switch.setChecked(True)
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel("点击"))
        click_layout.addStretch()
        click_layout.addWidget(self.click_switch)

        markers_layout.addLayout(move_layout)
        markers_layout.addLayout(hover_layout)
        markers_layout.addLayout(click_layout)
        markers_group.setLayout(markers_layout)
        main_layout.addWidget(markers_group)

        # 播放类型组
        playback_group = QGroupBox("播放类型")
        playback_layout = QVBoxLayout()

        self.speed_checkbox = QCheckBox("倍速播放")
        self.speed_checkbox.setChecked(True)
        speed_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 200)  # 0.5x to 20x
        self.speed_slider.setValue(10)  # 1.0x
        self.speed_label = QLabel("1.0x")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)

        self.interval_checkbox = QCheckBox("等距播放")
        interval_layout = QHBoxLayout()
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(10, 100)  # 1.0s to 10.0s
        self.interval_slider.setValue(30)  # 3.0s
        self.interval_label = QLabel("3.0 S")
        interval_layout.addWidget(self.interval_slider)
        interval_layout.addWidget(self.interval_label)
        self.interval_checkbox.toggled.connect(self.interval_slider.setEnabled)

        self.jump_layout = QHBoxLayout()
        self.jump_edit = QLineEdit()
        self.jump_edit.setPlaceholderText("页码")
        self.jump_button = QPushButton("跳转")
        self.jump_layout.addWidget(QLabel("跳转到:"))
        self.jump_layout.addWidget(self.jump_edit)
        self.jump_layout.addWidget(self.jump_button)

        playback_layout.addWidget(self.speed_checkbox)
        playback_layout.addLayout(speed_layout)
        playback_layout.addWidget(self.interval_checkbox)
        playback_layout.addLayout(interval_layout)
        playback_layout.addLayout(self.jump_layout)
        playback_group.setLayout(playback_layout)
        main_layout.addWidget(playback_group)

        # 播放控制
        play_control_layout = QHBoxLayout()
        self.play_button = QPushButton("▶ 播放")
        self.play_button.setCheckable(True)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)

        play_control_layout.addWidget(self.play_button)
        play_control_layout.addWidget(self.progress_slider)
        main_layout.addLayout(play_control_layout)

        # 连接信号
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        self.interval_slider.valueChanged.connect(self._update_interval_label)
        self.speed_checkbox.toggled.connect(self._on_playback_type_changed)
        self.interval_checkbox.toggled.connect(self._on_playback_type_changed)

    def _update_speed_label(self, value):
        self.speed_label.setText(f"{value / 10.0:.1f}x")

    def _update_interval_label(self, value):
        self.interval_label.setText(f"{value / 10.0:.1f} S")

    def _on_playback_type_changed(self, checked):
        sender = self.sender()
        if checked:
            if sender == self.speed_checkbox:
                self.interval_checkbox.setChecked(False)
            elif sender == self.interval_checkbox:
                self.speed_checkbox.setChecked(False)
        self.speed_slider.setEnabled(self.speed_checkbox.isChecked())
        self.interval_slider.setEnabled(self.interval_checkbox.isChecked())