# ui/widgets/chart_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QRadioButton,
                             QLineEdit, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
from ui.widgets.custom_widgets import Switch


class ChartControls(QWidget):
    generate_chart_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.variable_options = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        type_group = QGroupBox("图表类型")
        type_layout = QVBoxLayout()
        self.bar_switch = Switch();
        self.scatter_switch = Switch();
        self.line_switch = Switch()
        type_layout.addLayout(self._create_switch_layout("条形图", self.bar_switch))
        type_layout.addLayout(self._create_switch_layout("散点图", self.scatter_switch))
        type_layout.addLayout(self._create_switch_layout("折线图", self.line_switch))
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        # --- “图表编辑”组重构 ---
        edit_group = QGroupBox("图表编辑")
        # 使用QFormLayout可以更好地对齐标签和控件
        edit_form_layout = QFormLayout()

        # 新增：“指定”输入框
        self.page_filter_edit = QLineEdit()
        self.page_filter_edit.setPlaceholderText("0为全局")
        # 使用QIntValidator确保只能输入非负整数
        self.page_filter_edit.setValidator(QIntValidator(0, 9999))  # 允许0到9999

        self.x_var_combo = QComboBox()
        self.y_var_combo = QComboBox()

        edit_form_layout.addRow(QLabel("指定(页):"), self.page_filter_edit)
        edit_form_layout.addRow(QLabel("自变量 (X):"), self.x_var_combo)
        edit_form_layout.addRow(QLabel("因变量 (Y):"), self.y_var_combo)

        self.generate_button = QPushButton("生成/更新图表")

        # 将表单和按钮添加到主布局中
        edit_main_layout = QVBoxLayout()
        edit_main_layout.addLayout(edit_form_layout)
        edit_main_layout.addWidget(self.generate_button)
        edit_group.setLayout(edit_main_layout)
        main_layout.addWidget(edit_group)

        # 保存图表组
        save_group = QGroupBox("保存图表")
        save_layout = QVBoxLayout()
        format_layout = QHBoxLayout()
        self.png_radio = QRadioButton("PNG");
        self.svg_radio = QRadioButton("SVG");
        self.png_radio.setChecked(True)
        format_layout.addWidget(QLabel("格式:"));
        format_layout.addWidget(self.png_radio);
        format_layout.addWidget(self.svg_radio);
        format_layout.addStretch()
        self.export_chart_button = QPushButton("导出图表")
        save_layout.addLayout(format_layout);
        save_layout.addWidget(self.export_chart_button)
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)

    def _create_switch_layout(self, label_text, switch_widget):
        layout = QHBoxLayout();
        layout.addWidget(QLabel(label_text));
        layout.addStretch();
        layout.addWidget(switch_widget)
        return layout

    def _connect_signals(self):
        self.generate_button.clicked.connect(self._emit_generate_signal)

    def _emit_generate_signal(self):
        # --- 获取“指定”页码 ---
        page_filter_text = self.page_filter_edit.text()
        # 如果输入框为空或无效，则默认为0（全局）
        page_filter = int(page_filter_text) if page_filter_text.isdigit() else 0

        config = {
            'types': {
                'bar': self.bar_switch.isChecked(),
                'scatter': self.scatter_switch.isChecked(),
                'line': self.line_switch.isChecked()
            },
            'x_var': self.x_var_combo.currentText(),
            'y_var': self.y_var_combo.currentText(),
            'page_filter': page_filter  # <-- 新增配置项
        }
        self.generate_chart_signal.emit(config)

    def update_variable_options(self, columns):
        self.variable_options = columns + ["动作类型数量"]
        self.x_var_combo.clear();
        self.y_var_combo.clear()
        self.x_var_combo.addItems(self.variable_options)
        self.y_var_combo.addItems(self.variable_options)

    def get_save_config(self):
        return {"format": "png" if self.png_radio.isChecked() else "svg"}