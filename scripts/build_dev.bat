pip install uv

uv sync --no-dev --group pyinstaller

echo "It is recommended that you manually delete the dist and build folders now"
@RMDIR /S /Q build 2>nul
@RMDIR /S /Q dist 2>nul
uv run pyinstaller --onedir -n "movie_viewer" --icon="assets\icon.ico" --add-data "styles;styles" --add-data "assets;assets" main.py

copy config.json dist\movie_viewer\_internal\config.json 2>nul
