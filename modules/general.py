# -*- coding: utf-8 -*-
import maya.cmds as cmds


def topGroup():
    # get top node List
    AlltopNodeList= cmds.ls(assemblies=True)
    print(AlltopNodeList)
    topGroupList=[]
    for topNode in AlltopNodeList:
        shapeNode= cmds.listRelatives(topNode, shapes=True)
        if not shapeNode and cmds.nodeType(topNode) == 'transform':
            topGroupList.append(topNode)

    if len(topGroupList)==0:
        cmds.warning("There is no topGroup")
        return(False, None)

    elif len(topGroupList)==1:
        #print(topGroupList[0])
        return (True, topGroupList[0])
    else:
        cmds.warning("There are multiple topGroup")
        return(False, None)

def perspVeiw():
    # Viewport panel Check
    # if modelPanel4 is set to perspective view
    # 뷰포트 패널 이름 가져오기
    panels = cmds.getPanel(visiblePanels=True)
    
    # 쿼터뷰 카메라 설정 확인 결과 저장
    camera_setup = {}
    
    for panel in panels:
        # 패널이 뷰포트인지 확인
        if cmds.getPanel(typeOf=panel) == 'modelPanel':
            # 패널에 연결된 카메라 쿼리
            camera = cmds.modelEditor(panel, query=True, camera=True)
            camera_setup[panel] = camera

    # Check: modelPanel is one and it is set to perspective view
    # 모델 패널이 하나이고, 그 패널이 퍼스펙티브 뷰인지 확인
    if len(camera_setup) == 1:
        for panel, camera in camera_setup.items():
            if camera == '|persp':
                return True
            else:
                return False
            
def onlyDefaultCamera():
    pass

def onlyDefaultShader():
    # check if there are only lamber shader in the scene
    pass

