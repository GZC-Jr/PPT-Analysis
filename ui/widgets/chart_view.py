# ui/widgets/chart_view.py

import os
import json
import base64
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot


class ChartView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        # 加载本地HTML文件
        # 使用绝对路径确保在任何环境下都能找到文件
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'chart_view.html'))
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        self.current_chart_types = []  # 存储当前显示的图表类型，用于导出

    def update_charts(self, df, config):
        """
        处理数据，转换为JSON，并调用JS函数来更新ECharts。
        """
        page_filter = config.get('page_filter', 0)

        if page_filter > 0:
            source_df = df[df['SlideIndex'] == page_filter].copy()
            if source_df.empty:
                # 如果没有数据，可以调用JS显示提示信息
                js_code = 'document.getElementById("chart-container").innerHTML = \'<p style="color: orange; font-family: sans-serif; text-align: center;">指定页码 ' + str(
                    page_filter) + ' 无数据</p>\';'
                self.web_view.page().runJavaScript(js_code)
                return
        else:
            source_df = df.copy()

        # 数据预处理
        x_var, y_var = config['x_var'], config['y_var']
        if x_var == '动作类型数量' or y_var == '动作类型数量':
            data_to_plot = source_df['ActionType'].value_counts().reset_index()
            data_to_plot.columns = ['ActionType', 'Count']
            x_var, y_var = ('ActionType', 'Count') if x_var == '动作类型数量' else (x_var, 'Count')
        else:
            data_to_plot = source_df

        # 准备传递给JS的数据负载 (payload)
        self.current_chart_types = [k for k, v in config['types'].items() if v]

        # 将Pandas Series转换为Python list
        x_data = data_to_plot[x_var].tolist()
        y_data = data_to_plot[y_var].tolist()

        payload = {
            "active_charts": self.current_chart_types,
            "title": {
                "text": f"{y_var} vs {x_var}",
                "subtext": f"数据来源: {'全局' if page_filter == 0 else f'第 {page_filter} 页'}"
            },
            "data": {
                "x_var": x_var,
                "y_var": y_var,
                "x_data": x_data,
                "y_data": y_data,
            }
        }

        # 将Python字典序列化为JSON字符串
        json_data = json.dumps(payload)

        # 调用JS函数
        self.web_view.page().runJavaScript(f"updateCharts('{json_data}');")

    def export_chart(self, save_format):
        """
        调用JS获取图表的Base64数据，并保存为文件。
        """
        if not self.current_chart_types:
            QMessageBox.warning(self, "无图表", "没有可导出的图表。")
            return

        # ECharts目前主要导出PNG，SVG需要额外配置
        if save_format != 'png':
            QMessageBox.information(self, "格式提示", "ECharts当前配置主要支持导出为PNG格式。")
            save_format = 'png'

        # 简单起见，我们只导出一个图表（例如第一个）
        # 也可以修改JS和这里，将所有图表拼接成一张大图
        chart_to_export = self.current_chart_types[0]

        file_path, _ = QFileDialog.getSaveFileName(self, f"导出{chart_to_export}图表", "", f"PNG Files (*.png)")
        if file_path:
            # 定义一个Python槽函数来接收从JS返回的数据
            @pyqtSlot(str)
            def save_image_callback(base64_data):
                try:
                    # ECharts返回的base64字符串带有前缀，需要去掉
                    # e.g., "data:image/png;base64,iVBORw0KGgo..."
                    header, encoded = base64_data.split(",", 1)
                    data = base64.b64decode(encoded)
                    with open(file_path, "wb") as f:
                        f.write(data)
                    QMessageBox.information(self, "导出成功", f"图表已成功导出到:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "导出失败", f"保存图片时发生错误:\n{e}")

            # 调用JS函数，并将Python槽函数作为回调
            self.web_view.page().runJavaScript(f"getChartBase64('{chart_to_export}');", save_image_callback)