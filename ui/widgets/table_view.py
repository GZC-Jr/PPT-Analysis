# ui/widgets/table_view.py

import pandas as pd
from PyQt6.QtWidgets import (QTableView, QVBoxLayout, QWidget, QAbstractItemView,
                             QMenu, QHeaderView)
from PyQt6.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex, QTimer
from PyQt6.QtGui import QColor, QAction


class PandasModel(QAbstractTableModel):
    """
    增强版模型，现在也支持背景色样式。
    """

    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.copy()
        self._foregrounds = {}  # (row, col) -> QColor
        self._backgrounds = {}  # (row, col) -> QColor

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            value = self._df.iloc[index.row(), index.column()]
            if pd.isna(value): return ""
            if isinstance(value, pd.Timestamp): return value.strftime('%Y-%m-%d %H:%M:%S')
            return str(value)

        if role == Qt.ItemDataRole.ForegroundRole:
            color = self._foregrounds.get((index.row(), index.column()))
            if color: return QColor(color)

        # --- 新增：处理背景色角色 ---
        if role == Qt.ItemDataRole.BackgroundRole:
            color = self._backgrounds.get((index.row(), index.column()))
            if color: return QColor(color)

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        # ... (此方法保持不变) ...
        if role == Qt.ItemDataRole.EditRole:
            try:
                original_value = self._df.iloc[index.row(), index.column()]
                if isinstance(original_value, (int, float)):
                    value = type(original_value)(value)
                self._df.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
            except (ValueError, TypeError) as e:
                print(f"设置数据时类型转换错误: {e}")
                return False
        return False

    def headerData(self, section, orientation, role):
        # ... (此方法保持不变) ...
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])
        return QVariant()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def get_dataframe(self):
        return self._df.copy()

    def set_foreground_style(self, index, color):
        self._foregrounds[(index.row(), index.column())] = color
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.ForegroundRole])

    # --- 新增：背景色管理方法 ---
    def set_background_style(self, index, color):
        self._backgrounds[(index.row(), index.column())] = color
        # 通知视图，此单元格的背景色已更改
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

    def clear_background_style(self, index):
        if (index.row(), index.column()) in self._backgrounds:
            del self._backgrounds[(index.row(), index.column())]
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

    def clear_all_styles(self):
        self._foregrounds.clear()
        self._backgrounds.clear()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))

    def sort(self, column, order):
        # ... (此方法保持不变) ...
        col_name = self._df.columns[column]
        self.beginResetModel()
        self._df.sort_values(by=col_name, ascending=(order == Qt.SortOrder.AscendingOrder), inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.endResetModel()


class TableView(QWidget):
    # 定义高亮颜色和动画参数
    HIGHLIGHT_COLOR = QColor(255, 255, 0, 150)  # 黄色，半透明
    FLASH_INTERVAL_MS = 250
    HIGHLIGHT_DURATION_MS = 1500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table = QTableView()
        self.layout.addWidget(self.table)

        self.model = None

        # --- 动画相关属性 ---
        self.highlighted_index = QModelIndex()
        self.flash_on = False

        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(self.FLASH_INTERVAL_MS)
        self.flash_timer.timeout.connect(self._toggle_flash)

        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(self._stop_highlight)

        # --- 配置 ---
        self.table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self.show_header_menu)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def _start_highlight(self, index):
        """启动指定单元格的高亮闪烁动画"""
        if not index.isValid():
            return

        # 如果上一个动画还在运行，先停止它
        if self.highlight_timer.isActive():
            self._stop_highlight()

        self.highlighted_index = index
        self.flash_on = True

        # 立即设置高亮颜色
        self.model.set_background_style(self.highlighted_index, self.HIGHLIGHT_COLOR)

        # 启动两个定时器
        self.flash_timer.start()
        self.highlight_timer.start(self.HIGHLIGHT_DURATION_MS)

    def _toggle_flash(self):
        """切换高亮单元格的背景色，产生闪烁效果"""
        if not self.highlighted_index.isValid():
            return

        if self.flash_on:
            # 关闭高亮（设为透明）
            self.model.clear_background_style(self.highlighted_index)
        else:
            # 开启高亮
            self.model.set_background_style(self.highlighted_index, self.HIGHLIGHT_COLOR)

        self.flash_on = not self.flash_on

    def _stop_highlight(self):
        """停止所有动画并恢复单元格原始状态"""
        self.flash_timer.stop()
        if self.highlighted_index.isValid():
            # 确保最终状态是无高亮的
            self.model.clear_background_style(self.highlighted_index)
        self.highlighted_index = QModelIndex()

    def find_in_table(self, text, backward=False):
        # ... (查找逻辑基本不变, 只在找到后调用_start_highlight) ...
        if not self.model or not text: return

        start_index = self.table.currentIndex()
        if not start_index.isValid(): start_index = self.model.index(0, 0)

        target_index = QModelIndex()

        flags = Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchWrap
        if backward:
            row, col = start_index.row(), start_index.column() - 1
            while True:
                if col < 0:
                    col = self.model.columnCount() - 1
                    row = row - 1 if row > 0 else self.model.rowCount() - 1
                current_index = self.model.index(row, col)
                if not current_index.isValid() or current_index == start_index: break
                if text.lower() in str(self.model.data(current_index)).lower():
                    target_index = current_index
                    break
                col -= 1
        else:
            match_indexes = self.model.match(start_index, Qt.ItemDataRole.DisplayRole, text, 1, flags)
            if match_indexes:
                target_index = match_indexes[0]

        if target_index.isValid():
            self.table.setCurrentIndex(target_index)
            self._start_highlight(target_index)  # <--- 关键调用！

    # --- 其他方法保持不变 ---
    def show_header_menu(self, pos):
        # ...
        header = self.table.horizontalHeader()
        logical_index = header.logicalIndexAt(pos)
        menu = QMenu(self)
        asc_action = QAction("升序排列", self)
        desc_action = QAction("降序排列", self)
        asc_action.triggered.connect(lambda: self.sort_table(logical_index, Qt.SortOrder.AscendingOrder))
        desc_action.triggered.connect(lambda: self.sort_table(logical_index, Qt.SortOrder.DescendingOrder))
        menu.addAction(asc_action)
        menu.addAction(desc_action)
        menu.exec(header.mapToGlobal(pos))

    def sort_table(self, column_index, order):
        # ...
        if self.model:
            self.model.sort(column_index, order)
            self.table.horizontalHeader().setSortIndicator(column_index, order)

    def set_data(self, df):
        # ...
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()

    def get_data(self):
        # ...
        return self.model.get_dataframe() if self.model else pd.DataFrame()

    def replace_current(self, new_text):
        # ...
        if not self.model: return
        current_index = self.table.currentIndex()
        if current_index.isValid(): self.model.setData(current_index, new_text)

    def replace_all(self, find_text, replace_text):
        # ...
        if not self.model or not find_text: return
        self.model.beginResetModel()
        df = self.model.get_dataframe()
        df.replace(to_replace=find_text, value=replace_text, regex=True, inplace=True)
        self.set_data(df)
        self.model.endResetModel()

    def apply_color_to_selection(self, color):
        if not self.model: return
        selected_indexes = self.table.selectionModel().selectedIndexes()
        for index in selected_indexes:
            self.model.set_foreground_style(index, color)

    def restore_data(self, df):
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.model.clear_all_styles()