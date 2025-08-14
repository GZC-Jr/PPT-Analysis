import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 应用一个简单的暗色调样式表来接近设计图
    app.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: #FFFFFF;
            font-size: 11pt;
        }
        QMainWindow {
            background-color: #2E2E2E;
        }
        QMenuBar, QMenuBar::item {
            background-color: #3C3C3C;
            color: #FFFFFF;
        }
        QMenuBar::item:selected {
            background-color: #555555;
        }
        QToolBar {
            background-color: #3C3C3C;
            border: none;
        }
        QToolButton {
            background-color: #3C3C3C;
            padding: 8px;
        }
        QToolButton:checked, QToolButton:hover {
            background-color: #555555;
        }
        QStackedWidget {
            background-color: #252526;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
        }
        QLineEdit, QTextEdit, QTableView {
            background-color: #3C3C3C;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }
        QPushButton {
            background-color: #555555;
            border: 1px solid #777777;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QPushButton:pressed {
            background-color: #444444;
        }
        QSlider::groove:horizontal {
            border: 1px solid #555555;
            height: 8px;
            background: #3C3C3C;
            margin: 2px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #888888;
            border: 1px solid #AAAAAA;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        QSplitter::handle {
            background-color: #555555;
        }
        QSplitter::handle:horizontal {
            width: 2px;
        }
        QSplitter::handle:vertical {
            height: 2px;
        }
        QHeaderView::section {
            background-color: #3C3C3C;
            color: white;
            padding: 4px;
            border: 1px solid #555;
        }
    """)

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())