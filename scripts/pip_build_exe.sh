#!bin/bash
echo "This script was not tested"

pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onedir -n "movie_viewer" --windowed --icon="assets\icon.ico" main.py