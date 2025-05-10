import os

from media import Media

def get_file_list(folder_list: list, file_in_folder_func: callable, file_class: Media):
    file_path_list = []
    for folder in folder_list:
        file_path_list.extend(file_in_folder_func(folder))
    file_list = []
    for file in file_path_list:
        file_list.append(file_class(file))
    return file_list

def get_shows_in_folder(folder: str):
    show_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isdir(file_path):
            if file.startswith('-'):
                show_list.extend(
                    get_shows_in_folder(file_path)
                )
            else:
                show_list.append(file_path)
    return show_list

def get_movies_in_folder(folder: str):
    movie_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            movie_list.append(file_path)
        elif os.path.isdir(file_path):
            if file.startswith('-'):
                movie_list.append(file_path)
            else:
                movie_list.extend(
                    get_movies_in_folder(file_path)
                )
    return movie_list
