# ui/widgets/table_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFormLayout,
                             QColorDialog)
from PyQt6.QtCore import Qt


class TableControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 数据操作组
        data_group = QGroupBox("数据")
        data_layout = QVBoxLayout()

        # 查找
        find_layout = QHBoxLayout()
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("要查找的内容...")
        self.find_next_button = QPushButton("查找下一个")
        self.find_prev_button = QPushButton("查找上一个")
        find_layout.addWidget(self.find_edit)
        find_layout.addWidget(self.find_prev_button)
        find_layout.addWidget(self.find_next_button)

        # 替换
        replace_form_layout = QFormLayout()
        self.replace_with_edit = QLineEdit()
        self.replace_with_edit.setPlaceholderText("替换为...")
        replace_form_layout.addRow(QLabel("替换为:"), self.replace_with_edit)

        replace_buttons_layout = QHBoxLayout()
        self.replace_current_button = QPushButton("替换当前")
        self.replace_all_button = QPushButton("全部替换")
        replace_buttons_layout.addWidget(self.replace_current_button)
        replace_buttons_layout.addWidget(self.replace_all_button)

        data_layout.addLayout(find_layout)
        data_layout.addLayout(replace_form_layout)
        data_layout.addLayout(replace_buttons_layout)
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)

        # 样式组
        style_group = QGroupBox("样式")
        style_layout = QHBoxLayout()
        self.color_button = QPushButton("为选中项着色")
        style_layout.addWidget(self.color_button)
        style_group.setLayout(style_layout)
        main_layout.addWidget(style_group)

        # 操作按钮
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout()
        self.restore_button = QPushButton("还原")
        self.apply_button = QPushButton("应用")
        self.export_table_button = QPushButton("导出表格")
        action_layout.addWidget(self.restore_button)
        action_layout.addWidget(self.apply_button)
        action_layout.addWidget(self.export_table_button)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)