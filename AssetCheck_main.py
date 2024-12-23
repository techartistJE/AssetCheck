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
    

except:
    pkgPath = 'D:\myScript\maya\AssetCheck'



import AssetCheck.resource.ui.AssetCheck_ui as AssetCheck_ui
import AssetCheck.modules.model as model
import AssetCheck.modules.general as general
import AssetCheck.modules.simple_om_object as simple_om_object


if sys.version_info > (3, 7, 0):
    import importlib
    importlib.reload(AssetCheck_ui)
    importlib.reload(model)
    importlib.reload(general)
    importlib.reload(simple_om_object)


else:
    import imp
    imp.reload(AssetCheck_ui)
    imp.reload(model)
    imp.reload(general)
    imp.reload(simple_om_object)



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
        self.sceneCheckCount = 0
        self.allTargetCount = 0
        self.ui = AssetCheck_ui.AssetCheckWidgetUI(self.errorDataDict)
        self.setCentralWidget(self.ui)
       

        self.resize(1200, 600)
        # splliter position at middle of the window
        self.ui.mainSplitter.setSizes([600, 600])

        self.ui.inputButton.clicked.connect(self.updateInputTable)
        self.ui.runButton.clicked.connect(self.checkboxOnOffUpdate)

    def nodeFilter(self, inputNodeList):
        # ignore shape node
        # etc node: curve, deformer, constraint, camera, light
        # scnene : camera, material
        # filer type and input count to inputDataDict

        # print("inputNodeList: ", inputNodeList)
        meshList = []
        nullGroupList = []
        etcNodeList = []

        dafaultCamera = ["persp", "top", "front", "side"]
        filterdList = []
        for node in inputNodeList:
            
            omNode= simple_om_object.SimpleOMObject(node)
            """ print("node: ", node)
            print(omNode.objectType)
            print("isShape: ", str(omNode.IsShape))
            print(omNode.transformName)
            print(omNode.ShapeName) """
            
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
            
        
        """ print("========= result ===============")
        for node in meshList:
            print(node.shortName(node.selectedNodeName))
        print("================================")
        for node in nullGroupList:
            print(node.shortName(node.selectedNodeName))
        print("================================")
        for node in etcNodeList:
            print(node.shortName(node.selectedNodeName))  """
       

        filterdList.append(meshList)
        filterdList.append(nullGroupList)
        filterdList.append(etcNodeList)
    
        return (filterdList)

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
        allCategory = self.errorDataDict["errorData"]["category"]
        
        for category in allCategory.values():
            checkListDict = category.get("checkList", {})
            for checkOption in checkListDict.values():
                if checkOption.get("isSceneRelated", True):
                    if checkOption.get("isActive", True):
                        self.sceneCheckCount  += 1
        self.selCountList[4] = self.sceneCheckCount
        self.AllCountList[4] = self.sceneCheckCount
        

    def checkboxOnOffUpdate(self):
        # check checkbox status
        # update errorDataDict
        
        for catergoryName, checkDict in self.ui.allCheckboxesDict.items():
            for checkName, checkboxWidget in checkDict.items():
                onoffState = checkboxWidget.isChecked()
                self.errorDataDict["errorData"]["category"][catergoryName]["checkList"][checkName]["isActive"] = onoffState
                #print(catergoryName, checkName, onoffState)
        
        """ for categroyName, errorData in self.errorDataDict["errorData"]["category"].items():
            print(categroyName)
            for checkName, checkData in errorData["checkList"].items():
                print(checkName, checkData["isActive"]) """




    def updateInputTable(self):
        # 대상 입력 후 필터링한 결과만 남기기
        self.inputNode()
        # 전체 체크 박스 상태 확인
        self.checkboxOnOffUpdate()
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
        



def run():
    
    if cmds.window("AssetCheck_win", exists = True):
        
        cmds.deleteUI("AssetCheck_win")


    ToolWin = mainWin()
    ToolWin.show()



if __name__ == "__main__":
    run()