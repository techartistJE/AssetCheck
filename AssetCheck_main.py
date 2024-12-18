from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import maya.OpenMayaUI as mui
import maya.cmds as cmds


import shiboken2
import sys
import os

try:
    RootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pkgPath = os.path.dirname(os.path.abspath(__file__))

except:
    pkgPath = 'D:\myScript\maya\AssetCheck'



import AssetCheck.ui.AssetCheck_ui as AssetCheck_ui
import AssetCheck.modules.modelcheck as modelcheck


if sys.version_info > (3, 7, 0):
    import importlib
    importlib.reload(AssetCheck_ui)
    importlib.reload(modelcheck)


else:
    import imp
    imp.reload(AssetCheck_ui)
    imp.reload(modelcheck)



def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if sys.version_info >= (3, 0):
        return shiboken2.wrapInstance(int(ptr), QWidget)
    else:
        return shiboken2.wrapInstance(long(ptr), QWidget)

class mainWin(QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__(parent =getMayaWindow() )
        self.setObjectName("AssetCheck_win")
        self.setWindowTitle("AssetCheck")

        self.ui = AssetCheck_ui.AssetCheck_WidgetUI()
        self.setCentralWidget(self.ui)

        self.resize(600, 600)
        self.ui.topGroupLineEdit.setText(modelcheck.topGroup_check())


def run():
    
    if cmds.window("AssetCheck_win", exists = True):
        
        cmds.deleteUI("AssetCheck_win")


    ToolWin = mainWin()
    ToolWin.show()



if __name__ == "__main__":
    run()