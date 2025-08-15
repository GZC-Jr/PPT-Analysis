# ui/widgets/analysis_view.py
import os
import json
import base64
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtGui import QColor  # <-- 确保导入QColor
from core.analysis_utils import process_module_analysis, process_interpage_analysis


class AnalysisView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'analysis_view.html'))
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        self.full_df = None
        self.slide_images = None

    def _call_js_with_payload(self, function_name, payload):
        """
        一个健壮的、用于向JS传递数据的辅助函数。
        它将Python字典转换为JSON，然后安全地作为参数传递给JS函数。
        """
        # 1. 将Python字典序列化为JSON字符串
        json_string = json.dumps(payload)

        # 2. 构建JS代码。使用模板字符串 `` 和 JSON.parse() 是最安全的方式。
        #    这样可以避免任何由特殊字符（如引号、换行符）引起的语法错误。
        js_code = f"{function_name}(JSON.parse(`{json_string}`));"

        # 3. 执行JS
        self.web_view.page().runJavaScript(js_code)

    def set_data(self, df, slide_images):
        self.full_df = df
        self.slide_images = slide_images

    def run_analysis(self, config):
        if self.full_df is None or self.full_df.empty:
            QMessageBox.warning(self, "无数据", "请先加载CSV数据。")
            return

        payload = {}
        if config['module_on']:
            page_num = config['page_num']
            bg_url = ""

            if page_num > 0:
                if not self.slide_images or not (0 < page_num <= len(self.slide_images)):
                    # 即使没有背景图，也应该继续分析，只是不显示背景
                    if not self.slide_images:
                        print("警告: 未加载PPT，无法显示背景。")
                    else:
                        print(f"警告: 页码 {page_num} 无效，无法显示背景。")
                else:
                    bg_path = self.slide_images[page_num - 1]
                    bg_url = QUrl.fromLocalFile(os.path.abspath(bg_path)).toString()

            payload['mode'] = 'module'
            payload['page_bg_url'] = bg_url
            payload['data'] = process_module_analysis(
                self.full_df, page_num, config['eps'],
                config['min_samples'], config['strength_threshold']
            )


        elif config['interpage_on']:
            # --- 核心修改：简化调用流程 ---
            # 直接将原始DataFrame传递给新的分析函数
            payload['mode'] = 'interpage'
            payload['data'] = process_interpage_analysis(self.full_df)
            # (歧线/关联的开关逻辑保持不变)
            if not config['show_divergence'] and not config['show_association']:
                payload['data']['transitions'] = []
        else:
            self._call_js_with_payload("updateAnalysis", {}); return
        self._call_js_with_payload("updateAnalysis", payload)

    # --- 更新 handle_style_change 以使用新辅助函数 ---
    def handle_style_change(self, start_color: QColor, end_color: QColor, link_color: QColor):
        if start_color.isValid() and end_color.isValid() and link_color.isValid():
            style_payload = {
                'startColor': start_color.name(),
                'endColor': end_color.name(),
                'linkColor': link_color.name()
            }
            self._call_js_with_payload("setModuleStyle", style_payload)

    def handle_interpage_style_change(self, start_color: QColor, end_color: QColor):
        if start_color.isValid() and end_color.isValid():
            payload = {
                'startColor': start_color.name(),
                'endColor': end_color.name()
            }
            # 调用JS函数
            self._call_js_with_payload("setInterpageStyle", payload)

    def export_current_chart(self, save_format):
        """调用JS获取当前图表的Base64数据并保存。"""

        # 定义一个Python槽函数来接收JS返回的Base64数据
        @pyqtSlot(str)
        def save_image_from_base64(base64_data):
            if not base64_data or 'base64' not in base64_data:
                QMessageBox.warning(self, "导出失败", "无法从前端获取图表图像数据。图表可能为空。")
                return

            # 弹出文件保存对话框
            default_filename = f"analysis_chart.{save_format}"
            file_path, _ = QFileDialog.getSaveFileName(self, "保存分析图表", default_filename,
                                                       f"{save_format.upper()} Files (*.{save_format})")

            if file_path:
                try:
                    # 分离数据头和数据本身
                    header, encoded = base64_data.split(",", 1)
                    data = base64.b64decode(encoded)
                    with open(file_path, "wb") as f:
                        f.write(data)
                    QMessageBox.information(self, "导出成功", f"图表已成功保存到:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", f"保存文件时发生错误: \n{e}")

        # 调用JS函数，并将我们的Python槽函数作为回调传递
        # 注意：JS函数 getChartBase64 需要在 analysis_view.js 中定义
        self.web_view.page().runJavaScript(f"getChartBase64('{save_format}');", save_image_from_base64)