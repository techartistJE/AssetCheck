from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class AssetCheckWidgetUI(QWidget):
    def __init__(self, jsonData):
        super(AssetCheckWidgetUI, self).__init__()
        self.setObjectName("AssetCheckWidgetUI")
        self.errorData = jsonData["errorData"]  # Accessing the root "errorData"
        self.sceneCheckCount = 0
        
        self.initUI()
        self.createModelCleanUpCheckboxes()
        self.functionConnect()
        

    def initUI(self):
        """Initialize the main UI layout."""
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.addWidget(self.initLeftPanel())
        self.mainSplitter.addWidget(self.initRightPanel())
        self.mainSplitter.setStretchFactor(1, 1)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.mainSplitter)
        self.setLayout(self.mainLayout)

    def initLeftPanel(self):
        """Initialize the left panel for input and options."""
        self.leftWidget = QWidget()
        self.leftLayout = QVBoxLayout()

        # Input Button
        self.inputButton = QPushButton("검사 대상 선택 후 클릭")
        # text size 12 point and bold font
        # dark orange background color
        
        self.inputButton.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #DD6E13")
        self.inputButton.setObjectName("inputButton")
        self.inputButton.setFixedHeight(30)

        # Input Table
        self.inputTable = self.createInputTable()
        self.inputTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inputTable.selectRow(0)
        self.inputTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inputTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Option Group
        self.optionGroup = self.createOptionGroup()

        # Tab Widget for Options
        self.optionTab = self.createOptionTabs()

        # Add Widgets to Left Layout
        self.leftLayout.addWidget(self.inputButton)
        self.leftLayout.addWidget(self.inputTable)
        self.leftLayout.addWidget(self.optionGroup)
        self.leftLayout.addWidget(self.optionTab)

        # set Stretch Factor
        self.leftLayout.setStretchFactor(self.inputButton, 2)
        self.leftLayout.setStretchFactor(self.inputTable, 2)
        self.leftLayout.setStretchFactor(self.optionGroup, 1)
        self.leftLayout.setStretchFactor(self.optionTab, 7)

        self.leftWidget.setLayout(self.leftLayout)
        return self.leftWidget



    def createInputTable(self):
        """Create and configure the input table."""
        table = QTableWidget()
        table.setObjectName("inputTable")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["All Count", "Mesh", "Null Group", "Etc Node", "SceneFile"])
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
        self.allCheckboxesDict = {}
        categoryDict = self.errorData["category"]
        
        # create checkboxList sized by the number of categories
        for categoryDataDict in self.errorData["category"].values():
            checkBox = QCheckBox(categoryDataDict["uiText"])
            checkBox.setStyleSheet("font-size: 12pt")
            checkBox.setChecked(True)
            layout.addWidget(checkBox)
            self.CategoryCheckboxDict[categoryDataDict["id"]] = checkBox

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

        for categoryName, category_data in self.errorData["category"].items():
            tabWidget.addTab(self.createCategoryTab(categoryName, category_data), category_data["uiText"])

        return tabWidget

    def createCategoryTab(self, categoryName, category_data):
        """Create a tab for a specific category."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout = QVBoxLayout()
        
        self.allCheckboxesDict[categoryName]= {}
        for checkName, check_data in category_data.get("checkList", {}).items():
            
            checkbox = QCheckBox(check_data.get("checkBoxText", checkName))
            # text size 12 point
            checkbox.setStyleSheet("font-size: 11pt")
            checkbox.setChecked(check_data.get("isActive", True))

            self.allCheckboxesDict[categoryName][checkName] = checkbox
            layout.addWidget(checkbox)

        tab.setLayout(layout)
        scroll.setWidget(tab)
        return scroll
    
    def createModelCleanUpCheckboxes(self):
        
        """Add a divider and two checkboxes to the model tab."""
        # Find the model tab

        modelTab = self.optionTab.widget(self.errorData["category"]["model"]["id"])
        layout = modelTab.widget().layout()  # Access the layout of the inner widget
        # Create a divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

        # Create custom checkboxes
        vertexFreezeCheckbox = QCheckBox("Vertex 값 초기화")
        vertexFreezeCheckbox.setChecked(True)
        vertexFreezeCheckbox.setStyleSheet("font-size: 11pt")

        conformNormalCheckbox = QCheckBox("전체 Conform Normal 적용")
        conformNormalCheckbox.setChecked(True)
        conformNormalCheckbox.setStyleSheet("font-size: 11pt")

        # Add widgets to the layout
        layout.addWidget(divider)
        layout.addWidget(vertexFreezeCheckbox)
        layout.addWidget(conformNormalCheckbox)
      

    def initRightPanel(self):
        """Initialize the right panel for results."""
        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout()

        # Run Button
        self.runButton = QPushButton("검사 시작")
        self.runButton.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #DD6E13")
        self.runButton.setFixedHeight(30)
        self.runButton.setObjectName("runButton")

        # Error Result Tabs
        self.errorResultTab = QTabWidget()
        self.errorResultTab.setObjectName("errorResultTab")

        # Tab1: By Criteria
        self.errorResultTab.addTab(self.createErrorByCriteriaTab(), "기준별 Error 대상")

        # Tab2: By Element
        self.errorResultTab.addTab(self.createErrorByElementTab(), "대상별 Error 기준")

        # All Result Text
        self.allResult = QPlainTextEdit()
        self.allResult.setObjectName("allResult")
        self.allResult.setReadOnly(True)

        # Right Layout
        self.rightLayout.addWidget(self.runButton)
        self.rightLayout.addWidget(self.errorResultTab)
        self.rightLayout.addWidget(self.allResult)
        self.rightWidget.setLayout(self.rightLayout)

        return self.rightWidget

    def createErrorByCriteriaTab(self):
        """Create the error-by-criteria tab."""
        widget = QWidget()
        layout = QHBoxLayout()

        table = QTableWidget()
        table.setObjectName("errorByCriteriaTable")
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Error Count", "점검 필요 Count"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        listWidget = QListWidget()
        listWidget.setObjectName("errorElementList")

        layout.addWidget(table)
        layout.addWidget(listWidget)
        widget.setLayout(layout)
        return widget

    def createErrorByElementTab(self):
        """Create the error-by-element tab."""
        widget = QWidget()
        layout = QHBoxLayout()

        leftLayout = QVBoxLayout()
        nameFilter = QLineEdit()
        nameFilter.setObjectName("nameFilterLineEdit")
        nameFilter.setPlaceholderText("Name Filter")

        listWidget = QListWidget()
        listWidget.setObjectName("errorByElementList")

        leftLayout.addWidget(nameFilter)
        leftLayout.addWidget(listWidget)

        criteriaList = QListWidget()
        criteriaList.setObjectName("errorCriteriaList")

        layout.addLayout(leftLayout)
        layout.addWidget(criteriaList)
        widget.setLayout(layout)
        return widget


    def functionConnect(self):
        
        for id in range(len(self.CategoryCheckboxDict.items())):
            checkbox= self.CategoryCheckboxDict[id]
            state= checkbox.checkState()
            checkbox.stateChanged.connect(lambda state=state, id=id: self.toggleCategory(state, id))
        
