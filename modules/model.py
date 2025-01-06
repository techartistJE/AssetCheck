import maya.api.OpenMaya as om
import maya.cmds as cmds

# fuctions for modeling file check

def ngonFace(nodeList):
    errorCount=0
    errorNodeList=[]
    AllNgonList=[]
    for node in nodeList:
      
        nodeName= node.selectedNodeName
        MSelList = om.MSelectionList()
        MSelList.add(nodeName)

        NGonList=[]
        iter = om.MItSelectionList(MSelList, om.MFn.kMesh)

        while not iter.isDone():
            dagPath = iter.getDagPath()
            mesh = om.MFnMesh(dagPath)
            
            for i in range(mesh.numPolygons):
                vtxList = mesh.getPolygonVertices(i)
                if len(vtxList) > 4:
                    objName= cmds.listRelatives(mesh.partialPathName(), fullPath=1, p=1)[0]
                    compName= objName + '.f[' + str(i) + ']'
                    NGonList.append(compName)
    
            
            iter.next()
        if NGonList:
            errorCount+=1
            errorNodeList.append(node)
            AllNgonList.append(NGonList)

    return (errorCount, errorNodeList, AllNgonList)
    
def faceNormal():
    # check if there are reversed normal faces
    allObjList= cmds.ls(type='mesh')
    cmds.select(allObjList)
    cmds.polySelectConstraint( m=3, t=2, af=1 )




def lockedVertex(nodeList):
    # check if there are locked normal vertex
    errorCount=0
    errorNodeList=[]
  
    # 메시 이름을 가져오기
    for OMnode in nodeList:
        mesh_name = OMnode.shapeName
        selection_list = om.MSelectionList()
        selection_list.add(mesh_name)
        dag_path = selection_list.getDagPath(0)

        # 메시 데이터 접근
        mesh_fn = om.MFnMesh(dag_path)
        vertex_count = mesh_fn.numVertices

        Islocked = False
        locked_vertices = []
        for i in range(vertex_count):
            locked = mesh_fn.isNormalLocked(i)
            if locked:
                Islocked = True
                errorNodeList.append(OMnode)
                errorCount+=1
                break


    return (errorCount, errorNodeList)

def vertexInit(nodeList):
    # 입력된 nodeList가 비어 있는지 확인
    if not nodeList:
        print("nodeList가 비어 있습니다.")
        return
    
    errorCount=0
    errorNodeList=[]
    AllMovedVertexList=[]

    # 각 메시에 대해 처리
    for OMnode in nodeList:
        nodeName= OMnode.selectedNodeName
        shapeName= OMnode.shapeName
        isVertexInit=True
     
        try:
            # MSelectionList에 현재 메시 추가
            selection = om.MSelectionList()
            selection.add(shapeName)

            # DAG Path 가져오기
            dag_path = selection.getDagPath(0)

            # Mesh Shape 확인
            if not dag_path.hasFn(om.MFn.kMesh):
                print(f"{nodeName}는 Mesh Shape이 아닙니다.")
                continue

            # 노드 가져오기
            node = dag_path.node()
            dep_fn = om.MFnDependencyNode(node)

            # pnts 플러그 가져오기
            try:
                pnts_plug = dep_fn.findPlug("pnts", False)
            except Exception as e:
                #print(f"{shapeName}에서 pnts 플러그를 찾을 수 없습니다: {e}")
                continue

            # 모든 논리적 인덱스 가져오기
            indices = pnts_plug.getExistingArrayAttributeIndices()
            #print(f"{shapeName}: {len(indices)}개의 요소가 pnts 플러그에 있습니다.")

            # 각 요소의 값을 읽어오기
            for idx in indices:
                element_plug = pnts_plug.elementByLogicalIndex(idx)
                x = element_plug.child(0).asFloat()  # x값
                y = element_plug.child(1).asFloat()  # y값
                z = element_plug.child(2).asFloat()  # z값
                if x!=0 or y!=0 or z!=0:
                    errorCount+=1
                    errorNodeList.append(OMnode)
                    isVertexInit = False
                    break
      
        except Exception as e:
            print(f"{nodeName} 처리 중 오류가 발생했습니다: {e}")
    return (errorCount, errorNodeList)

def revNormal(nodeList):
    # checkButton은 QPushbutton

    return (len(nodeList), nodeList)


def selfIntersect(nodeList):
    # check if there are self-intersecting faces

    return (len(nodeList), nodeList)

  

def objectIntersect(nodeList):
    # check if there are intersecting faces with other objects

    return (len(nodeList), nodeList)
