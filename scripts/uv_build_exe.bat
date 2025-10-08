pip install uv

uv init

uv add -r requirements.txt pyinstaller

uv sync

echo "It is recommended that you manually delete the dist and build folders now"
@RMDIR /S dist
@RMDIR /S build
uv run pyinstaller --onedir -n "movie_viewer" --icon="assets\icon.ico" main.py

copy .env dist\movie_viewer