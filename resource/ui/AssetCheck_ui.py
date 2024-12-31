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

    def createModelCleanUpCheckboxes(self):
        """Add a divider and two checkboxes to the model tab."""
        modelTab = self.optionTab.widget(self.errorData["model"]["id"])
        layout = modelTab.widget().layout()

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

        vertexFreezeCheckbox = QCheckBox("Vertex 값 초기화")
        vertexFreezeCheckbox.setChecked(True)

        conformNormalCheckbox = QCheckBox("전체 Conform Normal 적용")
        conformNormalCheckbox.setChecked(True)

        layout.addWidget(divider)
        layout.addWidget(vertexFreezeCheckbox)
        layout.addWidget(conformNormalCheckbox)

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
        table.setHorizontalHeaderLabels(["Error Count"])
        table.setSelectionMode(QAbstractItemView.SingleSelection)

        # 열 크기 모드 설정
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)  # 마지막 열 확장

        listWidget = QListWidget()
        listWidget.setObjectName("errorTargetListA")
        listWidget.setSelectionMode(QAbstractItemView.MultiSelection)

        layout.addWidget(table)
        layout.addWidget(listWidget)
        layout.setStretch(0, 3)  # 테이블 확장 비율
        layout.setStretch(1, 2)  # 리스트 확장 비율
        widget.setLayout(layout)
        return widget

    def createErrorByTargetTab(self):
        widget = QWidget()
        layout = QHBoxLayout()

        leftLayout = QVBoxLayout()
        nameFilter = QLineEdit()
        nameFilter.setObjectName("nameFilterLineEdit")
        nameFilter.setPlaceholderText("Name Filter")

        listWidget = QListWidget()
        listWidget.setObjectName("errorTargetListB")

        leftLayout.addWidget(nameFilter)
        leftLayout.addWidget(listWidget)

        criteriaTree = QTreeWidget()
        criteriaTree.setSelectionMode(QAbstractItemView.MultiSelection)
        criteriaTree.setAlternatingRowColors(True)
        criteriaTree.setObjectName("errorCriteriaTree")
        criteriaTree.setHeaderLabels(["Error Count :"])
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
