from maya import OpenMaya
import maya.cmds as cmds



# Simple function using OpenMaya
# targetName should be a string and Transform (DagNode) or other type of node (dependency node)
class SimpleOMObject(object):
    def __init__(self, nodeName):
        self.selectedNodeName= nodeName
        self.transformName = None
        self.ShapeName = None
        self.coreNodeName = nodeName
        self.ConnectedDeformerAsDeformed = []
        self.ConnectedDeformerAsDeformer = []
        self.IsShape = False
        self.IsDeformer = False
        self.IsDeformed = False
        self.objectType = None
        self.compTypeTag= None
        # if it has shape node, get the type of the object using shape node, otherwise use the object type

        self.deformerType= ['blendShape', 'wire', 'ffd', 'cluster', 'skinCluster']
        self.deformerRefType= ['clusterHandle', 'joint', 'mesh', 'nurbsCurve', 'nurbsSurface', 'lattice']
        self.deformedType= ['mesh', 'nurbsCurve', 'nurbsSurface', 'lattice']

        self.getObjectState(nodeName)
        self.getCompTypeTag()
        self.setOMObjectTypes()
        self.getConnectedDeformer()

    def shortName(self, nodeName ):
        # if node name is long like |group1|group2|group3|nodeName, return only nodeName
        if '|' in nodeName:
            nodeName = nodeName.split('|')[-1]
        return nodeName
    
    def getObjectState(self, nodeName):
        OMObject = self.nameToOMObject(nodeName)
        if OMObject.hasFn(OpenMaya.MFn.kDagNode):
            #print("DagNode")
            currentNodeType= cmds.nodeType(nodeName)
            if currentNodeType == 'transform':
                if cmds.listRelatives(nodeName, shapes=True):
                    self.transformName = nodeName
                    self.ShapeName = cmds.listRelatives(nodeName, fullPath=1,shapes=True)[0]
                    
                    self.objectType= cmds.nodeType(self.ShapeName)

                    self.coreNodeName= self.ShapeName
                else:               
                    self.transformName = nodeName
                    self.objectType= cmds.nodeType(nodeName)
                    self.coreNodeName= nodeName
            else:
                # shape node has a transform node as a parent
                # ex1 parent: deformerHandle, child: deformerShape
                # ex2 parent: transform, child: locatorShape
                # ex3 parent: transform, child: meshShape
                # ex4 parent: transform, child: nurbsCurveShape
                # ex5 parent: light, child: lightShape

                # not shape node but also not transform node (ex: joint)
                # caution: paretnt of parent: transform, parent: joint3, child: joint4
                # caution: Constraint node (point, orient, scale, aim) can have transform node as a parent
                
                parentNode = cmds.listRelatives(nodeName, p=True)
                if parentNode:
                    if cmds.nodeType(parentNode[0]) == 'transform':

                        self.transformName = parentNode[0]
                        self.ShapeName = nodeName
                        self.IsShape = True
                        self.objectType= cmds.nodeType(nodeName)
                        self.coreNodeName= nodeName
                        if cmds.nodeType(nodeName) == 'joint':
                            self.objectType= 'joint'
                            self.transformName = None
                            self.ShapeName = None
                            self.IsShape = False
                        elif "Constraint" in cmds.nodeType(nodeName):
                            self.objectType= 'constraint'
                            self.transformName = None
                            self.ShapeName = None
                            self.IsShape = False
                    self.transformName = parentNode[0]

 

        else:
            #print("Not Dag & DependencyNode")
            self.objectType = cmds.nodeType(nodeName)
            self.coreNodeName= nodeName


    def getConnectedDeformer(self):
        if self.objectType  == 'joint':
            self.ConnectedDeformerAsDeformer.extend( self.getConnectedDepNode(self.coreNodeName, 'joint', downstream=True) )
        elif self.objectType == 'cluster' or self.objectType == 'clusterHandle':
            self.ConnectedDeformerAsDeformer.extend( self.getConnectedDepNode(self.coreNodeName, 'cluster', downstream=True) )
        elif self.objectType == 'nurbsCurve':
            self.ConnectedDeformerAsDeformer.extend( self.getConnectedDepNode(self.coreNodeName, 'wire', downstream=True) )
        elif self.objectType == 'lattice':
            self.ConnectedDeformerAsDeformer.extend( [self.getConnectedDepNode(self.coreNodeName, 'ffd', downstream=True)[0]] )
        elif self.objectType in self.deformedType:
            for type in self.deformerType:
                self.ConnectedDeformerAsDeformed.extend( self.getConnectedDepNode(self.coreNodeName, type, upstream=True) )
          
        if self.ConnectedDeformerAsDeformer:
            self.IsDeformer = True
        if self.ConnectedDeformerAsDeformed:
            self.IsDeformed = True


    def getConnectedDepNode(self, nodeName, nodeType, upstream=False, downstream=False):
        OMObject = self.nameToOMObject(nodeName)
        OMNodeType= self.OMObject_types[nodeType]

        if not upstream and not downstream:
            dependency_graph = OpenMaya.MItDependencyGraph(OMObject, OMNodeType)
        if upstream and not downstream:
            dependency_graph = OpenMaya.MItDependencyGraph(OMObject, OMNodeType,
                                                        OpenMaya.MItDependencyGraph.kUpstream,
                                                        OpenMaya.MItDependencyGraph.kDepthFirst,
                                                        OpenMaya.MItDependencyGraph.kNodeLevel)
        if not upstream and downstream:
            dependency_graph = OpenMaya.MItDependencyGraph(OMObject, OMNodeType,
                                                        OpenMaya.MItDependencyGraph.kDownstream,
                                                        OpenMaya.MItDependencyGraph.kDepthFirst,
                                                        OpenMaya.MItDependencyGraph.kNodeLevel)
                
        result = []

        while not dependency_graph.isDone():
            current_item = dependency_graph.currentItem()
            result.append(self.OMObjectToName(current_item))
            dependency_graph.next()
        return result
    
    def getCompTypeTag(self):
        if self.objectType == 'mesh':
            self.compTypeTag= 'vtx'
        elif self.objectType == 'nurbsCurve' or self.objectType == 'nurbsSurface':
            self.compTypeTag= 'cv'
        elif self.objectType == 'lattice':
            self.compTypeTag= 'pt'
        else:
            self.compTypeTag= None

    def setOMObjectTypes(self):
        self.OMObject_types = {'mesh': OpenMaya.MFn.kMesh,
                             'blendShape': OpenMaya.MFn.kBlendShape,
                             'wire': OpenMaya.MFn.kWire,
                             'lattice': OpenMaya.MFn.kLattice,
                             'ffd': OpenMaya.MFn.kFFD,
                             'cluster': OpenMaya.MFn.kClusterFilter,
                             'clusterHandle': OpenMaya.MFn.kClusterFilter,
                             'skinCluster': OpenMaya.MFn.kSkinClusterFilter,
                             'joint': OpenMaya.MFn.kSkinClusterFilter,
                             'transform': OpenMaya.MFn.kTransform
                             }
   
    def nameToOMObject(self, nodeName ):
        selectionList = OpenMaya.MSelectionList()
        selectionList.add( nodeName )
        OMObject = OpenMaya.MObject()
        selectionList.getDependNode( 0, OMObject )
        return OMObject

    # function that finds a plug given a node object and plug name
    def AttrNameToOMNodePlug(self, OMObject, attrName ):
        depNodeFn = OpenMaya.MFnDependencyNode( OMObject )
        attrObject = depNodeFn.attribute( attrName )
        plug = OpenMaya.MPlug( OMObject, attrObject )
        return plug

    def OMObjectToDagPath(self, OMObject):
        # check if Object is compatible with the given Function Type.
        if not OMObject.hasFn(OpenMaya.MFn.kDagNode):
            return None
        depNodeFn = OpenMaya.MFnDagNode(OMObject)
        dagPath = OpenMaya.MDagPath()
        depNodeFn.getPath(dagPath)
        return dagPath
    
    def OMObjectToDGNode(self, OMObject):
        # check if Object is compatible with the given Function Type.
        if not OMObject.hasFn(OpenMaya.MFn.kDependencyNode):
            return None
        depNodeFn = OpenMaya.MFnDependencyNode(OMObject)
        return depNodeFn
    
    def nameToDagPath(self, name ):
        selectionList = OpenMaya.MSelectionList()
        selectionList.add( name )
        dagPath = OpenMaya.MDagPath()
        selectionList.getDagPath( 0, dagPath )
        return dagPath
    
    def nameToStrDagPath(self, name, unique= False ):
        selectionList = OpenMaya.MSelectionList()
        selectionList.add( name )
        dagPath = OpenMaya.MDagPath()
        selectionList.getDagPath( 0, dagPath )
        
        if unique:
            return dagPath.partialPathName()
        else:
            return dagPath.fullPathName()


    def OMObjectToName(self, OMObject):
        if isinstance(OMObject, OpenMaya.MDagPath):
            return OMObject.fullPathName()
        if isinstance(OMObject, OpenMaya.MObject):
            mfn_dependency_node = OpenMaya.MFnDependencyNode(OMObject)
            return mfn_dependency_node.name()

    
    def getPlug(self, nodeName, attrName):
        mplug = OpenMaya.MPlug()
        mselection = OpenMaya.MSelectionList()
        mselection.add("%s.%s" % (nodeName, attrName))
        mselection.getPlug(0, mplug)
        return mplug

    def getOriginShape(self, shapeName):
        objectShape= shapeName
        if cmds.nodeType(objectShape) == 'mesh':
            originShape= cmds.geometryAttrInfo(objectShape +'.inMesh', og=1)
        elif cmds.nodeType(objectShape) == 'nurbsCurve' or cmds.nodeType(objectShape) == 'nurbsSurface':
            originShape= cmds.geometryAttrInfo(objectShape +'.create', og=1)
        elif cmds.nodeType(objectShape) == 'lattice':
            originShape= cmds.geometryAttrInfo(objectShape +'.latticeInput', og=1)
        if originShape:
                originShape= originShape[0]
                originShape= originShape.split('.')[0]
        else:
            originShape= None

        return (originShape)