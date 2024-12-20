import maya.api.OpenMaya as om
import maya.cmds as cmds
# fuctions for modeling file check




def ngonFace():
    allObjList= cmds.ls(type='mesh')
    cmds.select(allObjList)
    NGonList=[]
    cmds.selectMode(  component=True )
    cmds.selectType(polymeshFace=True)
    cmds.polySelectConstraint( size=3 )
    cmds.polySelectConstraint( m=3 )

    NGonList= mc.ls(sl=1)

    # Constraint Nothing : 0 
    cmds.polySelectConstraint( m=0 )
    cmds.selectMode( object=True )

    print(NGonList)
    cmds.select(clear=True)

    if NGonList:
        return NGonList
    else:    
        return None

def ngonFace_om():
    allObjList= cmds.ls(type='mesh')
    cmds.select(allObjList)
    selList= om.MGlobal.getActiveSelectionList()

    NGonList=[]
    iter = om.MItSelectionList(selList, om.MFn.kMesh)

    while not iter.isDone():
        dagPath = iter.getDagPath()
        mesh = om.MFnMesh(dagPath)
        
        for i in range(mesh.numPolygons):
            vtxList = mesh.getPolygonVertices(i)
            if len(vtxList) > 4:
                objName= cmds.listRelatives('pCubeShape3', p=1)[0]
                NGonList.append(objName +'.f['+ str(i) +']')
                #print(f"Ngons found in {dagPath.partialPathName()}.f[{i}]")
        
        iter.next()
    cmds.select(clear=True)

    if NGonList:
        return NGonList
    else:
        return None
    
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
        mc.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)


def objectPivot():
    # check each pivot of objects is at world origin
    # if not, move pivot to world origin
    
    
    # modelList=cmds.ls(type='mesh')
    pass