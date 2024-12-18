import sys

rootDir= "D:\myScript\maya"


if rootDir not in sys.path:
    sys.path.append(rootDir)


if 'AssetCheck.AssetCheck_main' in sys.modules:
    print("deldeted Modules")
    del sys.modules['AssetCheck.AssetCheck_main']
    
import AssetCheck.AssetCheck_main as AssetCheck_main

AssetCheck_main.run()
