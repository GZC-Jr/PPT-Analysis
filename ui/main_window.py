import os
import pandas as pd
from sklearn.cluster import DBSCAN
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QSplitter, QFileDialog, QToolBar,
                             QMessageBox, QColorDialog, QProgressDialog, QApplication,
                             QDialog, QDialogButtonBox, QPushButton)
from PyQt6.QtGui import QIcon, QAction, QActionGroup, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from core.data_model import DataModel
from ui.widgets.presentation_controls import PresentationControls
from ui.widgets.presentation_view import PresentationView
from ui.widgets.table_controls import TableControls
from ui.widgets.table_view import TableView
from ui.widgets.chart_controls import ChartControls
from ui.widgets.chart_view import ChartView
from ui.widgets.log_console import LogConsole
from ui.widgets.analysis_controls import AnalysisControls
from ui.widgets.analysis_view import AnalysisView
from core.analysis_utils import process_module_analysis # 用于导出


# --- 定义自定义对话框 ---
class ColorSettingsDialog(QDialog):
    def __init__(self, initial_start, initial_end, initial_link, parent=None):
        super().__init__(parent)
        self.setWindowTitle("样式设置")

        self.start_color = initial_start
        self.end_color = initial_end
        self.link_color = initial_link

        layout = QVBoxLayout(self)
        form_layout = QHBoxLayout()

        self.start_btn = self._create_color_button("起始颜色", self.start_color)
        self.end_btn = self._create_color_button("终止颜色", self.end_color)
        self.link_btn = self._create_color_button("连线颜色", self.link_color)

        self.start_btn.clicked.connect(self.pick_start_color)
        self.end_btn.clicked.connect(self.pick_end_color)
        self.link_btn.clicked.connect(self.pick_link_color)

        form_layout.addWidget(self.start_btn)
        form_layout.addWidget(self.end_btn)
        form_layout.addWidget(self.link_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def _create_color_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedSize(100, 40)
        self.update_button_color(btn, color)
        return btn

    def update_button_color(self, button, color):
        palette = button.palette()
        palette.setColor(QPalette.ColorRole.Button, color)
        button.setPalette(palette)
        button.setAutoFillBackground(True)

    def pick_start_color(self):
        color = QColorDialog.getColor(self.start_color, self, "选择起始颜色")
        if color.isValid():
            self.start_color = color
            self.update_button_color(self.start_btn, color)

    def pick_end_color(self):
        color = QColorDialog.getColor(self.end_color, self, "选择终止颜色")
        if color.isValid():
            self.end_color = color
            self.update_button_color(self.end_btn, color)

    def pick_link_color(self):
        color = QColorDialog.getColor(self.link_color, self, "选择连线颜色")
        if color.isValid():
            self.link_color = color
            self.update_button_color(self.link_btn, color)

    def getColors(self):
        return self.start_color, self.end_color, self.link_color

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # --- 添加样式状态变量 ---
        self.module_start_color = QColor("#4575b4")
        self.module_end_color = QColor("#d73027")
        self.module_link_color = QColor("#aaaaaa")
        self.interpage_start_color = QColor("#50a3ba")
        self.interpage_end_color = QColor("#d94e5d")

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
        self.analysis_controls = AnalysisControls()
        self.control_panel_stack.addWidget(self.file_controls)
        self.control_panel_stack.addWidget(self.presentation_controls)
        self.control_panel_stack.addWidget(self.table_controls)
        self.control_panel_stack.addWidget(self.chart_controls)
        self.control_panel_stack.addWidget(self.analysis_controls)

        # 2. 视图窗格 (右侧)
        self.view_stack = QStackedWidget()
        self.presentation_view = PresentationView()
        self.table_view = TableView()
        self.chart_view = ChartView()
        self.analysis_view = AnalysisView()
        self.view_stack.addWidget(self.presentation_view)  # 初始为空白
        self.view_stack.addWidget(self.table_view)
        self.view_stack.addWidget(self.chart_view)
        self.view_stack.addWidget(self.analysis_view)

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

        self.act_analysis = QAction("分析", self)
        self.act_analysis.setCheckable(True)

        self.act_other = QAction("其他", self)

        self.action_group.addAction(self.act_files)
        self.action_group.addAction(self.act_presentation)
        self.action_group.addAction(self.act_table)
        self.action_group.addAction(self.act_chart)
        self.action_group.addAction(self.act_analysis)

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
        top_toolbar.addAction(self.act_analysis)
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
        self.act_analysis.triggered.connect(lambda: self.switch_main_panel(4)) # for analysis

    def switch_main_panel(self, index):
        """切换主控制面板和视图"""
        self.control_panel_stack.setCurrentIndex(index)
        # 视图面板和控制面板的索引要对应，除了第一个文件面板
        if index > 0:
            self.view_stack.setCurrentIndex(index - 1)

        # 确保对应的顶部Action被选中
        actions = [self.act_files, self.act_presentation, self.act_table, self.act_chart, self.act_analysis]
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

        # # 表格控制信号
        # self.table_controls.export_table_button.clicked.connect(self.export_table)
        # self.table_controls.apply_button.clicked.connect(self.apply_table_changes)
        # --- 表格控制信号 (重构版) ---
        tc = self.table_controls
        # 查找/替换
        tc.find_next_button.clicked.connect(self.find_next_in_table)
        # 将 "上一个" 按钮连接到新的 backward=True 参数
        tc.find_prev_button.clicked.connect(lambda: self.find_in_table(backward=True))

        tc.replace_current_button.clicked.connect(self.replace_current_in_table)
        tc.replace_all_button.clicked.connect(self.replace_all_in_table)
        # 样式
        tc.color_button.clicked.connect(self.set_table_font_color)

        # 操作
        tc.restore_button.clicked.connect(self.restore_table)
        tc.apply_button.clicked.connect(self.apply_table_changes)
        tc.export_table_button.clicked.connect(self.export_table)

        # 图表控制信号
        self.chart_controls.generate_chart_signal.connect(self.generate_chart)
        self.chart_controls.export_chart_button.clicked.connect(self.export_chart)

        # --- 在分析功能的连接部分 ---
        self.analysis_controls.analysis_requested.connect(self.run_analysis)
        self.analysis_controls.export_csv_requested.connect(self.export_analysis_csv)
        self.analysis_controls.module_style_requested.connect(self.prompt_for_module_style)
        self.analysis_controls.interpage_style_requested.connect(self.prompt_for_interpage_style)
        self.analysis_controls.export_chart_requested.connect(self.export_analysis_chart)

        # --- 演示播放功能信号连接 (重构版) ---
        pc = self.presentation_controls
        pv = self.presentation_view

        # 基础播放控制
        pc.play_toggled.connect(pv.toggle_playback)
        pc.progress_scrubbed.connect(pv.scrub_to_position)
        pc.playback_mode_changed.connect(pv.set_playback_mode)
        pc.speed_changed.connect(pv.set_speed)
        pc.interval_changed.connect(pv.set_interval)
        pc.jump_to_slide_requested.connect(pv.jump_to_slide)

        # --- 新的绘图设置连接 ---
        pc.draw_visibility_changed.connect(pv.update_visibility)
        pc.trajectory_props_changed.connect(pv.update_trajectory_props)
        pc.marker_props_changed.connect(pv.update_marker_props)
        # pc.tail_props_changed.connect(pv.update_tail_props) # 如果需要单独设置尾迹属性

        # 从播放器 -> 控制器 (反馈)
        pv.progress_updated.connect(pc.update_progress)
        pv.playback_finished.connect(lambda: pc.play_button.setChecked(False))

    def on_ppt_loaded(self, slide_paths):
        self.presentation_view.set_slides(slide_paths)
        self.analysis_view.set_data(self.data_model.get_dataframe(), slide_paths)

    def on_data_loaded(self):
        """当CSV数据加载或更新时调用"""
        df = self.data_model.get_dataframe()
        self.analysis_view.set_data(df, self.data_model.slide_images)
        # --- 使用新的restore_data方法来刷新 ---
        self.table_view.restore_data(df)

        if df is not None and not df.empty:
            self.chart_controls.update_variable_options(list(df.columns))
            self.presentation_view.set_mouse_data(df)
            self.presentation_controls.set_progress_range(len(df) - 1)
            self.log_console.add_log("表格和图表视图已使用新数据更新。")
        else:
            self.presentation_controls.reset_controls()

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

        # --- 新增或修改的槽函数 ---

    def find_in_table(self, backward=False):
        find_text = self.table_controls.find_edit.text()
        if not find_text:
            return  # 如果没有输入，则不执行任何操作
        self.table_view.find_in_table(find_text, backward=backward)

    def find_next_in_table(self):
        self.find_in_table(backward=False)

    def replace_current_in_table(self):
        replace_text = self.table_controls.replace_with_edit.text()
        self.table_view.replace_current(replace_text)

    def replace_all_in_table(self):
        find_text = self.table_controls.find_edit.text()
        replace_text = self.table_controls.replace_with_edit.text()
        if not find_text:
            QMessageBox.warning(self, "输入为空", "请输入要查找的内容。")
            return

        reply = QMessageBox.question(self, "全部替换",
                                     f"您确定要将所有 '{find_text}' 替换为 '{replace_text}' 吗？\n此操作不可撤销。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.table_view.replace_all(find_text, replace_text)
            self.data_model.log_message.emit("“全部替换”操作已完成。")

    def set_table_font_color(self):
        color = QColorDialog.getColor(initial=QColor("red"), parent=self)
        if color.isValid():
            self.table_view.apply_color_to_selection(color)
            self.data_model.log_message.emit(f"已将选中项颜色设置为 {color.name()}。")

    def restore_table(self):
        reply = QMessageBox.question(self, "还原数据",
                                     "您确定要放弃所有未应用的更改，\n将表格还原到最初加载或上次应用时的状态吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.data_model.restore_to_original()

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
                                     "此操作将保存所有更改为新的基准，之后将无法还原到当前状态之前的版本。\n您确定要继续吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            current_df = self.table_view.get_data()
            self.data_model.apply_changes(current_df)
            QMessageBox.information(self, "成功", "所有更改已应用。")

    def generate_chart(self, config):
        df = self.data_model.get_dataframe()
        if df is None or df.empty:
            QMessageBox.warning(self, "无数据", "无法生成图表，请先加载数据。")
            return
        self.chart_view.update_charts(df, config)
        self.data_model.log_message.emit(
            f"生成ECharts图表: 类型={config['types']}, X={config['x_var']}, Y={config['y_var']}")

    def export_chart(self): # <--- 重写此方法
        """
        这个方法现在只是一个中继，它从controls获取保存格式，
        然后调用chart_view中真正的导出逻辑。
        """
        save_config = self.chart_controls.get_save_config()
        self.chart_view.export_chart(save_config['format'])

    def run_analysis(self, config):
        self.analysis_view.run_analysis(config)

    def prompt_for_module_style(self):
        dialog = ColorSettingsDialog(
            self.module_start_color, self.module_end_color, self.module_link_color, self
        )
        if dialog.exec():
            self.module_start_color, self.module_end_color, self.module_link_color = dialog.getColors()
            self.analysis_view.handle_style_change(
                self.module_start_color, self.module_end_color, self.module_link_color
            )

    # --- 新增槽函数 ---
    def prompt_for_interpage_style(self):
        # 复用ColorSettingsDialog
        dialog = ColorSettingsDialog(
            self.interpage_start_color, self.interpage_end_color, QColor("white"), self
        )
        # 隐藏不需要的连线颜色按钮，并更新标题
        dialog.link_btn.setVisible(False)
        dialog.setWindowTitle("页际样式设置")

        if dialog.exec():
            # 获取选择的颜色
            self.interpage_start_color, self.interpage_end_color, _ = dialog.getColors()
            # 将颜色传递给AnalysisView来处理
            self.analysis_view.handle_interpage_style_change(
                self.interpage_start_color, self.interpage_end_color
            )

    def export_analysis_csv(self, config):
        df = self.data_model.get_dataframe()
        if df is None or df.empty:
            QMessageBox.warning(self, "无数据", "没有可供分析的数据。")
            return

        all_pages = sorted(df['SlideIndex'].unique())
        total_pages = len(all_pages)

        # 创建进度条对话框
        progress = QProgressDialog("正在分析所有页面并导出模块...", "取消", 0, total_pages, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("正在导出")
        progress.show()

        all_modules_details = []

        try:
            for i, page_num in enumerate(all_pages):
                progress.setValue(i)
                if progress.wasCanceled():
                    break

                # 对每一页运行模块分析
                # 注意：这里我们复用了核心算法函数
                analysis_result = process_module_analysis(
                    df, page_num, config['eps'],
                    config['min_samples'], config['strength_threshold']
                )

                # DBSCAN在page_df上添加了'cluster'列，我们需要重新获取它
                page_df_with_clusters = df[df['SlideIndex'] == page_num].copy()
                if len(page_df_with_clusters) >= config['min_samples']:
                    db = DBSCAN(eps=config['eps'], min_samples=config['min_samples']).fit(
                        page_df_with_clusters[['X', 'Y']].values)
                    page_df_with_clusters['cluster'] = db.labels_
                else:
                    page_df_with_clusters['cluster'] = -1

                # 从返回的有效模块(nodes)中提取信息
                for node in analysis_result['nodes']:
                    # 从ID中解析出聚类标签
                    cluster_label = int(node['id'].split('_')[-1])

                    # 找到这个聚类包含的所有点
                    module_points_df = page_df_with_clusters[page_df_with_clusters['cluster'] == cluster_label]

                    for _, point in module_points_df.iterrows():
                        all_modules_details.append({
                            'Page': page_num,
                            'ModuleID': f"P{page_num}-M{cluster_label}",
                            'ModuleRadius(eps)': config['eps'],
                            'ModuleStrength': node['value'],
                            'PointTimestamp': point['Timestamp'],
                            'PointX': point['X'],
                            'PointY': point['Y'],
                            'PointAction': point['ActionType']
                        })
                QApplication.processEvents()  # 允许UI刷新

            progress.setValue(total_pages)

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "分析错误", f"在分析过程中发生错误: {e}")
            return

        if progress.wasCanceled():
            self.data_model.log_message.emit("导出操作已取消。")
            return

        if not all_modules_details:
            QMessageBox.information(self, "无模块", "在当前阈值下，所有页面均未找到可导出的模块。")
            return

        export_df = pd.DataFrame(all_modules_details)

        # 创建包含阈值信息的文件名
        filename = f"modules_eps{config['eps']}_minsamples{config['min_samples']}_strength{config['strength_threshold']}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出模块CSV文件", filename, "CSV Files (*.csv)")

        if file_path:
            try:
                export_df.to_csv(file_path, index=False)
                QMessageBox.information(self, "导出成功", f"模块数据已成功导出到:\n{file_path}")
                self.data_model.log_message.emit(f"模块数据已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时发生错误: {e}")

    def export_analysis_chart(self, config):
        """处理来自controls的图表导出请求。"""
        if config['mode'] == 'none':
            QMessageBox.warning(self, "无法导出", "请先选择并生成一个分析图表（模块或页际）。")
            return

        # 将请求委托给AnalysisView
        self.analysis_view.export_current_chart(config['format'])