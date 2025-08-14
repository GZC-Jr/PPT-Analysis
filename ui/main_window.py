import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QSplitter, QFileDialog, QToolBar,
                             QMessageBox)
from PyQt6.QtGui import QIcon, QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from core.data_model import DataModel
from ui.widgets.presentation_controls import PresentationControls
from ui.widgets.presentation_view import PresentationView
from ui.widgets.table_controls import TableControls
from ui.widgets.table_view import TableView
from ui.widgets.chart_controls import ChartControls
from ui.widgets.chart_view import ChartView
from ui.widgets.log_console import LogConsole


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPT-Analysis - 鼠标行为可视化分析工具")
        self.setGeometry(100, 100, 1600, 900)

        # 初始化核心数据模型
        self.data_model = DataModel()

        # 初始化UI组件
        self._init_ui()
        self._create_actions()
        self._create_toolbars()
        self._connect_signals()

        self.log_console.add_log("欢迎使用 PPT-Analysis。请先上传PPT和CSV文件。")

    def _init_ui(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建垂直分割器
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # 创建水平分割器 (上部区域)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. 控制面板区域 (中左侧)
        self.control_panel_stack = QStackedWidget()
        self.file_controls = self._create_file_controls()
        self.presentation_controls = PresentationControls()
        self.table_controls = TableControls()
        self.chart_controls = ChartControls()
        self.control_panel_stack.addWidget(self.file_controls)
        self.control_panel_stack.addWidget(self.presentation_controls)
        self.control_panel_stack.addWidget(self.table_controls)
        self.control_panel_stack.addWidget(self.chart_controls)

        # 2. 视图窗格 (右侧)
        self.view_stack = QStackedWidget()
        self.presentation_view = PresentationView()
        self.table_view = TableView()
        self.chart_view = ChartView()
        self.view_stack.addWidget(self.presentation_view)  # 初始为空白
        self.view_stack.addWidget(self.table_view)
        self.view_stack.addWidget(self.chart_view)

        h_splitter.addWidget(self.control_panel_stack)
        h_splitter.addWidget(self.view_stack)
        h_splitter.setStretchFactor(0, 1)
        h_splitter.setStretchFactor(1, 4)
        h_splitter.setSizes([350, 1250])

        # 3. 底部日志/终端区域
        self.log_console = LogConsole()

        v_splitter.addWidget(h_splitter)
        v_splitter.addWidget(self.log_console)
        v_splitter.setStretchFactor(0, 4)
        v_splitter.setStretchFactor(1, 1)
        v_splitter.setSizes([700, 200])

        main_layout.addWidget(v_splitter)

    def _create_file_controls(self):
        """创建文件上传控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        from PyQt6.QtWidgets import QPushButton, QLabel

        self.upload_ppt_btn = QPushButton("上传PPT")
        self.upload_csv_btn = QPushButton("上传CSV")
        self.upload_csv_batch_btn = QPushButton("批量上传CSV")

        layout.addWidget(QLabel("文件操作"))
        layout.addWidget(self.upload_ppt_btn)
        layout.addWidget(self.upload_csv_btn)
        layout.addWidget(self.upload_csv_batch_btn)
        return widget

    def _create_actions(self):
        # 顶部工作区切换动作
        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)

        self.act_files = QAction("文件", self)
        self.act_files.setCheckable(True)
        self.act_files.setChecked(True)

        self.act_presentation = QAction("演示", self)
        self.act_presentation.setCheckable(True)

        self.act_table = QAction("表格", self)
        self.act_table.setCheckable(True)

        self.act_chart = QAction("图表", self)
        self.act_chart.setCheckable(True)

        self.act_other = QAction("其他", self)

        self.action_group.addAction(self.act_files)
        self.action_group.addAction(self.act_presentation)
        self.action_group.addAction(self.act_table)
        self.action_group.addAction(self.act_chart)

    def _create_toolbars(self):
        # 顶部工具栏
        top_toolbar = QToolBar("主工具栏")
        top_toolbar.setMovable(False)
        top_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(top_toolbar)

        # 为了模拟图片中的效果，我们用一个特殊的action来显示汉堡菜单
        menu_action = QAction(QIcon.fromTheme("open-menu-symbolic", QIcon("assets/menu_icon.svg")), "菜单", self)
        top_toolbar.addAction(menu_action)
        top_toolbar.addSeparator()

        top_toolbar.addAction(self.act_presentation)
        top_toolbar.addAction(self.act_table)
        top_toolbar.addAction(self.act_chart)
        top_toolbar.addAction(self.act_other)

        # 左侧图标栏
        left_toolbar = QToolBar("侧边栏")
        left_toolbar.setMovable(False)
        left_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, left_toolbar)

        # QActionGroup for left toolbar buttons
        left_action_group = QActionGroup(self)
        left_action_group.setExclusive(True)

        act_file_panel = QAction(QIcon.fromTheme("folder", QIcon("assets/folder_icon.svg")), "文件", self)
        act_file_panel.setCheckable(True)
        act_file_panel.setChecked(True)  # 默认选中

        act_log_panel = QAction(QIcon.fromTheme("document-open-recent", QIcon("assets/time_icon.svg")), "日志", self)
        act_log_panel.setCheckable(True)
        act_log_panel.setChecked(True)

        act_console_panel = QAction(QIcon.fromTheme("utilities-terminal", QIcon("assets/terminal_icon.svg")), "终端",
                                    self)
        act_console_panel.setCheckable(True)

        left_toolbar.addAction(act_file_panel)
        left_toolbar.addSeparator()
        left_toolbar.addAction(act_log_panel)
        left_toolbar.addAction(act_console_panel)

        # 将左侧工具栏的Action添加到组中，用于切换底部面板
        self.bottom_action_group = QActionGroup(self)
        self.bottom_action_group.setExclusive(True)
        self.bottom_action_group.addAction(act_log_panel)
        self.bottom_action_group.addAction(act_console_panel)

        # 使用lambda来切换顶部的主控制面板
        act_file_panel.triggered.connect(lambda: self.switch_main_panel(0))  # 0 for files
        self.act_presentation.triggered.connect(lambda: self.switch_main_panel(1))  # 1 for presentation
        self.act_table.triggered.connect(lambda: self.switch_main_panel(2))  # 2 for table
        self.act_chart.triggered.connect(lambda: self.switch_main_panel(3))  # 3 for chart

    def switch_main_panel(self, index):
        """切换主控制面板和视图"""
        self.control_panel_stack.setCurrentIndex(index)
        # 视图面板和控制面板的索引要对应，除了第一个文件面板
        if index > 0:
            self.view_stack.setCurrentIndex(index - 1)

        # 确保对应的顶部Action被选中
        actions = [self.act_files, self.act_presentation, self.act_table, self.act_chart]
        if index < len(actions):
            actions[index].setChecked(True)

    def _connect_signals(self):
        # 数据模型信号
        self.data_model.log_message.connect(self.log_console.add_log)
        self.data_model.ppt_loaded.connect(self.on_ppt_loaded)  # 修改
        self.data_model.data_loaded.connect(self.on_data_loaded)

        # 文件控制信号
        self.upload_ppt_btn.clicked.connect(self.upload_ppt)
        self.upload_csv_btn.clicked.connect(self.upload_csv)

        # 底部面板切换
        self.bottom_action_group.triggered.connect(self.on_bottom_panel_changed)

        # 表格控制信号
        self.table_controls.export_table_button.clicked.connect(self.export_table)
        self.table_controls.apply_button.clicked.connect(self.apply_table_changes)

        # 图表控制信号
        self.chart_controls.generate_chart_signal.connect(self.generate_chart)
        self.chart_controls.export_chart_button.clicked.connect(self.export_chart)

        # --- 新增：演示播放功能信号连接 ---
        # 从控制器 -> 播放器
        pc = self.presentation_controls
        pv = self.presentation_view

        pc.play_toggled.connect(pv.toggle_playback)
        pc.progress_scrubbed.connect(pv.scrub_to_position)
        pc.playback_mode_changed.connect(pv.set_playback_mode)
        pc.speed_changed.connect(pv.set_speed)
        pc.interval_changed.connect(pv.set_interval)
        pc.jump_to_slide_requested.connect(pv.jump_to_slide)
        pc.draw_settings_changed.connect(pv.set_draw_settings)

        # 从播放器 -> 控制器 (反馈)
        pv.progress_updated.connect(pc.update_progress)
        # 当播放完成时，让播放按钮恢复到“播放”状态
        pv.playback_finished.connect(lambda: pc.play_button.setChecked(False))

    def on_ppt_loaded(self, slide_paths):
        self.presentation_view.set_slides(slide_paths)

    def on_data_loaded(self):
        """当CSV数据加载或更新时调用"""
        df = self.data_model.get_dataframe()
        if df is not None and not df.empty:
            self.table_view.set_data(df)
            self.chart_controls.update_variable_options(list(df.columns))
            # 更新演示视图的数据
            self.presentation_view.set_mouse_data(df)
            # 设置演示控制器的进度条范围
            self.presentation_controls.set_progress_range(len(df) - 1)
            self.log_console.add_log("表格和演示视图已使用新数据更新。")
        else:
            # 如果加载了空数据，重置
            self.presentation_controls.reset_controls()
            self.log_console.add_log("加载的数据为空或无效。")

    def on_bottom_panel_changed(self, action):
        """切换日志和终端视图"""
        if "日志" in action.text():
            self.log_console.switch_to_log()
        elif "终端" in action.text():
            self.log_console.switch_to_console()

    def upload_ppt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择PPT文件", "", "PowerPoint Files (*.pptx)")
        if file_path:
            self.data_model.load_ppt(file_path)

    def upload_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择CSV数据文件", "", "CSV Files (*.csv)")
        if file_path:
            self.data_model.load_csv(file_path)

    def export_table(self):
        df = self.table_view.get_data()
        if df is None:
            QMessageBox.warning(self, "无数据", "没有可导出的表格数据。")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出表格为CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                df.to_csv(file_path, index=False, sep='\t')
                self.data_model.log_message.emit(f"表格成功导出到: {file_path}")
                QMessageBox.information(self, "导出成功", f"表格已成功导出到:\n{file_path}")
            except Exception as e:
                self.data_model.log_message.emit(f"错误: 导出表格失败: {e}")
                QMessageBox.critical(self, "导出失败", f"导出表格时发生错误:\n{e}")

    def apply_table_changes(self):
        reply = QMessageBox.question(self, "应用更改",
                                     "此操作将保存所有更改，之后将无法还原。\n您确定要继续吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            current_df = self.table_view.get_data()
            if current_df is not None:
                self.data_model.update_dataframe(current_df.copy())
                QMessageBox.information(self, "成功", "所有更改已应用。")

    def generate_chart(self, config):
        df = self.data_model.get_dataframe()
        if df is None:
            QMessageBox.warning(self, "无数据", "无法生成图表，请先加载数据。")
            return
        self.chart_view.update_charts(df, config)
        self.data_model.log_message.emit(f"生成图表: 类型={config['types']}, X={config['x_var']}, Y={config['y_var']}")

    def export_chart(self):
        config = self.chart_controls.get_save_config()
        file_path, _ = QFileDialog.getSaveFileName(self, "导出图表", "",
                                                   f"{config['format'].upper()} Files (*.{config['format']})")
        if file_path:
            try:
                self.chart_view.figure.savefig(file_path, format=config['format'], bbox_inches='tight', dpi=300)
                self.data_model.log_message.emit(f"图表成功导出到: {file_path}")
                QMessageBox.information(self, "导出成功", f"图表已成功导出到:\n{file_path}")
            except Exception as e:
                self.data_model.log_message.emit(f"错误: 导出图表失败: {e}")
                QMessageBox.critical(self, "导出失败", f"导出图表时发生错误:\n{e}")