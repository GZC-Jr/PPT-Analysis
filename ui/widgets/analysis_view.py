# ui/widgets/analysis_view.py
import os
import json
import base64
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtGui import QColor
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
        self.current_page = 0 # 仍然需要知道当前是哪一页

    def _call_js_with_payload(self, function_name, payload):
        json_string = json.dumps(payload, default=int)
        js_code = f"{function_name}(JSON.parse(`{json_string}`));"
        self.web_view.page().runJavaScript(js_code)

    def set_data(self, df, slide_images):
        self.full_df = df
        self.slide_images = slide_images
        self.current_page = 0 # 数据加载后重置

    # --- run_analysis 重命名为 run_static_analysis ---
    def run_static_analysis(self, config):
        if self.full_df is None or self.full_df.empty:
            QMessageBox.warning(self, "无数据", "请先加载CSV数据。"); return

        payload = {}
        if config['module_on']:
            page_num = config['page_num']
            self.current_page = page_num # 更新当前页面
            bg_url = ""
            if page_num > 0 and self.slide_images and 0 < page_num <= len(self.slide_images):
                bg_path = self.slide_images[page_num - 1]
                bg_url = QUrl.fromLocalFile(os.path.abspath(bg_path)).toString()
            payload['mode'] = 'module'; payload['page_bg_url'] = bg_url
            payload['data'] = process_module_analysis(self.full_df, page_num, config['eps'], config['min_samples'], config['strength_threshold'])
        elif config['interpage_on']:
            self.current_page = -1 # 页际模式没有特定页面
            payload['mode'] = 'interpage'
            payload['data'] = process_interpage_analysis(self.full_df)
            if not config['show_divergence'] and not config['show_association']:
                payload['data']['transitions'] = []
        else:
            self._call_js_with_payload("updateAnalysis", {}); return
        self._call_js_with_payload("updateAnalysis", payload)

    def set_current_page(self, page_num):
        """槽函数，用于响应页面切换信号"""
        self.current_page = page_num
        # 页面切换后，自动重新生成分析图
        # 这个逻辑现在移到了controls中，以确保所有参数都是最新的

    def handle_style_change(self, start_color: QColor, end_color: QColor, link_color: QColor):
        if start_color.isValid() and end_color.isValid() and link_color.isValid():
            style_payload = {'startColor': start_color.name(), 'endColor': end_color.name(), 'linkColor': link_color.name()}
            self._call_js_with_payload("setModuleStyle", style_payload)

    def handle_interpage_style_change(self, start_color: QColor, end_color: QColor):
        if start_color.isValid() and end_color.isValid():
            payload = {'startColor': start_color.name(), 'endColor': end_color.name()}
            self._call_js_with_payload("setInterpageStyle", payload)

    def export_current_chart(self, save_format):
        @pyqtSlot(str)
        def save_image_from_base64(base64_data):
            if not base64_data or 'base64' not in base64_data:
                QMessageBox.warning(self, "导出失败", "无法从前端获取图表图像数据。"); return
            default_filename = f"analysis_chart.{save_format}"
            file_path, _ = QFileDialog.getSaveFileName(self, "保存分析图表", default_filename, f"{save_format.upper()} Files (*.{save_format})")
            if file_path:
                try:
                    header, encoded = base64_data.split(",", 1)
                    data = base64.b64decode(encoded)
                    with open(file_path, "wb") as f: f.write(data)
                    QMessageBox.information(self, "导出成功", f"图表已成功保存到:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", f"保存文件时发生错误: \n{e}")
        self.web_view.page().runJavaScript(f"getChartBase64('{save_format}');", save_image_from_base64)