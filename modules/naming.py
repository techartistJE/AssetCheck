# -*- coding: utf-8 -*-
import maya.cmds as cmds


def duplicatedNames(nodeList):
    # check if there are duplicated names in the scene
    errorCount=0
    errorNodeList=[]
    AllDuplicatedList=[]
    for node in nodeList:
        shortName= node.shortName(node.selectedNodeName)
        nodeList= cmds.ls(shortName, long=1)
        if len(nodeList)>1:
            errorCount+=1
            errorNodeList.append(node)
            nodeList.remove(node.selectedNodeName)
            AllDuplicatedList.append(nodeList)

    return (errorCount, errorNodeList, AllDuplicatedList)


def nameSpace(_inputList):
    # check if namespace is in the scene
    errorCount=0

    defaultNamespaces= ['UI', 'shared']
    namespaces = cmds.namespaceInfo(lon=True, recurse=True) or []
    namespaces = [ns for ns in namespaces if ns not in defaultNamespaces]
    
    if namespaces:
    
        errorCount+=1

    return (errorCount, ["scene"], namespaces)
    


def shapeName(nodeList):
    # check if shape name is named properly
    # pCylinder1 -> pCylinderShape1
    # pCylinder -> pCylinderShape
    # pCylinder10 -> pCylinderShape10
    errorCount=0
    errorNodeList=[]
   
    for node in nodeList:
        if node.ShapeName :
            nodeName= node.selectedNodeName
            shapeName= node.shortName(node.ShapeName)
            # from back to front
            refNodeName= shapeName.replace('Shape', '', -1)
            if node.shortName(node.selectedNodeName) != refNodeName:
                errorCount+=1
                errorNodeList.append(node)
    return (errorCount, errorNodeList)




    