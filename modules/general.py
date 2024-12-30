# -*- coding: utf-8 -*-
import maya.cmds as cmds


def topGroup():
    # get top node List
    AlltopNodeList= cmds.ls(assemblies=True)
 
    topGroupList=[]
    for topNode in AlltopNodeList:
        shapeNode= cmds.listRelatives(topNode, shapes=True)
        if not shapeNode and cmds.nodeType(topNode) == 'transform':
            topGroupList.append(topNode)

    if len(topGroupList)==0:
        cmds.warning("There is no topGroup")
        return(False, None)

    elif len(topGroupList)==1:

        return (True, topGroupList[0])
    else:
        cmds.warning("There are multiple topGroup")
        return(False, None)

def unfreezeTransform(nodeList):
    # check if the transform node is frozen
    # 노드 리스트 중 transform 노드가 frozen 되어 있는지 확인
    errorNodeList=[]
    errorCount=0
    translateAttList= ['tx', 'ty', 'tz']
    rotateAttList= ['rx', 'ry', 'rz']
    scaleAttList= ['sx', 'sy', 'sz']
    AllunfreezeAttrList= []
    for node in nodeList:
        nodeName= node.selectedNodeName
        isErrorWithNode=False
        unfreezeAttrList = []
        for att in translateAttList:
            
            if cmds.getAttr(nodeName+'.'+att)!=0:
                isErrorWithNode=True
                unfreezeAttrList.append(nodeName +'.'+ att)
        for att in rotateAttList:
            if cmds.getAttr(nodeName+'.'+att)!=0:
                isErrorWithNode=True
                unfreezeAttrList.append(nodeName +'.'+ att)
        for att in scaleAttList:
            if cmds.getAttr(nodeName+'.'+att)!=1:
                isErrorWithNode=True
                unfreezeAttrList.append(nodeName +'.'+ att)
        if isErrorWithNode:
            errorNodeList.append(node)
            AllunfreezeAttrList.append(unfreezeAttrList)
            errorCount+=1
    
    return(errorCount, errorNodeList, AllunfreezeAttrList)
                
def pivotAtWorldCenter(nodeList):
    # check if the pivot of the transform node is at the world center
    # 노드 리스트 중 transform 노드의 pivot이 월드 센터에 있는지 확인
    errorNodeList=[]
    errorCount=0
    for node in nodeList:
        nodeName= node.selectedNodeName
        pivot= cmds.xform(nodeName, q=True, ws=True, rp=True)
        if pivot != [0, 0, 0]:
            errorNodeList.append(node)
            errorCount+=1

    return(errorCount, errorNodeList)

def history(nodeList):
    # check if there is a history in the transform node
    # 노드 리스트 중 transform 노드에 히스토리가 있는지 확인
    errorNodeList=[]
    errorCount=0
    AllHistoryList=[]
    for node in nodeList:
        nodeName= node.selectedNodeName
        historyList= cmds.listHistory(nodeName, pruneDagObjects=True)
        if historyList:
            errorNodeList.append(node)
            AllHistoryList.append(historyList)
            errorCount+=1
        else:
            historyList =[]
    return(errorCount, errorNodeList, AllHistoryList)

def perspView():
    # Viewport panel Check
    # if modelPanel4 is set to perspective view
    # 뷰포트 패널 이름 가져오기
    panels = cmds.getPanel(visiblePanels=True)
 
    # 쿼터뷰 카메라 설정 확인 결과 저장
    camera_setup = []
    
    for panel in panels:

        # 패널이 뷰포트인지 확인
        if cmds.getPanel(typeOf=panel) == 'modelPanel':
            # 패널에 연결된 카메라 쿼리
            camera = cmds.modelEditor(panel, query=True, camera=True)
            camera_setup.append(panel +':' + camera)

    # Check: modelPanel is one and it is set to perspective view
    # 모델 패널이 하나이고, 그 패널이 퍼스펙티브 뷰인지 확인
    
    if len(camera_setup) == 1:
        for cameraData in camera_setup:
            camera = cameraData.split(":")[1]
            if camera == '|persp':
                return (0, [])
            else:
                return (1, ["scene"], [camera_setup] )
    else:
        # 패널이 여러개이면 그 중 하나가 perspective인지 확인
        isPersp = False
        for cameraData in camera_setup:
            camera = cameraData.split(":")[1]
            if camera == '|persp':
                isPersp = True
                break
        if isPersp:
            return (0, [])
        else:
            return (1, ["scene"], [camera_setup])
        
   
def animKey(nodeList):
    # check if there is an animation key in the transform node
    # 노드 리스트 중 transform 노드에 애니메이션 키가 있는지 확인
    errorNodeList=[]
    errorCount=0
    for node in nodeList:
        nodeName= node.selectedNodeName
        animKey= cmds.keyframe(nodeName, q=True)
        if animKey:
            errorNodeList.append(node)
            errorCount+=1

    return(errorCount, errorNodeList)

def layer():
    # check if there are layers in the scene
    layers = cmds.ls(type="displayLayer")
    
    # 기본 레이어는 항상 존재하므로 이를 제외합니다.
    layers = [layer for layer in layers if layer != "defaultLayer"]
    
    if layers:
        
        return (1, ["scene"], [layers])
    else:
   
        return (0, None)
    
def hidden(nodeList):
    # if there are hidden( visibility == 0) nodes in the scene
    # 숨겨진 노드가 있는지 확인
    errorCount=0
    errorNodeList=[]
    for node in nodeList:
        nodeName= node.selectedNodeName
        if not cmds.getAttr(nodeName+'.visibility'):
            errorCount+=1
            errorNodeList.append(node)
    return (errorCount, errorNodeList)
      
def onlyDefaultMaterial():
    allMaterials = cmds.ls(materials=True)
    defaultMaterials = ["lambert1", "standardSurface1", "particleCloud1"]
    allMaterials = [material for material in allMaterials if material not in defaultMaterials]
   
    if allMaterials:
        
        return (1, ["scene"], [allMaterials])
    else:
 
        return (0, None)

def onlyDefaultCamera():
    # input all camera in the scene
    dafaultCamera = ["persp", "top", "front", "side"]
    allCameraShape = cmds.ls(type="camera")
    allCamera = [cmds.listRelatives(camera, parent=True)[0] for camera in allCameraShape]
    allCamera = [camera for camera in allCamera if camera not in dafaultCamera]
    if allCamera:
     
        return (1, ["scene"], [allCamera])
    else:
        
        return (0, None)
    
def unKnown():
    # check if there are unknown nodes or plugin in the scene
    unknownPlugin = cmds.unknownPlugin(q=True, list=True)
    if not unknownPlugin:
        unknownPlugin = []
    unknownNodes = cmds.ls(type="unknown")
    unknownNodes += cmds.ls(type="unknownDag")
    unknownNodes += cmds.ls(type="unknownTransform")
    if not unknownNodes:
        unknownNodes = []
    detailUnkownList = []
    detailUnkownList.extend(unknownPlugin)
    detailUnkownList.extend(unknownNodes)
    if unknownPlugin or unknownNodes:
        
        return (1, ["scene"], [detailUnkownList] )
    else:
        
        return (0, ())


