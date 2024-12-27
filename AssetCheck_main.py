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


if sys.version_info >= (3, 0):
    import importlib

    for module in [AssetCheck_ui, general, model, naming, UV, simple_om_object]:
        importlib.reload(module)
else:
    import imp
    for module in [AssetCheck_ui, general, model, naming, UV, simple_om_object]:
        imp.reload(module)



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
        self.errorDataDict = loadJsonData(errorDataPath)
        self.simpleErrorDataDict = {}
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
            #print(node)
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

    def updateErrorTable(self):
        self.isActiveDict = {}
        for categoryName, categoryData in self.errorDataDict["errorData"]["category"].items():
            isActiveList = []
            for checkName, stateData in categoryData.get("checkList", {}).items():
                onOff= stateData.get("isActive")
                if onOff:
                    isActiveList.append(checkName)
            self.isActiveDict[categoryName] = isActiveList
       

    def unPackInputRePackResult(self, check_func, parmList, detailResult = False):
        
        AllErrorCount = 0
        AllErrorList = []
        detailResultList = []
 
        for inputNodeList in parmList:
            result = check_func(inputNodeList)
            if len(result) == 2:
                errorCount, errorNodeList = result
            else:
                errorCount, errorNodeList, detailResult = result
                detailResultList+= detailResult
            AllErrorCount += errorCount
            AllErrorList += errorNodeList
        
        if detailResult:
            return AllErrorCount, AllErrorList, detailResultList
        return AllErrorCount, AllErrorList

    def errorCheckFuncMatch(self, category, checkName):
    
        sceneRelatedList = ["layer", "hidden", "defaultMaterial", "defaultCamera", "perspView", "unKnown", "duplicatedNames", "nameSpace", "shapeName"]
        category_func_map = {
            "general": {
                "unfreeze": lambda: self.unPackInputRePackResult(general.unfreezeTransform, self.inputList[:-1]),
                "pivot": lambda: self.unPackInputRePackResult(general.pivotAtWorldCenter, self.inputList[:-1]),
                "history": lambda: self.unPackInputRePackResult(general.history, self.inputList[:-1]),
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
                "duplicatedNames": lambda: self.unPackInputRePackResult(naming.duplicatedNames, self.inputList),
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
             
            else:
                errorCount, errorNodeList, detailResult = result
             
            # update errorByNodeDict
            # left nodeName, right errorList
       
            if errorCount:
                if checkName in sceneRelatedList:
                    if "scene" in self.errorByNodeDict["scene"].keys():
                        continue
                        self.errorByNodeDict["scene"]["scene"].append(checkName)
                    
                    self.errorByNodeDict["scene"].setdefault("scene", []).append(checkName)
                else:
                    for node in errorNodeList:
                        print(node)
                        print("node: ", node.selectedNodeName)
                        targetType = node.objectType
                        if targetType == "mesh":
                            categoryName = "mesh"
                        elif targetType == "transform":
                            categoryName = "nullGroup"
                        else:
                            categoryName = "etcNode"
                        nodeName = node.selectedNodeName
                        # if checkName is in already in errorByNodeDict, pass
                        if checkName in self.errorByNodeDict[categoryName].get(nodeName, []):
                            continue
                        self.errorByNodeDict[categoryName].setdefault(nodeName, []).append(checkName)

            

            self.errorDataDict["errorData"]["category"][category]["checkList"][checkName]["errorCount"] = errorCount
            self.errorDataDict["errorData"]["category"][category]["checkList"][checkName]["errorNodeList"] = errorNodeList
            self.simpleErrorDataDict[checkName] = errorNodeList

        else:
            print(f"Unknown check: {category}.{checkName}")

    # update result table and list
    def updateErrorByCriteriaTable(self):
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


        table.itemSelectionChanged.connect(self.showErrorItemByCriteriaList)
        table.setCurrentCell(0, 0)
        

    def showErrorItemByCriteriaList(self):
        tableWidget= self.ui.findWidget(self.ui.errorResultTab, "errorByCriteriaTable")
        listWidget= self.ui.findWidget(self.ui.errorResultTab, "errorItemList")
        listWidget.clear()
        currentItem= tableWidget.currentItem()
        headetItem= tableWidget.verticalHeaderItem(currentItem.row())
    
        errorItemList= self.simpleErrorDataDict.get(headetItem.text())
        for errorItem in errorItemList:
            itemName= errorItem.selectedNodeName
            listWidget.addItem(itemName)
    

    def updateErrorNodeList(self):
        listWidget= self.ui.findWidget(self.ui.errorResultTab, "errorByNodeList")
       
        resultTableData = []
        for typeName in self.errorByNodeDict.keys():
            print("typeName: ", typeName)
            for errorNode, errorList in self.errorByNodeDict[typeName].items():
                
                errorList= self.errorByNodeDict[typeName][errorNode]
                resultTableData.append([errorNode, errorList])
            
        listWidget.clear()
        
        
        for i, dataList in enumerate(resultTableData):
            nodeName, errorList = dataList

            # set text center-align
            itemWidget = QListWidgetItem(nodeName)
            itemWidget.setTextAlignment(Qt.AlignCenter)

            listWidget.addItem(itemWidget)

        # if sceneRelated errorCount is not 0, add scene to errorByNodeList
        if self.errorByNodeDict["scene"].get("scene"):
            listWidget.addItem("scene")
        listWidget.itemSelectionChanged.connect(self.updateErrorListByNode)
        listWidget.setCurrentRow(0)
    
    def updateErrorListByNode(self):
        
        treeWidget= self.ui.findWidget(self.ui.errorResultTab, "errorcriteriaTree")
        listWidget= self.ui.findWidget(self.ui.errorResultTab, "errorByNodeList")
        currentText= listWidget.currentItem().text()
        
        for typeName in self.errorByNodeDict.keys():
            if currentText in self.errorByNodeDict[typeName].keys():
                errorList= self.errorByNodeDict[typeName][currentText]
                break
      
        
        # set Horizontal header label 0 : Error Count
        headerText= ["Error Count : " + str(len(errorList))]
        # set header labe text center-align
        treeWidget.setHeaderLabels(headerText)
        header = treeWidget.header()
        header.setDefaultAlignment(Qt.AlignCenter)

        treeWidget.clear()
        # add errorList to treeWidget of top level
        for errorName in errorList:
            itemWidget= QTreeWidgetItem([errorName])
            itemWidget.setTextAlignment(0, Qt.AlignCenter)
            treeWidget.addTopLevelItem(itemWidget)


    def PathToshortName(self, nodeName):
        if '|' in nodeName:
            return nodeName.rsplit('|', 1)[-1]
        else:
            return nodeName
        
    def errorCheckRun(self):
        # run error check
        rowID= self.ui.inputTable.currentRow()
        if rowID == 0:
            self.inputList = self.AllInputList
        else:
            self.inputList = self.selInputList
        
        
        self.allcheckboxOnOffUpdate()
        self.updateErrorTable()

        for category, checkList in self.isActiveDict.items():
            for checkName in checkList:
                self.errorCheckFuncMatch(category, checkName)
        #print("errorDataDict: ", self.errorDataDict)
        self.updateErrorByCriteriaTable()
        self.updateErrorNodeList()

        #self.ui.setUIStyle(self.ui.uiStyle)

    
    

    

def run():
    
    if cmds.window("AssetCheck_win", exists = True):
        
        cmds.deleteUI("AssetCheck_win")


    ToolWin = mainWin()
    ToolWin.show()



if __name__ == "__main__":
    run()