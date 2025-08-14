from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFormLayout,
                             QMenu)
from PyQt6.QtCore import Qt


class TableControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 排序组
        sort_group = QGroupBox("排序")
        sort_layout = QVBoxLayout()
        self.sort_time_button = QPushButton("按时间排序")
        self.sort_slide_button = QPushButton("按页数排序")
        self.sort_type_button = QPushButton("按类型排序")
        self.sort_coord_button = QPushButton("按坐标排序")
        sort_layout.addWidget(self.sort_time_button)
        sort_layout.addWidget(self.sort_slide_button)
        sort_layout.addWidget(self.sort_type_button)
        sort_layout.addWidget(self.sort_coord_button)
        sort_group.setLayout(sort_layout)
        main_layout.addWidget(sort_group)

        # 创建右键菜单
        for btn in [self.sort_time_button, self.sort_slide_button, self.sort_type_button, self.sort_coord_button]:
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(self.show_sort_menu)

        # 数据操作组
        data_group = QGroupBox("数据")
        data_layout = QVBoxLayout()

        # 查找
        find_layout = QFormLayout()
        self.find_edit = QLineEdit()
        self.find_button = QPushButton("查找")
        find_layout.addRow(QLabel("查找:"), self.find_edit)
        find_layout.addRow(self.find_button)

        # 替换
        replace_layout = QFormLayout()
        self.replace_find_edit = QLineEdit()
        self.replace_with_edit = QLineEdit()
        replace_buttons_layout = QHBoxLayout()
        self.replace_next_button = QPushButton("下一个")
        self.replace_prev_button = QPushButton("上一个")
        self.replace_all_button = QPushButton("全部替换")
        replace_buttons_layout.addWidget(self.replace_prev_button)
        replace_buttons_layout.addWidget(self.replace_next_button)
        replace_buttons_layout.addWidget(self.replace_all_button)

        replace_layout.addRow(QLabel("查找内容:"), self.replace_find_edit)
        replace_layout.addRow(QLabel("替换为:"), self.replace_with_edit)
        replace_layout.addRow(replace_buttons_layout)

        data_layout.addLayout(find_layout)
        data_layout.addLayout(replace_layout)
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)

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

    def show_sort_menu(self, pos):
        button = self.sender()
        menu = QMenu()
        asc_action = menu.addAction("升序排列")
        desc_action = menu.addAction("降序排列")

        action = menu.exec(button.mapToGlobal(pos))

        if action:
            order = 'asc' if action == asc_action else 'desc'
            # 在这里可以发出一个带参数的信号
            print(f"排序请求: {button.text()}, 顺序: {order}")
            # 例如: self.sort_signal.emit(button.text(), order)