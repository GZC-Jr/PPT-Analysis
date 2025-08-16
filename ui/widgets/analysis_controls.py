# # ui/widgets/analysis_controls.py
#
# from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel,
#                              QLineEdit, QPushButton, QButtonGroup, QColorDialog,
#                              QMessageBox)
# from PyQt6.QtGui import QIntValidator, QDoubleValidator, QColor
# from PyQt6.QtCore import pyqtSignal, Qt
# from ui.widgets.custom_widgets import Switch
#
#
# class AnalysisControls(QWidget):
#     # 移除所有播放相关的信号
#     analysis_requested = pyqtSignal(dict)
#     export_csv_requested = pyqtSignal(dict)
#     module_style_requested = pyqtSignal()
#     interpage_style_requested = pyqtSignal()
#     export_chart_requested = pyqtSignal(dict)
#     page_changed = pyqtSignal(int)  # 保留页面切换信号
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._init_ui()
#         self._connect_signals()
#         self.module_content_widget.setEnabled(False)
#         self.interpage_content_widget.setEnabled(False)
#
#     def _init_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
#
#         self.main_mode_group = QButtonGroup(self)
#         self.main_mode_group.setExclusive(True)
#
#         # --- 模块分析组 (简化版) ---
#         module_group = QGroupBox("模块")
#         module_main_layout = QVBoxLayout(module_group)
#
#         self.module_switch = Switch()
#         self.main_mode_group.addButton(self.module_switch, 1)
#         module_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.module_switch))
#
#         self.module_content_widget = QWidget()
#         module_content_layout = QVBoxLayout(self.module_content_widget)
#         module_content_layout.setContentsMargins(0, 5, 0, 0)
#
#         # -- 阈值设置 --
#         self.eps_edit = QLineEdit("50.0");
#         self.eps_edit.setValidator(QDoubleValidator(0.1, 1000.0, 2))
#         self.min_samples_edit = QLineEdit("5");
#         self.min_samples_edit.setValidator(QIntValidator(1, 1000))
#         self.strength_edit = QLineEdit("10.0");
#         self.strength_edit.setValidator(QDoubleValidator(0.0, 100.0, 2))
#         form_layout = QVBoxLayout()
#         form_layout.addLayout(self._create_edit_layout("邻近阈值", self.eps_edit))
#         form_layout.addLayout(self._create_edit_layout("聚集阈值", self.min_samples_edit))
#         form_layout.addLayout(self._create_edit_layout("强度阈值", self.strength_edit))
#
#         # -- 跳转控制 (从播放组移出并简化) --
#         self.jump_edit = QLineEdit("0");
#         self.jump_edit.setPlaceholderText("0为全局");
#         self.jump_edit.setValidator(QIntValidator(0, 9999))
#         self.prev_page_btn = QPushButton("◀");
#         self.prev_page_btn.setFixedWidth(30)
#         self.next_page_btn = QPushButton("▶");
#         self.next_page_btn.setFixedWidth(30)
#         jump_layout = QHBoxLayout()
#         jump_layout.addWidget(QLabel("跳转"));
#         jump_layout.addWidget(self.jump_edit)
#         jump_layout.addWidget(self.prev_page_btn);
#         jump_layout.addWidget(self.next_page_btn)
#
#         # -- 底部按钮 --
#         self.module_style_button = QPushButton("样式设置")
#         self.export_csv_button = QPushButton("导出CSV文件")
#
#         module_content_layout.addLayout(form_layout)
#         module_content_layout.addLayout(jump_layout)  # <-- 将跳转布局直接添加到这里
#         module_content_layout.addWidget(self.module_style_button)
#         module_content_layout.addWidget(self.export_csv_button)
#
#         module_main_layout.addWidget(self.module_content_widget)
#         main_layout.addWidget(module_group)
#
#         # ... (页际和保存组保持不变) ...
#         interpage_group = QGroupBox("页际");
#         interpage_main_layout = QVBoxLayout(interpage_group)
#         self.interpage_switch = Switch();
#         self.main_mode_group.addButton(self.interpage_switch, 2)
#         interpage_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.interpage_switch))
#         self.interpage_content_widget = QWidget();
#         interpage_content_layout = QVBoxLayout(self.interpage_content_widget)
#         interpage_content_layout.setContentsMargins(0, 5, 0, 0)
#         self.divergence_switch = Switch();
#         self.association_switch = Switch()
#         self.page_mode_group = QButtonGroup(self);
#         self.page_mode_group.setExclusive(True)
#         self.page_mode_group.addButton(self.divergence_switch);
#         self.page_mode_group.addButton(self.association_switch)
#         interpage_content_layout.addLayout(self._create_switch_layout(QLabel("歧线"), self.divergence_switch))
#         interpage_content_layout.addLayout(self._create_switch_layout(QLabel("关联"), self.association_switch))
#         self.interpage_style_button = QPushButton("样式设置");
#         interpage_content_layout.addWidget(self.interpage_style_button)
#         interpage_main_layout.addWidget(self.interpage_content_widget);
#         main_layout.addWidget(interpage_group)
#         save_group = QGroupBox("保存图表");
#         save_layout = QVBoxLayout()
#         self.png_switch = Switch();
#         self.png_switch.setChecked(True);
#         self.svg_switch = Switch()
#         self.format_group = QButtonGroup(self);
#         self.format_group.setExclusive(True);
#         self.format_group.addButton(self.png_switch);
#         self.format_group.addButton(self.svg_switch)
#         save_layout.addLayout(self._create_switch_layout(QLabel("PNG"), self.png_switch));
#         save_layout.addLayout(self._create_switch_layout(QLabel("SVG"), self.svg_switch))
#         self.export_chart_button = QPushButton("导出图表");
#         save_layout.addWidget(self.export_chart_button);
#         save_group.setLayout(save_layout)
#         main_layout.addWidget(save_group)
#         self.generate_button = QPushButton("生成分析图");
#         main_layout.addWidget(self.generate_button)
#
#     def _create_switch_layout(self, label, switch):
#         layout = QHBoxLayout();
#         layout.addWidget(label);
#         layout.addStretch();
#         layout.addWidget(switch)
#         return layout
#
#     def _create_edit_layout(self, label_text, edit_widget):
#         layout = QHBoxLayout();
#         label = QLabel(label_text);
#         label.setFixedWidth(60)
#         layout.addWidget(label);
#         layout.addWidget(edit_widget)
#         return layout
#
#     def _connect_signals(self):
#         self.main_mode_group.buttonToggled.connect(self.on_main_mode_changed)
#         self.generate_button.clicked.connect(self._emit_analysis_request)
#         self.export_csv_button.clicked.connect(self._emit_export_csv_request)
#         self.module_style_button.clicked.connect(self.module_style_requested.emit)
#         self.interpage_style_button.clicked.connect(self.interpage_style_requested.emit)
#         self.export_chart_button.clicked.connect(self._emit_export_chart_request)
#
#         # --- 连接简化的跳转信号 ---
#         self.jump_edit.editingFinished.connect(self._on_jump_changed)
#         self.prev_page_btn.clicked.connect(self._on_prev_page)
#         self.next_page_btn.clicked.connect(self._on_next_page)
#
#     def _on_jump_changed(self):
#         if self.jump_edit.text().isdigit():
#             self.page_changed.emit(int(self.jump_edit.text()))
#             self._emit_analysis_request()  # 跳转后自动生成图表
#
#     def _on_prev_page(self):
#         if self.jump_edit.text().isdigit():
#             page = max(0, int(self.jump_edit.text()) - 1)
#             self.jump_edit.setText(str(page))
#             self.page_changed.emit(page)
#             self._emit_analysis_request()  # 切换后自动生成图表
#
#     def _on_next_page(self):
#         if self.jump_edit.text().isdigit():
#             page = int(self.jump_edit.text()) + 1
#             self.jump_edit.setText(str(page))
#             self.page_changed.emit(page)
#             self._emit_analysis_request()  # 切换后自动生成图表
#
#     def on_main_mode_changed(self, button, checked):
#         if checked:
#             is_module_mode = (button == self.module_switch)
#             is_interpage_mode = (button == self.interpage_switch)
#             self.module_content_widget.setEnabled(is_module_mode)
#             self.interpage_content_widget.setEnabled(is_interpage_mode)
#         elif not self.main_mode_group.checkedButton():
#             self.module_content_widget.setEnabled(False)
#             self.interpage_content_widget.setEnabled(False)
#
#     def _emit_export_chart_request(self):
#         mode = 'none'
#         if self.module_switch.isChecked():
#             mode = 'module'
#         elif self.interpage_switch.isChecked():
#             mode = 'interpage'
#         config = {'mode': mode, 'format': 'svg' if self.svg_switch.isChecked() else 'png'}
#         self.export_chart_requested.emit(config)
#
#     def _emit_analysis_request(self):
#         try:
#             # 确保在发射信号前，当前跳转框的值被使用
#             current_page = int(self.jump_edit.text())
#             config = {
#                 'module_on': self.module_switch.isChecked(),
#                 'page_num': current_page,  # 使用当前文本框的值
#                 'eps': float(self.eps_edit.text()),
#                 'min_samples': int(self.min_samples_edit.text()),
#                 'strength_threshold': float(self.strength_edit.text()),
#                 'interpage_on': self.interpage_switch.isChecked(),
#                 'show_divergence': self.divergence_switch.isChecked(),
#                 'show_association': self.association_switch.isChecked()
#             }
#             self.analysis_requested.emit(config)
#         except ValueError:
#             QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")
#
#     def _emit_export_csv_request(self):
#         try:
#             config = {'eps': float(self.eps_edit.text()), 'min_samples': int(self.min_samples_edit.text()),
#                       'strength_threshold': float(self.strength_edit.text())}
#             self.export_csv_requested.emit(config)
#         except ValueError:
#             QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")


