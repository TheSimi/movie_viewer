pip install uv

uv sync --no-dev

echo "It is recommended that you manually delete the dist and build folders now"
@RMDIR /S main.build
@RMDIR /S main.dist
uv run nuitka --mode=onefile --windows-console-mode=attach --windows-icon-from-ico=assets\icon.ico --enable-plugin=pyqt6 --product-name="movie_viewer" --product-version=0.3.0 --file-description="Watch downloaded movies and shows easly" --zig main.py

copy .env main.dist\.env
ren .\main.dist\main.exe movie_viewer.exe