pip install -r requirements.txt
pip install pyinstaller

echo "It is recommended that you manually delete the dist and build folders now"
RMDIR /S dist
RMDIR /S build
pyinstaller --onedir -n "movie_viewer" --windowed --icon="assets\icon.ico" main.py

copy .env dist\movie_viewer