from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from functools import partial


class AssetCheckWidgetUI(QWidget):
    def __init__(self, jsonData, uiStylePath):
        super(AssetCheckWidgetUI, self).__init__()
        self.setObjectName("AssetCheckWidgetUI")
        self.errorData = jsonData["errors"]  # Using the full "errorData" object
        
        self.initUI()
        self.createModelCleanUpCheckboxes()
        self.addManulCheckboxDict()
        self.functionConnect()

        self.sceneRelatedColor = QColor(255, 200, 125, 255)
        self.sceneRelatedCheckBoxList = self.getSceneRelatedCheckBoxList()
        self.ColoringCheckboxes(self.sceneRelatedCheckBoxList, self.sceneRelatedColor)
        # coloring inputTable header(4) : self.sceneRelatedColor
        self.inputTable.horizontalHeaderItem(4).setForeground(QBrush(self.sceneRelatedColor))

        with open(uiStylePath, "r") as f:
            self.setStyleSheet(f.read())

    def initUI(self):
        """Initialize the main UI layout."""
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.addWidget(self.initLeftPanel())
        self.mainSplitter.addWidget(self.initRightPanel())
        self.mainSplitter.setStretchFactor(1, 3)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.mainSplitter)
        self.setLayout(self.mainLayout)

    def initLeftPanel(self):
        """Initialize the left panel for input and options."""
        self.leftWidget = QWidget()
        self.leftLayout = QVBoxLayout()

        # Input Button
        self.inputButton = QPushButton("검사 대상 선택 후 클릭")
        self.inputButton.setObjectName("inputButton")
        self.inputButton.setFixedHeight(30)

        # Input Table
        self.inputTable = self.createInputTable()
        self.inputTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inputTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.inputTable.selectRow(0)
        self.inputTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inputTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inputTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Option Group
        self.optionGroup = self.createOptionGroup()

        # Tab Widget for Options
        self.optionTab = self.createOptionTabs()

        # Add Widgets to Left Layout
        self.leftLayout.addWidget(self.inputButton)
        self.leftLayout.addWidget(self.inputTable)
        self.leftLayout.addWidget(self.optionGroup)
        self.leftLayout.addWidget(self.optionTab)

        self.leftLayout.setStretch(0, 1)
        self.leftLayout.setStretch(1, 2)
        self.leftLayout.setStretch(2, 1)
        self.leftLayout.setStretch(3, 7)

        self.leftWidget.setLayout(self.leftLayout)
        return self.leftWidget

    def createInputTable(self):
        """Create and configure the input table."""
        table = QTableWidget()
        table.setObjectName("inputTable")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["All Count", "Mesh", "Null Group", "Etc Node", "Scene File"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(2)
        table.setVerticalHeaderLabels(["Global", "Selected\nHierarchy"])
        return table

    def createOptionGroup(self):
        """Create the option group with checkboxes."""
        group = QGroupBox("전체 활성/비활성화")
        group.setObjectName("optionGroup")
        layout = QHBoxLayout()

        self.CategoryCheckboxDict = {}
        categoryDict = self.errorData

        for categoryName, categoryData in categoryDict.items():
            checkBox = QCheckBox(categoryData["uiText"])
            checkBox.setChecked(True)
            layout.addWidget(checkBox)
            self.CategoryCheckboxDict[categoryData["id"]] = checkBox

        group.setLayout(layout)
        return group

    def toggleCategory(self, state, category_id):
        """Toggle all checkboxes in the related tab when the category checkbox is toggled."""
        tab = self.optionTab.widget(category_id)
        self.optionTab.setCurrentWidget(tab)
        checkboxes = tab.findChildren(QCheckBox)
        for checkbox in checkboxes:
            checkbox.setChecked(state == Qt.Checked)

    def createOptionTabs(self):
        """Create the tab widget for detailed options."""
        tabWidget = QTabWidget()
        tabWidget.setObjectName("optionTab")
        self.allCheckboxesDict = {}
        for categoryName, categoryData in self.errorData.items():
            tabWidget.addTab(self.createCategoryTab(categoryName, categoryData), categoryData["uiText"])

        return tabWidget

    def createCategoryTab(self, categoryName, category_data):
        """Create a tab for a specific category."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout()

        
        for checkName, checkData in category_data.get("checkList", {}).items():
            checkbox = QCheckBox(checkData.get("checkBoxText", checkName))
            checkbox.setChecked(checkData.get("isActive", True))

            if categoryName not in self.allCheckboxesDict:
                self.allCheckboxesDict[categoryName] = {}
                self.allCheckboxesDict[categoryName][checkName] = checkbox
            else:
                self.allCheckboxesDict[categoryName][checkName] = checkbox

            layout.addWidget(checkbox)

        tab.setLayout(layout)
        scroll.setWidget(tab)
        return scroll
    def addManulCheckboxDict(self):
        self.allCheckboxesDict["model"]["revNormal"] = self.NormalCheckbox
        self.allCheckboxesDict["model"]["selfIntersect"] = self.InterSectionCheckbox
        self.allCheckboxesDict["model"]["objectIntersect"] = self.ObjectInterSectionCheckbox
        
    def createModelCleanUpCheckboxes(self):
        """Add a divider and two checkboxes to the model tab."""
        modelTab = self.optionTab.widget(self.errorData["model"]["id"])
        layout = modelTab.widget().layout()

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

    
        label = QLabel("[ 수동 점검 체크리스트 ]")
        label.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        label.setStyleSheet("font-weight: bold; font-size: 13pt;")
        label.setAlignment(Qt.AlignCenter)

        checkListLayout = QGridLayout()
  
        self.NormalCheckbox = QCheckBox("Normal 뒤집힘 확인")
        self.NormalCheckbox.setChecked(True)
        self.NormalModebutton = QPushButton("BackFace Culling Off")
        self.NormalModebutton.setFixedHeight(30)
        self.NormalModebutton.setObjectName("NormalModeButton")
        self.NormalCheckedButton = QPushButton("확인 안함")
        self.NormalCheckedButton.setFixedHeight(30)
        self.NormalCheckedButton.setObjectName("NormalCheckedButton")
      
        self.InterSectionCheckbox = QCheckBox("자기 자신과 겹침이 있는지 확인")
        self.InterSectionCheckbox.setChecked(True)
        self.InterSectionHelpButton = QPushButton("참고 자료 보기")
        self.InterSectionHelpButton.setFixedHeight(30)
        self.InterSectionHelpButton.setObjectName("InterSectionHelpButton")
        self.InterSectionCheckedButton = QPushButton("확인 안함")
        self.InterSectionCheckedButton.setFixedHeight(30)
        self.InterSectionCheckedButton.setObjectName("InterSectionCheckedButton")

        self.ObjectInterSectionCheckbox = QCheckBox("다른 오브젝트와 겹침이 있는지 확인")
        self.ObjectInterSectionCheckbox.setChecked(True)
        self.ObjectInterSectionHelpButton = QPushButton("참고 자료 보기")
        self.ObjectInterSectionHelpButton.setFixedHeight(30)
        self.ObjectInterSectionHelpButton.setObjectName("ObjectInterSectionHelpButton")
        self.ObjectInterSectionCheckedButton = QPushButton("확인 안함")
        self.ObjectInterSectionCheckedButton.setFixedHeight(30)
        self.ObjectInterSectionCheckedButton.setObjectName("ObjectInterSectionCheckedButton")
   
        checkListLayout.addWidget(self.NormalCheckbox, 0, 0)
        checkListLayout.addWidget(self.NormalModebutton, 0, 1)
        checkListLayout.addWidget(self.NormalCheckedButton, 0, 2)
        checkListLayout.addWidget(self.InterSectionCheckbox, 1, 0)
        checkListLayout.addWidget(self.InterSectionHelpButton, 1, 1)
        checkListLayout.addWidget(self.InterSectionCheckedButton, 1, 2)
        checkListLayout.addWidget(self.ObjectInterSectionCheckbox, 2, 0)
        checkListLayout.addWidget(self.ObjectInterSectionHelpButton, 2, 1)
        checkListLayout.addWidget(self.ObjectInterSectionCheckedButton, 2, 2)
        
        
        layout.addWidget(divider)
        layout.addWidget(label)
        layout.addLayout(checkListLayout)
    
      

    def initRightPanel(self):
        """Initialize the right panel for results."""
        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout()

        self.runButton = QPushButton("검사 시작")
        self.runButton.setFixedHeight(30)
        self.runButton.setObjectName("runButton")

        self.errorResultTab = QTabWidget()
        self.errorResultTab.setObjectName("errorResultTab")
        self.errorResultTab.addTab(self.createErrorByCriteriaTab(), "기준별 Error 대상")
        self.errorResultTab.addTab(self.createErrorByTargetTab(), "대상별 Error 기준")

        self.rightLayout.addWidget(self.runButton)
        self.rightLayout.addWidget(self.errorResultTab)
        self.rightWidget.setLayout(self.rightLayout)

        return self.rightWidget

    def createErrorByCriteriaTab(self):
        widget = QWidget()
        layout = QHBoxLayout()

        table = QTableWidget()
        table.setObjectName("errorByCriteriaTable")
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Error Count :"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # header font size 11 and bold
        table.horizontalHeader().setStyleSheet("font-size: 11pt; font-weight: bold;")
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 가로 최소 크기는 고정, 세로는 상관 없음음
        table.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 열 크기 모드 설정
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)  # 마지막 열 확장

        listWidget = QListWidget()
        listWidget.setObjectName("errorTargetListA")
        listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(table)
        layout.addWidget(listWidget)
        layout.setStretch(0, 2)  # 테이블 확장 비율
        layout.setStretch(1, 3)  # 리스트 확장 비율
        widget.setLayout(layout)
        return widget

    def createErrorByTargetTab(self):
        widget = QWidget()
        layout = QHBoxLayout()

        leftLayout = QVBoxLayout()

        nameFilterLayout = QHBoxLayout()
        self.nameFilter = QLineEdit()
        self.nameFilter.setFixedHeight(30)
        self.nameFilter.setObjectName("nameFilterLineEdit")
        self.nameFilter.setPlaceholderText("Name Filter")
        self.nameFilter.setStyleSheet("font-size: 11pt;")
        self.resetTextButton = QPushButton("X")
        self.resetTextButton.setObjectName("resetTextButton")
        self.resetTextButton.setFixedWidth(30)
        self.resetTextButton.setFixedHeight(30)
        nameFilterLayout.addWidget(self.nameFilter)
        nameFilterLayout.addWidget(self.resetTextButton)
  
        listWidget = QListWidget()
        listWidget.setObjectName("errorTargetListB")
        listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        leftLayout.addLayout(nameFilterLayout)
        leftLayout.addWidget(listWidget)

        criteriaTree = QTreeWidget()
        criteriaTree.setSelectionMode(QAbstractItemView.MultiSelection)
        criteriaTree.setAlternatingRowColors(True)
        criteriaTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        criteriaTree.setObjectName("errorCriteriaTree")
        criteriaTree.setHeaderLabels(["Error Count :"])
        # header font size 11 and bold 
        # set center alignment
        criteriaTree.header().setStyleSheet("font-size: 11pt; font-weight: bold;")
        criteriaTree.header().setDefaultAlignment(Qt.AlignCenter)
        criteriaTree.setColumnCount(1)

        layout.addLayout(leftLayout)
        layout.addWidget(criteriaTree)
        widget.setLayout(layout)
        return widget

    def getSceneRelatedCheckBoxList(self):
        sceneRelatedCheckBoxList = []
        for categoryName, categoryData in self.errorData.items():
            for checkName, checkData in categoryData.get("checkList", {}).items():
                if checkData.get("isSceneRelated", False):
                    checkboxWidget = self.allCheckboxesDict[categoryName][checkName]
                    sceneRelatedCheckBoxList.append(checkboxWidget)
        return sceneRelatedCheckBoxList
    
    def ColoringCheckboxes(self, checkboxList, color):

        for checkbox in checkboxList:
            # only text color not indicator color
            checkbox.setStyleSheet("color: rgb({},{},{})".format(color.red(), color.green(), color.blue()))

    def findWidget(self, parentWidget, widgetName):
        for widget in parentWidget.findChildren(QWidget):
            if widget.objectName() == widgetName:
                return widget
        return None

    def functionConnect(self):
        for id, checkbox in self.CategoryCheckboxDict.items():
            checkbox.stateChanged.connect(partial(self.toggleCategory, category_id=id))
        
        self.NormalCheckbox.stateChanged.connect(lambda state : self.NormalCheckedButton.setEnabled(state))
        self.InterSectionCheckbox.stateChanged.connect(lambda state : self.InterSectionCheckedButton.setEnabled(state))
        self.ObjectInterSectionCheckbox.stateChanged.connect(lambda state : self.ObjectInterSectionCheckedButton.setEnabled(state))

        self.resetTextButton.clicked.connect(lambda: self.nameFilter.clear())
