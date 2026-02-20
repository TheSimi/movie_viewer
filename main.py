# import os
# import dotenv
# import qt_material as qm
# from PyQt6.QtWidgets import QApplication

# from const import MOVIE_FOLDERS, SHOW_FOLDERS, CACHE_DIR, CACHE_VERSION
# from components.main_window import MainGUIWindow
# from utils.cache_utilis import clear_all_cache, make_cache_version_file

# def check_cache() -> bool:
#     if not os.path.exists(CACHE_DIR):
#         return False
#     version_file = os.path.join(CACHE_DIR, "version.txt")
#     if not os.path.exists(version_file):
#         return False
#     with open(version_file, 'r') as f:
#         version = f.read().strip()
#     return version == CACHE_VERSION

# def cache_version_handler() -> None:
#     if not check_cache():
#         os.makedirs(CACHE_DIR, exist_ok=True)
#         clear_all_cache()

#         # Update cache version
#         make_cache_version_file()

# def dotenv_check():
#     if not dotenv.find_dotenv():
#         with open('.env', 'w') as f:
#             f.write(
#                 'MOVIE_FOLDERS=""\n'
#                 'SHOW_FOLDERS=""\n'
#                 'MEDIA_PLAYER="vlc"\n'
#                 'SPEED="1"\n'
#             )

# def main():
#     dotenv_check()

#     app = QApplication([])
#     qm.apply_stylesheet(app, theme='dark_purple.xml')

#     cache_version_handler()

#     win = MainGUIWindow(movie_folders=MOVIE_FOLDERS, show_folders=SHOW_FOLDERS)
#     win.show()
#     win.showMaximized()

#     app.exec()

# if __name__ == "__main__":
#     main()

from media_classes.show import Show

show = Show("Attack on Titan")