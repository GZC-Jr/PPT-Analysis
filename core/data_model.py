# core/data_model.py

import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from pptx import Presentation
from core.ppt_utils import extract_slides_as_images
import os


class DataModel(QObject):
    data_loaded = pyqtSignal()
    ppt_loaded = pyqtSignal(list)
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = pd.DataFrame()  # 当前正在编辑的DataFrame
        self.original_df = pd.DataFrame()  # 首次加载时的原始副本，用于还原
        self.presentation = None
        self.slide_images = []
        self.ppt_path = None
        self.csv_path = None

    def load_csv(self, file_path):
        """加载并解析CSV文件，同时保存一份原始副本"""
        try:
            temp_df = pd.read_csv(
                file_path,
                encoding='utf-8-sig',
                sep=None,
                engine='python',
                parse_dates=['Timestamp']
            )
            # 排序后，同时设置当前和原始DataFrame
            self.df = temp_df.sort_values(by='Timestamp').reset_index(drop=True)
            self.original_df = self.df.copy()  # 创建深拷贝作为原始备份

            self.csv_path = file_path
            self.log_message.emit(f"成功加载并解析CSV文件: {os.path.basename(file_path)}")
            self.data_loaded.emit()
        except Exception as e:
            self.log_message.emit(f"错误：加载CSV文件失败: {e}")
            self.df = pd.DataFrame()
            self.original_df = pd.DataFrame()

    def restore_to_original(self):
        """将当前DataFrame还原到最初加载的状态"""
        if not self.original_df.empty:
            self.df = self.original_df.copy()
            self.log_message.emit("表格数据已成功还原到初始状态。")
            self.data_loaded.emit()  # 发送信号以刷新UI
        else:
            self.log_message.emit("没有可供还原的原始数据。")

    def apply_changes(self, current_df):
        """应用更改，将当前状态设为新的“原始”状态"""
        self.df = current_df.copy()
        self.original_df = current_df.copy()  # 新的基准
        self.log_message.emit("所有更改已应用并保存为新基准。")
        self.data_loaded.emit()  # 刷新UI

    def load_ppt(self, file_path, temp_dir="temp_slides"):
        # ... (此方法保持不变) ...
        try:
            self.presentation = Presentation(file_path)
            self.ppt_path = file_path
            self.log_message.emit(f"正在从 {os.path.basename(file_path)} 提取幻灯片...")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            self.slide_images = extract_slides_as_images(file_path, temp_dir)
            if self.slide_images:
                self.log_message.emit(f"成功提取 {len(self.slide_images)} 张幻灯片。")
                self.ppt_loaded.emit(self.slide_images)
            else:
                self.log_message.emit("警告：未能从PPT中提取任何幻灯片。演示功能将受限。")
        except Exception as e:
            self.log_message.emit(f"错误：加载PPT文件失败: {e}")
            self.presentation = None
            self.slide_images = []

    def get_dataframe(self):
        return self.df