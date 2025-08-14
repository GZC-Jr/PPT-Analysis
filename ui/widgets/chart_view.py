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

        # 创建Matplotlib图形和画布
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        # 设置暗色主题
        self.figure.patch.set_facecolor('#2E2E2E')
        matplotlib.rc('text', color='white')
        matplotlib.rc('axes', labelcolor='white', facecolor='#3C3C3C', edgecolor='white')
        matplotlib.rc('xtick', color='white')
        matplotlib.rc('ytick', color='white')
        matplotlib.rc('grid', color='#555555')

        self.layout.addWidget(self.canvas)

    def update_charts(self, df, config):
        self.figure.clear()

        active_charts = [k for k, v in config['types'].items() if v]
        if not active_charts or not config['x_var'] or not config['y_var']:
            self.canvas.draw()
            return

        num_charts = len(active_charts)

        # 处理特殊变量
        if config['x_var'] == '动作类型数量' or config['y_var'] == '动作类型数量':
            data_to_plot = df['ActionType'].value_counts().reset_index()
            data_to_plot.columns = ['ActionType', 'Count']
            if config['x_var'] == '动作类型数量':
                x_var, y_var = 'ActionType', 'Count'
            else:  # y_var is count
                x_var, y_var = config['x_var'], 'Count'
                # 需要聚合
                if df[x_var].dtype == 'object' or df[x_var].nunique() > 20:  # 分类或高基数
                    grouped = df.groupby(x_var).size().reset_index(name='Count')
                    data_to_plot = grouped
                else:  # 数值
                    data_to_plot = df[[x_var]].copy()
                    data_to_plot['Count'] = 1  # 只是为了让散点图能画

        else:
            data_to_plot = df
            x_var, y_var = config['x_var'], config['y_var']

        for i, chart_type in enumerate(active_charts):
            ax = self.figure.add_subplot(1, num_charts, i + 1)
            ax.set_facecolor('#3C3C3C')

            try:
                if chart_type == 'bar':
                    data_to_plot.plot(kind='bar', x=x_var, y=y_var, ax=ax, legend=False)
                    ax.set_title("条形图")
                elif chart_type == 'scatter':
                    data_to_plot.plot(kind='scatter', x=x_var, y=y_var, ax=ax)
                    ax.set_title("散点图")
                elif chart_type == 'line':
                    # 折线图需要数据有序
                    if pd.api.types.is_numeric_dtype(data_to_plot[x_var]):
                        data_to_plot.sort_values(by=x_var).plot(kind='line', x=x_var, y=y_var, ax=ax, legend=False)
                    else:
                        data_to_plot.plot(kind='line', x=x_var, y=y_var, ax=ax, legend=False)
                    ax.set_title("折线图")

                ax.set_xlabel(x_var)
                ax.set_ylabel(y_var)
                ax.grid(True, linestyle='--', alpha=0.6)
            except Exception as e:
                ax.text(0.5, 0.5, f"无法绘制图表:\n{e}", ha='center', va='center', color='red')

        self.figure.tight_layout(pad=3.0)
        self.figure.patch.set_facecolor('#2E2E2E')
        self.canvas.draw()