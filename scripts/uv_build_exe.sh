#!bin/bash
echo "This script was not tested"

pip install uv

uv init

uv add -r requirements.txt pyinstaller

uv sync

uv run pyinstaller --onedir -n "movie_viewer" --icon="assets\icon.ico" main.py