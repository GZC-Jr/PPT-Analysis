# ui/widgets/analysis_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QButtonGroup, QColorDialog, QMenu,
                             QMessageBox)
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QAction, QColor
from PyQt6.QtCore import pyqtSignal,Qt
from ui.widgets.custom_widgets import Switch
from functools import partial


class ContextMenuLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)


class AnalysisControls(QWidget):
    analysis_requested = pyqtSignal(dict)
    export_csv_requested = pyqtSignal(dict)

    # ====================  修改点 1: 明确定义两个独立的信号 ====================
    module_style_requested = pyqtSignal()
    interpage_style_requested = pyqtSignal()

    # ========================================================================

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 模块分析组
        module_group = QGroupBox("模块")
        module_layout = QVBoxLayout()
        self.module_switch = Switch()
        module_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.module_switch))

        self.jump_edit = QLineEdit("0");
        self.jump_edit.setPlaceholderText("0为全局")
        self.jump_edit.setValidator(QIntValidator(0, 9999))
        self.eps_edit = QLineEdit("50.0");
        self.eps_edit.setValidator(QDoubleValidator(0.1, 1000.0, 2))
        self.min_samples_edit = QLineEdit("5");
        self.min_samples_edit.setValidator(QIntValidator(1, 1000))
        self.strength_edit = QLineEdit("10.0");
        self.strength_edit.setValidator(QDoubleValidator(0.0, 100.0, 2))

        form_layout = QVBoxLayout()
        form_layout.addLayout(self._create_edit_layout("跳转", self.jump_edit))
        form_layout.addLayout(self._create_edit_layout("邻近阈值", self.eps_edit))
        form_layout.addLayout(self._create_edit_layout("聚集阈值", self.min_samples_edit))
        form_layout.addLayout(self._create_edit_layout("强度阈值", self.strength_edit))

        # 按钮重命名以区分
        self.module_style_button = QPushButton("样式设置")
        self.export_csv_button = QPushButton("导出CSV文件")

        module_layout.addLayout(form_layout)
        module_layout.addWidget(self.module_style_button)
        module_layout.addWidget(self.export_csv_button)
        module_group.setLayout(module_layout)
        main_layout.addWidget(module_group)

        # 页际分析组
        interpage_group = QGroupBox("页际")
        interpage_layout = QVBoxLayout()
        self.interpage_switch = Switch()
        interpage_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.interpage_switch))

        self.divergence_switch = Switch()
        self.association_switch = Switch()
        self.page_mode_group = QButtonGroup(self);
        self.page_mode_group.setExclusive(True)
        self.page_mode_group.addButton(self.divergence_switch);
        self.page_mode_group.addButton(self.association_switch)

        interpage_layout.addLayout(self._create_switch_layout(QLabel("歧线"), self.divergence_switch))
        interpage_layout.addLayout(self._create_switch_layout(QLabel("关联"), self.association_switch))

        self.interpage_style_button = QPushButton("样式设置")
        interpage_layout.addWidget(self.interpage_style_button)

        interpage_group.setLayout(interpage_layout)
        main_layout.addWidget(interpage_group)

        # 保存图表组
        save_group = QGroupBox("保存图表")
        save_layout = QVBoxLayout()
        self.png_switch = Switch();
        self.png_switch.setChecked(True)
        self.svg_switch = Switch()
        save_layout.addLayout(self._create_switch_layout(QLabel("PNG"), self.png_switch))
        save_layout.addLayout(self._create_switch_layout(QLabel("SVG"), self.svg_switch))
        self.export_chart_button = QPushButton("导出图表")
        save_layout.addWidget(self.export_chart_button)
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)

        self.generate_button = QPushButton("生成分析图")
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
        self.generate_button.clicked.connect(self._emit_analysis_request)
        self.export_csv_button.clicked.connect(self._emit_export_csv_request)

        # ====================  修改点 2: 将按钮连接到各自正确的信号 ====================
        self.module_style_button.clicked.connect(self.module_style_requested.emit)
        self.interpage_style_button.clicked.connect(self.interpage_style_requested.emit)
        # ===========================================================================

    def _emit_analysis_request(self):
        try:
            config = {
                'module_on': self.module_switch.isChecked(),
                'page_num': int(self.jump_edit.text()),
                'eps': float(self.eps_edit.text()),
                'min_samples': int(self.min_samples_edit.text()),
                'strength_threshold': float(self.strength_edit.text()),
                'interpage_on': self.interpage_switch.isChecked(),
                'show_divergence': self.divergence_switch.isChecked(),
                'show_association': self.association_switch.isChecked()
            }
            self.analysis_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")

    def _emit_export_csv_request(self):
        try:
            config = {
                'eps': float(self.eps_edit.text()),
                'min_samples': int(self.min_samples_edit.text()),
                'strength_threshold': float(self.strength_edit.text()),
            }
            self.export_csv_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")