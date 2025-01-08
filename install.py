# Install tool to Maya shelf without copying the script

import os
import maya.cmds as cmds
import maya.mel as mel
import sys

def onMayaDroppedPythonFile(*args):
    try:
        # 현재 스크립트가 든 폴더의 한 단계 상위 경로
        installer_directory = os.path.dirname(__file__)
        pkg_path = os.path.dirname(installer_directory)
        icon_path = os.path.join(installer_directory, "icon.png")

        # Shelf 버튼 이름
        button_name = "AssetCheck"

        # 현재 활성화된 Shelf 확인
        current_shelf = mel.eval("string $currentShelf = `tabLayout -query -selectTab $gShelfTopLevel`;")
        cmds.setParent(current_shelf)

        # Shelf에 추가될 실행 명령
        tool_script = f"""
import sys
import os

tool_dir = r"{pkg_path}"

if tool_dir not in sys.path:
    sys.path.append(tool_dir)

if 'AssetCheck.AssetCheck_main' in sys.modules:
    print("Reloading Module")
    import importlib
    importlib.reload(sys.modules['AssetCheck.AssetCheck_main'])

import AssetCheck.AssetCheck_main as AssetCheck_main
AssetCheck_main.run()
"""

        # Shelf 버튼 생성
        cmds.shelfButton(
            command=tool_script,
            ann="Asset Check Tool",  # 버튼 설명 (Tooltip)
            label=button_name,          # 버튼 라벨
            image=icon_path,            # 버튼 아이콘
            sourceType="python",        # 실행 타입
            iol=button_name             # 아이콘 라벨
        )

    except Exception as e:
        cmds.confirmDialog(
            message=f"Installation failed: {e}",
            icon="warning",
            title="ERROR"
        )

if __name__ == "__main__":
    # 기존 install.py 캐싱 제거
    module_name = os.path.splitext(os.path.basename(__file__))[0]
    if module_name in sys.modules:
        print(f"Reloading {module_name}")
        import importlib
        importlib.reload(sys.modules[module_name])
    
    print("Testing the installation script.")
    onMayaDroppedPythonFile()