# ui/widgets/analysis_controls.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QButtonGroup, QColorDialog,
                             QMessageBox)
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QColor
from PyQt6.QtCore import pyqtSignal, Qt

from ui.widgets.custom_widgets import Switch


class AnalysisControls(QWidget):
    analysis_requested = pyqtSignal(dict)
    export_csv_requested = pyqtSignal(dict)
    module_style_requested = pyqtSignal()
    interpage_style_requested = pyqtSignal()
    export_chart_requested = pyqtSignal(dict)
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

        # --- 新增：状态变量 ---
        self.max_page_number = 0

        self.module_content_widget.setEnabled(False)
        self.interpage_content_widget.setEnabled(False)

    # ... (_init_ui 保持不变) ...
    def _init_ui(self):
        main_layout = QVBoxLayout(self);
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_mode_group = QButtonGroup(self);
        self.main_mode_group.setExclusive(True)
        module_group = QGroupBox("模块");
        module_main_layout = QVBoxLayout(module_group)
        self.module_switch = Switch();
        self.main_mode_group.addButton(self.module_switch, 1)
        module_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.module_switch))
        self.module_content_widget = QWidget();
        module_content_layout = QVBoxLayout(self.module_content_widget)
        module_content_layout.setContentsMargins(0, 5, 0, 0)
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
        self.jump_edit = QLineEdit("0");
        self.jump_edit.setPlaceholderText("0为全局");
        self.jump_edit.setValidator(QIntValidator(0, 9999))
        self.prev_page_btn = QPushButton("◀");
        self.prev_page_btn.setFixedWidth(30)
        self.next_page_btn = QPushButton("▶");
        self.next_page_btn.setFixedWidth(30)
        jump_layout = QHBoxLayout()
        jump_layout.addWidget(QLabel("跳转"));
        jump_layout.addWidget(self.jump_edit)
        jump_layout.addWidget(self.prev_page_btn);
        jump_layout.addWidget(self.next_page_btn)
        self.module_style_button = QPushButton("样式设置");
        self.export_csv_button = QPushButton("导出CSV文件")
        module_content_layout.addLayout(form_layout);
        module_content_layout.addLayout(jump_layout)
        module_content_layout.addWidget(self.module_style_button);
        module_content_layout.addWidget(self.export_csv_button)
        module_main_layout.addWidget(self.module_content_widget);
        main_layout.addWidget(module_group)
        interpage_group = QGroupBox("页际");
        interpage_main_layout = QVBoxLayout(interpage_group)
        self.interpage_switch = Switch();
        self.main_mode_group.addButton(self.interpage_switch, 2)
        interpage_main_layout.addLayout(self._create_switch_layout(QLabel("开启"), self.interpage_switch))
        self.interpage_content_widget = QWidget();
        interpage_content_layout = QVBoxLayout(self.interpage_content_widget)
        interpage_content_layout.setContentsMargins(0, 5, 0, 0)
        self.divergence_switch = Switch();
        self.association_switch = Switch()
        self.page_mode_group = QButtonGroup(self);
        self.page_mode_group.setExclusive(True)
        self.page_mode_group.addButton(self.divergence_switch);
        self.page_mode_group.addButton(self.association_switch)
        interpage_content_layout.addLayout(self._create_switch_layout(QLabel("歧线"), self.divergence_switch))
        interpage_content_layout.addLayout(self._create_switch_layout(QLabel("关联"), self.association_switch))
        self.interpage_style_button = QPushButton("样式设置");
        interpage_content_layout.addWidget(self.interpage_style_button)
        interpage_main_layout.addWidget(self.interpage_content_widget);
        main_layout.addWidget(interpage_group)
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

    # ... (_create... 方法保持不变) ...
    def _create_switch_layout(self, label, switch):  # ...
        layout = QHBoxLayout();
        layout.addWidget(label);
        layout.addStretch();
        layout.addWidget(switch)
        return layout

    def _create_edit_layout(self, label_text, edit_widget):  # ...
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
        self.jump_edit.editingFinished.connect(self._on_jump_changed)
        self.prev_page_btn.clicked.connect(self._on_prev_page)
        self.next_page_btn.clicked.connect(self._on_next_page)

    # --- 核心修改：更新槽函数逻辑 ---
    def _on_jump_changed(self):
        if self.jump_edit.text().isdigit():
            page = int(self.jump_edit.text())
            # 边界检查
            if page > self.max_page_number:
                page = self.max_page_number
                self.jump_edit.setText(str(page))

            self.page_changed.emit(page)
            self._emit_analysis_request()

    def _on_prev_page(self):
        if self.jump_edit.text().isdigit():
            page = int(self.jump_edit.text())
            if page == 0:
                # 从第0页向前切换到最大页
                page = self.max_page_number
            else:
                page -= 1

            self.jump_edit.setText(str(page))
            self.page_changed.emit(page)
            self._emit_analysis_request()

    def _on_next_page(self):
        if self.jump_edit.text().isdigit():
            page = int(self.jump_edit.text())
            if page == self.max_page_number:
                # 从最大页向后切换到第0页（全局）
                page = 0
            else:
                page += 1

            self.jump_edit.setText(str(page))
            self.page_changed.emit(page)
            self._emit_analysis_request()

    # --- 新增：公共方法，由MainWindow调用 ---
    def set_max_page(self, max_page):
        self.max_page_number = max_page
        # 更新输入框的验证器，防止手动输入超过最大值的数字
        self.jump_edit.setValidator(QIntValidator(0, self.max_page_number, self))
        print(f"AnalysisControls max page set to: {self.max_page_number}")

    # ... (其他方法保持不变) ...
    def on_main_mode_changed(self, button, checked):  # ...
        if checked:
            is_module_mode = (button == self.module_switch)
            is_interpage_mode = (button == self.interpage_switch)
            self.module_content_widget.setEnabled(is_module_mode)
            self.interpage_content_widget.setEnabled(is_interpage_mode)
        elif not self.main_mode_group.checkedButton():
            self.module_content_widget.setEnabled(False)
            self.interpage_content_widget.setEnabled(False)

    def _emit_export_chart_request(self):  # ...
        mode = 'none'
        if self.module_switch.isChecked():
            mode = 'module'
        elif self.interpage_switch.isChecked():
            mode = 'interpage'
        config = {'mode': mode, 'format': 'svg' if self.svg_switch.isChecked() else 'png'}
        self.export_chart_requested.emit(config)

    def _emit_analysis_request(self):  # ...
        try:
            current_page = int(self.jump_edit.text())
            config = {'module_on': self.module_switch.isChecked(), 'page_num': current_page,
                      'eps': float(self.eps_edit.text()), 'min_samples': int(self.min_samples_edit.text()),
                      'strength_threshold': float(self.strength_edit.text()),
                      'interpage_on': self.interpage_switch.isChecked(),
                      'show_divergence': self.divergence_switch.isChecked(),
                      'show_association': self.association_switch.isChecked()}
            self.analysis_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")

    def _emit_export_csv_request(self):  # ...
        try:
            config = {'eps': float(self.eps_edit.text()), 'min_samples': int(self.min_samples_edit.text()),
                      'strength_threshold': float(self.strength_edit.text())}
            self.export_csv_requested.emit(config)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请确保所有阈值输入框都已填写正确的数值。")