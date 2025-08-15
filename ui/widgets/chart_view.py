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

        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'chart_view.html'))
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        self.current_chart_types = []

    def _call_js_error(self, message):
        """一个安全的调用JS showError函数的辅助方法"""
        # 使用json.dumps可以安全地处理消息中的特殊字符（如引号、换行符）
        escaped_message = json.dumps(message)
        self.web_view.page().runJavaScript(f"showError({escaped_message});")

    def _validate_combination(self, df, x_var, y_var, chart_type):
        """检查变量组合是否合理，返回 (is_valid, error_message)"""
        # 特殊变量 "动作类型数量" 是预计算的，总是有效的
        if x_var == "动作类型数量" or y_var == "动作类型数量":
            return True, ""

        # 检查列是否存在
        if x_var not in df.columns or y_var not in df.columns:
            return False, f"列 '{x_var}' 或 '{y_var}' 不存在。"

        x_dtype = df[x_var].dtype
        y_dtype = df[y_var].dtype

        # 散点图和折线图需要数值类型
        if chart_type in ['scatter', 'line']:
            is_x_valid = pd.api.types.is_numeric_dtype(x_dtype) or pd.api.types.is_datetime64_any_dtype(x_dtype)
            is_y_valid = pd.api.types.is_numeric_dtype(y_dtype)
            if not is_x_valid or not is_y_valid:
                return False, f"'{chart_type}' 图表要求X轴为数值/时间，Y轴为数值。"

        return True, ""

    def update_charts(self, df, config):
        try:
            active_charts = [k for k, v in config['types'].items() if v]
            if not active_charts or not config['x_var'] or not config['y_var']:
                self.web_view.page().runJavaScript(
                    'document.getElementById("chart-container").innerHTML = \'<p style="color: white; font-family: sans-serif; text-align:center;">请选择图表类型和变量。</p>\';')
                return

            # --- 1. 数据筛选 ---
            page_filter = config.get('page_filter', 0)
            if page_filter > 0:
                source_df = df[df['SlideIndex'] == page_filter].copy()
                if source_df.empty:
                    self._call_js_error(f"指定页码 {page_filter} 无数据")
                    return
            else:
                source_df = df.copy()

            # --- 2. 变量组合验证 ---
            x_var, y_var = config['x_var'], config['y_var']
            for chart_type in active_charts:
                is_valid, error_msg = self._validate_combination(source_df, x_var, y_var, chart_type)
                if not is_valid:
                    # 验证失败，弹窗提示并终止
                    QMessageBox.warning(self, "变量组合错误", error_msg)
                    self._call_js_error("变量组合不合理，请重新选择。")
                    return

            # --- 3. 数据预处理 ---
            if x_var == '动作类型数量' or y_var == '动作类型数量':
                data_to_plot = source_df['ActionType'].value_counts().reset_index()
                data_to_plot.columns = ['ActionType', 'Count']
                x_var, y_var = ('ActionType', 'Count') if x_var == '动作类型数量' else (x_var, 'Count')
            else:
                data_to_plot = source_df

            # --- 4. 准备JSON数据并发送到JS ---
            self.current_chart_types = active_charts

            x_data = data_to_plot[x_var].tolist()
            y_data = data_to_plot[y_var].tolist()

            payload = {
                "active_charts": self.current_chart_types,
                "title": {"text": f"{y_var} vs {x_var}",
                          "subtext": f"数据来源: {'全局' if page_filter == 0 else f'第 {page_filter} 页'}"},
                "data": {"x_var": x_var, "y_var": y_var, "x_data": x_data, "y_data": y_data, }
            }

            json_data = json.dumps(payload)
            self.web_view.page().runJavaScript(f"updateCharts('{json_data}');")

        except Exception as e:
            # --- 最终的捕获所有异常的防线 ---
            print(f"生成图表时发生未知错误: {e}")  # 在控制台打印详细错误以供调试
            # 在UI上显示友好的错误信息
            QMessageBox.critical(self, "生成图表时出错", f"发生了一个意外错误:\n{e}\n\n请检查您的变量选择或数据格式。")
            self._call_js_error(f"发生意外错误，请检查变量选择。")

    def export_chart(self, save_format):
        # ... (此方法保持不变) ...
        if not self.current_chart_types:
            QMessageBox.warning(self, "无图表", "没有可导出的图表。")
            return

        if save_format != 'png':
            QMessageBox.information(self, "格式提示", "ECharts当前配置主要支持导出为PNG格式。")
            save_format = 'png'

        chart_to_export = self.current_chart_types[0]
        file_path, _ = QFileDialog.getSaveFileName(self, f"导出{chart_to_export}图表", "", f"PNG Files (*.png)")
        if file_path:
            @pyqtSlot(str)
            def save_image_callback(base64_data):
                try:
                    header, encoded = base64_data.split(",", 1)
                    data = base64.b64decode(encoded)
                    with open(file_path, "wb") as f:
                        f.write(data)
                    QMessageBox.information(self, "导出成功", f"图表已成功导出到:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "导出失败", f"保存图片时发生错误:\n{e}")

            self.web_view.page().runJavaScript(f"getChartBase64('{chart_to_export}');", save_image_callback)