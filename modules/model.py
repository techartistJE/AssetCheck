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
            AllNgonList+=NGonList

    return (errorCount, errorNodeList, AllNgonList)
    
def faceNormal():
    # check if there are reversed normal faces
    allObjList= cmds.ls(type='mesh')
    cmds.select(allObjList)
    cmds.polySelectConstraint( m=3, t=2, af=1 )


def namespace():
    userDefinedNS=[]
    all_ns=mc.namespaceInfo(listOnlyNamespaces=True)
    # exclude default namespaces : [u'UI', u'shared']
    for ns in all_ns:
        if ns not in ['UI', 'shared']:
            userDefinedNS.append(ns)

    return userDefinedNS
    
def namespace_remove():
    userDefinedNS=namespace()
    for ns in userDefinedNS:
        cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)


def objectPivot():
    # check each pivot of objects is at world origin
    # if not, move pivot to world origin
    
    
    # modelList=cmds.ls(type='mesh')
    pass