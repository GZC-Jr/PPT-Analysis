# ui/widgets/analysis_view.py
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
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

            # --- 核心修改：准备背景图片URL ---
            bg_url = ""
            if page_num > 0:  # 全局模式(0)没有背景
                if not self.slide_images:
                    QMessageBox.warning(self, "无PPT", "请先加载PPT文件以显示背景。")
                elif 0 < page_num <= len(self.slide_images):
                    bg_path = self.slide_images[page_num - 1]
                    # 将本地文件路径转换为Web引擎可以访问的URL
                    bg_url = QUrl.fromLocalFile(os.path.abspath(bg_path)).toString()
                else:
                    QMessageBox.warning(self, "页码无效", f"指定的页码 {page_num} 超出范围。")
                    # 可以在JS中显示错误
                    payload = {'mode': 'error', 'message': f'页码 {page_num} 无效'}
                    self.web_view.page().runJavaScript(f"updateAnalysis('{json.dumps(payload)}');")
                    return

            payload['mode'] = 'module'
            payload['page_bg_url'] = bg_url  # <-- 将URL添加到payload
            payload['data'] = process_module_analysis(
                self.full_df, page_num, config['eps'],
                config['min_samples'], config['strength_threshold']
            )

        elif config['interpage_on']:
            payload['mode'] = 'interpage'
            all_modules = []
            for page in self.full_df['SlideIndex'].unique():
                modules = process_module_analysis(self.full_df, page, config['eps'], config['min_samples'],
                                                  config['strength_threshold'])['nodes']
                for m in modules:
                    all_modules.append({'page': page, 'strength': m['value']})
            payload['data'] = process_interpage_analysis(self.full_df, all_modules)
            if not config['show_divergence'] and not config['show_association']:
                payload['data']['transitions'] = []

        else:
            # 提示用户选择一种模式
            self.web_view.page().runJavaScript("updateAnalysis('{}');")  # 发送空JSON以清屏
            return

        json_data = json.dumps(payload)
        self.web_view.page().runJavaScript(f"updateAnalysis('{json_data}');")