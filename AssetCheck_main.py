from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import maya.OpenMayaUI as mui
import maya.cmds as cmds

import shiboken2
import sys
import os
import json

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
import AssetCheck.modules.uv as uv

import AssetCheck.modules.simple_om_object as simple_om_object

import importlib
for module in [AssetCheck_ui, general, model, naming, uv, simple_om_object]:
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

        self.sceneRelatedCheckBoxList = self.ui.sceneRelatedCheckBoxList

        self.setCentralWidget(self.ui)
        self.resize(1400, 800)
        self.ui.mainSplitter.setSizes([700, 700])
        self.updateInputTable()

        self.uiFuncConnect()

        self.is_short_path_listA = True
        self.is_short_path_listB = True
        self.is_short_path_tree = True

        self.listWidgetA = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListA")
        self.listWidgetA.viewport().installEventFilter(self)
        self.listWidgetB = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
        self.listWidgetB.viewport().installEventFilter(self)
        self.treeWidget = self.ui.findWidget(self.ui.errorResultTab, "errorCriteriaTree")
        self.treeWidget.viewport().installEventFilter(self)

    def uiFuncConnect(self):
        self.ui.inputButton.clicked.connect(self.updateInputTable)
        self.ui.runButton.clicked.connect(self.errorCheckRun)

        for checkbox in self.sceneRelatedCheckBoxList:
            checkbox.stateChanged.connect(self.updateSceneCheckCount)
    # ---------------------------- Input Table ----------------------------
    def updateInputTable(self):
        isSelected= self.inputNode()
       
        if isSelected:
            self.ui.inputTable.selectRow(1)
        else:
            self.ui.inputTable.selectRow(0)
        self.updateSceneCheckCount()
        self.updateInputTableUI()

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
    
        # Steop 0: errorData 초기화
        self.errorData = loadJsonData(errorDataPath)["errorData"]

        # Step 1: Update isActive status based on checkbox state
        for category, categoryData in self.errorData["errors"].items():
            for checkName, checkData in categoryData["checkList"].items():
                self.errorData["errors"][category]["checkList"][checkName]["isActive"] = self.ui.allCheckboxesDict[category][checkName].isChecked()

        # Step 2: Run error checks
        for categoryName, categoryData in self.errorData["errors"].items():
            for checkName, checkData in categoryData["checkList"].items():
                if checkData["isActive"]:
                    errorCount, nodes, detail = self.runEachErrorCheck(categoryName, checkName, inputList)
                    checkData["nodes"] = nodes
                    checkData["errorCount"] = len(nodes)

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
        criteriaTable = self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        criteriaTable.clearContents()
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
            criteriaHeaderItem.setFont(QFont("Arial", 12))
            criteriaHeaderItem.setTextAlignment(Qt.AlignCenter)
            criteriaTable.setVerticalHeaderItem(i, criteriaHeaderItem)

            # Set error count
            countItem = QTableWidgetItem(str(errorCount))
            countItem.setFont(QFont("Arial", 12))
            countItem.setTextAlignment(Qt.AlignCenter)
            criteriaTable.setItem(i, 0, countItem)

            allErrorCount += errorCount

            # set data: category
            criteriaHeaderItem.setData(Qt.UserRole, category)
        
        criteriaTable.setHorizontalHeaderLabels(["Error Count : " + str(allErrorCount)])
        # font size 12 center align
        criteriaTable.horizontalHeaderItem(0).setFont(QFont("Arial", 12))
        criteriaTable.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)
        criteriaTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        criteriaTable.horizontalHeader().setStretchLastSection(True)
        # Resize row and column
       
        criteriaTable.resizeColumnsToContents()
        criteriaTable.resizeRowsToContents()

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
        tableWidget = self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        listWidgetA = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListA")

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
        listWidgetB = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
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
        ListWidgetB = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
        treeWidget = self.ui.findWidget(self.ui.errorResultTab, "errorCriteriaTree")
     

        # full path
        nodeName= ListWidgetB.currentItem()
        if nodeName:
            nodeName = nodeName.data(Qt.UserRole)
        else:
            return
        treeWidget.clear()
        errorData= self.errorData["nodes"].get(nodeName, {})
        if not errorData:
            print("Can't find error data for node:", nodeName)
            return

        allErrorCount = len(errorData)
        headerItem= treeWidget.headerItem()
        headerItem.setText(0, f"Error Count: {allErrorCount}")
        headerItem.setFont(0, QFont("Arial", 11))
        headerItem.setTextAlignment(0, Qt.AlignCenter)
        for checkName, details in errorData.items():

            topLevelItem = QTreeWidgetItem()
            topLevelItem.setText(0, checkName)
            topLevelItem.setTextAlignment(0, Qt.AlignCenter)
            treeWidget.addTopLevelItem(topLevelItem)


            if not isinstance(details, list):
                details = [details]

            for detail in details:
                childItem = QTreeWidgetItem()
                
                detailPath = detail
                shortPath= detailPath.split("|")[-1]
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
                "layer": (general.layer, None),  # Use full list
                "hidden": (general.hidden, None),  # Use full list
                "defaultMaterial": (general.onlyDefaultMaterial, None),  # Use full list
                "defaultCamera": (general.onlyDefaultCamera, None),  # Use full list
                "perspView": (general.perspView, None),  # Use full list
                "unKnown": (general.unKnown, None),  # Use full list
            },
            "model": {
                "ngon": (model.ngonFace, 0),  # Use first element only
                
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
            

    def sceneRelatedCheckboxCountUpdate(self):
        self.updateSceneCheckCount()
        self.updateInputTableUI()

    def eventFilter(self, source, event):
        if event.type() == event.MouseButtonPress and event.button() == Qt.MiddleButton:
            if source == self.listWidgetA.viewport():
                self.togglePathModeInList(self.listWidgetA, "listA")
            elif source == self.listWidgetB.viewport():
                self.togglePathModeInList(self.listWidgetB, "listB")
            elif source == self.treeWidget.viewport():
                self.togglePathModeInTree()
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
      
            

def run():
    if cmds.window("AssetCheck_win", exists=True):
        cmds.deleteUI("AssetCheck_win")

    ToolWin = mainWin()
    ToolWin.show()

if __name__ == "__main__":
    run()
