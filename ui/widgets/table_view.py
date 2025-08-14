import pandas as pd
from PyQt6.QtWidgets import QTableView, QVBoxLayout, QWidget
from PyQt6.QtCore import QAbstractTableModel, Qt, QVariant


class PandasModel(QAbstractTableModel):
    """
    一个将Pandas DataFrame适配到QTableView的模型。
    这是在PyQt中显示和编辑大型数据集的最高效方法。
    """

    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return str(self._df.iloc[index.row(), index.column()])
        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            try:
                self._df.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index)
                return True
            except Exception as e:
                print(f"Error setting data: {e}")
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
        return self._df


class TableView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table = QTableView()
        self.layout.addWidget(self.table)

        self.model = None
        self.table.setSortingEnabled(True)

    def set_data(self, df):
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()

    def get_data(self):
        if self.model:
            return self.model.get_dataframe()
        return None