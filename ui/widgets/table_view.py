# ui/widgets/table_view.py

import pandas as pd
from PyQt6.QtWidgets import QTableView, QVBoxLayout, QWidget, QAbstractItemView
from PyQt6.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex
from PyQt6.QtGui import QColor


class PandasModel(QAbstractTableModel):
    """
    一个增强版的Pandas模型，支持数据编辑和单元格样式（前景色）。
    """

    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.copy()
        self._styles = {}  # 字典来存储样式: (row, col) -> QColor

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return str(self._df.iloc[index.row(), index.column()])

        # --- 新增：处理前景色角色 ---
        if role == Qt.ItemDataRole.ForegroundRole:
            color = self._styles.get((index.row(), index.column()))
            if color:
                return QColor(color)

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            try:
                self._df.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
            except Exception as e:
                print(f"设置数据时出错: {e}")
                return False
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])
        return QVariant()

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def get_dataframe(self):
        return self._df.copy()  # 返回副本以防外部修改

    # --- 新增：样式管理方法 ---
    def set_style(self, index, color):
        self._styles[(index.row(), index.column())] = color
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.ForegroundRole])

    def clear_styles(self):
        self._styles.clear()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))


class TableView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table = QTableView()
        self.layout.addWidget(self.table)

        self.model = None
        self._last_find_index = QModelIndex()  # 记录上次查找的位置

        # --- 配置表格行为 ---
        self.table.setSortingEnabled(True)  # 开启内置排序
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setSectionsClickable(True)

    def set_data(self, df):
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self._last_find_index = QModelIndex()  # 重置查找位置

    def get_data(self):
        return self.model.get_dataframe() if self.model else pd.DataFrame()

    def find_in_table(self, text, backward=False):
        if not self.model or not text:
            return

        start_index = self.table.currentIndex() if self._last_find_index.isValid() else self.model.index(0, 0)

        # 使用Qt的内建查找功能
        match_indexes = self.model.match(
            start_index,
            Qt.ItemDataRole.DisplayRole,
            text,
            -1,  # 查找所有行
            Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchWrap  # 包含匹配且循环查找
        )

        if match_indexes:
            # match返回一个列表，我们简单地选择第一个
            # 更复杂的逻辑可以处理“下一个/上一个”
            next_index = match_indexes[0]
            self.table.setCurrentIndex(next_index)
            self._last_find_index = next_index

    def replace_current(self, new_text):
        if not self.model: return
        current_index = self.table.currentIndex()
        if current_index.isValid():
            self.model.setData(current_index, new_text)

    def replace_all(self, find_text, replace_text):
        if not self.model or not find_text: return
        self.model.beginResetModel()
        df = self.model.get_dataframe()
        # 对整个DataFrame进行字符串替换
        df.replace(to_replace=find_text, value=replace_text, regex=True, inplace=True)
        # 重新设置模型数据
        self.set_data(df)
        self.model.endResetModel()

    def apply_color_to_selection(self, color):
        if not self.model: return
        selected_indexes = self.table.selectionModel().selectedIndexes()
        for index in selected_indexes:
            self.model.set_style(index, color)

    def restore_data(self, df):
        """用于从外部（如DataModel）恢复数据和样式"""
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        # 如果需要，也可以在这里重置样式
        self.model.clear_styles()