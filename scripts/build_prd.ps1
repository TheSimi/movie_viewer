pip install uv

uv sync --no-dev --group pyinstaller

Write-Output "It is recommended that you manually delete the dist and build folders now"
Remove-Item build
Remove-Item dist
uv run pyinstaller --onedir -n "movie_viewer" --noconsole --icon="assets\icon.ico" main.py

Copy-Item config.json dist\movie_viewer\config.json