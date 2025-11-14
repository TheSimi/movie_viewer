pip install uv

uv init

uv add -r requirements.txt pyinstaller

uv sync

Write-Output "It is recommended that you manually delete the dist and build folders now"
Remove-Item /S dist
Remove-Item /S build
uv run pyinstaller --onedir -n "movie_viewer" --windowed --icon="assets\icon.ico" main.py

Copy-Item .env dist\movie_viewer