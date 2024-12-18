# -*_ coding: utf-8 -*-
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class AssetCheck_WidgetUI(QWidget):
    def __init__(self):
        super(AssetCheck_WidgetUI, self).__init__()
        self.setObjectName("AssetCheck_Widget")
        self.setupUi()
    
    def setupUi(self):
        # main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignHCenter)

        # topGroup Layout
        self.topGroupLayout = QHBoxLayout()
        self.topGroupLayout.setAlignment(Qt.AlignHCenter)
        
        # topGroup LineEdit
        self.topGroupLineEdit = QLineEdit()
        self.topGroupLineEdit.setObjectName("topGroupLineEdit")
        self.topGroupLineEdit.setAlignment(Qt.AlignCenter)
        self.topGroupLineEdit.setPlaceholderText("Asset Top Group Name")
        self.topGroupLineEdit.setFixedHeight(30)
        self.topGroupLineEdit.setReadOnly(True)
        
       
        self.topGroupBtn = QPushButton("입력")
        self.topGroupBtn.setFixedHeight(30)
        self.topGroupBtn.setFixedWidth(100)

        self.topGroupLayout.addWidget(self.topGroupLineEdit)
        self.topGroupLayout.addWidget(self.topGroupBtn)


        # Create Table Widget for Asset CheckList
        # row: Ngon, face normal, overlapped objects, history, object pivot, Transform Value, Useless NameSpace, Same name, Shape Name, vertex has ptvalue, perspective view save
        # column: P or NP, description
        self.assetCheckTable = QTableWidget()
        self.assetCheckTable.setRowCount(11)
        self.assetCheckTable.setVerticalHeaderLabels(["N-gon Face", "뒤집힌 노말", "겹친 오브젝트", "히스토리", "오브젝트 피봇", "Freeze 트랜스폼", "네임스페이스", "중복된 이름", "잘못된 Shape 노드 이름", "수치가 들어간 Vertex", "Perspective View 저장여부"])
        # VerticalHeaderLabels text bold
        for i in range(11):
            self.assetCheckTable.verticalHeaderItem(i).setFont(QFont("Arial", 10, QFont.Bold))
        
        self.assetCheckTable.setColumnCount(2)
        self.assetCheckTable.setHorizontalHeaderLabels(["P / NP", "Description"])
        for i in range(2):
            self.assetCheckTable.horizontalHeaderItem(i).setFont(QFont("Arial", 10, QFont.Bold))
        self.assetCheckTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assetCheckTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # refresh button
        self.refreshBtn = QPushButton("Refresh")
        self.refreshBtn.setFixedHeight(30)
        self.refreshBtn.setFixedWidth(100)


        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addStretch(1)  # Add stretchable space before the button
        self.buttonLayout.addWidget(self.refreshBtn)
        self.buttonLayout.addStretch(1)  # Add stretchable space after the button

        # add all widget to main layout
        self.mainLayout.addLayout(self.topGroupLayout)
        self.mainLayout.addWidget(self.assetCheckTable)
        self.mainLayout.addWidget(self.refreshBtn)
      
        
        # set layout
        self.setLayout(self.mainLayout)
        