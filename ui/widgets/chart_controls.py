from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QRadioButton)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.widgets.custom_widgets import Switch


class ChartControls(QWidget):
    # 信号: (配置字典)
    generate_chart_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.variable_options = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 图表类型组
        type_group = QGroupBox("图表类型")
        type_layout = QVBoxLayout()
        self.bar_switch = Switch()
        self.scatter_switch = Switch()
        self.line_switch = Switch()
        type_layout.addLayout(self._create_switch_layout("条形图", self.bar_switch))
        type_layout.addLayout(self._create_switch_layout("散点图", self.scatter_switch))
        type_layout.addLayout(self._create_switch_layout("折线图", self.line_switch))
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        # 图表编辑组
        edit_group = QGroupBox("图表编辑")
        edit_layout = QVBoxLayout()

        self.x_var_combo = QComboBox()
        self.y_var_combo = QComboBox()

        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("自变量 (X):"))
        var_layout.addWidget(self.x_var_combo)

        var_layout2 = QHBoxLayout()
        var_layout2.addWidget(QLabel("因变量 (Y):"))
        var_layout2.addWidget(self.y_var_combo)

        self.generate_button = QPushButton("生成/更新图表")

        edit_layout.addLayout(var_layout)
        edit_layout.addLayout(var_layout2)
        edit_layout.addWidget(self.generate_button)
        edit_group.setLayout(edit_layout)
        main_layout.addWidget(edit_group)

        # 保存图表组
        save_group = QGroupBox("保存图表")
        save_layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        self.png_radio = QRadioButton("PNG")
        self.svg_radio = QRadioButton("SVG")
        self.png_radio.setChecked(True)
        format_layout.addWidget(QLabel("格式:"))
        format_layout.addWidget(self.png_radio)
        format_layout.addWidget(self.svg_radio)
        format_layout.addStretch()

        self.export_chart_button = QPushButton("导出图表")

        save_layout.addLayout(format_layout)
        save_layout.addWidget(self.export_chart_button)
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)

    def _create_switch_layout(self, label_text, switch_widget):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addStretch()
        layout.addWidget(switch_widget)
        return layout

    def _connect_signals(self):
        self.generate_button.clicked.connect(self._emit_generate_signal)

    def _emit_generate_signal(self):
        config = {
            'types': {
                'bar': self.bar_switch.isChecked(),
                'scatter': self.scatter_switch.isChecked(),
                'line': self.line_switch.isChecked()
            },
            'x_var': self.x_var_combo.currentText(),
            'y_var': self.y_var_combo.currentText()
        }
        self.generate_chart_signal.emit(config)

    def update_variable_options(self, columns):
        self.variable_options = columns + ["动作类型数量"]  # 添加衍生变量
        self.x_var_combo.clear()
        self.y_var_combo.clear()
        self.x_var_combo.addItems(self.variable_options)
        self.y_var_combo.addItems(self.variable_options)

    def get_save_config(self):
        return {
            "format": "png" if self.png_radio.isChecked() else "svg"
        }