# ui/widgets/analysis_view.py
import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtGui import QColor  # <-- 确保导入QColor
from core.analysis_utils import process_module_analysis, process_interpage_analysis, precompute_clusters


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
            # --- 核心修改：先预计算，再分析 ---
            # 1. 调用新的预计算函数
            df_with_clusters = precompute_clusters(self.full_df, config['eps'], config['min_samples'])

            # 2. 将带有聚类结果的DataFrame传递给纯聚合函数
            payload['mode'] = 'interpage'
            payload['data'] = process_interpage_analysis(
                df_with_clusters,
                config['strength_threshold']
            )
            if not config['show_divergence'] and not config['show_association']:
                payload['data']['transitions'] = []

        else:
            self._call_js_with_payload("updateAnalysis", {})
            return

        # 使用新的、健壮的辅助函数来调用JS
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