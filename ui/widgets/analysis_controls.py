# ui/widgets/analysis_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QButtonGroup, QColorDialog, QMenu,
                             QMessageBox, QSlider, QCheckBox)
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QAction, QColor, QRegularExpressionValidator
from PyQt6.QtCore import pyqtSignal, Qt, QRegularExpression
from ui.widgets.custom_widgets import Switch
from functools import partial


class AnalysisControls(QWidget):
    analysis_requested = pyqtSignal(dict)
    export_csv_requested = pyqtSignal(dict)
    module_style_requested = pyqtSignal()
    interpage_style_requested = pyqtSignal()
    export_chart_requested = pyqtSignal(dict)
    # 播放控制信号
    play_toggled = pyqtSignal(bool)
    progress_scrubbed = pyqtSignal(int)
    playback_mode_changed = pyqtSignal(str)
    speed_changed = pyqtSignal(float)
    interval_changed = pyqtSignal(float)
    page_changed = pyqtSignal(int)  # 用于跳转和左右键

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        # 初始时禁用两个内容面板
        self.module_content_widget.setEnabled(False)
        self.interpage_content_widget.setEnabled(False)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_mode_group = QButtonGroup(self)
        self.main_mode_group.setExclusive(True)

        # --- 模块分析组重构 ---
        module_group = QGroupBox("模块")
        module_main_layout = QVBoxLayout(module_group)

        self.module_switch = Switch()
        self.main_mode_group.addButton(self.module_switch, 1)
        module_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.module_switch))

        # 创建一个容器Widget来存放所有会被禁用的控件
        self.module_content_widget = QWidget()
        module_content_layout = QVBoxLayout(self.module_content_widget)
        module_content_layout.setContentsMargins(0, 5, 0, 0)  # 添加一点顶部间距

        # -- 阈值设置 --
        self.eps_edit = QLineEdit("50.0");
        self.eps_edit.setValidator(QDoubleValidator(0.1, 1000.0, 2))
        self.min_samples_edit = QLineEdit("5");
        self.min_samples_edit.setValidator(QIntValidator(1, 1000))
        self.strength_edit = QLineEdit("10.0");
        self.strength_edit.setValidator(QDoubleValidator(0.0, 100.0, 2))
        form_layout = QVBoxLayout()
        form_layout.addLayout(self._create_edit_layout("邻近阈值", self.eps_edit))
        form_layout.addLayout(self._create_edit_layout("聚集阈值", self.min_samples_edit))
        form_layout.addLayout(self._create_edit_layout("强度阈值", self.strength_edit))

        # -- 播放控制 (从PresentationControls借鉴并修改) --
        playback_group = QGroupBox("播放控制")
        playback_layout = QVBoxLayout(playback_group)

        # 播放类型
        self.play_mode_group = QButtonGroup(self);
        self.play_mode_group.setExclusive(True)
        self.speed_checkbox = QCheckBox("倍速");
        self.speed_checkbox.setChecked(True);
        self.play_mode_group.addButton(self.speed_checkbox)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal);
        self.speed_slider.setRange(5, 200);
        self.speed_slider.setValue(10)
        self.speed_edit = QLineEdit("1.0");
        self.speed_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")));
        self.speed_edit.setFixedWidth(40)
        speed_layout = QHBoxLayout();
        speed_layout.addWidget(self.speed_checkbox);
        speed_layout.addWidget(self.speed_slider);
        speed_layout.addWidget(self.speed_edit);
        speed_layout.addWidget(QLabel("x"))

        self.interval_checkbox = QCheckBox("等距");
        self.play_mode_group.addButton(self.interval_checkbox)
        self.interval_slider = QSlider(Qt.Orientation.Horizontal);
        self.interval_slider.setRange(1, 100);
        self.interval_slider.setValue(30);
        self.interval_slider.setEnabled(False)
        self.interval_edit = QLineEdit("3.0");
        self.interval_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9.]{1,4}")));
        self.interval_edit.setFixedWidth(40);
        self.interval_edit.setEnabled(False)
        interval_layout = QHBoxLayout();
        interval_layout.addWidget(self.interval_checkbox);
        interval_layout.addWidget(self.interval_slider);
        interval_layout.addWidget(self.interval_edit);
        interval_layout.addWidget(QLabel("S"))

        # 跳转控制
        self.jump_edit = QLineEdit("0");
        self.jump_edit.setPlaceholderText("0为全局");
        self.jump_edit.setValidator(QIntValidator(0, 9999))
        self.prev_page_btn = QPushButton("◀");
        self.next_page_btn = QPushButton("▶")
        self.prev_page_btn.setFixedWidth(30);
        self.next_page_btn.setFixedWidth(30)
        jump_layout = QHBoxLayout();
        jump_layout.addWidget(QLabel("跳转"));
        jump_layout.addWidget(self.jump_edit);
        jump_layout.addWidget(self.prev_page_btn);
        jump_layout.addWidget(self.next_page_btn)

        # 播放进度条
        self.play_button = QPushButton("▶");
        self.play_button.setCheckable(True);
        self.play_button.setFixedWidth(40)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_label = QLabel("0/0");
        self.progress_label.setFixedWidth(60)
        play_bar_layout = QHBoxLayout();
        play_bar_layout.addWidget(self.play_button);
        play_bar_layout.addWidget(self.progress_slider);
        play_bar_layout.addWidget(self.progress_label)

        playback_layout.addLayout(speed_layout);
        playback_layout.addLayout(interval_layout);
        playback_layout.addLayout(jump_layout);
        playback_layout.addLayout(play_bar_layout)

        # -- 底部按钮 --
        self.module_style_button = QPushButton("样式设置")
        self.export_csv_button = QPushButton("导出CSV文件")

        module_content_layout.addLayout(form_layout)
        module_content_layout.addWidget(playback_group)
        module_content_layout.addWidget(self.module_style_button)
        module_content_layout.addWidget(self.export_csv_button)

        module_main_layout.addWidget(self.module_content_widget)
        main_layout.addWidget(module_group)

        # --- 页际分析组重构 ---
        interpage_group = QGroupBox("页际")
        interpage_main_layout = QVBoxLayout(interpage_group)

        self.interpage_switch = Switch()
        self.main_mode_group.addButton(self.interpage_switch, 2)
        interpage_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.interpage_switch))

        # 创建第二个容器Widget
        self.interpage_content_widget = QWidget()
        interpage_content_layout = QVBoxLayout(self.interpage_content_widget)
        interpage_content_layout.setContentsMargins(0, 5, 0, 0)

        self.divergence_switch = Switch()
        self.association_switch = Switch()
        self.page_mode_group = QButtonGroup(self);
        self.page_mode_group.setExclusive(True)
        self.page_mode_group.addButton(self.divergence_switch);
        self.page_mode_group.addButton(self.association_switch)
        interpage_content_layout.addLayout(self._create_switch_layout(QLabel("歧线"), self.divergence_switch))
        interpage_content_layout.addLayout(self._create_switch_layout(QLabel("关联"), self.association_switch))
        self.interpage_style_button = QPushButton("样式设置")
        interpage_content_layout.addWidget(self.interpage_style_button)

        interpage_main_layout.addWidget(self.interpage_content_widget)
        main_layout.addWidget(interpage_group)

        # ... (保存图表组和生成按钮保持不变) ...
        save_group = QGroupBox("保存图表");
        save_layout = QVBoxLayout()
        self.png_switch = Switch();
        self.png_switch.setChecked(True);
        self.svg_switch = Switch()
        self.format_group = QButtonGroup(self);
        self.format_group.setExclusive(True);
        self.format_group.addButton(self.png_switch);
        self.format_group.addButton(self.svg_switch)
        save_layout.addLayout(self._create_switch_layout(QLabel("PNG"), self.png_switch));
        save_layout.addLayout(self._create_switch_layout(QLabel("SVG"), self.svg_switch))
        self.export_chart_button = QPushButton("导出图表");
        save_layout.addWidget(self.export_chart_button);
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)
        self.generate_button = QPushButton("生成分析图");
        main_layout.addWidget(self.generate_button)

    def _create_switch_layout(self, label, switch):
        layout = QHBoxLayout();
        layout.addWidget(label);
        layout.addStretch();
        layout.addWidget(switch)
        return layout

    def _create_edit_layout(self, label_text, edit_widget):
        layout = QHBoxLayout();
        label = QLabel(label_text);
        label.setFixedWidth(60)
        layout.addWidget(label);
        layout.addWidget(edit_widget)
        return layout

    def _connect_signals(self):
        self.main_mode_group.buttonToggled.connect(self.on_main_mode_changed)
        self.generate_button.clicked.connect(self._emit_analysis_request)
        self.export_csv_button.clicked.connect(self._emit_export_csv_request)
        self.module_style_button.clicked.connect(self.module_style_requested.emit)
        self.interpage_style_button.clicked.connect(self.interpage_style_requested.emit)
        self.export_chart_button.clicked.connect(self._emit_export_chart_request)
        # --- 连接新的播放控制信号 ---
        self.play_button.toggled.connect(self._on_play_toggled)
        self.progress_slider.sliderReleased.connect(self.progress_scrubbed.emit)
        self.speed_checkbox.toggled.connect(self._on_play_mode_changed)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        self.speed_edit.editingFinished.connect(self._on_speed_edit_changed)
        self.interval_slider.valueChanged.connect(self._on_interval_slider_changed)
        self.interval_edit.editingFinished.connect(self._on_interval_edit_changed)
        self.jump_edit.editingFinished.connect(self._on_jump_changed)
        self.prev_page_btn.clicked.connect(self._on_prev_page)
        self.next_page_btn.clicked.connect(self._on_next_page)

     # --- 新的槽函数 ---
    def _on_play_toggled(self, checked):
        self.play_button.setText("❚❚" if checked else "▶")
        self.play_toggled.emit(checked)

    def _on_play_mode_changed(self, is_speed_mode):
        self.speed_slider.setEnabled(is_speed_mode)
        self.speed_edit.setEnabled(is_speed_mode)
        self.interval_slider.setEnabled(not is_speed_mode)
        self.interval_edit.setEnabled(not is_speed_mode)
        self.playback_mode_changed.emit('speed' if is_speed_mode else 'interval')

    def _on_speed_slider_changed(self, value):
        speed = value / 10.0;
        self.speed_edit.setText(f"{speed:.1f}");
        self.speed_changed.emit(speed)

    def _on_speed_edit_changed(self):
        try:
            speed = float(self.speed_edit.text()); self.speed_slider.setValue(int(speed * 10))
        except ValueError:
            self._on_speed_slider_changed(self.speed_slider.value())

    def _on_interval_slider_changed(self, value):
        interval = value / 10.0;
        self.interval_edit.setText(f"{interval:.1f}");
        self.interval_changed.emit(interval)

    def _on_interval_edit_changed(self):
        try:
            interval = float(self.interval_edit.text()); self.interval_slider.setValue(int(interval * 10))
        except ValueError:
            self._on_interval_slider_changed(self.interval_slider.value())

    def _on_jump_changed(self):
        if self.jump_edit.text().isdigit(): self.page_changed.emit(int(self.jump_edit.text()))

    def _on_prev_page(self):
        if self.jump_edit.text().isdigit():
            page = max(0, int(self.jump_edit.text()) - 1)
            self.jump_edit.setText(str(page))
            self.page_changed.emit(page)

    def _on_next_page(self):
        if self.jump_edit.text().isdigit():
            page = int(self.jump_edit.text()) + 1
            self.jump_edit.setText(str(page))
            self.page_changed.emit(page)

        # --- 公共方法 ---

    def set_progress_range(self, max_val):
        self.progress_slider.setRange(0, max_val)

    def update_progress(self, val):
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(val)
        self.progress_slider.blockSignals(False)
        self.progress_label.setText(f"{val}/{self.progress_slider.maximum()}")

    # --- 逻辑修正的槽函数 ---
    def on_main_mode_changed(self, button, checked):
        # 我们只关心哪个按钮被选中了
        if checked:
            is_module_mode = (button == self.module_switch)
            is_interpage_mode = (button == self.interpage_switch)

            # 控制内部容器的可用状态，而不是整个GroupBox
            self.module_content_widget.setEnabled(is_module_mode)
            self.interpage_content_widget.setEnabled(is_interpage_mode)
        # 当一个按钮被取消选中时（因为另一个被选中了），我们不需要做任何事
        # 当用户手动取消选中时，我们需要禁用两个面板
        elif not self.main_mode_group.checkedButton():
            self.module_content_widget.setEnabled(False)
            self.interpage_content_widget.setEnabled(False)

    def _emit_export_chart_request(self):
        mode = 'none'
        if self.module_switch.isChecked():
            mode = 'module'
        elif self.interpage_switch.isChecked():
            mode = 'interpage'
        config = {'mode': mode, 'format': 'svg' if self.svg_switch.isChecked() else 'png'}
        self.export_chart_requested.emit(config)

    def _emit_analysis_request(self):
        try:
            config = {'module_on': self.module_switch.isChecked(), 'page_num': int(self.jump_edit.text()),
                      'eps': float(self.eps_edit.text()), 'min_samples': int(self.min_samples_edit.text()),
                      'strength_threshold': float(self.strength_edit.text()),
                      'interpage_on': self.interpage_switch.isChecked(),
                      'show_divergence': self.divergence_switch.isChecked(),
                      'show_association': self.association_switch.isChecked()}
            self.analysis_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")

    def _emit_export_csv_request(self):
        try:
            config = {'eps': float(self.eps_edit.text()), 'min_samples': int(self.min_samples_edit.text()),
                      'strength_threshold': float(self.strength_edit.text())}
            self.export_csv_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")