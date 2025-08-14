# PPT-Analysis/ui/widgets/file_controls.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox
from PyQt6.QtCore import pyqtSignal

class FileControls(QWidget):
    upload_ppt_clicked = pyqtSignal()
    upload_csv_clicked = pyqtSignal()
    batch_upload_csv_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        
        group_box = QGroupBox("选择文件")
        group_layout = QVBoxLayout()
        
        self.btn_upload_ppt = QPushButton("上传PPT")
        self.btn_upload_csv = QPushButton("上传CSV")
        self.btn_batch_upload_csv = QPushButton("批量上传CSV")
        
        self.btn_upload_ppt.clicked.connect(self.upload_ppt_clicked)
        self.btn_upload_csv.clicked.connect(self.upload_csv_clicked)
        self.btn_batch_upload_csv.clicked.connect(self.batch_upload_csv_clicked)
        
        group_layout.addWidget(self.btn_upload_ppt)
        group_layout.addWidget(self.btn_upload_csv)
        group_layout.addWidget(self.btn_batch_upload_csv)
        
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        layout.addStretch()