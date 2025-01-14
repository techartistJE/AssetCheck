from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import maya.OpenMayaUI as mui
import maya.cmds as cmds

import shiboken2
import sys
import os
import json

import fnmatch

try:
    RootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pkgPath = os.path.dirname(os.path.abspath(__file__))
    inputDataPath = os.path.join(pkgPath, 'resource', 'data', 'inputData.json')
    errorDataPath = os.path.join(pkgPath, 'resource', 'data', 'errorData.json')
    uiStylePath = os.path.join(pkgPath, 'resource', 'ui', 'uiStyle.css')
except:
    pkgPath = 'D:\myScript\maya\AssetCheck'

import AssetCheck.resource.ui.AssetCheck_ui as AssetCheck_ui
import AssetCheck.modules.general as general
import AssetCheck.modules.model as model
import AssetCheck.modules.naming as naming


import AssetCheck.modules.simple_om_object as simple_om_object

import importlib
for module in [AssetCheck_ui, general, model, naming, simple_om_object]:
    importlib.reload(module)

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(ptr), QWidget)

def loadJsonData(jsonPath):
    with open(jsonPath, 'r', encoding="utf-8") as f:
        return json.load(f)

class mainWin(QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__(parent=getMayaWindow())
        self.setObjectName("AssetCheck_win")
        self.setWindowTitle("AssetCheck")

        self.selInputList = []
        self.AllInputList = []
        
        self.errorData = loadJsonData(errorDataPath)["errorData"]
        

        self.sceneCheckCount = 0
        self.ui = AssetCheck_ui.AssetCheckWidgetUI(self.errorData, uiStylePath)

        self.initManualErrorData()
        self.errorMessages = self.getErrorMsgs()
        self.sceneRelatedCheckBoxList = self.ui.sceneRelatedCheckBoxList

        self.setCentralWidget(self.ui)
  
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # 화면 크기에 비례하여 윈도우 크기 설정
        self.resize(int(screen_width * 0.5), int(screen_height * 0.5))
        self.ui.mainSplitter.setSizes([int(screen_width * 0.25), int(screen_width * 0.25)])
        self.updateInputTable()

        self.uiFuncConnect()

        self.is_short_path_listA = True
        self.is_short_path_listB = True
        self.is_short_path_tree = True

        self.criteriaTable = self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        self.criteriaTable.viewport().installEventFilter(self)
        self.listWidgetA = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListA")
        self.listWidgetA.viewport().installEventFilter(self)
        self.listWidgetA.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidgetA.customContextMenuRequested.connect(self.showContextMenu)
        self.listWidgetB = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
        self.listWidgetB.viewport().installEventFilter(self)
        self.listWidgetB.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidgetB.customContextMenuRequested.connect(self.showContextMenu)
        self.treeWidget = self.ui.findWidget(self.ui.errorResultTab, "errorCriteriaTree")
        self.treeWidget.viewport().installEventFilter(self)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)

    def uiFuncConnect(self):
        self.ui.inputButton.clicked.connect(self.updateInputTable)
        self.ui.runButton.clicked.connect(self.errorCheckRun)
        self.ui.nameFilter.textChanged.connect(lambda: self.filterItemsInList(self.listWidgetB, self.ui.nameFilter.text()))

        for checkbox in self.sceneRelatedCheckBoxList:
            checkbox.stateChanged.connect(self.updateSceneCheckCount)

        self.ui.NormalModebutton.clicked.connect(self.backfaceCullingOnOff)
        self.ui.NormalCheckedButton.clicked.connect(lambda: self.selfCheckedToggle(self.ui.NormalCheckedButton))
        self.ui.InterSectionCheckedButton.clicked.connect(lambda: self.selfCheckedToggle(self.ui.InterSectionCheckedButton))
        self.ui.ObjectInterSectionCheckedButton.clicked.connect(lambda: self.selfCheckedToggle(self.ui.ObjectInterSectionCheckedButton))

    # ---------Init Manual Error Data Structure 추가 -------------
    def initManualErrorData(self):
    # errorData.json 파일에 내용이 ui 자동 생성용으로 쓰여서
    # 아래 수동 검사 구조는 ui 생성 후에 추가해야 함
    
        modelManualCheckDict = {
            "revNormal": {
                "id": 3,
                "checkBoxText": "뒤집힌 면 확인",
                "errorMessage": "뒤집힌 면이 있는지 확인해주세요.",
                "isActive": True,
                "isSceneRelated": False,
                "nodes": []
            },
            "selfIntersect": {
                "id": 4,
                "checkBoxText": "자기 자신과 겹침이 있는지 확인",
                "errorMessage": "자기 자신과 겹침이 있는지 확인해주세요.",
                "isActive": True,
                "isSceneRelated": False,
                "nodes": []
            },
            "objectIntersect": {
                "id": 5,
                "checkBoxText": "다른 오브젝트와 겹침이 있는지 확인",
                "errorMessage": "다른 오브젝트와 겹침이 있는지 확인해주세요.",
                "isActive": True,
                "isSceneRelated": False,
                "nodes": []
            }
        }

        # model 카테고리의 checkList에 병합
        if "model" in self.errorData["errors"]:
            self.errorData["errors"]["model"]["checkList"].update(modelManualCheckDict)
        else:
            # model 카테고리가 없으면 새로 추가
            self.errorData["errors"]["model"] = {
                "id": 1,
                "uiText": "모델링",
                "checkList": modelManualCheckDict
            }

        



    # ---------------------------- Input Table ----------------------------
    def updateInputTable(self):
        isSelected= self.inputNode()
       
        if isSelected:
            self.ui.inputTable.selectRow(1)
        else:
            self.ui.inputTable.selectRow(0)
        self.updateSceneCheckCount()
        self.updateInputTableUI()
        self.resetManualCheckUI()

    def updateSceneCheckCount(self):
       
        self.sceneCheckCount = sum(1 for checkbox in self.sceneRelatedCheckBoxList if checkbox.isChecked())
        self.AllCountList[-1] = self.sceneCheckCount
        self.selCountList[-1] = self.sceneCheckCount
        self.updateInputTableUI()

    def updateInputTableUI(self):
        for row in range(2):
            for col in range(5):
                if row == 0:
                    value = self.AllCountList[col]
                else:
                    value = self.selCountList[col]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Arial", 12))
                self.ui.inputTable.setItem(row, col, item)

    def inputNode(self):
        outliner = cmds.getPanel(type='outlinerPanel')[0]
        cmds.outlinerEditor(outliner, edit=True, showDagOnly=True)

        selectedNode = cmds.ls(sl=True, long=True, dag=True)
        allSceneNode = cmds.ls(assemblies=True, long=True, dag=True)

        self.selInputList = self.nodeFilter(selectedNode)
        self.selCountList = self.createCountList(self.selInputList)

        self.AllInputList = self.nodeFilter(allSceneNode)
        self.AllCountList = self.createCountList(self.AllInputList)

        if selectedNode:
            return True
        else:
            return False
        
    def checkExistNode(self, inputList):
        # before check run, check if the node exists
        error = False
        allNodeList = []
        for group in inputList:
            for node in group:
                allNodeList.append(node)

        for node in allNodeList:
            nodeName = node.selectedNodeName
            if not cmds.objExists(nodeName):
                error = True
                break
        #  경고창 윈도우 띄우기
        if error:
            warningWin= QMessageBox()
            message= "삭제되거나 이름이 변경된 노드가 있습니다.\n노드를 재입력 후 다시 시도해주세요."
            warningWin.setWindowTitle("Warning")
            # warningWin size
            warningWin.setFixedSize(400, 150)
            # set font style and size
            # set font bold
            warningWin.setFont(QFont("Arial", 12))
            warningWin.setStyleSheet("font-weight: bold;")
            warningWin.setText(message)
            # window position center of the self window
        
            warningWin.move(self.x() + self.width() / 2 - warningWin.width() / 2, self.y() + self.height() / 2 - warningWin.height() / 2)
            warningWin.exec_()

        return error
            
        


    def nodeFilter(self, inputNodeList):
        meshList, nullGroupList, etcNodeList = [], [], []
        defaultCameras = {"persp", "top", "front", "side"}

        for node in inputNodeList:
            omNode = simple_om_object.SimpleOMObject(node)
            if omNode.IsShape:
                continue

            if omNode.objectType == 'mesh':
                meshList.append(omNode)
            elif omNode.objectType == 'transform':
                nullGroupList.append(omNode)
            elif omNode.objectType != 'camera' or omNode.shortName(node) not in defaultCameras:
                etcNodeList.append(omNode)

        return [meshList, nullGroupList, etcNodeList]

    def createCountList(self, inputList):
        tableCouintList = [0, 0, 0, 0, 0]
        allCount= 0
        for id, group in enumerate(inputList):
            tableCouintList[id+1] = len(group)
            allCount += len(group)
        tableCouintList[0] = allCount
        tableCouintList[-1] = self.sceneCheckCount

        return tableCouintList
    # ---------------------------- Error Check ----------------------------

    def errorCheckRun(self):
        if self.ui.inputTable.currentRow() == 0:
            inputList = self.AllInputList
        else:
            inputList = self.selInputList

        if self.checkExistNode(inputList):
            return

        # Steop 0: errorData 초기화
        self.errorData = loadJsonData(errorDataPath)["errorData"]
        self.initManualErrorData()
        # Result UI 초기화
        self.resultUIInit()

        # Step 1: Update isActive status based on checkbox state
        for category, categoryData in self.errorData["errors"].items():
            for checkName, checkData in categoryData["checkList"].items():
                self.errorData["errors"][category]["checkList"][checkName]["isActive"] = self.ui.allCheckboxesDict[category][checkName].isChecked()

        manualCheckUIDict= {"revNormal": self.ui.NormalCheckedButton, "selfIntersect": self.ui.InterSectionCheckedButton, "objectIntersect": self.ui.ObjectInterSectionCheckedButton}
        # Step 2: Run error checks
        for categoryName, categoryData in self.errorData["errors"].items():
            for checkName, checkData in categoryData["checkList"].items():
                if checkData["isActive"]:
                    errorCount, nodes, detail = self.runEachErrorCheck(categoryName, checkName, inputList)
                    errorCount = len(nodes)
                  
                    if checkName in manualCheckUIDict:
                        isCheckedText= manualCheckUIDict[checkName].text()
                        
                        if "안함" not in isCheckedText:
                            errorCount= 0
                            nodes= []
                            detail= []
            
                    
                    checkData["nodes"] = nodes
                    checkData["errorCount"] = errorCount
                    
                    for id, node in enumerate(nodes):
                        if isinstance(node, str):
                            nodeName = node
                        else:
                            nodeName = node.selectedNodeName

                        # Initialize nodeName if not present
                        if nodeName not in self.errorData["nodes"]:
                            self.errorData["nodes"][nodeName] = {}

                        # Validate detail and store data
                        if not isinstance(detail, list):
                            print(f"Invalid detail structure for node '{nodeName}': {detail}")
                            continue

                        if detail:
                            self.errorData["nodes"][nodeName][checkName] = detail[id]
                        else:
                            self.errorData["nodes"][nodeName][checkName] = []
                       

        # Step 3: Update UI with results
        self.resultUIUpdate()

    def runEachErrorCheck(self, category, checkName, inputList):
        """
        Run the error check for a specific category and check name.
        
        Args:
            category (str): The category of the error check (e.g., "general").
            checkName (str): The specific check name (e.g., "unfreeze").
            inputList (list): The full input list to be processed.
        
        Returns:
            tuple: (errorCount, errorNodes)
        """
        result = self.getCheckFunction(category, checkName)
        if result == None:
            print(f"Skipping check '{checkName}' in category '{category}' as it is not implemented.")
            return 0, [], []
        
        func, inputRange = result

        # Apply input range if specified
        if isinstance(inputRange, slice):
            filteredInput = inputList[inputRange]
        elif isinstance(inputRange, int):
            filteredInput = [inputList[inputRange]]
        else:
            filteredInput = inputList  # Default: use full list

        # Run the check function with the filtered input
        allErrorNodes = []
        allDetail = []
        allErrorCount = 0
        for group in filteredInput:
             
            result= func(group)
            if len(result) == 2:
                errorCount, errorNodes = result
                details = []
            else:
                errorCount, errorNodes, details = result

            allErrorCount += errorCount
            allErrorNodes.extend(errorNodes)
            allDetail.append(details)
        
        return allErrorCount, allErrorNodes, allDetail

    def resultUIUpdate(self):
        """
        Updates the UI with the error check results.
        """
      
        # Step 1: Update errorByCriteriaTable
        criteriaTable = self.criteriaTable
        resultTableData = []

        for category, checkList in self.errorData["errors"].items():
            for checkName, checkData in checkList.get("checkList", {}).items():
                errorCount = checkData.get("errorCount", 0)
                errorNodeList = checkData.get("nodes", [])
                if errorCount > 0:
                    resultTableData.append([category, checkName, errorCount, errorNodeList])

        criteriaTable.setRowCount(len(resultTableData))

        allErrorCount = 0
        for i, data in enumerate(resultTableData):
            category, checkName, errorCount, errorNodeList = data

            # Set category and checkName
            criteriaHeaderItem = QTableWidgetItem(checkName)
            criteriaHeaderItem.setFont(QFont("Arial", 11))
            criteriaHeaderItem.setTextAlignment(Qt.AlignCenter)
            criteriaTable.setVerticalHeaderItem(i, criteriaHeaderItem)

            # Set error count
            countItem = QTableWidgetItem(str(errorCount))
            countItem.setFont(QFont("Arial", 11))
            countItem.setTextAlignment(Qt.AlignCenter)
            criteriaTable.setItem(i, 0, countItem)

            allErrorCount += errorCount

            # set data: category
            criteriaHeaderItem.setData(Qt.UserRole, category)
        
        criteriaTable.setHorizontalHeaderLabels(["Error Count : " + str(allErrorCount)])
        # font size 11 center align
        criteriaTable.horizontalHeaderItem(0).setFont(QFont("Arial", 11))
        criteriaTable.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        criteriaTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
  
        # Resize row and column
        criteriaTable.resizeColumnsToContents()
        criteriaTable.resizeRowsToContents()
        criteriaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        

        # Connect selection change to update listWidgetA
        criteriaTable.itemSelectionChanged.connect(self.showErrorTargetByCriteria)
       
        # Step 2: Update errorTargetListA
        criteriaTable.setCurrentCell(0, 0)

        # Step 3: Update errorTargetListB
        self.updateErrorTargetListB()


 
    def populateErrorList(self, listWidget, errorNodeList, isShortPath):
        """
        Populates a given listWidget with error nodes.
        Args:
            listWidget (QListWidget): The widget to update.
            errorNodeList (list): The list of error nodes to display.
            isShortPath (bool): Whether to display shortPath (True) or fullPath (False).
        """

        for node in errorNodeList:
            nodeName = node if isinstance(node, str) else node.selectedNodeName
            shortName = self.PathToshortName(nodeName)

            itemWidget = QListWidgetItem(shortName if isShortPath else nodeName)
            itemWidget.setData(Qt.UserRole, nodeName)
            itemWidget.setData(Qt.UserRole + 1, shortName)
            listWidget.addItem(itemWidget)

    def showErrorTargetByCriteria(self):
        """
        Updates errorTargetListA based on the selected criteria in the errorByCriteriaTable.
        """
        tableWidget = self.criteriaTable
        listWidgetA = self.listWidgetA

        currentItem = tableWidget.currentItem()
        if not currentItem:
            return
        listWidgetA.clear()
        currentRow = currentItem.row()
        currentHeader = tableWidget.verticalHeaderItem(currentRow)
        category = currentHeader.data(Qt.UserRole)

     
        errorNodeList = self.errorData["errors"][category]["checkList"][currentHeader.text()]["nodes"]
        if "scene" in errorNodeList:
            errorNodeList = self.errorData["nodes"]["scene"][currentHeader.text()]
        self.populateErrorList(listWidgetA, errorNodeList, self.is_short_path_listA)

       
    
    def updateErrorTargetListB(self):
        """
        Updates errorTargetListB with all nodes that have errors.
        """
        listWidgetB = self.listWidgetB
        errorNodes = list(self.errorData["nodes"].keys())

        listWidgetB.clear()
        self.populateErrorList(listWidgetB, errorNodes, self.is_short_path_listB)

        
        listWidgetB.itemSelectionChanged.connect(self.updateErrorTreeByNode)
        if listWidgetB.count() > 0:
            listWidgetB.setCurrentRow(0)

    def updateErrorTreeByNode(self):
        """
        Updates errorCriteriaTree based on the selected criteria.
        """
        ListWidgetB = self.listWidgetB
        treeWidget = self.treeWidget
     

        # full path
        nodeName= ListWidgetB.currentItem()
        if nodeName:
            nodeName = nodeName.data(Qt.UserRole)
        else:
            return
        treeWidget.clear()
        errorData= self.errorData["nodes"].get(nodeName, {})
        if not errorData:
            #print("Can't find error data for node:", nodeName)
            return

        allErrorCount = len(errorData)
        headerItem= treeWidget.headerItem()
        headerItem.setText(0, f"Error Count: {allErrorCount}")
        headerItem.setFont(0, QFont("Arial", 11))
        headerItem.setTextAlignment(0, Qt.AlignCenter)
        for checkName, details in errorData.items():
            errorMessage = self.errorMessages[checkName]
            topLevelItem = QTreeWidgetItem()
            topLevelItem.setData(0, Qt.UserRole, checkName)
            topLevelItem.setData(0, Qt.UserRole + 1, errorMessage)
            topLevelItem.setText(0, errorMessage)
            topLevelItem.setTextAlignment(0, Qt.AlignCenter)
            treeWidget.addTopLevelItem(topLevelItem)

            # 단일 리스트로 맞춰주기 : string -> [string] / [[string]] -> [string]
            if not isinstance(details, list):
                details = [details]

            if isinstance(details, list):
                if details and isinstance(details[0], list):
                    details =[]
                    for detail in details:
                        details.extend(detail)

            for detail in details:
                childItem = QTreeWidgetItem()
                
                detailPath = detail
                if "|" in detailPath:
                    shortPath= detailPath.split("|")[-1]
                else:
                    shortPath= detailPath

                childItem.setData(0, Qt.UserRole, detailPath)
                childItem.setData(0, Qt.UserRole + 1, shortPath)
                childItem.setText(0, shortPath if self.is_short_path_tree else detailPath)
                topLevelItem.addChild(childItem)

            topLevelItem.setExpanded(True)

        self.setTopLevelItemColors(treeWidget)




    def runEachErrorCheck(self, category, checkName, inputList):
        """
        Run the error check for a specific category and check name.
        
        Args:
            category (str): The category of the error check (e.g., "general").
            checkName (str): The specific check name (e.g., "unfreeze").
            inputList (list): The full input list to be processed.
        
        Returns:
            tuple: (errorCount, errorNodes)
        """
        result = self.getCheckFunction(category, checkName)
    
        if result == None:
            print(f"Skipping check '{checkName}' in category '{category}' as it is not implemented.")
            return 0, [], []
    
        
        func, inputRange = result

        # Apply input range if specified
        if isinstance(inputRange, slice):
            filteredInput = inputList[inputRange]
        elif isinstance(inputRange, int):
            filteredInput = [inputList[inputRange]]
        else:
            filteredInput = inputList  # Default: use full list

        # Run the check function with the filtered input
        allErrorNodes = []
        allDetail = []
        allErrorCount = 0
        for group in filteredInput:
            result= func(group)
            if len(result) == 2:
                errorCount, errorNodes = result
                details = []
            else:
                errorCount, errorNodes, details = result

            if errorNodes==None:
                errorNodes=[]

            if errorCount:
                if errorNodes[0] == "scene":
                    
                    if "scene" not in allErrorNodes:
                        allDetail.append(details)
                        allErrorNodes.extend(errorNodes)
                        allErrorCount += errorCount

                else:
                    allErrorNodes.extend(errorNodes)
                    allErrorCount += errorCount
                  
 
            if details:
                for id in range(len(errorNodes)):
                    allDetail.append(details[id])
        


        return allErrorCount, allErrorNodes, allDetail
      

    def getCheckFunction(self, category, checkName):
        """
        Returns the function and input range for a specific check.
        
        Args:
            category (str): Category name (e.g., "general").
            checkName (str): Check name (e.g., "unfreeze").
        
        Returns:
            tuple: (function, inputRange)
        """
        funcMap = {
            "general": {
                "unfreeze": (general.unfreezeTransform, slice(None, -1)),  # Exclude last element
                "pivot": (general.pivotAtWorldCenter, slice(None, -1)),  # Exclude last element
                "history": (general.history, slice(None, -1)),  # Exclude last element
                "animkey": (general.animKey, None),  # Use full list
                "topGroup": (general.topGroup, None),  # Use full list
                "layer": (general.layer, None),  # Use full list
                "hidden": (general.hidden, None),  # Use full list
                "defaultMaterial": (general.onlyDefaultMaterial, None),  # Use full list
                "defaultCamera": (general.onlyDefaultCamera, None),  # Use full list
                "perspView": (general.perspView, None),  # Use full list
                "unKnown": (general.unKnown, None),  # Use full list
            },
            "model": {
                "ngon": (model.ngonFace, 0),  # Use first element only
                "lockedVertex": (model.lockedVertex, 0),  # Use first element only
                "vertexInit": (model.vertexInit, 0),  # Use first element only
                "revNormal": (model.revNormal, 0),  # Use first element only
                "selfIntersect": (model.selfIntersect, 0),  # Use first element only
                "objectIntersect": (model.objectIntersect, 0),  # Use first element only
            },
            "naming": {
                "duplicatedNames": (naming.duplicatedNames, None),  # Use full list
                "nameSpace": (naming.nameSpace, None),  # Use full list
                "shapeName": (naming.shapeName, None),  # Use full list

            }
           
        }

        if category in funcMap and checkName in funcMap[category]:
            return funcMap[category][checkName]
        else:
            return None
            
    def resetManualCheckUI(self):
        manualCheckUIDict= {"revNormal": self.ui.NormalCheckedButton, "selfIntersect": self.ui.InterSectionCheckedButton, "objectIntersect": self.ui.ObjectInterSectionCheckedButton}
        for checkName, buttonWidget in manualCheckUIDict.items():
            buttonWidget.setText("확인 안함")
            buttonWidget.setStyleSheet("background-color: #7e2c1e;")

    def sceneRelatedCheckboxCountUpdate(self):
        self.updateSceneCheckCount()
        self.updateInputTableUI()

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                # 중간 버튼 클릭 처리
                if source == self.listWidgetA.viewport():
                    self.togglePathModeInList(self.listWidgetA, "listA")
                elif source == self.listWidgetB.viewport():
                    self.togglePathModeInList(self.listWidgetB, "listB")
                elif source == self.treeWidget.viewport():
                    self.togglePathModeInTree()
            elif event.button() == Qt.LeftButton:
                # 왼쪽 버튼 클릭 처리
                if source == self.criteriaTable.viewport():
                    self.showErrorTargetByCriteria()
        
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                # 왼쪽 버튼 클릭 해제 처리
                if source == self.criteriaTable.viewport():
                    self.showErrorTargetByCriteria()

        return super().eventFilter(source, event)


    def togglePathModeInList(self, widget, widgetName):
        isShort = getattr(self, f"is_short_path_{widgetName}")
        setattr(self, f"is_short_path_{widgetName}", not isShort)

        for i in range(widget.count()):
            item = widget.item(i)
            fullPath = item.data(Qt.UserRole)
            shortPath = item.data(Qt.UserRole + 1)
            item.setText(shortPath if not isShort else fullPath)

    def togglePathModeInTree(self):
        """
        Toggles the display mode (fullPath/shortPath) for childLevel items in the treeWidget.
        """
        self.is_short_path_tree = not self.is_short_path_tree
        treeWidget = self.treeWidget
        root = treeWidget.invisibleRootItem()

        # Iterate over topLevel items
        for i in range(root.childCount()):
            topLevelItem = root.child(i)
            self.updateTreeItemsToPath(topLevelItem, self.is_short_path_tree)

    def updateTreeItemsToPath(self, topLevelItem, toShort):
        """
        Updates the display mode (fullPath/shortPath) for childLevel items of the given topLevel item.
        Args:
            topLevelItem (QTreeWidgetItem): The topLevel item whose children will be updated.
            toShort (bool): Whether to display shortPath (True) or fullPath (False).
        """
        # Iterate over childLevel items (1st-level children of topLevelItem)
        for j in range(topLevelItem.childCount()):
            childItem = topLevelItem.child(j)
            fullPath = childItem.data(0, Qt.UserRole)  # Full path
            shortPath = childItem.data(0, Qt.UserRole + 1)  # Short path

            if fullPath and shortPath:
                # Update text to shortPath or fullPath based on the toggle state
                childItem.setText(0, shortPath if toShort else fullPath)
            else:
                # If paths are not set, fallback to existing text
                fullPath = childItem.text(0)
                shortPath = self.PathToshortName(fullPath)
                childItem.setData(0, Qt.UserRole, fullPath)
                childItem.setData(0, Qt.UserRole + 1, shortPath)
                childItem.setText(0, shortPath if toShort else fullPath)

    def PathToshortName(self, nodeName):
        return nodeName.rsplit("|", 1)[-1] if "|" in nodeName else nodeName

    def setTopLevelItemColors(self, treeWidget):
        root = treeWidget.invisibleRootItem()
        for i in range(root.childCount()):
            topItem = root.child(i)
            color = QColor(70, 70, 70) if i % 2 == 0 else QColor(80, 80, 80)
            for col in range(topItem.columnCount()):
                topItem.setBackground(col, color)
      
    def resultUIInit(self):
        allResultUI = [self.criteriaTable, self.listWidgetA, self.listWidgetB, self.treeWidget]  
        for ui in allResultUI:
            ui.clear()

        self.criteriaTable.setRowCount(0)
        self.treeWidget.headerItem().setText(0, "Error Count: 0")

    def getErrorMsgs(self):
        MessageDict= {}
        errorCategory = self.errorData["errors"]
        for category, checkList in errorCategory.items():
            for checkName, checkData in checkList["checkList"].items():
                errorMessages = checkData.get("errorMessage", [])
                MessageDict[checkName] = errorMessages
    
        return MessageDict

    def backfaceCullingOnOff(self):
        currentText= self.ui.NormalModebutton.text()
        OnOff= False
        if "On" in currentText:
            self.ui.NormalModebutton.setText("BackFace Culling Off")
            self.ui.NormalModebutton.setStyleSheet("background-color: #3f3f3d;")
            OnOff = False
        elif "Off" in currentText:
            self.ui.NormalModebutton.setText("BackFace Culling On")
            self.ui.NormalModebutton.setStyleSheet("background-color: #7c7c7c;")
            OnOff = True 
        panels = cmds.getPanel(typ= 'modelPanel')
        for panel in panels:
            cmds.modelEditor(panel, edit=True, backfaceCulling= OnOff)

    def selfCheckedToggle(self, buttonWidget):
        currentText= buttonWidget.text()
        if "안함" in currentText:
            buttonWidget.setText("확인함")
            # 녹색으로 변경
            buttonWidget.setStyleSheet("background-color: green;")
        else:
            buttonWidget.setText("확인 안함")
            # 빨간색으로 변경
            buttonWidget.setStyleSheet("background-color: #7e2c1e;")

    def filterItemsInList(self, listWidget, filterText):
        # 필터 텍스트가 없거나 공백만 포함하는 경우 모든 항목 표시
        if not filterText.strip():
            for i in range(listWidget.count()):
                listWidget.item(i).setHidden(False)
            return

        # 필터 텍스트 분리
        allFilterText = filterText.split()
        includePatterns = []
        excludePatterns = []

        for text in allFilterText:
            if text.startswith("-"):
                excludePatterns.append(text[1:])
            else:
                includePatterns.append(text)
        
        # pattern에 앞 뒤로 * 붙이기
        includePatterns = [f"*{pattern}*" for pattern in includePatterns]
        excludePatterns = [f"*{pattern}*" for pattern in excludePatterns]

        # 필터링
        for i in range(listWidget.count()):
            item = listWidget.item(i)
            text = item.text()
            isHidden = True

            for pattern in includePatterns:
                if fnmatch.fnmatch(text, pattern):
                    isHidden = False
                    break
                else:
                    isHidden = True
                    

            for pattern in excludePatterns:
                if fnmatch.fnmatch(text, pattern):
                    isHidden = True
                    break

            item.setHidden(isHidden)
            
       
     # ------------------ Context Menu for Selecting Error Nodes ----------------------
    def showContextMenu(self, position):
        """Context menu for listWidget and treeWidget."""
        widget = self.sender()
        selectedItems = []

        # Context menu setup
        menu = QMenu()
        menu.setFont(QFont("Arial", 11))  # Set font size
        selectAllAction = menu.addAction("전체 아이템 선택하기")
        selectCurrentAction = menu.addAction("선택한 것들만 선택하기")

        # Initialize selectChildrenAction to avoid unbound error
        selectChildrenAction = None

        # Determine the source widget and filter selected items
        if isinstance(widget, QListWidget):
            selectedItems = widget.selectedItems()
        elif isinstance(widget, QTreeWidget):
            # 하위 아이템 선택 Action deSelectAllAction 전에 추가
            selectChildrenAction = menu.addAction("선택한 에러 하위 아이템 선택하기")
            selectedItems = [item for item in widget.selectedItems() if item.parent() is not None]

        deSelectAllAction = menu.addAction("전체 선택 해제하기")

        # Execute the context menu and handle actions
        action = menu.exec_(widget.mapToGlobal(position))

        if action == selectCurrentAction:
            self.selectItemsFromWidget(widget, selectedItems)
        elif action == selectAllAction:
            self.selectAllItemsFromWidget(widget)
        elif action == deSelectAllAction:
            self.deselectAllItemsFromWidget(widget)
        elif action == selectChildrenAction:
            self.selectChildrenInTree()


    def selectItemsFromWidget(self, widget, selectedItems):
        """Select items in Maya based on the source widget."""
        if isinstance(widget, QListWidget):
            # Select nodes from QListWidget
            nodes = [item.data(Qt.UserRole) for item in selectedItems]
            if "scene" in nodes:
                nodes.remove("scene")
        elif isinstance(widget, QTreeWidget):
            # Select child-level nodes from QTreeWidget
            nodes = [item.data(0, Qt.UserRole) or item.text(0) for item in selectedItems]

        if nodes:
            cmds.select(nodes, replace=True)
        else:
            print("선택된 노드가 없습니다.")

    def selectAllItemsFromWidget(self, widget):
        """Select all items in Maya based on the source widget."""
        if isinstance(widget, QListWidget):
            # Select all items in QListWidget
            widget.selectAll()
            nodes = [widget.item(i).data(Qt.UserRole) for i in range(widget.count())]
            if "scene" in nodes:
                nodes.remove("scene")
        elif isinstance(widget, QTreeWidget):
            # Select all child-level items in QTreeWidget
            allrootItems = widget.invisibleRootItem()
            treeItems = []
            
            nodes = []
            for i in range(allrootItems.childCount()):
                topItem = allrootItems.child(i)
                for j in range(topItem.childCount()):
                    childItem = topItem.child(j)
                    childItem.setSelected(True)
                    treeItems.append(childItem)
                    nodes.append(childItem.data(0, Qt.UserRole) or childItem.text(0))
      
        if nodes:
            cmds.select(nodes, replace=True)
        else:
            print("아이템을 선택할 수 없습니다.")

    def selectChildrenInTree(self):
        # get selected top level item
        topLevelItems = []
        treeWidget = self.treeWidget
        for item in treeWidget.selectedItems():
            if item.parent() is None:
                topLevelItems.append(item)
        # get all children of selected top level item
        allChildren = []
        for item in topLevelItems:
            for i in range(item.childCount()):
                childItem = item.child(i)
                childItem.setSelected(True)
                allChildren.append(childItem)
        # get all nodes from children
        nodes = [child.data(0, Qt.UserRole) or child.text(0) for child in allChildren]
        if nodes:
            cmds.select(nodes, replace=True)
        else:
            print("선택된 아이템이 없습니다.")


    def deselectAllItemsFromWidget(self, widget):
        """Deselect all items in Maya based on the source widget."""
        if isinstance(widget, QListWidget):
            # Deselect all items in QListWidget
            widget.clearSelection()
        elif isinstance(widget, QTreeWidget):
            # Deselect all items in QTreeWidget
            allrootItems = widget.invisibleRootItem()
            for i in range(allrootItems.childCount()):
                topItem = allrootItems.child(i)
                topItem.setSelected(False)
                for j in range(topItem.childCount()):
                    childItem = topItem.child(j)
                    childItem.setSelected(False)
        cmds.select(clear=True)
def run():
    if cmds.window("AssetCheck_win", exists=True):
        cmds.deleteUI("AssetCheck_win")

    ToolWin = mainWin()
    ToolWin.show()

if __name__ == "__main__":
    run()
