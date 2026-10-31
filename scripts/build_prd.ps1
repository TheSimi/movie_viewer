pip install uv

uv sync --no-dev --group pyinstaller

Write-Output "It is recommended that you manually delete the dist and build folders now"
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
uv run pyinstaller --onedir -n "movie_viewer" --noconsole --icon="assets\icon.ico" --add-data "styles;styles" --add-data "assets;assets" main.py

Copy-Item config.json dist\movie_viewer\_internal\config.json -ErrorAction SilentlyContinue
