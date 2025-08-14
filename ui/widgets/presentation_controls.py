# ui/widgets/presentation_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QSlider, QLineEdit, QPushButton, QCheckBox,
                             QButtonGroup, QMenu, QInputDialog, QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator, QAction, QColor
from ui.widgets.custom_widgets import Switch
from functools import partial


class ContextMenuLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)


class PresentationControls(QWidget):
    play_toggled = pyqtSignal(bool)
    progress_scrubbed = pyqtSignal(int)
    playback_mode_changed = pyqtSignal(str)
    speed_changed = pyqtSignal(float)
    interval_changed = pyqtSignal(float)
    jump_to_slide_requested = pyqtSignal(int)
    draw_visibility_changed = pyqtSignal(dict)
    trajectory_props_changed = pyqtSignal(dict)
    marker_props_changed = pyqtSignal(str, dict)
    tail_props_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        self.playback_mode_changed.emit('speed')

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        trajectory_group = QGroupBox("轨迹线")
        trajectory_layout = QVBoxLayout()
        traj_line_layout = QHBoxLayout()
        self.trajectory_label = ContextMenuLabel("轨迹线")
        self.show_trajectory_switch = Switch();
        self.show_trajectory_switch.setChecked(True)
        traj_line_layout.addWidget(self.trajectory_label);
        traj_line_layout.addStretch();
        traj_line_layout.addWidget(self.show_trajectory_switch)
        tail_layout = QHBoxLayout()
        self.tail_label = QLabel("尾迹")
        self.show_tail_switch = Switch();
        self.show_tail_switch.setChecked(False);
        self.show_tail_switch.setEnabled(True)
        tail_layout.addWidget(self.tail_label);
        tail_layout.addStretch();
        tail_layout.addWidget(self.show_tail_switch)
        trajectory_layout.addLayout(traj_line_layout);
        trajectory_layout.addLayout(tail_layout)
        trajectory_group.setLayout(trajectory_layout)
        main_layout.addWidget(trajectory_group)

        markers_group = QGroupBox("标记点")
        markers_layout = QVBoxLayout()
        self.move_switch = Switch();
        self.move_label = ContextMenuLabel("移动")
        self.hover_switch = Switch();
        self.hover_switch.setChecked(True);
        self.hover_label = ContextMenuLabel("停留")
        self.click_switch = Switch();
        self.click_switch.setChecked(True);
        self.click_label = ContextMenuLabel("点击")
        markers_layout.addLayout(self._create_switch_layout(self.move_label, self.move_switch))
        markers_layout.addLayout(self._create_switch_layout(self.hover_label, self.hover_switch))
        markers_layout.addLayout(self._create_switch_layout(self.click_label, self.click_switch))
        markers_group.setLayout(markers_layout)
        main_layout.addWidget(markers_group)

        playback_group = QGroupBox("播放类型")
        playback_layout = QVBoxLayout()
        self.mode_button_group = QButtonGroup(self)

        # 倍速
        self.speed_checkbox = QCheckBox("倍速播放");
        self.speed_checkbox.setChecked(True)
        self.mode_button_group.addButton(self.speed_checkbox)
        speed_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal);
        self.speed_slider.setRange(5, 200);
        self.speed_slider.setValue(10)
        self.speed_edit = QLineEdit("1.0");
        self.speed_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")));
        self.speed_edit.setFixedWidth(50)
        speed_layout.addWidget(self.speed_slider);
        speed_layout.addWidget(self.speed_edit);
        speed_layout.addWidget(QLabel("x"))

        # 等距
        self.interval_checkbox = QCheckBox("等距播放")
        self.mode_button_group.addButton(self.interval_checkbox)
        interval_layout = QHBoxLayout()
        self.interval_slider = QSlider(Qt.Orientation.Horizontal);
        self.interval_slider.setRange(1, 100);
        self.interval_slider.setValue(30);
        self.interval_slider.setEnabled(False)
        self.interval_edit = QLineEdit("3.0");
        self.interval_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")));
        self.interval_edit.setFixedWidth(50);
        self.interval_edit.setEnabled(False)
        interval_layout.addWidget(self.interval_slider);
        interval_layout.addWidget(self.interval_edit);
        interval_layout.addWidget(QLabel("S"))

        # 跳转
        jump_layout = QHBoxLayout()
        self.jump_edit = QLineEdit();
        self.jump_edit.setPlaceholderText("页码");
        self.jump_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]{1,4}")))
        self.jump_button = QPushButton("跳转")
        jump_layout.addWidget(QLabel("跳转到:"));
        jump_layout.addWidget(self.jump_edit);
        jump_layout.addWidget(self.jump_button)

        # ====================  修改点 ====================
        # 将所有控件按正确顺序添加到布局中，不再使用单行写法
        playback_layout.addWidget(self.speed_checkbox)
        playback_layout.addLayout(speed_layout)
        playback_layout.addWidget(self.interval_checkbox)  # <-- 这就是被遗漏的那一行
        playback_layout.addLayout(interval_layout)
        playback_layout.addLayout(jump_layout)
        # ===============================================

        playback_group.setLayout(playback_layout)
        main_layout.addWidget(playback_group)

        play_control_group = QGroupBox("播放控制")
        play_control_layout = QHBoxLayout()
        self.play_button = QPushButton("▶ 播放");
        self.play_button.setCheckable(True)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_label = QLabel("0 / 0")
        play_control_layout.addWidget(self.play_button);
        play_control_layout.addWidget(self.progress_slider);
        play_control_layout.addWidget(self.progress_label)
        play_control_group.setLayout(play_control_layout)
        main_layout.addWidget(play_control_group)

    def _create_switch_layout(self, label_widget, switch_widget):
        layout = QHBoxLayout();
        layout.addWidget(label_widget);
        layout.addStretch();
        layout.addWidget(switch_widget)
        return layout

    def _connect_signals(self):
        self.trajectory_label.customContextMenuRequested.connect(self._show_trajectory_menu)
        self.move_label.customContextMenuRequested.connect(partial(self._show_marker_menu, 'MOVE'))
        self.hover_label.customContextMenuRequested.connect(partial(self._show_marker_menu, 'HOVER'))
        self.click_label.customContextMenuRequested.connect(partial(self._show_marker_menu, 'CLICK'))
        self.show_trajectory_switch.toggled.connect(self._emit_visibility_settings);
        self.show_tail_switch.toggled.connect(self._emit_visibility_settings);
        self.move_switch.toggled.connect(self._emit_visibility_settings);
        self.hover_switch.toggled.connect(self._emit_visibility_settings);
        self.click_switch.toggled.connect(self._emit_visibility_settings)
        self.show_trajectory_switch.toggled.connect(self.show_tail_switch.setEnabled)
        self.play_button.toggled.connect(self._on_play_toggled);
        self.progress_slider.sliderReleased.connect(self._on_progress_scrubbed);
        self.speed_checkbox.toggled.connect(self._on_mode_changed);
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed);
        self.speed_edit.editingFinished.connect(self._on_speed_edit_changed);
        self.interval_slider.valueChanged.connect(self._on_interval_slider_changed);
        self.interval_edit.editingFinished.connect(self._on_interval_edit_changed);
        self.jump_button.clicked.connect(self._on_jump_requested)

    def _show_trajectory_menu(self, pos):
        menu = QMenu(self)
        thickness_action = QAction("设置粗细...", self);
        color_action = QAction("设置颜色...", self);
        style_menu = QMenu("设置线型", self)
        thickness_action.triggered.connect(self.handle_trajectory_thickness_dialog);
        color_action.triggered.connect(self.handle_trajectory_color_dialog)
        styles = {"实线": Qt.PenStyle.SolidLine, "虚线": Qt.PenStyle.DashLine, "点线": Qt.PenStyle.DotLine}
        for name, style in styles.items():
            action = QAction(name, self);
            action.triggered.connect(partial(self.trajectory_props_changed.emit, {'style': style}));
            style_menu.addAction(action)
        menu.addAction(thickness_action);
        menu.addAction(color_action);
        menu.addMenu(style_menu)
        menu.exec(self.trajectory_label.mapToGlobal(pos))

    def _show_marker_menu(self, marker_type, pos):
        menu = QMenu(self)
        radius_action = QAction("设置半径...", self);
        color_action = QAction("设置颜色...", self)
        radius_action.triggered.connect(partial(self.handle_marker_radius_dialog, marker_type));
        color_action.triggered.connect(partial(self.handle_marker_color_dialog, marker_type))
        menu.addAction(radius_action);
        menu.addAction(color_action)
        menu.exec(self.sender().mapToGlobal(pos))

    def handle_trajectory_thickness_dialog(self):
        val, ok = QInputDialog.getInt(self, "轨迹线粗细", "输入粗细 (1-10):", value=2, min=1, max=10)
        if ok: self.trajectory_props_changed.emit({'thickness': val})

    def handle_trajectory_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid(): self.trajectory_props_changed.emit({'color': color})

    def handle_marker_radius_dialog(self, marker_type):
        val, ok = QInputDialog.getInt(self, f"{marker_type} 标记点半径", "输入半径 (1-20):", value=5, min=1, max=20)
        if ok: self.marker_props_changed.emit(marker_type, {'radius': val})

    def handle_marker_color_dialog(self, marker_type):
        color = QColorDialog.getColor()
        if color.isValid(): self.marker_props_changed.emit(marker_type, {'color': color})

    def _emit_visibility_settings(self):
        settings = {'show_trajectory': self.show_trajectory_switch.isChecked(),
                    'show_tail': self.show_tail_switch.isChecked(),
                    'show_markers': {'MOVE': self.move_switch.isChecked(), 'HOVER': self.hover_switch.isChecked(),
                                     'CLICK': self.click_switch.isChecked()}}
        self.draw_visibility_changed.emit(settings)

    def _on_play_toggled(self, checked):
        self.play_button.setText("❚❚ 暂停" if checked else "▶ 播放"); self.play_toggled.emit(checked)

    def _on_progress_scrubbed(self):
        self.progress_scrubbed.emit(self.progress_slider.value())

    def _on_mode_changed(self, is_speed_mode):
        self.speed_slider.setEnabled(is_speed_mode); self.speed_edit.setEnabled(
            is_speed_mode); self.interval_slider.setEnabled(not is_speed_mode); self.interval_edit.setEnabled(
            not is_speed_mode); self.playback_mode_changed.emit('speed' if is_speed_mode else 'interval')

    def _on_speed_slider_changed(self, value):
        speed = value / 10.0; self.speed_edit.setText(f"{speed:.1f}"); self.speed_changed.emit(speed)

    def _on_speed_edit_changed(self):
        try:
            speed = float(self.speed_edit.text()); self.speed_slider.setValue(
                int(speed * 10) if 0.5 <= speed <= 20.0 else self.speed_slider.value())
        except ValueError:
            self._on_speed_slider_changed(self.speed_slider.value())

    def _on_interval_slider_changed(self, value):
        interval = value / 10.0; self.interval_edit.setText(f"{interval:.1f}"); self.interval_changed.emit(interval)

    def _on_interval_edit_changed(self):
        try:
            interval = float(self.interval_edit.text()); self.interval_slider.setValue(
                int(interval * 10) if 0.1 <= interval <= 10.0 else self.interval_slider.value())
        except ValueError:
            self._on_interval_slider_changed(self.interval_slider.value())

    def _on_jump_requested(self):
        if self.jump_edit.text().isdigit(): self.jump_to_slide_requested.emit(int(self.jump_edit.text()))

    def set_progress_range(self, max_value):
        self.progress_slider.setRange(0, max_value)

    def update_progress(self, value):
        self.progress_slider.blockSignals(True); self.progress_slider.setValue(
            value); self.progress_slider.blockSignals(False); self.progress_label.setText(
            f"{value} / {self.progress_slider.maximum()}")

    def reset_controls(self):
        self.play_button.setChecked(False); self.progress_slider.setRange(0, 0); self.update_progress(0)