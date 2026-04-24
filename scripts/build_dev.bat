pip install uv

uv sync --no-dev --group pyinstaller

echo "It is recommended that you manually delete the dist and build folders now"
@RMDIR /S build
@RMDIR /S dist
uv run pyinstaller --onedir -n "movie_viewer" --icon="assets\icon.ico" main.py

copy config.json dist\movie_viewer\config.json