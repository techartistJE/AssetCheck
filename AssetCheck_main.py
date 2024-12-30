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
    inputDataPath = os.path.join(pkgPath, 'resource','data', 'inputData.json')
    errorDataPath = os.path.join(pkgPath, 'resource','data', 'errorData.json')
    uiStylePath = os.path.join(pkgPath, 'resource', 'ui','uiStyle.css')
    

except:
    pkgPath = 'D:\myScript\maya\AssetCheck'



import AssetCheck.resource.ui.AssetCheck_ui as AssetCheck_ui
import AssetCheck.modules.general as general
import AssetCheck.modules.model as model
import AssetCheck.modules.naming as naming
import AssetCheck.modules.UV as UV

import AssetCheck.modules.simple_om_object as simple_om_object


import importlib
for module in [AssetCheck_ui, general, model, naming, UV, simple_om_object]:
    importlib.reload(module)



def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if sys.version_info >= (3, 0):
        return shiboken2.wrapInstance(int(ptr), QWidget)
    else:
        return shiboken2.wrapInstance(long(ptr), QWidget)
    
def loadJsonData(jsonPath):
    with open(jsonPath, 'r', encoding= "utf-8") as f:
        errorDataDict = json.load(f)
    return errorDataDict

class mainWin(QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__(parent =getMayaWindow() )
        self.setObjectName("AssetCheck_win")
        self.setWindowTitle("AssetCheck")

        self.selInputList= []
        self.AllInputList= []
        self.inputDataDict = loadJsonData(inputDataPath)["inputData"]
        self.resultDataInit()
        
        self.errorByNodeDict = {"mesh": {}, "nullGroup": {}, "etcNode": {}, "scene": {}}
        
        self.sceneCheckCount = 0
        self.allTargetCount = 0
        self.ui = AssetCheck_ui.AssetCheckWidgetUI(self.errorDataDict, uiStylePath)

        self.sceneRelatedCheckBoxList= self.ui.sceneRelatedCheckBoxList
  
            
        self.setCentralWidget(self.ui)
       

        self.resize(1200, 600)
        # splliter position at middle of the window
        self.ui.mainSplitter.setSizes([600, 600])
        self.updateInputTable()

        self.uiFuncConnect()


         # 각 위젯별 경로 상태 플래그
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
            checkbox.stateChanged.connect(self.sceneRelatedCheckboxCountUpdate)
  
    def nodeFilter(self, inputNodeList):
        # ignore shape node
        # etc node: curve, deformer, constraint, camera, light
        # scnene : camera, material
        # filer type and input count to inputDataDict

        meshList = []
        nullGroupList = []
        etcNodeList = []

        dafaultCamera = ["persp", "top", "front", "side"]
        filterdList = []
        for node in inputNodeList:
            
            omNode= simple_om_object.SimpleOMObject(node)
            # ignore shape node
            if omNode.IsShape:
                continue

            if omNode.objectType == 'mesh':
                meshList.append(omNode)
            elif omNode.objectType == 'transform':
                nullGroupList.append(omNode)
            else:
                if omNode.objectType == 'camera':
                    if omNode.shortName(node) in dafaultCamera:
                        continue
                etcNodeList.append(omNode)

    
        return ( [meshList, nullGroupList, etcNodeList])

    def inputNode(self):
        # check dagObject only Mode is on
        # Outliner 이름 가져오기 (기본값은 'outlinerPanel1')
        outliner = cmds.getPanel(type='outlinerPanel')[0]
        # DAG Objects Only 켜기
        cmds.outlinerEditor(outliner, edit=True, showDagOnly=True)

        selectedNode = cmds.ls(sl=True, long=True, dag=True)
        allSceneNode = cmds.ls(assemblies=True, long=True, dag=True)
        
        self.selInputList = self.nodeFilter(selectedNode)
        self.selCountList= self.createCountList(self.selInputList)
        
        self.AllInputList = self.nodeFilter(allSceneNode)
        self.AllCountList = self.createCountList(self.AllInputList)
    
    def createCountList(self, inputList):
        allCount= 0
        # countList: [allCount, meshCount, nullGroupCount, etcNodeCount, sceneRelatedCount]
        countList=[0]*5
        for i in range(3):
            countList[1+i]= len(inputList[i])
            allCount += countList[1+i]
        countList[0]= allCount
      
        return countList
    
    def countSceneCheckList(self):
        # find all checkList that 'isSceneRelated' is true in the errorData
        self.sceneCheckCount = 0
        for checkbox in self.ui.sceneRelatedCheckBoxList:
            if checkbox.isChecked():
                self.sceneCheckCount  += 1
        self.selCountList[4] = self.sceneCheckCount
        self.AllCountList[4] = self.sceneCheckCount


    def sceneRelatedCheckboxCountUpdate(self):
        self.countSceneCheckList()
        self.ui.inputTable.item(0, 4).setText(str(self.sceneCheckCount))
        self.ui.inputTable.item(1, 4).setText(str(self.sceneCheckCount))
        
    def resultDataInit(self):
        self.errorDataDict ={"nodes":{}, "errors":{}}
        self.errorDataDict = loadJsonData(errorDataPath)
        # errorCritera별 에러 노드 리스트 저장
        self.errorToTargetDataDict = {}
        # 타겟별 error 목록과 세부내용 저장
        self.targetToErrorDataDict = {}

        
    def allcheckboxOnOffUpdate(self):
        # check checkbox status
        # update errorDataDict
        for catergoryName, checkDict in self.ui.allCheckboxesDict.items():
            for checkName, checkboxWidget in checkDict.items():
                self.errorDataDict["errorData"]["category"][catergoryName]["checkList"][checkName]["isActive"] = checkboxWidget.isChecked()


    def updateInputTable(self):
        # 대상 입력 후 필터링한 결과만 남기기
        self.inputNode()
        # 전체 체크 박스 상태 확인
        self.allcheckboxOnOffUpdate()
        # 씬 관련 활성화 된 체크리스트를 세서 카운트 리스트 업데이트허기기
        self.countSceneCheckList()
        
        if self.selCountList[0] == 0:
            self.ui.inputTable.selectRow(0)
        else:
            self.ui.inputTable.selectRow(1)
            
        # row 2 column 5
        for i in range(2):
            for j in range(5):
                if i == 0:
                    text = str(self.AllCountList[j])
                else:
                    text = str(self.selCountList[j])
                # tableItem text size 12 and align center
                tableItem = QTableWidgetItem(text)
                tableItem.setTextAlignment(Qt.AlignCenter)
                tableItem.setFont(QFont("Arial", 12))
                self.ui.inputTable.setItem(i, j, tableItem)

    def updateCriteriaTable(self):
        self.isActiveDict = {}
        for categoryName, categoryData in self.errorDataDict["errorData"]["category"].items():
            isActiveList = []
            for checkName, stateData in categoryData.get("checkList", {}).items():
                onOff= stateData.get("isActive")
                if onOff:
                    isActiveList.append(checkName)
            self.isActiveDict[categoryName] = isActiveList
       

    def unPackInputRePackResult(self, check_func, parmList, IsDetailResult = False):
        
        AllErrorCount = 0
        AllErrorList = []
        detailResultList = []

        for inputNodeList in parmList:
            result = check_func(inputNodeList)  
        
            if len(result) == 2:
                errorCount, errorNodeList = result
            else:
                errorCount, errorNodeList, detailResult = result
                detailResultList.extend( detailResult)
            AllErrorCount += errorCount
            AllErrorList += errorNodeList

        if IsDetailResult:

            return AllErrorCount, AllErrorList, detailResultList
        else:

            return AllErrorCount, AllErrorList

    def errorCheckFuncMatch(self, category, checkName):
    
        sceneRelatedList = ["layer", "hidden", "defaultMaterial", "defaultCamera", "perspView", "unKnown", "duplicatedNames", "nameSpace", "shapeName"]
        category_func_map = {
            "general": {
                "unfreeze": lambda: self.unPackInputRePackResult(general.unfreezeTransform, self.inputList[:-1], True),
                "pivot": lambda: self.unPackInputRePackResult(general.pivotAtWorldCenter, self.inputList[:-1]),
                "history": lambda: self.unPackInputRePackResult(general.history, self.inputList[:-1], True),
                "animkey": lambda: self.unPackInputRePackResult(general.animKey, self.inputList),
                "layer": lambda: general.layer(),
                "hidden": lambda: self.unPackInputRePackResult(general.hidden, self.inputList),
                "defaultMaterial": lambda: general.onlyDefaultMaterial(),
                "defaultCamera": lambda: general.onlyDefaultCamera(),
                "perspView": lambda: general.perspView(),
                "unKnown" : lambda: general.unKnown(),
            },
            "model": {
                "ngon": lambda: self.unPackInputRePackResult(model.ngonFace, [self.inputList[0]], True),
            },
            "naming": {
                "duplicatedNames": lambda: self.unPackInputRePackResult(naming.duplicatedNames, self.inputList, True),
                "nameSpace": lambda: naming.nameSpace(),
                "shapeName": lambda: self.unPackInputRePackResult(naming.shapeName, self.inputList),
            },
            # UV와 기타 카테고리 나중에 추가
        }

        func = category_func_map.get(category, {}).get(checkName)
        
   
        if func:
            result = func()
       
            if len(result) == 2:
                errorCount, errorNodeList = result
                detailResult = []
             
            else:
                # error has detailResult 
                # model: ngon
                # scene: defaultMaterial, defaultCamera, perspView, unKnown
                errorCount, errorNodeList, detailResult = result
            
            # update targetToErrorDataDict
            # left nodeName, right errorList
            if errorCount:
      
                for id, node in enumerate(errorNodeList):
                    # check if keyward: nodeName is already in targetToErrorDataDict
                    if isinstance(node, simple_om_object.SimpleOMObject):
                        nodeName = node.selectedNodeName
                    else:
                        nodeName = node
             
                    if nodeName in self.targetToErrorDataDict.keys():
                        if detailResult:
                            self.targetToErrorDataDict[nodeName]["errorList"][checkName] = detailResult[id]
                        else:
                            self.targetToErrorDataDict[nodeName]["errorList"][checkName] = []
              
                    else:
                        # initialize targetToErrorDataDict[nodeName]
                        self.targetToErrorDataDict[nodeName] = {}
                        self.targetToErrorDataDict[nodeName]["omNode"] = node
                        self.targetToErrorDataDict[nodeName]["type"] = category
                        if "errorList" not in self.targetToErrorDataDict[nodeName].keys():
                            self.targetToErrorDataDict[nodeName]["errorList"] = {}
                        if detailResult:
                            self.targetToErrorDataDict[nodeName]["errorList"][checkName] = detailResult[id]
                        else:
                            self.targetToErrorDataDict[nodeName]["errorList"][checkName] = []
  
            

            self.errorDataDict["errorData"]["category"][category]["checkList"][checkName]["errorCount"] = errorCount
            self.errorDataDict["errorData"]["category"][category]["checkList"][checkName]["errorNodeList"] = errorNodeList
            
            self.errorToTargetDataDict[checkName] = errorNodeList 
            if errorNodeList:
                if errorNodeList[0] == 'scene':
                    AllDetailResult = []
                    for detail in detailResult:
                        AllDetailResult+= detail
                    self.errorToTargetDataDict[checkName] = AllDetailResult


        else:
            print(f"Unknown check: {category}.{checkName}")

    # update result table and list
    def CriteriaToTargetTable(self):
        table= self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        
        resultTableData= []
        for category, checkList in self.errorDataDict["errorData"]["category"].items():
            for checkName, checkData in checkList.get("checkList", {}).items():
                errorCount= checkData.get("errorCount", 0)
                errorNodeList= checkData.get("errorNodeList", [])
                if errorCount:
                    resultTableData.append([category, checkName, errorCount, errorNodeList])
        
        table.setRowCount(len(resultTableData))
        for i, dataList in enumerate(resultTableData):
            # vertical header : checkName
            headerItem = QTableWidgetItem(dataList[1])
            headerItem.setFont(QFont("Arial", 12))
            headerItem.setTextAlignment(Qt.AlignCenter)
            table.setVerticalHeaderItem(i,headerItem)

            itemWidget = QTableWidgetItem(str(dataList[2]))
            itemWidget.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 0, QTableWidgetItem(itemWidget))


        table.itemSelectionChanged.connect(self.showErrorTargetByCriteria)
        table.setCurrentCell(0, 0)
        

    def showErrorTargetByCriteria(self):
        """
        에러 기준별로 타겟을 리스트에 표시하고 초기 설정에 따라 shortPath 또는 fullPath로 설정.
        """
        tableWidget = self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        listWidget = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListA")
        listWidget.clear()

        currentItem = tableWidget.currentItem()
        if not currentItem:
            return

        headetItem = tableWidget.verticalHeaderItem(currentItem.row())
        errorItemList = self.errorToTargetDataDict.get(headetItem.text(), [])

        for errorItem in errorItemList:
            if isinstance(errorItem, simple_om_object.SimpleOMObject):
                full_path = errorItem.selectedNodeName
            else:
                full_path = errorItem

            short_path = self.PathToshortName(full_path)

            # ListWidgetItem 생성 및 데이터 저장
            itemWidget = QListWidgetItem(short_path if self.is_short_path_listA else full_path)
            itemWidget.setData(Qt.UserRole, full_path)  # fullPath 저장
            itemWidget.setData(Qt.UserRole + 1, short_path)  # shortPath 저장

            listWidget.addItem(itemWidget)

    

    def updateErrorTargetList(self):
        """
        에러 타겟 리스트를 업데이트하고 초기 설정에 따라 shortPath 또는 fullPath로 설정.
        """
        listWidget = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
        listWidget.clear()

        errorNodeList = list(self.targetToErrorDataDict.keys())

        for nodeName in errorNodeList:
            full_path = nodeName
            short_path = self.PathToshortName(full_path)

            # ListWidgetItem 생성 및 데이터 저장
            itemWidget = QListWidgetItem(short_path if self.is_short_path_listB else full_path)
            itemWidget.setData(Qt.UserRole, full_path)  # fullPath 저장
            itemWidget.setData(Qt.UserRole + 1, short_path)  # shortPath 저장

            listWidget.addItem(itemWidget)

        # 선택 변경 시 에러 트리 업데이트 연결
        listWidget.itemSelectionChanged.connect(self.updateErrorTreeByNode)

        # 리스트가 비어 있지 않다면 첫 번째 항목 선택
        if listWidget.count() > 0:
            listWidget.setCurrentRow(0)


    
    def updateErrorTreeByNode(self):
        """
        선택된 노드의 에러 리스트를 트리에 표시하고 초기 설정에 따라 shortPath 또는 fullPath로 설정.
        """
        listWidget = self.ui.findWidget(self.ui.errorResultTab, "errorTargetListB")
        treeWidget = self.ui.findWidget(self.ui.errorResultTab, "errorCriteriaTree")

        currentWidget = listWidget.currentItem()
        if not currentWidget:
            listWidget.setCurrentRow(0)
            currentWidget = listWidget.currentItem()

        currentText = currentWidget.data(Qt.UserRole) or currentWidget.text()
        errorList = self.targetToErrorDataDict.get(currentText, {}).get("errorList", {})

        treeWidget.clear()

        # 모든 데이터를 추가
        for checkName, detailResult in errorList.items():
            topLevelItem = QTreeWidgetItem()
            full_path = checkName
            short_path = self.PathToshortName(full_path)
            topLevelItem.setText(0, short_path if self.is_short_path_tree else full_path)
            topLevelItem.setData(0, Qt.UserRole, full_path)
            topLevelItem.setData(0, Qt.UserRole + 1, short_path)
            treeWidget.addTopLevelItem(topLevelItem)

            # 세부 데이터 추가
            if not isinstance(detailResult, list):
                detailResult = [detailResult]
            for detail in detailResult:
                childItem = QTreeWidgetItem()
                full_detail = str(detail)
                short_detail = self.PathToshortName(full_detail)
                childItem.setText(0, short_detail if self.is_short_path_tree else full_detail)
                childItem.setData(0, Qt.UserRole, full_detail)
                childItem.setData(0, Qt.UserRole + 1, short_detail)
                topLevelItem.addChild(childItem)

            topLevelItem.setExpanded(True)  # 기본적으로 펼침

        self.setTopLevelItemColors(treeWidget)  # 스타일 설정


        
    def errorCheckRun(self):
        # run error check
        rowID= self.ui.inputTable.currentRow()
        if rowID == 0:
            self.inputList = self.AllInputList
        else:
            self.inputList = self.selInputList
        
        self.resultDataInit()
        self.allcheckboxOnOffUpdate()
        self.updateCriteriaTable()

        for category, checkList in self.isActiveDict.items():
            for checkName in checkList:
                self.errorCheckFuncMatch(category, checkName)

        self.CriteriaToTargetTable()
        self.updateErrorTargetList()

        self.setTopLevelItemColors(self.treeWidget)
        
        #self.ui.setUIStyle(self.ui.uiStyle)

    def eventFilter(self, source, event):
        if source == self.listWidgetA.viewport():
            if event.type() == event.MouseButtonPress and event.button() == Qt.MiddleButton:
                self.togglePathModeInList(self.listWidgetA, "listA")
        elif source == self.listWidgetB.viewport():
            if event.type() == event.MouseButtonPress and event.button() == Qt.MiddleButton:
                self.togglePathModeInList(self.listWidgetB, "listB")
        elif source == self.treeWidget.viewport():
            if event.type() == event.MouseButtonPress and event.button() == Qt.MiddleButton:
                self.togglePathModeInTree()
        return super().eventFilter(source, event)

    def togglePathModeInList(self, widget, widget_name):
        """
        ListWidget의 경로를 전체/짧은 경로로 전환.
        """
        if widget_name == "listA":
            self.is_short_path_listA = not self.is_short_path_listA
            is_short = self.is_short_path_listA
        elif widget_name == "listB":
            self.is_short_path_listB = not self.is_short_path_listB
            is_short = self.is_short_path_listB

        for i in range(widget.count()):
            item = widget.item(i)
            full_path = item.data(Qt.UserRole)  # 전체 경로
            short_path = item.data(Qt.UserRole + 1)  # 짧은 경로

            if full_path and short_path:  # 데이터가 설정되어 있는 경우
                item.setText(short_path if is_short else full_path)
            else:  # 데이터가 없는 경우 기본 설정
                full_path = item.text()
                short_path = self.PathToshortName(full_path)
                item.setData(Qt.UserRole, full_path)
                item.setData(Qt.UserRole + 1, short_path)
                item.setText(short_path if is_short else full_path)

    def togglePathModeInTree(self):
        """
        TreeWidget의 경로를 전체/짧은 경로로 전환.
        """
        self.is_short_path_tree = not self.is_short_path_tree
        root = self.treeWidget.invisibleRootItem()
        self.updateTreeItemsToPath(root, self.is_short_path_tree)


    def updateTreeItemsToPath(self, item, to_short):
        """
        TreeWidget 아이템의 경로를 전체/짧은 경로로 전환.
        """
        for i in range(item.childCount()):
            child = item.child(i)
            full_path = child.data(0, Qt.UserRole)  # 전체 경로
            short_path = child.data(0, Qt.UserRole + 1)  # 짧은 경로

            if full_path and short_path:  # 데이터가 설정되어 있는 경우
                child.setText(0, short_path if to_short else full_path)
            else:  # 데이터가 없는 경우 기본 설정
                full_path = child.text(0)
                short_path = self.PathToshortName(full_path)
                child.setData(0, Qt.UserRole, full_path)
                child.setData(0, Qt.UserRole + 1, short_path)
                child.setText(0, short_path if to_short else full_path)

            # 재귀 호출로 자식 노드 처리
            self.updateTreeItemsToPath(child, to_short)

    def PathToshortName(self, nodeName):
        """
        전체 경로에서 짧은 이름을 추출.
        """
        if "|" in nodeName:
            return nodeName.rsplit("|", 1)[-1]
        return nodeName

    
    def setTopLevelItemColors(self, treeWidget):
        """
        QTreeWidget의 topLevel 항목에만 번갈아 색상을 적용.
        """
        root = treeWidget.invisibleRootItem()
        for top_index in range(root.childCount()):
            top_item = root.child(top_index)

            # 색상 설정 (홀수, 짝수 구분)
            if top_index % 2 == 0:
                color = QColor(70, 70, 70)  # 회색
            else:
                color = QColor(80, 80, 80)  # 좀 더 밝은 회색 

            for col in range(treeWidget.columnCount()):
                top_item.setBackground(col, color)

def run():
    
    if cmds.window("AssetCheck_win", exists = True):
        
        cmds.deleteUI("AssetCheck_win")


    ToolWin = mainWin()
    ToolWin.show()



if __name__ == "__main__":
    run()