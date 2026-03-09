pip install uv

uv sync

Write-Output "It is recommended that you manually delete the dist and build folders now"
Remove-Item main.build
Remove-Item main.dist
uv run nuitka --mode=onefile --windows-console-mode=attach --windows-icon-from-ico=assets\icon.ico --enable-plugin=pyqt6 --product-name="movie_viewer" --product-version=0.3.0 --file-description="Watch downloaded movies and shows easly" --zig main.py

Copy-Item .env main.dist\.env
Rename-Item main.dist\main.exe movie_viewer.exe