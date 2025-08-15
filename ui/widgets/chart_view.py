# ui/widgets/chart_view.py

import matplotlib

matplotlib.use('qtagg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class ChartView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        self.figure.patch.set_facecolor('#2E2E2E')
        matplotlib.rc('text', color='white')
        matplotlib.rc('axes', labelcolor='white', facecolor='#3C3C3C', edgecolor='white')
        matplotlib.rc('xtick', color='white');
        matplotlib.rc('ytick', color='white')
        matplotlib.rc('grid', color='#555555')

        self.layout.addWidget(self.canvas)

    def update_charts(self, df, config):
        self.figure.clear()

        active_charts = [k for k, v in config['types'].items() if v]
        if not active_charts or not config['x_var'] or not config['y_var']:
            self.canvas.draw()
            return

        # --- 1. 数据筛选 (核心修改) ---
        page_filter = config.get('page_filter', 0)

        if page_filter > 0:
            source_df = df[df['SlideIndex'] == page_filter].copy()
            if source_df.empty:
                # 如果指定页码没有数据，则显示提示信息并返回
                ax = self.figure.add_subplot(1, 1, 1)
                ax.text(0.5, 0.5, f"指定页码 {page_filter} 无数据", ha='center', va='center', color='orange',
                        fontsize=14)
                ax.set_facecolor('#3C3C3C')
                ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False,
                               labelbottom=False, labelleft=False)
                self.canvas.draw()
                return
        else:  # page_filter为0，使用全局数据
            source_df = df.copy()

        # --- 2. 数据预处理 (现在基于 source_df) ---
        if config['x_var'] == '动作类型数量' or config['y_var'] == '动作类型数量':
            data_to_plot = source_df['ActionType'].value_counts().reset_index()
            data_to_plot.columns = ['ActionType', 'Count']
            if config['x_var'] == '动作类型数量':
                x_var, y_var = 'ActionType', 'Count'
            else:
                x_var = config['x_var']
                y_var = 'Count'
                if source_df[x_var].dtype == 'object' or source_df[x_var].nunique() > 20:
                    data_to_plot = source_df.groupby(x_var).size().reset_index(name='Count')
                else:
                    data_to_plot = source_df[[x_var]].copy();
                    data_to_plot['Count'] = 1
        else:
            data_to_plot = source_df
            x_var, y_var = config['x_var'], config['y_var']

        # --- 3. 绘图 (现在基于处理后的数据) ---
        num_charts = len(active_charts)
        for i, chart_type in enumerate(active_charts):
            ax = self.figure.add_subplot(1, num_charts, i + 1)
            ax.set_facecolor('#3C3C3C')

            try:
                title_suffix = f" (第{page_filter}页)" if page_filter > 0 else " (全局)"
                if chart_type == 'bar':
                    data_to_plot.plot(kind='bar', x=x_var, y=y_var, ax=ax, legend=False)
                    ax.set_title("条形图" + title_suffix)
                elif chart_type == 'scatter':
                    data_to_plot.plot(kind='scatter', x=x_var, y=y_var, ax=ax)
                    ax.set_title("散点图" + title_suffix)
                elif chart_type == 'line':
                    if pd.api.types.is_numeric_dtype(data_to_plot[x_var]):
                        data_to_plot.sort_values(by=x_var).plot(kind='line', x=x_var, y=y_var, ax=ax, legend=False)
                    else:
                        data_to_plot.plot(kind='line', x=x_var, y=y_var, ax=ax, legend=False)
                    ax.set_title("折线图" + title_suffix)

                ax.set_xlabel(x_var);
                ax.set_ylabel(y_var)
                ax.grid(True, linestyle='--', alpha=0.6)
                # 自动旋转x轴标签以防重叠
                self.figure.autofmt_xdate(rotation=45)

            except Exception as e:
                ax.text(0.5, 0.5, f"无法绘制图表:\n{e}", ha='center', va='center', color='red')

        self.figure.tight_layout(pad=3.0)
        self.figure.patch.set_facecolor('#2E2E2E')
        self.canvas.draw()