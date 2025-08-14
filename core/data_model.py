
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from pptx import Presentation
from core.ppt_utils import extract_slides_as_images
import os


class DataModel(QObject):
    """
    负责管理和处理所有数据（PPT和CSV）的类。
    当数据加载或更改时，它会发出信号，通知UI进行更新。
    """
    # 定义信号
    data_loaded = pyqtSignal()
    ppt_loaded = pyqtSignal(list)  # 传递幻灯片图像路径列表
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = None
        self.presentation = None
        self.slide_images = []
        self.ppt_path = None
        self.csv_path = None

    def load_csv(self, file_path):
        """加载并解析CSV文件"""
        try:
            self.df = pd.read_csv(
                file_path,
                sep=',',  # 根据描述，格式为制表符分隔
                parse_dates=['Timestamp']
            )
            self.csv_path = file_path
            # 数据清洗和预处理可以在这里添加
            self.df = self.df.sort_values(by='Timestamp').reset_index(drop=True)
            self.log_message.emit(f"成功加载并解析CSV文件: {os.path.basename(file_path)}")
            self.data_loaded.emit()
        except Exception as e:
            self.log_message.emit(f"错误：加载CSV文件失败: {e}")
            self.df = None

    def load_ppt(self, file_path, temp_dir="temp_slides"):
        """加载PPT并提取幻灯片为图片"""
        try:
            self.presentation = Presentation(file_path)
            self.ppt_path = file_path
            self.log_message.emit(f"正在从 {os.path.basename(file_path)} 提取幻灯片...")

            # 创建临时目录存放幻灯片图片
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # 调用工具函数提取图片
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

    def update_dataframe(self, new_df):
        """应用表格中的修改"""
        self.df = new_df
        self.log_message.emit("表格数据已更新。")
        self.data_loaded.emit()  # 发出信号以更新所有视图

    def save_dataframe_to_csv(self, file_path):
        """将当前DataFrame保存为CSV"""
        if self.df is not None:
            try:
                self.df.to_csv(file_path, index=False, sep='\t')
                self.log_message.emit(f"表格已成功导出到: {file_path}")
            except Exception as e:
                self.log_message.emit(f"错误：导出CSV失败: {e}")

